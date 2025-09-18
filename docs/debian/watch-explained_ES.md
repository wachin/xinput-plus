
## ¿Qué es `debian/watch` y qué hace `uscan`?

* **`debian/watch`** le dice a **`uscan`** dónde mirar las *nuevas versiones* de tu código “upstream” (tu repositorio).
* `uscan`:

  1. Lee tu versión actual desde `debian/changelog`.
  2. Descarga una **página índice** (por ejemplo `/tags` en GitHub).
  3. Busca enlaces que **contengan un número de versión** usando una **expresión regular** (regex).
  4. Elige la **más nueva** y descarga el tarball.
  5. Lo renombra con `filenamemangle` para que se llame como **Debian espera** (`xinput-plus-<versión>.tar.gz`).
  6. Llama a `mk-origtargz` para colocarlo en `../xinput-plus_<versión>.orig.tar.gz` (a veces como *symlink*).

---

## El archivo `debian/watch` actual (vía GitHub *tags*)

```watch
version=4
opts=filenamemangle=s%.*archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz%xinput-plus-$1.tar.gz% \
  https://github.com/wachin/xinput-plus/tags .*/archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz
```

### Línea 1: `version=4`

* Formato moderno del fichero *watch* (hay que usar `4`).

### Línea 2: `opts=...` y la **URL + regex**

* El formato de la línea es:
  **`<URL_base> <regex_para_enlaces>`**

* `https://github.com/wachin/xinput-plus/tags` es la **página índice** que `uscan` va a descargar y analizar.

* El segundo campo es una **regex** que busca los enlaces reales de descarga dentro de esa página:

  ```
  .*/archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz
  ```

  * `v?` → la “v” es **opcional** (cubre `v6.6.2` y `6.6.2`).
  * `(\d[\d\.]*)` → **captura** la parte de versión: empieza por un dígito y sigue con dígitos o puntos (`6`, `6.6`, `6.6.2`, etc.).
  * Esa **captura** (el grupo `(...)`) es **\$1** y la usaremos abajo para renombrar el fichero.

* `filenamemangle=...` → regla para **renombrar** el archivo descargado:

  ```
  s%.*archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz%xinput-plus-$1.tar.gz%
  ```

  Traducción:
  “Si el nombre/URL coincide con `.../archive/refs/tags/v<versión>.tar.gz`, renómbralo a `xinput-plus-<versión>.tar.gz`”.

  **¿Por qué?**
  Porque GitHub descarga como `v6.6.2.tar.gz`. Debian espera `xinput-plus-6.6.2.tar.gz`. Si no renombraras, `dpkg-source` se quejaría o no casaría bien con tu paquete.

> #### Pitfalls típicos (lo que te salió en pantalla)
>
> * A veces verás **el mismo enlace dos veces** en la salida de `uscan` (“Found the following matching hrefs…”) — GitHub puede repetir el anchor o mostrarlo arriba y en una vista comprimida. **No es problema**.
> * Si tus tags son `v6.6.2` (con “v”), tu regex ya los soporta (`v?`); si algún día usas `6.6.2` sin “v”, también funcionará.

---

## ¿Y la firma OpenPGP? (lintian: `debian-watch-does-not-check-openpgp-signature`)

* Tu watch busca **auto-tarballs** de GitHub (`/archive/refs/tags/...`). Esos **no** vienen con `.asc`, así que **no puedes** verificar firma.
  → lintian te lo marca como **X: informativo** (no bloquea).

**Si quieres verificación de firma de verdad:**

### Opción A (recomendada a medio plazo): subir **assets** propios firmados en Releases

1. En GitHub **Releases**, sube tus propios archivos:
   `xinput-plus-6.6.2.tar.xz` y `xinput-plus-6.6.2.tar.xz.asc` (firmado con tu GPG).
2. Usa un `watch` que apunte a **Releases + assets** y construya la URL de la firma con `pgpsigurlmangle`.

Ejemplo:

```watch
version=4
opts=\
  uversionmangle=s/^v//,\
  filenamemangle=s%.*/download/v?(\d[\d\.]*)/xinput-plus-\1\.tar\.xz%xinput-plus-$1.tar.xz%,\
  pgpsigurlmangle=s/$/.asc/
https://github.com/wachin/xinput-plus/releases .*/download/v?(\d[\d\.]*)/xinput-plus-\1\.tar\.xz
```

* `uversionmangle=s/^v//` → a la **versión upstream** (`v6.6.2`) le quita la “v” para comparar con tu `debian/changelog` (`6.6.2`).
* La regex busca enlaces del estilo:
  `.../releases/download/v6.6.2/xinput-plus-6.6.2.tar.xz`
