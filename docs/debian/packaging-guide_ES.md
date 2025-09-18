
# Guía completa: empaquetar `xinput-plus` para Debian y subirlo a mentors & Salsa

> Objetivo: partir de tu repo de código, crear `debian/`, construir el paquete, verificar calidad, y subir el **source package** firmado a [mentors.debian.net](https://mentors.debian.net). Además, dejar listo el repositorio en Salsa.

---

## 0) Requisitos del sistema

Instala las herramientas básicas:

```bash
sudo apt update
sudo apt install build-essential devscripts debhelper dh-python \
                 pyqt6-dev-tools qt6-tools-dev-tools \
                 lintian appstream appstream-util desktop-file-utils \
                 uscan quilt
```

* **`dh-python`** proporciona `dh-sequence-python3`.
* **`qt6-tools-dev-tools`** proporciona `lrelease-qt6`/`linguist-qt6`.
* **`devscripts`** trae `dch`, `debuild`, `dput`, etc.

> ### Errores típicos que podrían pasar si no se hace así
>
> * Sino se instala `dh-python` faltará `dh-sequence-python3`

---

## 1) Estructura del proyecto

Tu árbol final (tras instalar el .deb) queda así:

```
/usr/bin/xinput-plus
/usr/share/applications/xinput-plus.desktop
/usr/share/metainfo/xinput-plus.metainfo.xml
/usr/share/icons/hicolor/scalable/apps/xinput-plus.svg
/usr/share/xinput-plus/i18n/xinput-plus_es.qm
/usr/share/doc/xinput-plus/{changelog.Debian.gz,changelog.gz,copyright}
```

En el **código**:

* Asegúrate de que **buscas traducciones** en `/usr/share/xinput-plus/i18n` (y en `./i18n` durante desarrollo).
* El **icono** se obtiene con `QIcon.fromTheme("xinput-plus")` y *fallbacks* a rutas instaladas y a `src/emucon.svg`.

> ### Errores típicos que podrían pasar si no se hace así
>
> * El programa solo miraba `./i18n` y `./src`
>  Para hacer esto está añadido un loader robusto (rutas del sistema + dev) y el helper `get_app_icon()`.

---

## 2) El directorio `debian/`

Este es mi fichero debian/control, lo puedes modificar y ajustar campos con tus datos:

### `debian/control`

```debcontrol
Source: xinput-plus
Section: x11
Priority: optional
Maintainer: Washington Indacochea Delgado <wachin.id@gmail.com>
Build-Depends:
 debhelper-compat (= 13),
 dh-python,
 pyqt6-dev-tools,
 qt6-tools-dev-tools
Standards-Version: 4.6.2
Rules-Requires-Root: no
Homepage: https://github.com/wachin/xinput-plus
Vcs-Git: https://salsa.debian.org/wachin/xinput-plus.git
Vcs-Browser: https://salsa.debian.org/wachin/xinput-plus

Package: xinput-plus
Architecture: all
Depends: ${python3:Depends}, ${misc:Depends}, python3-pyqt6, xinput, libqt6svg6, libinput-tools, python3-simplejson
Recommends: qt6-translations-l10n
Description: PyQt6 GUI to adjust pointer speed per device (Xorg, via xinput)
 xinput-plus is a simple GUI to manage per-device pointer acceleration for Xorg.
 It supports device-specific profiles by ID or by name, a whitelist to hide
 virtual/master/XTEST devices, and a CTM fallback when “libinput Accel Speed”
 is not exposed by xinput. Translations are supported via Qt .qm files.
 .
 Note: xinput works on Xorg. On Wayland, this tool will not function.
```

### `debian/rules`

En este programa no se usa `pybuild`en `debian/rules` sino un archivo simple:

```make
#!/usr/bin/make -f
export DH_VERBOSE=1

%:
	dh $@

override_dh_auto_build:
	# Compilar traducciones (.ts -> .qm), si existen
	if [ -d i18n ]; then \
	  (command -v lrelease-qt6 >/dev/null && lrelease-qt6 i18n/xinput-plus_*.ts) || \
	  (command -v lrelease >/dev/null && lrelease i18n/xinput-plus_*.ts) || true; \
	fi

override_dh_auto_install:
	# Binario
	install -D -m0755 xinput-plus.py debian/xinput-plus/usr/bin/xinput-plus

	# Desktop + AppStream
	install -D -m0644 debian/xinput-plus.desktop \
	  debian/xinput-plus/usr/share/applications/xinput-plus.desktop
	install -D -m0644 debian/xinput-plus.metainfo.xml \
	  debian/xinput-plus/usr/share/metainfo/xinput-plus.metainfo.xml

	# Icono
	install -D -m0644 src/emucon.svg \
	  debian/xinput-plus/usr/share/icons/hicolor/scalable/apps/xinput-plus.svg

	# Traducciones (.qm)
	if ls i18n/xinput-plus_*.qm >/dev/null 2>&1; then \
	  install -d debian/xinput-plus/usr/share/xinput-plus/i18n; \
	  install -m0644 i18n/xinput-plus_*.qm \
	    debian/xinput-plus/usr/share/xinput-plus/i18n/; \
	fi
```

### `debian/changelog`

Se edita con `dch`. Para una nueva versión:

```bash
dch -v 6.6.2-1 "New upstream release 6.6.2. Sync docs and metadata."
```

y con el siguiente comando  se abre desde la terminal el archivo hacer alguna edición:

```bash
dch -r
```

> ### Errores típicos que podrían pasar si no se hace así
>
> * Si etiquetaste `v6.6.2` pero dejaste `debian/changelog` en `6.6.1-1` → lintian avisará “possible-new-upstream-release-without-new-version”.
>   **Solución:** **siempre** sincroniza `debian/changelog` con la etiqueta más reciente.

### `debian/source/format`

En este archivo está escrito lo siguiente:

```
3.0 (quilt)
```

### `debian/watch`

```watch
version=4
opts=filenamemangle=s%.*archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz%xinput-plus-$1.tar.gz% \
  https://github.com/wachin/xinput-plus/tags .*/archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz
```

> ### Nota:
>
> * watch no verifica firma OpenPGP (lintian `X: debian-watch-does-not-check-openpgp-signature`) → **informativo**. Puedes añadir firma más adelante si firmas tus tarballs.
> * Usa `/tags` y patrón con `v6.6.2`.



### `debian/xinput-plus.desktop`

* `Icon=xinput-plus` (sin extensión)
* Valídalo con:

```bash
desktop-file-validate debian/xinput-plus.desktop
```

### `debian/xinput-plus.metainfo.xml`

* **Obligatorio:** `<metadata_license>CC0-1.0</metadata_license>` (AppStream exige licencia permisiva para **metadatos**).
* `<project_license>GPL-3.0-or-later</project_license>` (este software es GPLv3+).

Validar con:

```bash
appstreamcli validate --pedantic debian/xinput-plus.metainfo.xml
```

> ### Errores típicos que podrían pasar si no se hace así
>
> * Si la licencia en <metadata_license> es diferente da  → **Error** en AppStream.
>   **Solución:** CC0-1.0 para *metadata*. Aun así el **código** sigue GPL-3+.

### `debian/copyright` (formato DEP-5)

Estos son los copyright que le puse:

```
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: xinput-plus
Source: https://github.com/wachin/xinput-plus

Files: *
Copyright: 2024-2025 Washington Indacochea Delgado <wachin.id@gmail.com>
License: GPL-3+
 On Debian systems, the full text of the GNU General Public License
 version 3 can be found in /usr/share/common-licenses/GPL-3.

Files: debian/*
Copyright: 2025 Washington Indacochea Delgado <wachin.id@gmail.com>
License: GPL-3+
 On Debian systems, the full text of the GNU General Public License
 version 3 can be found in /usr/share/common-licenses/GPL-3.

Files: debian/xinput-plus.metainfo.xml
Copyright: 2025 Washington Indacochea Delgado <wachin.id@gmail.com>
License: CC0-1.0
 Creative Commons Zero v1.0 Universal (CC0 1.0).
 https://creativecommons.org/publicdomain/zero/1.0/legalcode

Files: src/emucon.svg
Comment:
 Derived from “Joystick Icon (OpenEmu icon Yosemite)” on Openclipart.
 Title: Joystick Icon
 URL: https://openclipart.org/detail/239389/openemu-icon-yosemite
 Author: toranonly (https://openclipart.org/artist/toranonly)
 Uploaded: 2016-01-31
 “An old style joystick from playing video games.”
License: CC0-1.0
 Creative Commons Zero v1.0 Universal (CC0 1.0).
 https://creativecommons.org/publicdomain/zero/1.0/legalcode
```

> ### Errores que podrían pasar si no se hace así:
>
> * Para que Lintian  no de este error `no-dep5-copyright` → **usa** el formato DEP-5.
> * Licencias inconsistentes con AppStream o el icono → **decláralas por archivo**.

---

## 3) Versionado y etiquetas upstream

Como **yo soy el upstream** (“upstream” = el proyecto/autor original del software que publica el código fuente y las releases; a partir de ahí, las distribuciones Debian lo empaquetan “downstream”), lo ideal es:

```bash
# commit de cambios (README, CHANGELOG, etc.)
git commit -am "Upstream: docs and metadata updates"

# etiquetar release
git tag -a v6.6.2 -m "Upstream release 6.6.2"
git push origin main v6.6.2

# actualizar debian/changelog
dch -v 6.6.2-1 "New upstream release 6.6.2. Sync docs and metadata."
dch -r
```

> ### Errores típicos que podrían pasar si no se hace así
>
> * Cambiaste cosas en el árbol que no estaban en el tarball upstream (p.ej. algún archivo nuevo que se ponga en el repositorio) → `dpkg-source` aborta por “cambios locales”.
>   **Solución:** no metas archivos personales en el repo o añádelos a `.gitignore`.
>   **Nunca pongas `.dput.cf` dentro del repo** (va en `~/.dput.cf`).

---

## 4) `uscan` y tarball original

`uscan` descarga el tarball de GitHub a partir de `debian/watch` y crea el `xinput-plus_6.6.2.orig.tar.gz`:

```bash
uscan --verbose --force-download
```

---

## 5) Construir **paquete fuente** firmado (para mentors)

Primero, crea tu **clave GPG de 4096-bit** y configúrala (ver tutorial más abajo). Luego:

```bash
debian/rules clean || true
debuild -S -sa -k<YOUR_LONG_KEYID>
```

Si quieres probar sin firmar:

```bash
debuild -S -sa -us -uc
```

Revisa con `lintian`:

```bash
lintian ../xinput-plus_*_source.changes
```

> ### Errores típicos que podrían pasar si no se hace así
>
> * Sin GPG: “No secret key”.
> * Con GPG nuevo: **subiste** la clave en mentors y la usaste en `-k<KEYID>` → perfecto.

---

## 6) Subir a mentors

Configura `~/.dput.cf` (ojo al **incoming**):

```ini
[mentors]
fqdn = mentors.debian.net
method = https
incoming = /upload
allow_unsigned_uploads = 0
progress_indicator = 2
# Permitir subidas con UNRELEASED si hiciera falta:
allowed_distributions = .*
```

Sube:

```bash
dput mentors ../xinput-plus_6.6.2-1_source.changes
```

Comprueba en tu página de mentors.

**Explicación.-** En **dput**, el campo **`incoming`** es **la ruta del servidor** (no de tu PC) a la que se suben los ficheros firmados del paquete fuente (`.dsc`, `.changes`, `.orig.tar.*`, `.debian.tar.*`, `.buildinfo`).
Piensa en ello como el **“endpoint de subida”** del servicio.

* En **mentors.debian.net** debe ser **`/upload`** (exactamente así).
* Si pones otra cosa (p. ej. `/uploads/`), el servidor responde **404 Not Found** porque estás apuntando a una ruta que no existe.
* No es el directorio final donde quedará tu paquete; es solo el **punto de entrada**. Después, el servidor mueve y procesa los ficheros y los muestra en tu página de mentors.

### Mini-FAQ

* **¿Es una carpeta local?** No, es la **ruta remota** en el servidor.
* **¿Tiene que terminar con “/”?** No es necesario; `/upload` funciona.
* **Me da 404** → casi siempre es `incoming` mal puesto.
* **Me da 401/403** → clave GPG no asociada a tu cuenta o problema de firma/autorización.
* **Cómo comprobar** → `dput -d mentors …` para ver salida detallada.

---

## 7) Construir e instalar **.deb local** para test

Activa `deb-src` en `/etc/apt/sources.list` pero es posible que ya esté activado, en Debian 12 yo tengo así:

```plaintext
deb http://deb.debian.org/debian/ bookworm main non-free-firmware non-free contrib 
deb-src http://deb.debian.org/debian/ bookworm main non-free-firmware non-free contrib 

deb http://security.debian.org/debian-security/ bookworm-security main non-free-firmware 
deb-src http://security.debian.org/debian-security/ bookworm-security main non-free-firmware 

# bookworm-updates, to get updates before a point release is made;
# see https://www.debian.org/doc/manuals/debian-reference/ch02.en.html#_updates_and_backports
deb http://deb.debian.org/debian/ bookworm-updates main non-free-firmware 
deb-src http://deb.debian.org/debian/ bookworm-updates main non-free-firmware 
```

 (si quieres usa `apt build-dep`). 
 
Luego:

```bash
sudo apt-get build-dep . || true   # opcional

debian/rules clean || true
debuild -us -uc -b

sudo apt install ../xinput-plus_6.6.2-1_all.deb

# ejecutar
xinput-plus --lang=es
```

**Nota**: Una vez instalado ya no es necesario escribir xinput-plus.py

> ### Errores típicos que podrían pasar si no se hace así
>
> * Un error que me pasaba es que en el dir de traducciones no se creaba esta al instalar → ya corregido en `rules`.

---

## 8) Verificaciones útiles

```bash
# Valida .desktop
desktop-file-validate debian/xinput-plus.desktop

# Valida AppStream (metainfo)
appstreamcli validate --pedantic debian/xinput-plus.metainfo.xml

# Lintian (lee las notas y decide si corregir ahora o más tarde)
lintian ../xinput-plus_*_source.changes
```

Lintian “info/pedantic” que viste (no bloqueantes):

* `out-of-date-standards-version` (pon 4.7.2 cuando migres a testing/unstable recientes)
* `maintainer-desktop-entry` / `maintainer-manual-page` (asegúrate de mantenerlos)
* `very-long-line-length-in-source-file` (informativo)
* `upstream-metadata-file-is-missing` (opcional: añade `debian/upstream/metadata` en el futuro)

---

## 9) Subir a Salsa

Como ya tengo el proyecot en github lo puedo Importar:

* Entra a `https://salsa.debian.org/`,  y usa **Import project** desde GitHub.

En `debian/control` entonces puse:

```
Vcs-Git: https://salsa.debian.org/wachin/xinput-plus.git
Vcs-Browser: https://salsa.debian.org/wachin/xinput-plus
```

> Consejo: puedes mantener **el código y el empaquetado juntos** (como ahora), o usar ramas (`debian/sid`) con `git-buildpackage` más adelante.

---

## 10) Tutorial de GPG (4096 bits) Keys for Debian Packaging

### 📋 Prerequisites
- Have an account at [mentors.debian.net](https://mentors.debian.net)
- Have `gpg` installed (comes by default in Debian)

---

### 1. **Create a GPG Key (if you don't have one)**

### Interactive Method:

```bash
gpg --full-generate-key
````

**Selections:**

* Key type: **1** (RSA and RSA)
* Key size: **4096**
* Validity: **2y** (2 years)
* Name and email: **Your full name and email**

### Automated Method (batch):

```bash
gpg --batch --generate-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: Your Full Name
Name-Email: your-email@domain.com
Expire-Date: 2y
%commit
EOF
```

---

## 2. **Verify Existing Keys**

```bash
gpg --list-keys
```

---

## 3. **Export Public Key in Required Format**

```bash
gpg --export --export-options export-minimal --armor YOUR_KEYID
```

---

## 4. **Configure Key on mentors.debian.net**

1. Go to mentors.
2. Log in and open your profile.
3. Paste the full ASCII-armored key.
4. Save.

---

## 5. **Upload Key to Keyservers (recommended)**

```bash
gpg --send-keys YOUR_KEYID
```


---

## 7. **Useful GPG Management Commands**

```bash
gpg --list-secret-keys --keyid-format LONG
gpg --export-secret-keys --armor YOUR_KEYID > my-private-key.asc
gpg --import my-private-key.asc
gpg --edit-key YOUR_KEYID   # then: expire
```

---

## 8. **Verify Everything Works**

```bash
echo "test" | gpg --clearsign
```

---

## 🚨 Best Practices

* Backup your private key safely.
* Use 1–2 years expiry.
* Protect with a strong passphrase.
* Generate a revocation certificate.

---

## 🔧 Troubleshooting

```bash
export GPG_TTY=$(tty)       # if pinentry issues
chmod 700 ~/.gnupg          # permissions
```

````

---

## 11) Resumen de errores que solucionaste (y cómo evitarlos)

1) **metadata_license inválida (AppStream)** → usa **CC0-1.0** en metainfo.  
2) **Inconsistencia de licencias** → declara en `debian/copyright`:
   - `*` y `debian/*` → **GPL-3+**
   - `debian/xinput-plus.metainfo.xml` → **CC0-1.0**
   - `src/emucon.svg` → **CC0-1.0** (Openclipart)
3) **Changelog no sincronizado con tag** → `dch -v <upstream>-1`, `dch -r`, etiqueta `v<upstream>`.
4) **Archivo personal dentro del repo (`.dput.cf`)** → muévelo a `~/.dput.cf` y añádelo a `.gitignore`.
5) **Error al copiar .qm** → crea el directorio antes (`install -d`) y luego copia.
6) **Icono/idiomas no cargan tras instalar** → loader robusto: busca en `/usr/share/xinput-plus/i18n` y `QIcon.fromTheme`.
7) **dput 404** → `incoming=/upload` (no `/uploads/`).
8) **Sin GPG o clave pobre** → Crea una de 4096 y usa `-k<KEYID>` al firmar el source package.

---

## 12) Flujo sugerido para futuras versiones

```bash
# 1) Cambios en código y docs
git commit -am "Feature/fix"

# 2) Etiqueta upstream
git tag -a v6.7.0 -m "Upstream release 6.7.0"
git push origin main v6.7.0

# 3) Changelog Debian
dch -v 6.7.0-1 "New upstream release 6.7.0."
dch -r

# 4) uscan & build source
uscan --verbose --force-download
debuild -S -sa -kYOUR_KEYID

# 5) Revisiones
lintian ../xinput-plus_*_source.changes
appstreamcli validate --pedantic debian/xinput-plus.metainfo.xml

# 6) Upload mentors
dput mentors ../xinput-plus_6.7.0-1_source.changes
````


