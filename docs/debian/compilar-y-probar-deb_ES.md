# Cómo compilar y probar el paquete .deb en tu ordenador

Esta guía es para el desarrollador que quiere construir el paquete
`xinput-plus` localmente, instalar el `.deb` resultante y probarlo en su
propio sistema Debian antes de publicarlo. No necesitas ser Debian Developer
ni tener ninguna cuenta especial para hacer esto.

Se asume que usas **Debian 12 (Bookworm)**. Los comandos son los mismos en
Debian 13 (Trixie) salvo que se indique lo contrario.

---

## ¿Qué vamos a hacer?

1. Instalar las herramientas de compilación.
2. Clonar el repositorio.
3. Instalar las dependencias de compilación.
4. Construir el paquete con `debuild`.
5. Revisar el paquete con `lintian`.
6. Instalar el `.deb` y probar el programa.
7. Desinstalar cuando ya no lo necesites.

---

## Paso 1 — Instalar las herramientas de compilación

Abre una terminal y ejecuta:

```bash
sudo apt install \
  build-essential \
  devscripts \
  debhelper \
  dh-python \
  pyqt6-dev-tools \
  qt6-tools-dev-tools \
  lintian
```

¿Para qué sirve cada uno?

| Paquete | Para qué sirve |
|---------|----------------|
| `build-essential` | Compilador C y herramientas básicas de construcción |
| `devscripts` | Proporciona `debuild`, `dch`, `uscan` y otros ayudantes |
| `debhelper` | El sistema de construcción que usa `debian/rules` |
| `dh-python` | Soporte para paquetes Python (`dh-sequence-python3`) |
| `pyqt6-dev-tools` | Proporciona `pylupdate6` para extraer cadenas de traducción |
| `qt6-tools-dev-tools` | Proporciona `lrelease-qt6` para compilar traducciones `.qm` |
| `lintian` | Comprobador automático de política Debian |

---

## Paso 2 — Clonar el repositorio

Si aún no tienes el código fuente:

```bash
git clone https://github.com/wachin/xinput-plus
cd xinput-plus
```

Si ya lo tienes clonado, asegúrate de estar en la rama principal y
actualizado:

```bash
git checkout main
git pull
```

---

## Paso 3 — Habilitar las fuentes de código (recomendado)

Este paso permite que `apt` lea tu `debian/control` e instale
automáticamente las dependencias de compilación. Si lo saltas, tendrás que
instalarlas a mano.

Edita el archivo `/etc/apt/sources.list` como root:

```bash
sudo nano /etc/apt/sources.list
```

Busca las líneas que empiezan por `deb-src` y asegúrate de que **no** están
comentadas (sin `#` al principio). Deben verse así:

```
deb-src http://deb.debian.org/debian bookworm main
deb-src http://deb.debian.org/debian-security bookworm-security main
deb-src http://deb.debian.org/debian bookworm-updates main
```

Guarda el archivo y actualiza:

```bash
sudo apt update
```

---

## Paso 4 — Instalar las dependencias de compilación

Desde la carpeta raíz del repositorio (donde está la carpeta `debian/`):

```bash
sudo apt build-dep .
```

Este comando lee el campo `Build-Depends:` de `debian/control` e instala
todo lo necesario automáticamente.

> Si ves el error `E: You must put some 'source' URIs in your sources.list`,
> vuelve al Paso 3 y habilita las líneas `deb-src`.

Si prefieres instalar las dependencias a mano sin tocar `sources.list`:

```bash
sudo apt install \
  debhelper-compat \
  dh-python \
  python3-all \
  pyqt6-dev-tools \
  qt6-tools-dev-tools
```

---

## Paso 5 — Construir el paquete

Desde la carpeta raíz del repositorio ejecuta:

```bash
debuild -us -uc -b
```

¿Qué significan esas opciones?

- `-us` — "unsigned source": no firma el paquete fuente (no necesitas GPG
  para pruebas locales).
- `-uc` — "unsigned changes": no firma el archivo `.changes`.
- `-b` — construye solo el paquete binario (el `.deb`), no el fuente.

