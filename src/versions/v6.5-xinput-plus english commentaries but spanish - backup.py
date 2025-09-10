#!/usr/bin/env python3
# xinput-plus.py / v6.4
# PyQt6 GUI to tweak cursor speed via xinput (Xorg)
#
# What's new in 6.4:
# - Visible devices whitelist, editable from the UI.
# - "Show only whitelist" toggle.
# - Profiles by ID in addition to by name ("Save by ID" checkbox).
# - Disambiguation by ID, local icon, virtual/master pointers filtered out.
# - Check for 'libinput Accel Speed' before applying; fallback to CTM if missing.
# - Auto-apply settings on startup.
#
# Configuration (~/.config/xinput-plus.json) uses this structure:
# {
#   "by_name": { "<name>": {"speed": float, "extended": bool}, ... },
#   "by_id":   { "<id>":   {"speed": float, "extended": bool}, ... },
#   "_whitelist": [ {"name": "<name>", "id": "<id>"}, ... ],
#   "_show_only_whitelist": true/false
# }
#
# Automatic migration: if an old flat mapping is found ({name: {speed, extended}})
# it is moved under "by_name".
#
# NOTE: UI strings remain in Spanish by request; only code comments are in English
# to aid contributors.

import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Set

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QSlider, QPushButton, QMessageBox, QCheckBox, QDialog, QDialogButtonBox,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

CONFIG_PATH = Path.home() / ".config" / "xinput-plus.json"
ICON_PATH = Path(__file__).parent / "src" / "emucon.svg"


def debug(msg: str) -> None:
    """Prints a namespaced debug line to stdout."""
    print(f"[xinput-plus] {msg}")


