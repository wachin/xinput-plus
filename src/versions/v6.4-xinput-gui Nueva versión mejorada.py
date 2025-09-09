#!/usr/bin/env python3
# xinput-plus.py / v6.4
# PyQt6 GUI para ajustar velocidad del cursor vía xinput (Xorg)
#
# Novedades:
# - Lista blanca (whitelist) de dispositivos visibles, editable desde la UI.
# - Opción "Mostrar sólo whitelist".
# - Perfiles por ID además de por nombre (checkbox "Guardar por ID").
# - Desambiguación por ID, icono local, filtro de virtual/master pointers,
#   verificación de 'libinput Accel Speed' y fallback a CTM, auto-aplicación al iniciar.
#
# Config (~/.config/xinput-plus.json) ahora tiene esta forma:
# {
#   "by_name": { "<nombre>": {"speed": float, "extended": bool}, ... },
#   "by_id":   { "<id>":      {"speed": float, "extended": bool}, ... },
#   "_whitelist": [ {"name": "<nombre>", "id": "<id>"}, ... ],
#   "_show_only_whitelist": true/false
# }
#
# Migración automática: si encuentra el formato antiguo (clave = nombre), lo mueve a "by_name".

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
    print(f"[xinput-plus] {msg}")


def _migrate_old_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Convierte config antigua {name: settings} a nueva estructura con by_name/by_id."""
    if not isinstance(cfg, dict):
        return {"by_name": {}, "by_id": {}, "_whitelist": [], "_show_only_whitelist": False}

    # Ya está migrada
    if "by_name" in cfg or "by_id" in cfg:
        cfg.setdefault("by_name", {})
        cfg.setdefault("by_id", {})
        cfg.setdefault("_whitelist", [])
        cfg.setdefault("_show_only_whitelist", False)
        return cfg

    # Migración desde plano
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
    """Diálogo para editar la whitelist de dispositivos visibles (por name+id)."""
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

        self.listw = QListWidget()
        self.listw.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for dev in devices:
            name, did = dev["name"], dev["id"]
            text = f"{name}  (id {did})"
            item = QListWidgetItem(text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if (name, did) in whitelist else Qt.CheckState.Unchecked)
            # Guarda los datos
            item.setData(Qt.ItemDataRole.UserRole, did)
            item.setData(Qt.ItemDataRole.UserRole + 1, name)
            self.listw.addItem(item)
        layout.addWidget(self.listw)

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def result_whitelist(self) -> List[dict]:
        """Devuelve la whitelist como lista de dicts [{'name':..., 'id':...}, ...]."""
        res = []
        for i in range(self.listw.count()):
            item = self.listw.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                res.append({"name": item.data(Qt.ItemDataRole.UserRole + 1),
                            "id":   item.data(Qt.ItemDataRole.UserRole)})
        return res


class LibinputGUI(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("xinput-plus")
        self.setMinimumWidth(800)

        # Ícono de ventana
        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))
        else:
            debug(f"Advertencia: No se encontró el ícono en {ICON_PATH}")
            try:
                self.setWindowIcon(QIcon.fromTheme("input-mouse"))
            except Exception:
                pass

        # Estado
        self.all_devices: List[dict] = []          # todos los slave pointers en el sistema
        self.visible_devices: List[dict] = []      # lo que mostramos en la lista (tras filtro)
        self.selected_device_name: str = ""
        self.selected_device_id: Optional[str] = None

        # Config
        self.config = self.load_config()

        # UI
        self.build_ui()
        self.load_devices()

        # Auto-aplicar tras 1s
        QTimer.singleShot(1000, self.apply_all_configs)

    # --------------------------
    # Persistencia
    # --------------------------
    def load_config(self) -> Dict[str, Any]:
        try:
            if CONFIG_PATH.exists():
                raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                return _migrate_old_config(raw)
        except Exception as e:
            debug(f"Error leyendo config: {e}")
        return {"by_name": {}, "by_id": {}, "_whitelist": [], "_show_only_whitelist": False}

    def save_config(self) -> None:
        try:
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(self.config, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            debug(f"Error guardando config: {e}")

    # --------------------------
    # UI
    # --------------------------
    def build_ui(self) -> None:
        layout = QHBoxLayout(self)

        # Lista dispositivos (izquierda)
        self.device_list = QListWidget()
        self.device_list.itemSelectionChanged.connect(self.on_device_selected)
        layout.addWidget(self.device_list, 2)

        # Panel derecho
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

        # Botonera
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
    # Dispositivos
    # --------------------------
    def _is_virtual_pointer_line(self, raw: str) -> bool:
        """True si es un Virtual/Master pointer que no debemos mostrar/controlar."""
        low = raw.lower()
        if "master pointer" in low:
            return True
        if "virtual core" in low:
            return True
        if "xtest" in low:
            return True
        return False

    def _parse_id_from_short_line(self, line: str) -> Optional[str]:
        # Busca 'id=<num>'
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
        """Calcula visible_devices aplicando (o no) la whitelist."""
        show_only = bool(self.config.get("_show_only_whitelist", False))
        wl = self._whitelist_set()

        if show_only and wl:
            self.visible_devices = [d for d in self.all_devices if (d["name"], d["id"]) in wl]
        else:
            self.visible_devices = list(self.all_devices)

    def load_devices(self) -> None:
        """Carga TODOS los slave pointers desde xinput y luego filtra para la lista visible."""
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

            # Extrae nombre e id
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

        # Calcula visibles según whitelist
        self._compute_visible()

        # Pinta la lista visible
        for dev in self.visible_devices:
            name, did = dev["name"], dev["id"]
            item_text = f"{name}  (id {did})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, did)
            item.setData(Qt.ItemDataRole.UserRole + 1, name)
            self.device_list.addItem(item)

        # Selección predeterminada
        if self.device_list.count() > 0:
            self.device_list.setCurrentRow(0)

    # --------------------------
    # Config lookup & aplicación
    # --------------------------
    def device_has_prop(self, device_id: str, prop_name: str) -> bool:
        out = self.run_cmd(["xinput", "list-props", device_id])
        return (prop_name in out) if out else False

    def run_cmd(self, cmd: list[str]) -> str:
        """Ejecuta un comando y devuelve stdout (string)."""
        try:
            debug(f"Ejecutando: {' '.join(cmd)}")
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
            return out.strip()
        except subprocess.CalledProcessError as e:
            debug(f"Error ejecutando {' '.join(cmd)}:\n{e.output.strip()}")
            return ""

    def get_settings_for(self, name: str, dev_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Devuelve settings priorizando por ID y luego por nombre."""
        if dev_id and dev_id in self.config.get("by_id", {}):
            return self.config["by_id"][dev_id]
        if name in self.config.get("by_name", {}):
            return self.config["by_name"][name]
        return None

    def _apply_to_device_id(self, device_id: str, speed: float, extended: bool) -> None:
        if extended:
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
        """Aplica config al/los dispositivos (en el sistema) que se llamen 'name'."""
        cfg = self.get_settings_for(name, None)  # por nombre
        if not cfg:
            return
        speed = float(cfg.get("speed", 0.0))
        extended = bool(cfg.get("extended", False))

        # Aplica a TODOS los dispositivos con ese nombre (de la lista completa)
        for dev in self.all_devices:
            if dev["name"] == name:
                self._apply_to_device_id(dev["id"], speed, extended)

        # Fallback por si el scan aún no encontró devices
        out = self.run_cmd(["xinput", "list", "--id-only", f"pointer:{name}"])
        if out:
            for dev_id in out.split():
                self._apply_to_device_id(dev_id, speed, extended)

    def apply_all_configs(self) -> None:
        """Aplica todas las configs conocidas (por id y por nombre) a todos los devices del sistema."""
        if not self.all_devices:
            self.load_devices()

        # Primero por ID (más específico)
        for dev in self.all_devices:
            did = dev["id"]
            cfg = self.config.get("by_id", {}).get(did)
            if cfg:
                self._apply_to_device_id(did, float(cfg.get("speed", 0.0)), bool(cfg.get("extended", False)))

        # Luego por nombre, pero SIN sobrescribir los que ya tuvieron config por ID
        applied_ids = {d["id"] for d in self.all_devices if d["id"] in self.config.get("by_id", {})}
        for dev in self.all_devices:
            if dev["id"] in applied_ids:
                continue
            name = dev["name"]
            cfg = self.config.get("by_name", {}).get(name)
            if cfg:
                self._apply_to_device_id(dev["id"], float(cfg.get("speed", 0.0)), bool(cfg.get("extended", False)))

        # Seleccionar algo en la UI si nada está seleccionado
        if self.device_list.currentRow() < 0 and self.device_list.count() > 0:
            self.device_list.setCurrentRow(0)

    # --------------------------
    # Slots UI
    # --------------------------
    def on_device_selected(self) -> None:
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

        # Auto-check "Guardar por ID" si ya hay perfil por id para este dispositivo
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

        # Aplica inmediatamente lo que tenemos guardado (útil al seleccionar)
        if did:
            self._apply_to_device_id(did, speed, extended)

    def on_speed_changed(self, value: int) -> None:
        if not self.selected_device_name:
            return

        extended = self.extended_speed_cb.isChecked()
        speed = value / 100.0
        did = self.selected_device_id
        name = self.selected_device_name

        # Guarda por nombre SIEMPRE
        self.config.setdefault("by_name", {})
        self.config["by_name"].setdefault(name, {})
        self.config["by_name"][name]["speed"] = speed
        self.config["by_name"][name]["extended"] = extended

        # Guarda por ID si está marcado
        if self.profile_by_id_cb.isChecked() and did:
            self.config.setdefault("by_id", {})
            self.config["by_id"].setdefault(did, {})
            self.config["by_id"][did]["speed"] = speed
            self.config["by_id"][did]["extended"] = extended

        self.save_config()
        self.label_speed.setText(f"Velocidad: {speed:.2f}")

        # Aplica al device seleccionado por ID si lo tenemos
        if did:
            self._apply_to_device_id(did, speed, extended)
        else:
            self.apply_config_to_device(name)

    def on_extended_toggled(self, checked: bool) -> None:
        cur = self.slider_speed.value()
        if checked:
            self.slider_speed.setMinimum(-200)
            self.slider_speed.setMaximum(200)
            cur = int(cur * 2)
        else:
            self.slider_speed.setMinimum(-100)
            self.slider_speed.setMaximum(100)
            cur = int(cur / 2)

        cur = max(self.slider_speed.minimum(), min(self.slider_speed.maximum(), cur))

        self.slider_speed.blockSignals(True)
        self.slider_speed.setValue(cur)
        self.slider_speed.blockSignals(False)

        # Reaplica con el nuevo modo
        self.on_speed_changed(self.slider_speed.value())

    def on_toggle_show_only_whitelist(self, checked: bool) -> None:
        self.config["_show_only_whitelist"] = bool(checked)
        self.save_config()
        self.load_devices()

    def open_whitelist_dialog(self) -> None:
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