* `pgpsigurlmangle=s/$/.asc/` → le dice a `uscan` que la firma está en la **misma URL + `.asc`**.

> **Ventaja**: ahora sí puedes tener **verificación criptográfica**.
> **Desventaja**: requiere que *tú* subas los assets firmados por cada release.

### Opción B: seguir con `/tags` (como ahora)

* Más simple. Sin firma. lintian te dejará una nota informativa.

---

## ¿Qué pasa si mi versión tiene sufijos? (`rc1`, `beta`, etc.)

* La parte `(\d[\d\.]*)` solo captura números y puntos.
  Si algún día quieres permitir sufijos tipo `-rc1`, `~beta1`, etc., usarías otra regex y, a veces, necesitarás **mangles**:

  * `uversionmangle` → transforma la versión *upstream* que encontró `uscan`.
  * `dversionmangle` → transforma la versión *debian* (de tu `debian/changelog`) para compararla con la upstream.

Ejemplo (permitir `-rc1` en upstream y convertirlo a `~rc1` para que “orden” sea menor que la final):

```watch
version=4
opts=\
  uversionmangle=s/-rc/~rc/;\
  filenamemangle=s%.*archive/refs/tags/v?(\d[\d\.~-]*)\.tar\.gz%xinput-plus-$1.tar.gz%
https://github.com/wachin/xinput-plus/tags .*/archive/refs/tags/v?(\d[\d\.~-]*)\.tar\.gz
```

*(No lo necesitas hoy; solo para que sepas que existe.)*

---

## ¿Y si hay que limpiar el tarball? (`+ds`, `files-excluded`)

* Si algún día **reempacas** para excluir cosas ( blobs precompilados, etc.), usarás:

  * `debian/copyright`: `Files-Excluded: ...`
  * `debian/watch`: `opts=repacksuffix=+ds, ...`
* `uscan` descargará, **reempacará** y añadirá `+ds` a la versión del `.orig.tar.*`.

*(No es tu caso ahora, porque tu icono es CC0 y no tienes binarios precompilados.)*

---

## ¿Por qué aparece el aviso “prefer-uscan-symlink”?

* Lintian a veces informa (X:) que es **preferible** que `uscan` deje un **symlink** al `.orig.tar.*` en lugar de copiarlo.
* En tu flujo ya viste mensajes de “Successfully symlinked …” → **estás bien**. Es informativo.

---

## Variantes listas-para-usar

### A) **La que ya usas** (simple, sin firma, `/tags`):

```watch
version=4
opts=filenamemangle=s%.*archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz%xinput-plus-$1.tar.gz%
https://github.com/wachin/xinput-plus/tags .*/archive/refs/tags/v?(\d[\d\.]*)\.tar\.gz
```

### B) **Con firma**, usando **Releases + assets firmados**:

```watch
version=4
opts=\
  uversionmangle=s/^v//,\
  filenamemangle=s%.*/download/v?(\d[\d\.]*)/xinput-plus-\1\.tar\.xz%xinput-plus-$1.tar.xz%,\
  pgpsigurlmangle=s/$/.asc/
https://github.com/wachin/xinput-plus/releases .*/download/v?(\d[\d\.]*)/xinput-plus-\1\.tar\.xz
```

*(Cambia `.tar.xz` por el formato que publiques.)*

---

## Buenas prácticas rápidas

* **No cambies el nombre de tus tags** una vez publicados.
* **Publica** la misma **versión** en `debian/changelog` que etiquetas upstream (`6.6.2` vs `v6.6.2` → usa `uversionmangle=s/^v//` si tiras de Releases).
* Si miras `/tags`, tu regex ya acepta `v` opcional (perfecto para GitHub).
* Si migras a assets firmados, **sube `.tar.xz` y `.tar.xz.asc`** en cada Release y cambia el `watch` a la variante B.

---

## Cómo probar tu `watch`

```bash
uscan --verbose --force-download
# Mira qué URL encontró, qué versión detectó,
# y cómo renombró el archivo con filenamemangle.
```

Si todo cuadra, verás:

* “Newest version …”
* “Downloading upstream package…”
* “Renamed upstream package to: xinput-plus-\<versión>.tar.gz”
* (opcional) “Successfully symlinked … to …orig.tar.gz”

---

## En conclusión
`debian/watch`: mira las siguientes cosas, cómo encuentra versiones, cómo renombra, cómo añadir firma, y cómo evitar los avisos de error