Verás mucho texto en la terminal. Si todo va bien, las últimas líneas serán
algo como:

```
dpkg-deb: building package 'xinput-plus' in '../xinput-plus_6.6.4-1_all.deb'.
...
dpkg-buildpackage: info: binary-only upload (no source included)
```

El archivo `.deb` se crea **en el directorio padre**, es decir, un nivel
arriba de donde está el repositorio:

```bash
ls ../xinput-plus_*.deb
# ../xinput-plus_6.6.4-1_all.deb
```

### ¿Qué hacer si la compilación falla?

Lee el mensaje de error con calma. Los errores más comunes son:

**"command not found: lrelease-qt6"**
Instala `qt6-tools-dev-tools`:
```bash
sudo apt install qt6-tools-dev-tools
```

**"dh: error: unable to load addon python3"**
Instala `dh-python`:
```bash
sudo apt install dh-python
```

**"Makefile:X: *** missing separator. Stop."**
El archivo `debian/rules` tiene espacios donde debería haber tabuladores.
Ábrelo con un editor que muestre caracteres invisibles y reemplaza los
espacios de indentación por tabuladores reales.

**"dpkg-source: error: can't build with source format '3.0 (quilt)'"**
Falta el archivo `debian/source/format`. Créalo:
```bash
echo "3.0 (quilt)" > debian/source/format
```

---

## Paso 6 — Revisar el paquete con lintian

`lintian` analiza el `.deb` y el `.changes` en busca de errores de política
Debian. Ejecuta:

```bash
lintian --pedantic ../xinput-plus_6.6.4-1_all.deb
```

La salida usa estas letras para indicar la gravedad:

| Letra | Significado |
|-------|-------------|
| `E:` | **Error** — problema grave, el paquete sería rechazado |
| `W:` | **Warning** — advertencia, hay que corregirlo |
| `I:` | **Info** — problema menor, corregir si es fácil |
| `P:` | **Pedantic** — sugerencia de estilo, opcional |

Si ves errores `E:`, corrígelos antes de continuar. Para entender qué
significa cualquier etiqueta:

```bash
lintian-explain-tags nombre-de-la-etiqueta
```

Por ejemplo:

```bash
lintian-explain-tags no-upstream-changelog
```

También puedes buscarla en https://lintian.debian.org/tags/

El objetivo es llegar a una salida limpia, sin líneas `E:` ni `W:`.

---

## Paso 7 — Instalar el .deb y probar el programa

Instala el paquete con `apt` (recomendado porque resuelve dependencias
automáticamente):

```bash
sudo apt install ../xinput-plus_6.6.4-1_all.deb
```

> Si `apt` dice que no puede encontrar el archivo, asegúrate de usar la
> ruta correcta. El `../` indica que el archivo está en el directorio padre.

Ahora prueba el programa:

```bash
# Lanzar normalmente:
xinput-plus

# Lanzar en español:
xinput-plus --lang=es

# Lanzar en inglés:
xinput-plus --lang=en
```

Comprueba también que el manual está instalado:

```bash
man xinput-plus
```

Y que aparece en el menú de aplicaciones de tu escritorio (si usas uno).

---

## Paso 8 — Desinstalar el paquete

Cuando termines de probar:

```bash
# Desinstala pero conserva los archivos de configuración del usuario:
sudo apt remove xinput-plus

# Desinstala y elimina también los archivos de configuración:
sudo apt purge xinput-plus
```

---

## Flujo de trabajo para hacer cambios y volver a compilar

Cuando modificas el código y quieres probar una nueva versión, el flujo
habitual es:

**1. Haz tus cambios en el código.**

**2. Añade una entrada al changelog:**

```bash
dch -v 6.6.4-2 "Descripción del cambio que hiciste."
```

Esto abre el editor con la nueva entrada lista. Guarda y cierra.

**3. Marca la entrada como lista (cambia UNRELEASED a unstable):**

```bash
dch -r ""
```

**4. Limpia los artefactos de la compilación anterior:**

```bash
debian/rules clean
```

**5. Vuelve a compilar:**

```bash
debuild -us -uc -b
```

