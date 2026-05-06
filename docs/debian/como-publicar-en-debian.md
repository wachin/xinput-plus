# Cómo publicar tu programa en packages.debian.org

Una guía práctica para desarrolladores independientes que nunca han
empaquetado para Debian.

Esta guía usa `xinput-plus` como ejemplo concreto a lo largo de todo el
texto, para que puedas ver exactamente cómo se ve cada paso en un proyecto
real. Reemplaza cada aparición de `xinput-plus`, `wachin` y los datos del
autor con los tuyos propios.

---

## Qué es lo que realmente estás intentando hacer

Cuando la gente dice "meter mi paquete en Debian" se refiere a esta cadena
de eventos:

1. Preparas tu código fuente en un formato específico que Debian entiende.
2. Lo subes a un área de espera llamada **mentors.debian.net**.
3. Un **Debian Developer (DD)** lo revisa y, si pasa la revisión, lo sube
   al archivo oficial de Debian en tu nombre. Esta persona se llama
   **patrocinador** (sponsor).
4. El paquete entra en la **cola NEW**, donde el Equipo FTP comprueba que
   cumple los requisitos legales y de política.
5. Una vez aceptado, llega a **unstable** (también llamado **Sid**).
6. Después de aproximadamente dos días sin errores críticos, migra a
   **testing**.
7. Cuando se congela y publica la siguiente versión estable, pasa a formar
   parte de **stable**.

No puedes subir directamente a Debian a menos que seas Debian Developer.
Hasta entonces, siempre necesitas un patrocinador. Esto es normal y
esperado — no es un rechazo, es el proceso.

---

## Parte 1 — Requisitos previos

### 1.1 Instalar las herramientas de empaquetado

En Debian 12 (Bookworm):

```bash
sudo apt install \
  devscripts \
  debhelper \
  dh-python \
  build-essential \
  lintian \
  pbuilder \
  python3-all \
  git \
  gpg \
  reportbug
```

`devscripts` te proporciona `debuild`, `dch`, `uscan` y otros ayudantes.
`lintian` es el comprobador automático de política — debes pasarlo antes
de pedir un patrocinador. `pbuilder` te permite compilar en un entorno
limpio.

### 1.2 Crear una clave GPG

Cada subida a Debian debe estar firmada con una clave GPG. Si aún no
tienes una:

```bash
gpg --full-generate-key
```

Elige **RSA y RSA**, tamaño de clave **4096**, y establece una fecha de
caducidad (1–2 años está bien; puedes extenderla más adelante). Usa la
misma dirección de correo electrónico que pondrás en `debian/changelog` y
`debian/control`.

Para ver tu ID de clave:

```bash
gpg --list-secret-keys --keyid-format LONG
```

La salida tiene este aspecto:

```
sec   rsa4096/AABBCCDD11223344 2025-01-01 [SC]
```

`AABBCCDD11223344` es tu ID de clave. Lo necesitarás en el siguiente paso.

### 1.3 Subir tu clave a un servidor de claves

```bash
gpg --keyserver keyserver.ubuntu.com --send-keys AABBCCDD11223344
```

La infraestructura de Debian usa la red de servidores de claves de Ubuntu.
Tu clave debe ser públicamente accesible antes de que un patrocinador pueda
verificar tus subidas.

### 1.4 Crear una cuenta en Salsa

