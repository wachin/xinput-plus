# 🖱️ xinput-plus

# Ajusta la velocidad de tu mouse o touchpad (¡muy fácil!)

Este programa te permite **cambiar la velocidad del puntero** (el cursor del mouse o touchpad) en Linux de forma gráfica para usarlo en X11 Window Manager como en: Openbox, JWM, iceWM, Fluxbox, sin tener que escribir comandos complicados. Es ideal si usas teclados externos que traen **teclado con touchpad integrado**, como el **Logitech K400**, y sientes que el cursor va muy lento.

---

## 🎯 ¿Para qué sirve?

- ✅ Aumentar o disminuir la velocidad del mouse o touchpad.
- ✅ Guardar la configuración para que no se pierda al reiniciar.
- ✅ Funciona con dispositivos como:
  - Teclados con touchpad (ej: Logitech K400)
  - Mouses USB
  - Touchpads de laptop

---

## 🖥️ Requisitos

Antes de usarlo, asegúrate de tener instalado lo siguiente en tu computadora con Linux:

```bash
sudo apt install xinput libinput-tools python3-pyqt6
```

1. ⚠️ Este programa solo funciona en **X11**, no en Wayland.  
2. Es sólo para X11 WM como Openbox, JWM, iceWM, Fluxbox, Xubuntu, etc
3. En el 2025 ejemplo en GNOME, KDE antes de hacer login se puede seleccionar X11 para entrar en vez de con Wayland.


---

## 🚀 Cómo instalarlo

1. Descarga el archivo `xinput-plus.py`.
2. Ábrelo con un editor de texto o Python.
3. Dale permisos de ejecución:

```bash
chmod +x xinput-plus.py
```

4. Ejecútalo así:

```bash
python3 xinput-plus.py
```

![](vx_images/403085416299084.png)

> 💡 Puedes hacer doble clic en el archivo `xinput-plus.py` si ya tienes Python instalado, esto en algunos Escritorios de Linux es posible, pero no en todos

---

## 🎛️ Cómo usarlo

1. Al abrir el programa.
2. En la lista de la izquierda, **haz clic en tu dispositivo** (por ejemplo: "Logitech K400").
3. Usa la barra deslizante para cambiar la velocidad:
   - ← Más lento
   - → Más rápido (¡hasta 2 veces más rápido!)
4. Cuando encuentres la velocidad perfecta, haz clic en **"Guardar configuración"**.

✅ ¡Listo! El cambio se aplica al instante y se guarda para la próxima vez.

---

## 💾 ¿Dónde se guarda la configuración?

El programa guarda tus ajustes en este archivo (no lo borres si no quieres perder la configuración):

```
~/.config/libinput-gui.json
```

---

## 🤓 ¿Cómo funciona por dentro?

Usa comandos de Linux como `xinput` para cambiar la velocidad del dispositivo en tiempo real.  
Pero para usarlo: ¡la interfaz lo hace todo por ti!

---

## 🛠️ ¿Quieres mejorar este programa?

Este código está hecho en Python con PyQt6, perfecto para estudiantes que quieren aprender sobre:
- Interfaces gráficas
- Automatización en Linux
- Control de hardware

¡Siéntete libre de modificarlo, mejorarlo o usarlo en tus proyectos escolares!

---

## 🙌 Sobre este programa

Creado por: **Washington Indacochea** (wachin.id@gmail.com)  
Licencia: **GNU GPL3** (gratis y open source)

✨ Gracias por usar `xinput-plus`!  

Para los que aman X11 y los gestores de ventana minimalistas. 👀💙

---

> 🌟 Si te sirvió, dale una estrella ⭐ en GitHub. ¡Ayuda mucho!
```

Dios te bendiga