**6. Instala la nueva versión:**

```bash
sudo apt install ../xinput-plus_6.6.4-2_all.deb
```

`apt` detectará que ya tienes una versión instalada y la actualizará
automáticamente.

---

## Compilación en entorno limpio con pbuilder (opcional pero recomendado)

El método anterior compila en tu sistema, que tiene muchos paquetes
instalados. Esto puede ocultar dependencias que faltan en `debian/control`.
`pbuilder` construye en un entorno mínimo aislado, igual que lo haría el
servidor oficial de Debian.

### Configurar pbuilder (solo la primera vez)

```bash
sudo apt install pbuilder
```

Crea un chroot para la distribución objetivo. Usa `unstable` si estás
preparando un paquete para Debian (recomendado), o `bookworm` si solo
quieres probar localmente en Debian 12:

```bash
sudo pbuilder create --distribution unstable
```

Esto descarga un sistema Debian mínimo y lo guarda como imagen. Tarda unos
minutos la primera vez.

### Construir con pbuilder

Ejecuta estos comandos desde dentro del directorio del proyecto
(p. ej. `~/Dev/xinput-plus-dev/xinput-plus`):

```bash
# 1. Crear el tarball orig upstream (requerido por el formato de fuentes 3.0 (quilt))
tar --exclude=./debian --exclude=./.git -czf ../xinput-plus_6.6.4.orig.tar.gz .

# 2. Construir el paquete fuente
debuild -us -uc -S

# 3. Construir el paquete binario dentro del chroot limpio
sudo pbuilder build --distribution unstable ../xinput-plus_6.6.4-1.dsc
```

Tras una compilación exitosa el directorio padre contendrá:

```
xinput-plus_6.6.4-1.dsc
xinput-plus_6.6.4-1.debian.tar.xz
xinput-plus_6.6.4-1_source.build
xinput-plus_6.6.4-1_source.buildinfo
xinput-plus_6.6.4-1_source.changes
xinput-plus_6.6.4.orig.tar.gz
```

El `.deb` construido y los archivos relacionados se colocan en el directorio
de resultados de pbuilder:

```
/var/cache/pbuilder/result/xinput-plus_6.6.4-1_all.deb
/var/cache/pbuilder/result/xinput-plus_6.6.4-1_amd64.buildinfo
/var/cache/pbuilder/result/xinput-plus_6.6.4-1_amd64.changes
/var/cache/pbuilder/result/xinput-plus_6.6.4.orig.tar.gz
```

Instala y prueba el resultado:

```bash
sudo apt install /var/cache/pbuilder/result/xinput-plus_6.6.4-1_all.deb
xinput-plus
xinput-plus --lang=es
man xinput-plus
sudo apt purge xinput-plus
```

### ¿Por qué usar pbuilder?

Si `pbuilder` falla pero `debuild` funciona, significa que te falta declarar
alguna dependencia en `Build-Depends:` de `debian/control`. Esto es
exactamente el tipo de error que el equipo de Debian detectaría al revisar
tu paquete, así que es mejor encontrarlo tú primero.

> **Nota sobre el tarball orig:** El paso con `tar` es necesario porque
> `debian/source/format` es `3.0 (quilt)`, que requiere un tarball upstream
> separado. Sin él, `debuild -S` fallará con:
> `dpkg-source: error: can't build with source format '3.0 (quilt)'`.

---

## Resumen rápido

```bash
# 1. Instalar herramientas (solo una vez)
sudo apt install build-essential devscripts debhelper dh-python \
                 pyqt6-dev-tools qt6-tools-dev-tools lintian

# 2. Clonar el repositorio
git clone https://github.com/wachin/xinput-plus
cd xinput-plus

# 3. Instalar dependencias de compilación
sudo apt build-dep .

# 4. Compilar
debuild -us -uc -b

# 5. Revisar con lintian
lintian --pedantic ../xinput-plus_6.6.4-1_all.deb

# 6. Instalar y probar
sudo apt install ../xinput-plus_6.6.4-1_all.deb
xinput-plus

# 7. Desinstalar cuando termines
sudo apt purge xinput-plus
```
