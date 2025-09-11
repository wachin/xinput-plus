#!/usr/bin/env python3
# xinput-plus.py / v6.5 (full, corrected, i18n-ready)
# PyQt6 GUI to tweak pointer speed via xinput (Xorg only).
#
# Key features:
# - Whitelist of visible devices (by name+id), editable in a dialog.
# - "Show only whitelist" toggle.
# - Profiles by ID (device-specific) and by Name (fallback).
# - Filters out Virtual/Master/XTEST pointers.
# - Uses "libinput Accel Speed" when available; falls back to CTM matrix otherwise.
# - Applies saved configs automatically on startup (after a short delay).
# - English source strings with self.tr(...) for i18n; QTranslator loader keeps references.
#
# Config file (~/.config/xinput-plus.json):
# {
#   "by_name": { "<name>": {"speed": float, "extended": bool} },
#   "by_id":   { "<id>":   {"speed": float, "extended": bool} },
#   "_whitelist": [ {"name": "<name>", "id": "<id>"} ],
#   "_show_only_whitelist": true/false
# }
#
# NOTE: Wayland is not supported by xinput; run under Xorg.
# NOTE: This script expects compiled translations in ./i18n (xinput-plus_<lang>.qm).

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
from PyQt6.QtCore import Qt, QTimer, QLocale, QTranslator, QLibraryInfo
from PyQt6.QtGui import QIcon

CONFIG_PATH = Path.home() / ".config" / "xinput-plus.json"
ICON_PATH = Path(__file__).parent / "src" / "emucon.svg"


# --------------------------
# Helpers & config migration
# --------------------------

def debug(msg: str) -> None:
    """Print a namespaced debug line to stdout."""
    print(f"[xinput-plus] {msg}")