Salsa es la instancia GitLab de Debian en [https://salsa.debian.org](https://salsa.debian.org).
Necesitas una cuenta para alojar allí tu repositorio de empaquetado
(requerido por los campos `Vcs-Git` y `Vcs-Browser` en `debian/control`).

1. Regístrate en [https://salsa.debian.org/users/sign_up](https://salsa.debian.org/users/sign_up)
2. Crea un nuevo proyecto con el nombre de tu paquete (p. ej. `xinput-plus`).
3. Añade la huella digital de tu clave GPG a tu perfil de Salsa en
   **Preferences → GPG Keys**.

---

### 1.5 Si ya tenías una cuenta y un repositorio

Si ya habías creado una cuenta y si ya habías creado el repositorio, entra e inicia sesión en [https://salsa.debian.org](https://salsa.debian.org)

Allí ve a la sección:

`Personal Projects`

Dale clic a tu proyecto y copia su url, en este caso:

[https://salsa.debian.org/wachin/xinput-plus](https://salsa.debian.org/wachin/xinput-plus)

y luego busca una carpeta en tu ordenador donde puedas tener proyectos en salsa.debian.org y clonalo allí:

```bash
git clone https://salsa.debian.org/wachin/xinput-plus
```



---

## Parte 2 — Estructurar el código fuente

### 2.1 Qué espera Debian

Debian usa el formato de fuentes **3.0 (quilt)**. Tu árbol de fuentes debe
contener un directorio `debian/` con al menos estos archivos:

```
debian/
  changelog       — historial de versiones en un formato estricto
  control         — metadatos del paquete y dependencias
  copyright       — información de licencias en formato DEP-5
  rules           — instrucciones de compilación (un Makefile)
  source/
    format        — contiene el texto "3.0 (quilt)"
```

Archivos adicionales muy recomendados (y obligatorios para aplicaciones
con interfaz gráfica):

```
debian/
  xinput-plus.desktop      — entrada en el menú de aplicaciones
  xinput-plus.metainfo.xml — metadatos AppStream
  xinput-plus.1            — página de manual
  watch                    — indica a uscan dónde encontrar nuevas versiones
```

### 2.2 `debian/source/format`

Este archivo debe contener exactamente una línea:

```
3.0 (quilt)
```

### 2.3 `debian/changelog`

Es el archivo con el formato más estricto de todo el paquete. Cada entrada
debe seguir exactamente este diseño — espacios, guiones y todo:

```
xinput-plus (6.6.4-1) unstable; urgency=medium

  * New upstream release 6.6.4.

 -- Washington Indacochea Delgado <linuxfrontier@proton.me>  Wed, 17 Sep 2025 22:37:19 -0500
```

Reglas:
- La versión entre paréntesis es `<versión-upstream>-<revisión-debian>`.
  La primera vez que empaquetas algo, la revisión Debian siempre es `1`.
- La suite debe ser `unstable` cuando estés listo para subir. Usa
  `UNRELEASED` mientras trabajas localmente.
- La línea del mantenedor empieza con exactamente un espacio, luego ` -- `,
  luego el nombre, el correo entre ángulos, dos espacios y la fecha RFC 2822.
- Nunca edites este archivo a mano para nuevas entradas. Usa `dch`:

```bash
# Iniciar una nueva entrada para una nueva versión upstream:
dch -v 6.6.5-1 "New upstream release 6.6.5."

# Marcar la entrada superior como lista para subir:
dch -r ""
```

`dch -r` cambia `UNRELEASED` a `unstable` y actualiza la marca de tiempo.

### 2.4 `debian/control`

Este archivo tiene dos estrofas: una para el **paquete fuente** y otra para
cada **paquete binario** que produce. Para un paquete sencillo de un solo
binario:

```
Source: xinput-plus
Section: x11
Priority: optional
Maintainer: Washington Indacochea Delgado <linuxfrontier@proton.me>
Build-Depends:
 debhelper-compat (= 13),
 dh-sequence-python3,
 python3-all,
 pyqt6-dev-tools,
 qt6-tools-dev-tools
Standards-Version: 4.7.3
Rules-Requires-Root: no
Homepage: https://github.com/wachin/xinput-plus
Vcs-Git: https://salsa.debian.org/wachin/xinput-plus.git
Vcs-Browser: https://salsa.debian.org/wachin/xinput-plus

Package: xinput-plus
Architecture: all
Depends: ${python3:Depends}, ${misc:Depends}, python3-pyqt6, xinput, libqt6svg6
Recommends: qt6-translations-l10n
Suggests: qt6ct, qt6-style-kvantum
Description: PyQt6 GUI to adjust pointer speed per device (Xorg, via xinput)
 xinput-plus is a simple GUI to manage per-device pointer acceleration for Xorg.
 It supports device-specific profiles by ID or by name, a whitelist to hide
 virtual/master/XTEST devices, and a CTM fallback when "libinput Accel Speed"
 is not exposed by xinput. Translations are supported via Qt .qm files.
 .
 Note: xinput works on Xorg. On Wayland, this tool will not function.
```

Puntos clave:
- `Standards-Version` debe coincidir con la versión actual de la Política
  Debian. Consulta https://www.debian.org/doc/debian-policy/ para la más
  reciente. A principios de 2026 es `4.7.3`.
- `Architecture: all` significa que el paquete es independiente de la
  arquitectura (Python puro, scripts de shell, etc.). Usa `any` para
  binarios compilados.
- `${python3:Depends}` y `${misc:Depends}` son variables de sustitución
  que `dh-python` y `debhelper` rellenan automáticamente en tiempo de
  compilación. Inclúyelas siempre en paquetes Python.
- `Vcs-Git` y `Vcs-Browser` deben apuntar a tu repositorio en Salsa.
- La descripción larga (líneas con sangría) no debe tener espacios al
  final. Las líneas en blanco dentro de la descripción se representan con
  un solo ` .` (espacio y punto).

### 2.5 `debian/copyright` (formato DEP-5)

Es el archivo que más errores causa en los principiantes. Debe seguir
exactamente el formato legible por máquina **DEP-5**. Los errores más
comunes son:

- Que falte la cabecera `Format:` al principio del todo.
- Poner comentarios `#` en la misma línea que un campo (`Files: foo # comentario`
  no es válido — los comentarios deben ir en su propia línea).
- Sangrar las estrofas (cada estrofa debe empezar en la columna 0).

Un ejemplo mínimo correcto:

```
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: xinput-plus
Upstream-Contact: Washington Indacochea Delgado <linuxfrontier@proton.me>
Source: https://github.com/wachin/xinput-plus

Files: *
Copyright:
  2024-2025 Washington Indacochea Delgado <linuxfrontier@proton.me>
License: GPL-3+
 On Debian systems, the full text of the GNU General Public License
 version 3 can be found in /usr/share/common-licenses/GPL-3.

Files: debian/*
Copyright:
  2025 Washington Indacochea Delgado <linuxfrontier@proton.me>
License: GPL-3+
 On Debian systems, the full text of the GNU General Public License
 version 3 can be found in /usr/share/common-licenses/GPL-3.
```

Si tu proyecto incluye archivos bajo licencias distintas (iconos,
bibliotecas incluidas, etc.), cada grupo de archivos necesita su propia
estrofa `Files:`. Todos los archivos del árbol de fuentes deben estar
cubiertos por al menos una estrofa.

### 2.6 `debian/rules`

Es un Makefile que le dice a `debhelper` cómo compilar tu paquete. Para
la mayoría de los paquetes modernos, el archivo completo es simplemente:

```makefile
#!/usr/bin/make -f
export DH_VERBOSE=1

%:
	dh $@
```

La línea `dh $@` delega todo en `debhelper`, que se encarga de la
compilación, instalación, stripping y más de forma automática.

Si necesitas personalizar algún paso, añade un objetivo
`override_dh_<paso>`:

```makefile
override_dh_auto_install:
	install -D -m0755 xinput-plus.py \
	  debian/xinput-plus/usr/bin/xinput-plus
```

Importante: la sangría en `debian/rules` debe usar **tabuladores**, no
espacios. Es un requisito de los Makefiles. Si usas espacios, la
compilación fallará con un error críptico.

### 2.7 `debian/watch`

Este archivo le dice a `uscan` (y a las herramientas de control de calidad
de Debian) dónde encontrar nuevas versiones upstream automáticamente. Para
un proyecto en GitHub:

```
version=4
opts=filenamemangle=s%.*archive/refs/tags/v?(\d+[\d\.]*)\.tar\.gz%xinput-plus-$1.tar.gz% \
  https://github.com/wachin/xinput-plus/tags \
  .*/archive/refs/tags/v?(\d+[\d\.]*)\.tar\.gz
```

### 2.8 Página de manual (`debian/xinput-plus.1`)

Todo programa que instale un binario en `/usr/bin` debe tener una página
de manual. Las secciones mínimas requeridas son `NAME`, `SYNOPSIS`,
`DESCRIPTION` y `SEE ALSO`. La macro `.TH` al principio debe incluir la
fecha y la versión:

```nroff
.TH XINPUT-PLUS 1 "2025-09-17" "xinput-plus 6.6.4" "User Commands"
.SH NAME
xinput-plus \- adjust pointer speed per device (Xorg) via xinput
.SH SYNOPSIS
.B xinput-plus
.RI [ \-\-lang= locale ]
.SH DESCRIPTION
xinput-plus is a PyQt6 GUI that lets you configure per-device pointer speed.
.SH OPTIONS
.TP
.BI \-\-lang= locale
Force the UI language (e.g. \fBes\fR, \fBpt_BR\fR).
.SH FILES
.TP
.I ~/.config/xinput-plus.json
Per-user configuration file.
.SH SEE ALSO
xinput(1)
```

---

## Parte 3 — Compilar y probar localmente

### 3.1 Compilar con `debuild`

Desde la raíz de tu árbol de fuentes (el directorio que contiene
`debian/`):

```bash
debuild -us -uc
```

`-us -uc` significa "fuente sin firmar, changes sin firmar" — omites la
firma durante las pruebas locales. Esto produce varios archivos en el
directorio padre:

```
../xinput-plus_6.6.4-1.dsc
../xinput-plus_6.6.4.orig.tar.gz
../xinput-plus_6.6.4-1.debian.tar.xz
../xinput-plus_6.6.4-1_all.deb
../xinput-plus_6.6.4-1_amd64.changes
```

Si la compilación falla, lee la salida con calma — `debhelper` es muy
detallado y normalmente te dice exactamente qué ha ido mal.

### 3.2 Ejecutar `lintian`

`lintian` es el comprobador automático de política. Debes tener cero
errores e idealmente cero advertencias antes de pedir un patrocinador:

```bash
lintian --pedantic ../xinput-plus_6.6.4-1_amd64.changes
```

Etiquetas comunes de lintian y su significado:

| Etiqueta |                          Significado                          |
| -------- | ------------------------------------------------------------- |
| `E:`     | Error — causará rechazo. Hay que corregirlo.                  |
| `W:`     | Warning — hay que corregirlo. Los patrocinadores preguntarán. |
| `I:`     | Info — problema menor. Corregir si es fácil.                  |
| `P:`     | Pedantic — sugerencia de estilo. Opcional.                    |

Para consultar qué significa cualquier etiqueta:

```bash
lintian-explain-tags <nombre-de-etiqueta>
# o en línea: https://lintian.debian.org/tags/<nombre-de-etiqueta>
```

### 3.3 Probar en un entorno limpio con `pbuilder`

Tu máquina tiene muchos paquetes instalados que podrían ocultar
dependencias de compilación que faltan. `pbuilder` compila en un chroot
mínimo para que detectes esos problemas antes que el patrocinador.

Configura pbuilder una sola vez:

```bash
sudo pbuilder create --distribution unstable
```

Luego compila tu paquete dentro de él. Ejecuta estos comandos desde dentro
del directorio del proyecto (p. ej. `~/Dev/xinput-plus-dev/xinput-plus`):

```bash
# 1. Crear el tarball orig upstream (requerido por el formato de fuentes 3.0 (quilt))
tar --exclude=./debian --exclude=./.git -czf ../xinput-plus_6.6.4.orig.tar.gz .

# 2. Construir el paquete fuente
debuild -us -uc -S

# 3. Construir el paquete binario dentro del chroot limpio
sudo pbuilder build --distribution unstable ../xinput-plus_6.6.4-1.dsc
```

El `.deb` resultante se coloca en `/var/cache/pbuilder/result/`.

> **Nota sobre el tarball orig:** El paso con `tar` es necesario porque
> `debian/source/format` es `3.0 (quilt)`, que requiere un tarball upstream
> separado. Sin él, `debuild -S` fallará con:
> `dpkg-source: error: can't build with source format '3.0 (quilt)'`.

### 3.4 Instalar y probar el `.deb` manualmente

```bash
sudo dpkg -i /var/cache/pbuilder/result/xinput-plus_6.6.4-1_all.deb
# Comprobar que arranca:
xinput-plus
# Comprobar que la página de manual se instaló correctamente:
man xinput-plus
# Desinstalarlo:
sudo dpkg -r xinput-plus
```

---

## Parte 4 — Presentar un ITP (Intent to Package)

Antes de subir nada a ningún sitio, debes presentar un **bug ITP** contra
el pseudopaquete `wnpp`. Esto le comunica a la comunidad Debian que estás
trabajando en este paquete y evita el trabajo duplicado.

```bash
reportbug wnpp
```

Cuando se te pregunte:
- Elige **ITP** (Intent to Package).
- Nombre del paquete: `xinput-plus`
- Descripción corta: `PyQt6 GUI to adjust pointer speed per device (Xorg, via xinput)`
- Licencia: `GPL-3+`
- URL: `https://github.com/wachin/xinput-plus`

`reportbug` enviará un correo a `submit@bugs.debian.org` y recibirás de
vuelta un número de bug (p. ej. `#1234567`). Añade ese número a tu entrada
de `debian/changelog`:

```
xinput-plus (6.6.4-1) unstable; urgency=medium

  * Initial release. (Closes: #1234567)

 -- Washington Indacochea Delgado <linuxfrontier@proton.me>  Wed, 17 Sep 2025 22:37:19 -0500
```

La sintaxis `Closes: #NNNNNN` cierra automáticamente el bug ITP cuando tu
paquete es aceptado en el archivo.

---

## Parte 5 — Subir a mentors.debian.net

`mentors.debian.net` es el área de espera donde los no-DD suben paquetes
para que los patrocinadores los revisen. No es el archivo oficial de
Debian — es una sala de espera.

### 5.1 Firmar el paquete

Ahora compila con la firma activada:

```bash
debuild -sa
```

`-sa` significa "incluir el tarball fuente original". Se te pedirá la
contraseña de tu clave GPG. Esto produce un archivo `.changes` firmado.

### 5.2 Configurar `dput`

`dput` es la herramienta que sube tu paquete. Crea o edita `~/.dput.cf`:

```ini
[mentors]
fqdn = mentors.debian.net
incoming = /upload
method = https
allow_unsigned_uploads = 0
progress_indicator = 2
```

### 5.3 Subir

```bash
dput mentors ../xinput-plus_6.6.4-1_amd64.changes
```

Si la subida tiene éxito, recibirás un correo de confirmación y tu paquete
aparecerá en:
`https://mentors.debian.net/package/xinput-plus`

---

## Parte 6 — Encontrar un patrocinador

Un patrocinador es un Debian Developer que revisa tu paquete y lo sube al
archivo oficial en tu nombre. Encontrar uno es a menudo la parte más difícil
del proceso — requiere paciencia.

### 6.1 Suscribirse a la lista de correo debian-mentors

```
https://lists.debian.org/debian-mentors/
```

Este es el canal principal para las solicitudes de patrocinio. Lee la lista
durante una semana antes de publicar para entender el tono y las
expectativas.

### 6.2 Enviar una solicitud de patrocinio

Publica en `debian-mentors@lists.debian.org` con un asunto como:

```
RFS: xinput-plus/6.6.4-1 -- PyQt6 GUI to adjust pointer speed per device
```

RFS significa **Request for Sponsorship** (solicitud de patrocinio). Tu
correo debe incluir:
- Una breve descripción de lo que hace el programa.
- El número del bug ITP.
- La URL de mentors.debian.net.
- Una nota indicando que lintian está limpio y que pbuilder compila con éxito.
- Cualquier problema conocido o cosa de la que no estés seguro.

Ejemplo:

```
Package: xinput-plus
Version: 6.6.4-1
ITP: https://bugs.debian.org/1234567
mentors: https://mentors.debian.net/package/xinput-plus
License: GPL-3+
Section: x11

xinput-plus is a PyQt6 GUI for adjusting mouse and touchpad pointer speed
per device on Xorg. It supports per-ID and per-name profiles, a device
whitelist, natural scrolling, tap-to-click, and a CTM fallback.

The package is lintian-clean and builds successfully in a pbuilder
unstable chroot.

I am looking for a sponsor for this package.
```

### 6.3 Sé paciente y receptivo

Los patrocinadores son voluntarios. Una respuesta puede tardar días o
semanas. Cuando un patrocinador revise tu paquete y pida cambios, hazlos
con prontitud, sube una nueva versión a mentors.debian.net y responde al
hilo.

No envíes el mismo correo RFS repetidamente a la lista. Una publicación
por versión del paquete es la norma. Si pasan semanas sin respuesta, puedes
publicar de nuevo cuando subas una nueva versión.

---

## Parte 7 — La cola NEW

Cuando tu patrocinador sube el paquete por primera vez, entra en la
**cola NEW** en https://ftp-master.debian.org/new.html. El Equipo FTP la
revisa comprobando:

- Cumplimiento de licencias (cada archivo debe tener una licencia clara y
  libre según las DFSG).
- `debian/copyright` correcto (formato DEP-5, todos los archivos cubiertos).
- Sección y prioridad apropiadas.
- Que no haya conflictos de nombre con paquetes existentes.

La cola NEW puede tardar desde unos pocos días hasta varios meses según la
carga de trabajo del Equipo FTP. No puedes acelerar esto. Solo espera.

Cuando el paquete sea aceptado recibirás un correo y aparecerá en
`https://packages.debian.org/unstable/xinput-plus`.

---

## Parte 8 — Mantener el paquete tras la aceptación

Entrar no es el final — es el comienzo de un compromiso continuo.

### 8.1 Actualizar para una nueva versión upstream

1. Actualiza tu código fuente.
2. Ejecuta `uscan` para verificar que el archivo watch funciona:
   ```bash
   uscan --verbose
   ```
3. Añade una nueva entrada al changelog:
   ```bash
   dch -v 6.6.5-1 "New upstream release 6.6.5."
   dch -r ""
   ```
4. Compila, ejecuta lintian, prueba con pbuilder.
5. Sube a mentors.debian.net y pide a tu patrocinador que suba de nuevo.

Una vez que tengas un historial de paquetes limpios, puedes solicitar
convertirte en **Debian Maintainer (DM)**, lo que te da derechos de subida
para tus propios paquetes sin necesitar un patrocinador cada vez.

### 8.2 Responder a los informes de errores

Los usuarios presentarán bugs contra tu paquete en `bugs.debian.org`.
Suscríbete al rastreador de bugs de tu paquete:

```
https://bugs.debian.org/xinput-plus
```

Responde a los bugs con prontitud. Un paquete con muchos bugs sin atender
puede ser eliminado del archivo.

### 8.3 Mantener `Standards-Version` actualizado

La Política Debian se actualiza regularmente. Consulta la versión actual en
https://www.debian.org/doc/debian-policy/ y actualiza `Standards-Version`
en `debian/control` cuando hagas una nueva subida. Lee el listado de cambios
en https://www.debian.org/doc/debian-policy/upgrading-checklist.html para
ver qué ha cambiado.

---

## Parte 9 — De unstable a stable

No necesitas hacer nada para que tu paquete llegue a stable. La migración
ocurre automáticamente:

1. Tu paquete llega a **unstable** (Sid).
2. Después de 2–10 días sin bugs RC (release-critical), migra a **testing**
   automáticamente.
3. Cuando el Equipo de Publicación de Debian congela testing para una nueva
   versión estable (aproximadamente cada dos años), tu paquete se incluye
   si no tiene bugs RC.
4. Se publica la nueva versión estable y tu paquete está ahora en
   `packages.debian.org/stable/xinput-plus`.

Lo único que necesitas hacer es mantener el paquete libre de bugs RC
durante el período de congelación.

---

## Referencia rápida — lista de comprobación de archivos

Antes de pedir un patrocinador, verifica cada elemento:

```
[ ] debian/source/format        contiene "3.0 (quilt)"
[ ] debian/changelog            la suite de la entrada superior es "unstable",
                                 sin duplicados, contiene "Closes: #número-ITP"
[ ] debian/control              Standards-Version es actual, los campos Vcs-*
                                 apuntan a Salsa, la descripción larga no tiene
                                 espacios al final de línea
[ ] debian/copyright            empieza con la cabecera Format:, todos los
                                 archivos cubiertos, sin comentarios # en línea
                                 en los campos Fields:
[ ] debian/rules                usa tabuladores (no espacios), compila limpio
[ ] debian/watch                uscan puede encontrar el tarball upstream más
                                 reciente
[ ] debian/<paquete>.1          existe página de manual para cada binario en
                                 /usr/bin
[ ] debian/<paquete>.desktop    Name es legible por humanos, Categories correcto
[ ] debian/<paquete>.metainfo.xml  versión actual en <releases>, sin etiqueta
                                    <developer_name> obsoleta
[ ] lintian --pedantic          cero errores, idealmente cero advertencias
[ ] pbuilder build              tiene éxito en un chroot unstable limpio
[ ] ITP presentado              número de bug registrado en el changelog
[ ] Repositorio en Salsa        las URLs Vcs-Git y Vcs-Browser son accesibles
[ ] Clave GPG                   en keyserver.ubuntu.com, mismo correo que en
                                 debian/changelog
```

---

## Enlaces útiles

| Recurso | URL |
|---------|-----|
| Manual de Política Debian | https://www.debian.org/doc/debian-policy/ |
| Referencia del Desarrollador Debian | https://www.debian.org/doc/manuals/developers-reference/ |
| Formato de copyright DEP-5 | https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/ |
| mentors.debian.net | https://mentors.debian.net/ |
| Cola NEW | https://ftp-master.debian.org/new.html |
| Referencia de etiquetas lintian | https://lintian.debian.org/tags/ |
| ITP / WNPP | https://www.debian.org/devel/wnpp/ |
| Lista de correo debian-mentors | https://lists.debian.org/debian-mentors/ |
| Salsa | https://salsa.debian.org/ |
| Proceso Debian Maintainer | https://wiki.debian.org/DebianMaintainer |
| Proceso Debian New Member | https://nm.debian.org/ |
