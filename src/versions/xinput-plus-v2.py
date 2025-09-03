#!/usr/bin/env python3
# xinput-plus.py
# Prototipo mejorado para gestionar velocidad del mouse/touchpad con PyQt6
# Autor: Adaptado desde xinput-gui por Washington Indacochea Delgado

import sys
import subprocess
import simplejson as json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QLabel, QSlider, QPushButton, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt

CONFIG_FILE = Path.home() / ".config/xinput-plus.json"


class LibinputGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("xinput-plus")
        self.resize(600, 400)

        # Estado
        self.devices = []
        self.selected_device = None
        self.config = self.load_config()

        # Verificar si libinput está disponible
        if not self.check_libinput():
            QMessageBox.critical(self, "Error",
                                 "No se encontró el comando 'libinput'.\n"
                                 "Instala el paquete:\n\n  sudo apt install libinput-tools")
            sys.exit(1)

        # UI
        layout = QHBoxLayout(self)

        # Lista de dispositivos
        self.device_list = QListWidget()
        self.device_list.itemSelectionChanged.connect(self.on_device_selected)
        layout.addWidget(self.device_list, 2)

        # Panel derecho
        right_panel = QVBoxLayout()

        self.label_device = QLabel("Seleccione un dispositivo")
        right_panel.addWidget(self.label_device)

        # Slider de velocidad
        self.label_speed = QLabel("Velocidad: 0.00")
        right_panel.addWidget(self.label_speed)

        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setMinimum(-100)  # -1.0 por defecto
        self.slider_speed.setMaximum(100)   # 1.0 por defecto
        self.slider_speed.setValue(0)
        self.slider_speed.valueChanged.connect(self.on_speed_changed)
        right_panel.addWidget(self.slider_speed)

        # Casilla para modo de velocidad extendida
        self.extended_speed_cb = QCheckBox("Habilitar velocidad extendida (hasta 2.0)")
        self.extended_speed_cb.stateChanged.connect(self.on_extended_speed_changed)
        right_panel.addWidget(self.extended_speed_cb)

        # Botón guardar
        btn_save = QPushButton("Guardar configuración")
        btn_save.clicked.connect(self.save_config)
        right_panel.addWidget(btn_save)

        layout.addLayout(right_panel, 3)

        # Cargar dispositivos
        self.load_devices()

    def run_cmd(self, cmd):
        try:
            output = subprocess.check_output(cmd, shell=True, text=True)
            return output.strip()
        except subprocess.CalledProcessError:
            return ""

    def check_libinput(self):
        return bool(self.run_cmd("command -v libinput"))

    def load_devices(self):
        output = self.run_cmd("libinput list-devices")
        self.devices.clear()
        self.device_list.clear()

        current_name = None
        current_cap = None
        for line in output.splitlines():
            if line.startswith("Device:"):
                current_name = line.split("Device:")[1].strip()
                current_cap = None
            elif "Capabilities:" in line:
                current_cap = line.split("Capabilities:")[1].strip()
                if "pointer" in current_cap.lower():
                    self.devices.append(current_name)
                    self.device_list.addItem(current_name)

    def on_device_selected(self):
        selected_items = self.device_list.selectedItems()
        if not selected_items:
            return
        name = selected_items[0].text()
        self.selected_device = name
        self.label_device.setText(f"Dispositivo: {name}")
        # Cargar configuración del dispositivo
        device_config = self.config.get(name, {"speed": 0.0, "extended": False})
        speed = device_config["speed"]
        extended = device_config["extended"]
        # Actualizar slider y casilla
        self.extended_speed_cb.setChecked(extended)
        self.slider_speed.setMinimum(-200 if extended else -100)
        self.slider_speed.setMaximum(200 if extended else 100)
        self.slider_speed.setValue(int(speed * 100))
        self.label_speed.setText(f"Velocidad: {speed:.2f}")

    def on_extended_speed_changed(self, state):
        extended = state == Qt.CheckState.Checked.value
        if self.selected_device:
            # Actualizar rango del slider
            self.slider_speed.setMinimum(-200 if extended else -100)
            self.slider_speed.setMaximum(200 if extended else 100)
            # Actualizar velocidad actual
            current_speed = self.slider_speed.value() / 100.0
            self.on_speed_changed(self.slider_speed.value())
            # Guardar estado de la casilla en la configuración
            self.config[self.selected_device] = {
                "speed": current_speed,
                "extended": extended
            }

    def on_speed_changed(self, value):
        speed = value / 100.0
        self.label_speed.setText(f"Velocidad: {speed:.2f}")
        if self.selected_device:
            device_id = self.get_device_id(self.selected_device)
            if device_id:
                extended = self.extended_speed_cb.isChecked()
                if extended:
                    # Usar Coordinate Transformation Matrix para velocidades > 1.0
                    matrix = f"{speed} 0 0 0 {speed} 0 0 0 1"
                    result = self.run_cmd(f"xinput --set-prop {device_id} 'Coordinate Transformation Matrix' {matrix}")
                else:
                    # Usar libinput Accel Speed para rango estándar
                    result = self.run_cmd(f"xinput --set-prop {device_id} 'libinput Accel Speed' {speed}")
                if result == "":
                    self.config[self.selected_device] = {
                        "speed": speed,
                        "extended": extended
                    }
                else:
                    QMessageBox.warning(self, "Error",
                                        f"No se pudo cambiar la velocidad de {self.selected_device}")
            else:
                QMessageBox.warning(self, "Error",
                                    f"No se encontró ID para {self.selected_device}")

    def get_device_id(self, name):
        output = self.run_cmd("xinput list")
        for line in output.splitlines():
            if name in line:
                for part in line.split():
                    if part.startswith("id="):
                        return part.replace("id=", "")
        return None

    def load_config(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_config(self):
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)
        QMessageBox.information(self, "Guardado", "Configuración guardada correctamente.")
        
    def run_cmd(self, cmd):
        try:
            print(f"Ejecutando: {cmd}")
            output = subprocess.check_output(cmd, shell=True, text=True)
            print(f"Salida: {output.strip()}")
            return output.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error al ejecutar {cmd}: {e}")
            return ""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = LibinputGUI()
    gui.show()
    sys.exit(app.exec())
