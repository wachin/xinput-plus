# 🖱️ xinput-plus

# Ajusta la velocidad de tu mouse o touchpad (¡muy fácil!)

Este programa es para **Linux** y te permite **cambiar la velocidad del puntero** (el cursor del mouse o touchpad) de forma gráfica para usarlo en X11 Window Manager como en: Openbox, JWM, iceWM, Fluxbox, y otros Gestores o Administradores de ventana minimalistas en los cuales no hay un programa con GUI para hacerlo, sin tener que escribir comandos complicados. Es ideal si usas teclados externos que traen **teclado con touchpad integrado**, como el **Logitech K400**, o incluso para el touchpad de tu laptop si sientes que el cursor va muy lento.

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
sudo apt install xinput libinput-tools python3-pyqt6 python3-pyqt6.qtsvg
```

1. ⚠️ Este programa solo funciona en **X11**, no en Wayland.  
2. Es sólo para X11 WM como Openbox, JWM, iceWM, Fluxbox, Xubuntu, etc
3. En el 2025 ejemplo en GNOME, KDE antes de hacer login se puede seleccionar X11 para entrar en vez de con Wayland.


---

## 🚀 Cómo usar el programa

### **1era OPCIÓN: Descargar el repositorio**
En:

[https://github.com/wachin/xinput-plus](https://github.com/wachin/xinput-plus)

da clic en la especie de flecha abajo en Code:

**<>  Code ▼**

y clic en:

**Download ZIP**

 descompríme, y allí dentro de la carpeta está el archivo `xinput-plus.py`.

o lo puedes clonar:

### **2da OPCIÓN: Clonar el repositorio**

**1.-** Como ya tenemos instalado a git poner en una terminal en una carpeta donde tenga programas de Linux:

```bash
git clone https://github.com/wachin/xinput-plus
```

**2.-** Dale permisos de ejecución

Puede ser con clic derecho en el **administrador de archivos** y en la pestaña "**Permisos**" verificar que esté marcado como ejecutatable

o desde la terminal con:

```bash
chmod +x xinput-plus.py
```


## Ejecutando con Launcher.sh

Asegúrate que el script `Launcher.sh`está como ejecutable, en el administrador de archivos dele clic derecho y en la pestaña "**Permisos**" asegúrese de que "**es ejecutable**"

Dele doble clic al script `Launcher.sh` y clic en `Ejecutar`

👉 Se abrirá una ventana con dos controles:

![](https://blogger.googleusercontent.com/img/a/AVvXsEjpX652hNVrABN1QASxS3bgTiZvC7MDDoRjhIIVs2a0rrQHemqm4vwVZD_mpVAeuiflGv-gyLAW5oxTi6vLmUcq5KKwnPwLVxp0ycoP4jfHSpk24yWO_6TD888U2tjl4aRW_gPvxTCF5eMuoVJ0Ea4J0FxHTnzogi7PhdcSs9K6z5g7PLxzFNRB-u0nX2c=s16000)

## Ejecutando a xinput-plus

**1.-** **Abre una terminal**  
**2.-** **Ve a la carpeta** donde está el archivo `xinput-plus.py`, o abre una terminal allí desde tu administrador de archivos  
**3.-** **Ejecuta el programa** con este comando:  

```bash
python3 xinput-plus.py
```

y se abrirá.


> 💡 En algunos Linux puedes dar clic derecho en el archivo `xinput-plus.py` y abrir con python.

---

## 🎛️ Cómo usarlo

1. Al abrir el programa.
2. En la lista de la izquierda, **haz clic en tu dispositivo** (por ejemplo: "Logitech K400").
3. Usa la barra deslizante para cambiar la velocidad:
   - ← Más lento (hasta -1.0)
   - → Más rápido (hasta 1.0 por defecto; hasta 2.0 en modo extendido CTM)
4. Cuando encuentres la velocidad perfecta, el cambio se guarda automáticamente.

✅ ¡Listo! El cambio se aplica al instante y se guarda automáticamente para la próxima vez.

---

## 💾 ¿Dónde se guarda la configuración?

El programa guarda tus ajustes en este archivo (no lo borres si no quieres perder la configuración):

```
~/.config/xinput-plus.json
```

---

## 🤓 ¿Cómo funciona por dentro?

Usa comandos de Linux con `xinput` para cambiar la velocidad del dispositivo en tiempo real.  
Pero para usarlo: ¡la interfaz lo hace todo por ti!

---

## 🛠️ ¿Quieres mejorar este programa?

Este código está hecho en Python con PyQt6, perfecto para estudiantes que quieren aprender sobre:

- Interfaces gráficas
- Automatización en Linux
- Control de hardware

¡Siéntete libre de modificarlo, mejorarlo o usarlo en tus proyectos!

---

## 🙌 Sobre este programa

- Creado por: **Washington Indacochea Delgado**
- Licencia: **GNU GPL3** (gratis y open source)

✨ Gracias por usar `xinput-plus`!  

Para los que aman X11 y los gestores de ventana minimalistas. 👀💙

---

> 🌟 Si te sirvió, dale una estrella ⭐ en GitHub. ¡Ayuda mucho!

Dios te bendiga