def _migrate_old_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrades a legacy flat config into the new by_name/by_id schema."""
    if not isinstance(cfg, dict):
        return {"by_name": {}, "by_id": {}, "_whitelist": [], "_show_only_whitelist": False}

    # Already in new format
    if "by_name" in cfg or "by_id" in cfg:
        cfg.setdefault("by_name", {})
        cfg.setdefault("by_id", {})
        cfg.setdefault("_whitelist", [])
        cfg.setdefault("_show_only_whitelist", False)
        return cfg

    # Migrate from flat {name: {speed, extended}}
    by_name = {}
    for k, v in cfg.items():
        if isinstance(v, dict) and ("speed" in v or "extended" in v):
            by_name[k] = v
    return {
        "by_name": by_name,
        "by_id": {},
        "_whitelist": [],
        "_show_only_whitelist": False,
    }


class WhitelistDialog(QDialog):
    """Dialog to edit the visible-devices whitelist (entries are (name, id))."""
    def __init__(self, parent: QWidget, devices: List[dict], whitelist: Set[Tuple[str, str]]):
        super().__init__(parent)
        self.setWindowTitle("Editar lista blanca de dispositivos")
        self.setMinimumWidth(520)
        self._devices = devices
        self._initial = whitelist

        layout = QVBoxLayout(self)

        info = QLabel("Selecciona los dispositivos que deseas mantener visibles.\n"
                      "Si dejas la lista vacía, se mostrarán todos.")
        layout.addWidget(info)

        # Build a checkable list with all current devices; pre-check those in whitelist
        self.listw = QListWidget()
        self.listw.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for dev in devices:
            name, did = dev["name"], dev["id"]
            text = f"{name}  (id {did})"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if (name, did) in whitelist else Qt.CheckState.Unchecked)
            # Store device data for retrieval
            item.setData(Qt.ItemDataRole.UserRole, did)
            item.setData(Qt.ItemDataRole.UserRole + 1, name)
            self.listw.addItem(item)
        layout.addWidget(self.listw)

        # OK/Cancel buttons
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def result_whitelist(self) -> List[dict]:
        """Returns the whitelist as a list of dicts [{'name':..., 'id':...}, ...]."""
        res = []
        for i in range(self.listw.count()):
            item = self.listw.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                res.append({"name": item.data(Qt.ItemDataRole.UserRole + 1),
                            "id":   item.data(Qt.ItemDataRole.UserRole)})
        return res


class LibinputGUI(QWidget):
    """Main window for xinput-plus."""
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("xinput-plus")
        self.setMinimumWidth(800)

        # Window icon (local svg preferred; fallback to theme icon)
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))
        else:
            debug(f"Advertencia: No se encontró el ícono en {ICON_PATH}")
            try:
                self.setWindowIcon(QIcon.fromTheme("input-mouse"))
            except Exception:
                pass

        # State
        self.all_devices: List[dict] = []          # all slave pointers detected
        self.visible_devices: List[dict] = []      # devices shown in the list (after whitelist filter)
        self.selected_device_name: str = ""
        self.selected_device_id: Optional[str] = None

        # Config
        self.config = self.load_config()

        # UI
        self.build_ui()
        self.load_devices()

        # Auto-apply after a short delay to avoid session-start races
        QTimer.singleShot(1000, self.apply_all_configs)

    # --------------------------
    # Persistence
    # --------------------------
    def load_config(self) -> Dict[str, Any]:
        """Loads config JSON and migrates legacy shape if needed."""
        try:
            if CONFIG_PATH.exists():
                raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                return _migrate_old_config(raw)
        except Exception as e:
            debug(f"Error leyendo config: {e}")
        return {"by_name": {}, "by_id": {}, "_whitelist": [], "_show_only_whitelist": False}

    def save_config(self) -> None:
        """Persists current config JSON to disk."""
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(self.config, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            debug(f"Error guardando config: {e}")

    # --------------------------
    # UI
    # --------------------------
    def build_ui(self) -> None:
        """Constructs the main layout and binds signals."""
        layout = QHBoxLayout(self)

        # Device list (left column)
        self.device_list = QListWidget()
        self.device_list.itemSelectionChanged.connect(self.on_device_selected)
        layout.addWidget(self.device_list, 2)

        # Right panel with controls
        right = QVBoxLayout()

        self.label_device = QLabel("Seleccione un dispositivo")
        right.addWidget(self.label_device)

        self.extended_speed_cb = QCheckBox("Modo extendido (CTM)")
        self.extended_speed_cb.toggled.connect(self.on_extended_toggled)
        right.addWidget(self.extended_speed_cb)

        self.profile_by_id_cb = QCheckBox("Guardar por ID (perfil específico)")
        right.addWidget(self.profile_by_id_cb)

        self.label_speed = QLabel("Velocidad: 0.00")
        right.addWidget(self.label_speed)

        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setMinimum(-100)
        self.slider_speed.setMaximum(100)
        self.slider_speed.setValue(0)
        self.slider_speed.setSingleStep(1)
        self.slider_speed.valueChanged.connect(self.on_speed_changed)
        right.addWidget(self.slider_speed)

        # Buttons row
        btns = QHBoxLayout()
        self.btn_refresh = QPushButton("🔄 Actualizar")
        self.btn_refresh.clicked.connect(self.load_devices)
        btns.addWidget(self.btn_refresh)

        self.btn_reapply = QPushButton("⚙️ Reaplicar todo")
        self.btn_reapply.clicked.connect(self.apply_all_configs)
        btns.addWidget(self.btn_reapply)

        # Whitelist controls
        self.show_only_whitelist_cb = QCheckBox("Mostrar sólo whitelist")
        self.show_only_whitelist_cb.setChecked(bool(self.config.get("_show_only_whitelist", False)))
        self.show_only_whitelist_cb.toggled.connect(self.on_toggle_show_only_whitelist)
        btns.addWidget(self.show_only_whitelist_cb)

        self.btn_edit_whitelist = QPushButton("✏️ Editar whitelist")
        self.btn_edit_whitelist.clicked.connect(self.open_whitelist_dialog)
        btns.addWidget(self.btn_edit_whitelist)

        right.addLayout(btns)
        right.addStretch(1)

        layout.addLayout(right, 3)

    # --------------------------
    # Device discovery & list
    # --------------------------
    def _is_virtual_pointer_line(self, raw: str) -> bool:
        """Returns True for Virtual/Master/XTEST pointers we should hide/ignore."""
        low = raw.lower()
        if "master pointer" in low:
            return True
        if "virtual core" in low:
            return True
        if "xtest" in low:
            return True
        return False

    def _parse_id_from_short_line(self, line: str) -> Optional[str]:
        """Parses 'id=<digits>' from a line produced by `xinput list --short`."""
        try:
            left = line.split("id=", 1)[1]
            digits = ""
            for ch in left:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            return digits or None
        except Exception:
            return None

    def _whitelist_set(self) -> Set[Tuple[str, str]]:
        """Returns the whitelist as a set of (name, id) tuples for quick filtering."""
        wl = self.config.get("_whitelist", [])
        out: Set[Tuple[str, str]] = set()
        if isinstance(wl, list):
            for d in wl:
                try:
                    out.add((str(d["name"]), str(d["id"])))
                except Exception:
                    continue
        return out

    def _compute_visible(self) -> None:
        """Computes visible_devices by applying the whitelist (if enabled and non-empty)."""
        show_only = bool(self.config.get("_show_only_whitelist", False))
        wl = self._whitelist_set()

        if show_only and wl:
            self.visible_devices = [d for d in self.all_devices if (d["name"], d["id"]) in wl]
        else:
            self.visible_devices = list(self.all_devices)

    def load_devices(self) -> None:
        """Scans all slave pointers via xinput, then repopulates the visible list."""
        self.all_devices = []
        self.device_list.clear()

        out = self.run_cmd(["xinput", "list", "--short"])
        if not out:
            QMessageBox.warning(
                self,
                "xinput",
                ("No se pudo obtener la lista de dispositivos."
                 "\n¿Está disponible xinput?")
            )
            return

        seen = set()
        for raw in out.splitlines():
            line = raw.strip()
            if "pointer" not in line:
                continue
            if self._is_virtual_pointer_line(line):
                continue

            # Strip leading decoration chars, then extract name + id
            clean = line
            while clean and (clean[0] in "⎡⎣⎜⎟↳⎜⎢⎥" or clean[0].isspace()):
                clean = clean[1:]
            name = clean.split("id=")[0].rstrip()
            dev_id = self._parse_id_from_short_line(clean)

            if not name or not dev_id:
                continue

            key = (name, dev_id)
            if key in seen:
                continue
            seen.add(key)

            self.all_devices.append({"name": name, "id": dev_id})

        # Apply whitelist logic to compute visible_devices
        self._compute_visible()

        # Paint the list with "Name  (id N)" and store id/name in item data roles
        for dev in self.visible_devices:
            name, did = dev["name"], dev["id"]
            item_text = f"{name}  (id {did})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, did)
            item.setData(Qt.ItemDataRole.UserRole + 1, name)
            self.device_list.addItem(item)

        # Default selection for convenience
        if self.device_list.count() > 0:
            self.device_list.setCurrentRow(0)

    # --------------------------
    # Config lookup & application
    # --------------------------
    def device_has_prop(self, device_id: str, prop_name: str) -> bool:
        """Returns True if the given property appears in `xinput list-props <id>` output."""
        out = self.run_cmd(["xinput", "list-props", device_id])
        return (prop_name in out) if out else False

    def run_cmd(self, cmd: list[str]) -> str:
        """Executes a command and returns stdout as text; logs errors to debug()."""
        try:
            debug(f"Ejecutando: {' '.join(cmd)}")
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            return out.strip()
        except subprocess.CalledProcessError as e:
            debug(f"Error ejecutando {' '.join(cmd)}:\n{e.output.strip()}")
            return ""

    def get_settings_for(self, name: str, dev_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Fetches settings giving priority to ID profile, falling back to name profile."""
        if dev_id and dev_id in self.config.get("by_id", {}):
            return self.config["by_id"][dev_id]
        if name in self.config.get("by_name", {}):
            return self.config["by_name"][name]
        return None

    def _apply_to_device_id(self, device_id: str, speed: float, extended: bool) -> None:
        """Applies either libinput Accel Speed or CTM matrix to a specific device id."""
        if extended:
            # CTM scale is clamped to prevent freezing (avoid zero/near-zero)
            scale = max(speed, -5.0) if speed < 0 else max(min(speed, 5.0), 0.05)
            matrix = f"{scale} 0 0 0 {scale} 0 0 0 1"
            self.run_cmd(["xinput", "--set-prop", device_id, "Coordinate Transformation Matrix", *matrix.split()])
        else:
            if self.device_has_prop(device_id, "libinput Accel Speed"):
                self.run_cmd(["xinput", "--set-prop", device_id, "libinput Accel Speed", f"{speed:.2f}"])
            else:
                debug("Propiedad 'libinput Accel Speed' no disponible; usando CTM como alternativa.")
                scale = max(speed, -5.0) if speed < 0 else max(min(speed, 5.0), 0.05)
                matrix = f"{scale} 0 0 0 {scale} 0 0 0 1"
                self.run_cmd(["xinput", "--set-prop", device_id, "Coordinate Transformation Matrix", *matrix.split()])

    def apply_config_to_device(self, name: str) -> None:
        """Applies the 'by_name' profile to all devices currently reporting that name."""
        cfg = self.get_settings_for(name, None)  # name profile
        if not cfg:
            return
        speed = float(cfg.get("speed", 0.0))
        extended = bool(cfg.get("extended", False))

        # Apply to all matching name devices (from the full device set)
        for dev in self.all_devices:
            if dev["name"] == name:
                self._apply_to_device_id(dev["id"], speed, extended)

        # Fallback: try pointer:<name> to resolve current ids if discovery hasn't caught up
        out = self.run_cmd(["xinput", "list", "--id-only", f"pointer:{name}"])
        if out:
            for dev_id in out.split():
                self._apply_to_device_id(dev_id, speed, extended)

    def apply_all_configs(self) -> None:
        """Applies all known profiles (by id first, then by name) to connected devices."""
        if not self.all_devices:
            self.load_devices()

        # 1) Apply per-ID profiles (highest priority)
        for dev in self.all_devices:
            did = dev["id"]
            cfg = self.config.get("by_id", {}).get(did)
            if cfg:
                self._apply_to_device_id(did, float(cfg.get("speed", 0.0)), bool(cfg.get("extended", False)))

        # 2) Apply per-name profiles to devices that didn't get an ID profile
        applied_ids = {d["id"] for d in self.all_devices if d["id"] in self.config.get("by_id", {})}
        for dev in self.all_devices:
            if dev["id"] in applied_ids:
                continue
            name = dev["name"]
            cfg = self.config.get("by_name", {}).get(name)
            if cfg:
                self._apply_to_device_id(dev["id"], float(cfg.get("speed", 0.0)), bool(cfg.get("extended", False)))

        # Ensure something is selected in the UI
        if self.device_list.currentRow() < 0 and self.device_list.count() > 0:
            self.device_list.setCurrentRow(0)

    # --------------------------
    # UI slots
    # --------------------------
    def on_device_selected(self) -> None:
        """Syncs UI state when a device list item becomes selected; applies stored profile."""
        items = self.device_list.selectedItems()
        if not items:
            return
        item = items[0]
        self.selected_device_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_device_name = item.data(Qt.ItemDataRole.UserRole + 1)

        name, did = self.selected_device_name, self.selected_device_id
        cfg = self.get_settings_for(name, did)

        if cfg:
            speed = float(cfg.get("speed", 0.0))
            extended = bool(cfg.get("extended", False))
        else:
            speed = 0.0
            extended = False

        # Auto-check "Save by ID" if we already have a per-ID profile for this device
        self.profile_by_id_cb.blockSignals(True)
        self.profile_by_id_cb.setChecked(bool(did and did in self.config.get("by_id", {})))
        self.profile_by_id_cb.blockSignals(False)

        self.extended_speed_cb.blockSignals(True)
        self.extended_speed_cb.setChecked(extended)
        self.extended_speed_cb.blockSignals(False)

        self.slider_speed.blockSignals(True)
        self.slider_speed.setMinimum(-200 if extended else -100)
        self.slider_speed.setMaximum( 200 if extended else  100)
        self.slider_speed.setValue(int(round(speed * 100)))
        self.slider_speed.blockSignals(False)

        self.label_device.setText(f"Dispositivo: {name} (id {did})" if did else f"Dispositivo: {name}")
        self.label_speed.setText(f"Velocidad: {speed:.2f}")

        # Apply immediately to give instant feedback when selecting
        if did:
            self._apply_to_device_id(did, speed, extended)

    def on_speed_changed(self, value: int) -> None:
        """Persists current slider value and applies it to the selected device."""
        if not self.selected_device_name:
            return

        extended = self.extended_speed_cb.isChecked()
        speed = value / 100.0
        did = self.selected_device_id
        name = self.selected_device_name

        # Always store by name
        self.config.setdefault("by_name", {})
        self.config["by_name"].setdefault(name, {})
        self.config["by_name"][name]["speed"] = speed
        self.config["by_name"][name]["extended"] = extended

        # Optionally store by ID
        if self.profile_by_id_cb.isChecked() and did:
            self.config.setdefault("by_id", {})
            self.config["by_id"].setdefault(did, {})
            self.config["by_id"][did]["speed"] = speed
            self.config["by_id"][did]["extended"] = extended

        self.save_config()
        self.label_speed.setText(f"Velocidad: {speed:.2f}")

        # Apply to selected device by exact ID when available
        if did:
            self._apply_to_device_id(did, speed, extended)
        else:
            self.apply_config_to_device(name)

    def on_extended_toggled(self, checked: bool) -> None:
        """Adjusts slider range when toggling CTM mode; re-applies setting."""
        cur = self.slider_speed.value()
        if checked:
            self.slider_speed.setMinimum(-200)
            self.slider_speed.setMaximum(200)
            cur = int(cur * 2)
        else:
            self.slider_speed.setMinimum(-100)
            self.slider_speed.setMaximum(100)
            cur = int(cur / 2)

        # Clamp to range
        cur = max(self.slider_speed.minimum(), min(self.slider_speed.maximum(), cur))

        self.slider_speed.blockSignals(True)
        self.slider_speed.setValue(cur)
        self.slider_speed.blockSignals(False)

        # Re-apply with the new mode
        self.on_speed_changed(self.slider_speed.value())

    def on_toggle_show_only_whitelist(self, checked: bool) -> None:
        """Toggles the 'show only whitelist' mode and refreshes the device list."""
        self.config["_show_only_whitelist"] = bool(checked)
        self.save_config()
        self.load_devices()

    def open_whitelist_dialog(self) -> None:
        """Opens the whitelist editor dialog; saves and reloads on acceptance."""
        wl_set = self._whitelist_set()
        dlg = WhitelistDialog(self, self.all_devices, wl_set)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.config["_whitelist"] = dlg.result_whitelist()
            self.save_config()
            self.load_devices()


def main() -> int:
    app = QApplication(sys.argv)
    gui = LibinputGUI()
    gui.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