def _migrate_old_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrade a legacy flat config into the new by_name/by_id schema."""
    base = {"by_name": {}, "by_id": {}, "_whitelist": [], "_show_only_whitelist": False}
    if not isinstance(cfg, dict):
        return base

    if "by_name" in cfg or "by_id" in cfg:
        # Already new-ish format: ensure all keys exist.
        base.update(cfg)
        base.setdefault("by_name", {})
        base.setdefault("by_id", {})
        base.setdefault("_whitelist", [])
        base.setdefault("_show_only_whitelist", False)
        return base

    # Legacy flat: {name: {speed, extended}}
    by_name = {}
    for k, v in cfg.items():
        if isinstance(v, dict) and ("speed" in v or "extended" in v):
            by_name[k] = {"speed": float(v.get("speed", 0.0)), "extended": bool(v.get("extended", False))}

    out = base.copy()
    out["by_name"] = by_name
    return out


# --------------------------
# i18n loader (keeps refs)
# --------------------------

def install_translators(app: QApplication, forced_locale: Optional[str] = None, verbose: bool = False) -> None:
    """
    Install Qt base + app translators and KEEP references on `app` to avoid GC.
    Looks for app .qm files in ./i18n next to this script.
    """
    if not hasattr(app, "_translators"):
        app._translators: List[QTranslator] = []

    locale = QLocale(forced_locale) if forced_locale else QLocale.system()
    if verbose:
        print(f"[i18n] locale: {locale.name()} (forced={forced_locale})")

    # Qt base (optional)
    qt_tr = QTranslator()
    qt_dir = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    if qt_tr.load(locale, "qtbase", "_", qt_dir):
        app.installTranslator(qt_tr)
        app._translators.append(qt_tr)
        if verbose:
            print(f"[i18n] Loaded Qt base from {qt_dir}")
    elif verbose:
        print(f"[i18n] Qt base NOT loaded for {locale.name()} in {qt_dir} (ok)")

    # App translations
    i18n_dir = str(Path(__file__).parent / "i18n")
    if verbose:
        print(f"[i18n] i18n dir: {i18n_dir}")

    # Candidates in order
    candidates = [
        f"xinput-plus_{locale.name()}.qm",                 # es_ES
        f"xinput-plus_{locale.bcp47Name()}.qm",            # es-ES
        f"xinput-plus_{locale.name().split('_')[0]}.qm",   # es
    ]
    lang = locale.name().split('_')[0]
    if lang:
        candidates.append(f"xinput-plus_{lang}.qm")

    # Deduplicate
    seen = set()
    candidates = [c for c in candidates if not (c in seen or seen.add(c))]

    loaded = False
    for fn in candidates:
        tr = QTranslator()
        if tr.load(fn, i18n_dir):
            app.installTranslator(tr)
            app._translators.append(tr)
            loaded = True
            if verbose:
                print(f"[i18n] Loaded app translation: {fn}")
            break

    if not loaded:
        tr = QTranslator()
        if tr.load(locale, "xinput-plus", "_", i18n_dir):
            app.installTranslator(tr)
            app._translators.append(tr)
            loaded = True
            if verbose:
                print(f"[i18n] Loaded app translation via locale loader for {locale.name()}")

    if not loaded and verbose:
        print(f"[i18n] No app translation found for {locale.name()} in {i18n_dir}")


# --------------------------
# Whitelist dialog
# --------------------------

class WhitelistDialog(QDialog):
    """Dialog to edit the visible-devices whitelist (entries are (name, id))."""
    def __init__(self, parent: QWidget, devices: List[dict], whitelist: Set[Tuple[str, str]]):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit device whitelist"))
        self.setMinimumWidth(520)
        self._devices = devices
        self._initial = whitelist

        layout = QVBoxLayout(self)

        info = QLabel(self.tr("Select the devices you want to keep visible.\n"
                              "If you leave the list empty, all devices will be shown."))
        layout.addWidget(info)

        # Checkable list with all current devices; pre-check those in whitelist
        self.listw = QListWidget()
        self.listw.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for dev in devices:
            name, did = dev["name"], dev["id"]
            text = f"{name}  (id {did})"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if (name, did) in whitelist else Qt.CheckState.Unchecked)
            # Store device data
            item.setData(Qt.ItemDataRole.UserRole, did)
            item.setData(Qt.ItemDataRole.UserRole + 1, name)
            self.listw.addItem(item)
        layout.addWidget(self.listw)

        # OK/Cancel
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def result_whitelist(self) -> List[dict]:
        """Return the whitelist as [{'name':..., 'id':...}, ...]."""
        res = []
        for i in range(self.listw.count()):
            item = self.listw.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                res.append({"name": item.data(Qt.ItemDataRole.UserRole + 1),
                            "id":   item.data(Qt.ItemDataRole.UserRole)})
        return res


# --------------------------
# Main window
# --------------------------

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
            debug(f"Warning: icon not found at {ICON_PATH}")
            try:
                self.setWindowIcon(QIcon.fromTheme("input-mouse"))
            except Exception:
                pass

        # State
        self.all_devices: List[dict] = []          # all slave pointers detected
        self.visible_devices: List[dict] = []      # filtered by whitelist mode
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
        """Load config JSON and migrate legacy shape if needed."""
        try:
            if CONFIG_PATH.exists():
                raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                return _migrate_old_config(raw)
        except Exception as e:
            debug(f"Error reading config: {e}")
        return {"by_name": {}, "by_id": {}, "_whitelist": [], "_show_only_whitelist": False}

    def save_config(self) -> None:
        """Persist current config JSON to disk."""
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(self.config, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            debug(f"Error saving config: {e}")

    # --------------------------
    # UI
    # --------------------------
    def build_ui(self) -> None:
        """Construct the main layout and bind signals."""
        layout = QHBoxLayout(self)

        # Device list (left column)
        self.device_list = QListWidget()
        self.device_list.itemSelectionChanged.connect(self.on_device_selected)
        layout.addWidget(self.device_list, 2)

        # Right panel with controls
        right = QVBoxLayout()

        self.label_device = QLabel(self.tr("Select a device"))
        right.addWidget(self.label_device)

        self.extended_speed_cb = QCheckBox(self.tr("Extended mode (CTM)"))
        self.extended_speed_cb.toggled.connect(self.on_extended_toggled)
        right.addWidget(self.extended_speed_cb)

        self.profile_by_id_cb = QCheckBox(self.tr("Save by ID (specific profile)"))
        right.addWidget(self.profile_by_id_cb)

        self.label_speed = QLabel(self.tr("Speed: 0.00"))
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
        self.btn_refresh = QPushButton(self.tr("🔄 Refresh"))
        self.btn_refresh.clicked.connect(self.load_devices)
        btns.addWidget(self.btn_refresh)

        self.btn_reapply = QPushButton(self.tr("⚙️ Re-apply all"))
        self.btn_reapply.clicked.connect(self.apply_all_configs)
        btns.addWidget(self.btn_reapply)

        # Whitelist controls
        self.show_only_whitelist_cb = QCheckBox(self.tr("Show only whitelist"))
        self.show_only_whitelist_cb.setChecked(bool(self.config.get("_show_only_whitelist", False)))
        self.show_only_whitelist_cb.toggled.connect(self.on_toggle_show_only_whitelist)
        btns.addWidget(self.show_only_whitelist_cb)

        self.btn_edit_whitelist = QPushButton(self.tr("✏️ Edit whitelist"))
        self.btn_edit_whitelist.clicked.connect(self.open_whitelist_dialog)
        btns.addWidget(self.btn_edit_whitelist)
        
        # NEW: About button
        self.btn_about = QPushButton(self.tr("🛈 About"))
        self.btn_about.clicked.connect(self.show_about)
        btns.addWidget(self.btn_about)

        right.addLayout(btns)
        right.addStretch(1)

        layout.addLayout(right, 3)

    # --------------------------
    # Device discovery & list
    # --------------------------
    def _is_virtual_pointer_line(self, raw: str) -> bool:
        """Return True for Virtual/Master/XTEST pointers we should hide/ignore."""
        low = raw.lower()
        if "master pointer" in low:
            return True
        if "virtual core" in low:
            return True
        if "xtest" in low:
            return True
        return False

    def _parse_id_from_short_line(self, line: str) -> Optional[str]:
        """Parse 'id=<digits>' from one line of `xinput list --short` output."""
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
        """Return whitelist as a set of (name, id) tuples for quick filtering."""
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
        """Compute visible_devices by applying the whitelist (if enabled and non-empty)."""
        show_only = bool(self.config.get("_show_only_whitelist", False))
        wl = self._whitelist_set()

        if show_only and wl:
            self.visible_devices = [d for d in self.all_devices if (d["name"], d["id"]) in wl]
        else:
            self.visible_devices = list(self.all_devices)

    def load_devices(self) -> None:
        """Scan all slave pointers via xinput, then repopulate the visible list."""
        self.all_devices = []
        self.device_list.clear()

        out = self.run_cmd(["xinput", "list", "--short"])
        if not out:
            QMessageBox.warning(
                self,
                "xinput",
                self.tr("Could not obtain the device list.\nIs xinput available?")
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
        """Return True if the given property appears in `xinput list-props <id>` output."""
        out = self.run_cmd(["xinput", "list-props", device_id])
        return (prop_name in out) if out else False

    def run_cmd(self, cmd: List[str]) -> str:
        """Execute a command and return stdout as text; log errors to debug()."""
        try:
            debug(f"Running: {' '.join(cmd)}")
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            return out.strip()
        except subprocess.CalledProcessError as e:
            debug(f"Error running {' '.join(cmd)}:\n{e.output.strip()}")
            return ""

    def get_settings_for(self, name: str, dev_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Fetch settings giving priority to ID profile, falling back to name profile."""
        if dev_id and dev_id in self.config.get("by_id", {}):
            return self.config["by_id"][dev_id]
        if name in self.config.get("by_name", {}):
            return self.config["by_name"][name]
        return None

    def _apply_to_device_id(self, device_id: str, speed: float, extended: bool) -> None:
        """Apply either libinput Accel Speed or CTM matrix to a specific device id."""
        if extended:
            # CTM scale clamped to avoid freezing (no zero/near-zero)
            scale = max(speed, -5.0) if speed < 0 else max(min(speed, 5.0), 0.05)
            matrix = f"{scale} 0 0 0 {scale} 0 0 0 1"
            self.run_cmd(["xinput", "--set-prop", device_id, "Coordinate Transformation Matrix", *matrix.split()])
        else:
            if self.device_has_prop(device_id, "libinput Accel Speed"):
                self.run_cmd(["xinput", "--set-prop", device_id, "libinput Accel Speed", f"{speed:.2f}"])
            else:
                debug("Property 'libinput Accel Speed' not available; using CTM as a fallback.")
                scale = max(speed, -5.0) if speed < 0 else max(min(speed, 5.0), 0.05)
                matrix = f"{scale} 0 0 0 {scale} 0 0 0 1"
                self.run_cmd(["xinput", "--set-prop", device_id, "Coordinate Transformation Matrix", *matrix.split()])

    def apply_config_to_device(self, name: str) -> None:
        """Apply the 'by_name' profile to all devices currently reporting that name."""
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
        """Apply all known profiles (by id first, then by name) to connected devices."""
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
        """Sync UI state when a device item is selected; apply stored profile."""
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

        if did:
            self.label_device.setText(self.tr("Device: {name} (id {id})").format(name=name, id=did))
        else:
            self.label_device.setText(self.tr("Device: {name}").format(name=name))
        self.label_speed.setText(self.tr("Speed: {val:.2f}").format(val=speed))

        # Apply immediately to give instant feedback
        if did:
            self._apply_to_device_id(did, speed, extended)

    def on_speed_changed(self, value: int) -> None:
        """Persist current slider value and apply it to the selected device."""
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
        self.label_speed.setText(self.tr("Speed: {val:.2f}").format(val=speed))

        # Apply to selected device by exact ID when available
        if did:
            self._apply_to_device_id(did, speed, extended)
        else:
            self.apply_config_to_device(name)

    def on_extended_toggled(self, checked: bool) -> None:
        """Adjust slider range when toggling CTM mode; re-apply setting."""
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
        """Toggle 'show only whitelist' mode and refresh the device list."""
        self.config["_show_only_whitelist"] = bool(checked)
        self.save_config()
        self.load_devices()

    def open_whitelist_dialog(self) -> None:
        """Open the whitelist editor dialog; save and reload on acceptance."""
        wl_set = self._whitelist_set()
        dlg = WhitelistDialog(self, self.all_devices, wl_set)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.config["_whitelist"] = dlg.result_whitelist()
            self.save_config()
            self.load_devices()

    def show_about(self) -> None:
        """Show an About dialog with translatable HTML content."""
        program = "xinput-plus.py"
        year = "2025"
        author = "Washington Indacochea Delgado"
        email = "wachin.id@gmail.com"
        license_text = self.tr("GPL-3 License")
        url = "https://github.com/wachin/xinput-plus"

        # All text is translatable; keep placeholders as-is.
        about_html = self.tr(
            "<h2><b>{program}</b></h2>"
            "<p>🖱️ A simple GUI tool for adjusting mouse and touchpad speed in X11 Linux "
            "window managers like Openbox, JWM, iceWM, and Fluxbox. Perfect for external, "
            "keyboards with integrated touchpads (like Logitech K400) and laptop touchpads.</p>"
            "<p>&copy; {year} {author}.<br>"
            "{email}<br>"
            "{license}</p>"
            "<p>More info:</p>"
            '<a href="{url}">{url}</a>'
        ).format(program=program, year=year, author=author, email=email, license=license_text, url=url)

        # Rich-text About dialog (links clickable)
        QMessageBox.about(self, self.tr("About xinput-plus"), about_html)


# --------------------------
# CLI & main
# --------------------------

def parse_forced_locale(argv: List[str]) -> Optional[str]:
    """Parse --lang=<locale> from argv and return locale string or None."""
    for arg in argv[1:]:
        if arg.startswith("--lang="):
            return arg.split("=", 1)[1]
    return None


def main() -> int:
    app = QApplication(sys.argv)

    # Install translators (Qt base + app), optionally forced via --lang=xx
    forced = parse_forced_locale(sys.argv)
    install_translators(app, forced_locale=forced, verbose=True)

    gui = LibinputGUI()
    gui.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
