# xinput-plus — Fix Roadmap for Debian Packaging

This file tracks every issue found during the pre-upload review of this
repository. The goal is to get the package accepted into Debian unstable
(and eventually stable). Each item is marked with its current status.

Legend:
- `[ ]` — not yet fixed
- `[x]` — fixed

Issues are grouped by file and ordered from most critical (would cause
rejection in the NEW queue or by `lintian`) to minor (style / quality).

---

## `debian/changelog`

- [ ] **CRITICAL — Duplicate version entry.**
  Version `6.6.1-1` appears twice with different timestamps and different
  descriptions. `dpkg` and `lintian` will reject this. Remove or renumber
  one of the two entries.

- [ ] **CRITICAL — Top entry says `UNRELEASED`.**
  `UNRELEASED` is a local work-in-progress marker. Before uploading to
  Debian the suite must be changed to `unstable`. Change:
  ```
  xinput-plus (6.6.4-1) UNRELEASED; urgency=medium
  ```
  to:
  ```
  xinput-plus (6.6.4-1) unstable; urgency=medium
  ```

- [ ] **CRITICAL — Version mismatch across the project.**
  The Python file header says `v6.5`, the top changelog entry says `6.6.4`,
  and `debian/xinput-plus.metainfo.xml` only lists releases up to `6.6`.
  All three must agree on the current version. See also the metainfo item
  below.

- [ ] **Minor — Changelog entry for `6.6.1-1` describes `6.6.2`.**
  The first `6.6.1-1` entry reads `"New upstream release 6.6.2. Sync docs
  and metadata."` — the version number in the description does not match
  the entry version. Fix the description to say `6.6.1`.

---

## `debian/control`

- [ ] **Minor — `Standards-Version` is outdated.**
  The file declares `4.6.2`. The current version as of 2025 is `4.7.0`.
  Update the field and review the policy changes between the two versions:
  https://www.debian.org/doc/debian-policy/upgrading-checklist.html

- [ ] **Minor — `Vcs-Git` should end in `.git`.**
  Change:
  ```
  Vcs-Git: https://salsa.debian.org/wachin/xinput-plus.git
  ```
  Also confirm the Salsa repository actually exists before uploading.

- [ ] **Minor — Trailing blank lines at end of file.**
  There are two blank lines after the long description. Remove them; one
  blank line between stanzas is the maximum.

- [ ] **Minor — `libqt6svg6` note for Bookworm vs. Trixie/Sid.**
  On Debian 12 (Bookworm) and Debian 13 (Trixie) the package is named
  `libqt6svg6` — confirmed on packages.debian.org. No alternative name is
  needed. The current `Depends:` line is correct for both releases.
  *(No change required; recorded here for future reference.)*

- [ ] **Minor — Add `Suggests:` for optional theming packages.**
  `qt6ct` and `qt6-style-kvantum` are documented in the README as the way
  to enable dark themes. Add them as suggestions:
  ```
  Suggests: qt6ct, qt6-style-kvantum
  ```

---

## `debian/copyright`

- [ ] **CRITICAL — Missing `Format:` header stanza.**
  A DEP-5 copyright file must begin with a header stanza. Add this as the
  very first block (before any `Files:` stanza):
  ```
  Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
  Upstream-Name: xinput-plus
  Upstream-Contact: Washington Indacochea Delgado <wachin.id@gmail.com>
  Source: https://github.com/wachin/xinput-plus
  ```

- [ ] **CRITICAL — Inline comments on `Files:` lines are not valid DEP-5.**
  Lines like:
  ```
  Files: debian/*                                  # packaging files
  Files: src/emucon.svg                            # the ONLY CC0 file
  ```
  are invalid. DEP-5 does not allow inline comments. Move the explanatory
  text into a `Comment:` field within the stanza, or simply remove it.

- [ ] **CRITICAL — `Files: debian/xinput-plus.metainfo.xml` stanza is
  nested inside `Files: debian/*`.**
  Each stanza must start at column 0 with a blank line separating it from
  the previous stanza. The metainfo stanza is currently indented, which
  makes it unparseable.

- [ ] **Minor — `src/emucon-openclipart.org.txt` is not covered.**
  Every file in the source tree must be covered by a `Files:` stanza.
  Add an entry for this file (it can share the `CC0-1.0` stanza with
  `src/emucon.svg`, or have its own).

---

## `debian/rules`

- [ ] **Minor — Comments are in Spanish.**
  `debian/rules` is a public packaging file reviewed by Debian maintainers
  worldwide. Translate all comments to English. Examples:
  - `# Compilar traducciones Qt (PyQt6)` → `# Compile Qt translations (PyQt6)`
  - `# Binario (lanzador)` → `# Main executable`
  - `# Icono` → `# Application icon`
  - `# Traducciones (.qm)` → `# Compiled translations (.qm)`
  - `# Instalar el changelog "upstream" (tu CHANGELOG.md)` →
    `# Install the upstream changelog`
  - `# Ajusta la ruta si lo moviste de carpeta.` →
    `# Adjust the path if the file is moved.`

- [ ] **Minor — `lrelease` glob may fail on a clean source tree.**
  If no `.ts` files are present (e.g., a minimal source tarball), the glob
  `i18n/xinput-plus_*.ts` expands to nothing and some `lrelease` versions
  error out. The `|| true` catches this, but the logic is fragile. A safer
  pattern:
  ```makefile
  override_dh_auto_build:
  	if ls i18n/xinput-plus_*.ts >/dev/null 2>&1; then \
  	  (command -v lrelease-qt6 >/dev/null && lrelease-qt6 i18n/xinput-plus_*.ts) || \
  	  (command -v lrelease >/dev/null && lrelease i18n/xinput-plus_*.ts) || true; \
  	fi
  ```

---

## `debian/watch`

- [ ] **Minor — Version regex could be anchored more tightly.**
  The current pattern `v?(\d[\d\.]*)` matches tags like `v6.6` but also
  pathological strings like `6.6.4.1.2.3`. Consider:
  ```
  v?(\d+[\d\.]*)
  ```
  (`\d+` instead of `\d` ensures at least one digit before the dot sequence.)

---

## `debian/xinput-plus.1` (man page)

- [ ] **CRITICAL — `.TH` macro is malformed.**
  The current line:
  ```
  .TH XINPUT-PLUS 1 "xinput-plus"
  ```
  is missing the date (3rd argument) and the section-source / manual-title
  (4th and 5th arguments). The correct form is:
  ```
  .TH XINPUT-PLUS 1 "2025-09-15" "xinput-plus 6.6.4" "User Commands"
  ```

- [ ] **Minor — `--lang` option is not documented.**
  The man page has no `OPTIONS` section. Add one documenting `--lang=<locale>`.

- [ ] **Minor — Config file path is not documented.**
  Add a `FILES` section documenting `~/.config/xinput-plus.json`.

- [ ] **Minor — `SYNOPSIS` is incomplete.**
  Update to show the optional argument:
  ```
  .B xinput-plus
  .RI [ \-\-lang= locale ]
  ```

---

## `debian/xinput-plus.desktop`

- [ ] **Minor — `Name` is the technical package name, not a human label.**
  `Name=xinput-plus` will appear literally in application menus. Change to
  something readable, e.g.:
  ```
  Name=Xinput Plus
  ```

- [ ] **Minor — Missing Spanish localization entries.**
  Since a Spanish translation exists, add:
  ```
  Name[es]=Xinput Plus
  Comment[es]=Ajusta la velocidad del puntero por dispositivo (Xorg, via xinput)
  ```

- [ ] **Minor — `Categories` could be more specific.**
  `Settings;` is valid but `Settings;HardwareSettings;` places the app
  more precisely in desktop environment menus.

---

## `debian/xinput-plus.metainfo.xml`

- [ ] **CRITICAL — Current release version is missing from `<releases>`.**
  The `<releases>` block only lists `6.6` and `6.5`. The version being
  packaged (`6.6.4`) must be listed:
  ```xml
  <release version="6.6.4" date="2025-09-17"/>
  <release version="6.6" date="2025-09-15"/>
  <release version="6.5" date="2025-09-10"/>
  ```

- [ ] **Minor — `<developer_name>` is deprecated in AppStream 1.0.**
  Replace:
  ```xml
  <developer_name>Washington Indacochea Delgado</developer_name>
  ```
  with:
  ```xml
  <developer>
    <name>Washington Indacochea Delgado</name>
  </developer>
  ```

- [ ] **Minor — No bugtracker URL.**
  Add:
  ```xml
  <url type="bugtracker">https://github.com/wachin/xinput-plus/issues</url>
  ```

---

## `xinput-plus.py` (main source)

- [ ] **Minor — File header version comment says `v6.5`.**
  The first comment line reads `# xinput-plus.py / v6.5 (full, corrected,
  i18n-ready)`. Update to match the current release version.

- [ ] **Minor — Dead code: `btns = QHBoxLayout()` in `build_ui()`.**
  This layout is created but immediately abandoned in favour of `row1` and
  `row2`. Remove the unused variable.

- [ ] **Minor — Spanish comments in source code.**
  Several inline comments are in Spanish:
  - `# ----- Fila 1: acciones principales -----`
  - `# ----- Fila 2: edición y acerca de -----`
  - `# Añadir ambas filas al panel derecho`
  - `# opcional: empuja contenido hacia la izquierda`
  - `# opcional: alinea a la izquierda`
  - `# ← aquí el icono que querías`
  Translate all to English.

- [ ] **Minor — `_qm_candidates` has a misleading `if parts:` guard.**
  `str.split()` always returns a non-empty list, so `if parts:` is always
  `True`. The intent is to add the language-only variant only when a
  country code is present. Change to `if len(parts) > 1:`.

- [ ] **Minor — Grammatical error in About dialog text.**
  `"Perfect for external, keyboards with integrated touchpads"` has a
  spurious comma. Fix to:
  `"Perfect for external keyboards with integrated touchpads"`

- [ ] **Minor — `on_natural_toggled` and `on_tapping_toggled` ignore their
  `checked` parameter.**
  Both methods accept `checked: bool` but never use it. This is harmless
  but misleading. Add `_ = checked` or a brief comment explaining the
  parameter is intentionally unused, since Qt's signal requires it.

---

## `README.md`

- [ ] **Minor — Broken image reference.**
  `![](vx_images/403085416299084.png)` points to a path that does not exist
  in the repository (a leftover from a VNote note-taking app). Replace with
  the correct asset path or remove the image.

- [ ] **Minor — "Save configuration" button no longer exists.**
  Step 5 in "How to use it" says `click "Save configuration"`. That button
  was removed; configuration now saves automatically when the slider moves.
  Update the instructions to reflect the current behaviour.

- [ ] **Minor — `python3-all` and `dh-python` listed as end-user requirements.**
  `python3-all` and `dh-sequence-python3` / `dh-python` are build-time
  packaging tools. End users do not need them to run the program or create
  translations. Remove them from the user-facing install command.

- [ ] **Minor — Double H1 heading at the top.**
  The file opens with two consecutive `#` headings. The project name should
  be the only H1; the subtitle should be H2 (`##`).

- [ ] **Minor — "God bless you" sign-off.**
  This personal sign-off is fine for a personal blog but looks out of place
  in a package README reviewed by Debian maintainers. Consider moving it to
  a personal note or removing it.

---

## `README_ES.md`

- [ ] **CRITICAL — Wrong config file path.**
  The file says `~/.config/libinput-gui.json` — this is the old name from
  a previous version of the program. The correct path is
  `~/.config/xinput-plus.json`. Fix every occurrence.

- [ ] **Minor — "Guardar configuración" button no longer exists.**
  Step 4 says `haz clic en "Guardar configuración"`. That button was
  removed; configuration saves automatically. Update the instructions.

- [ ] **Minor — Speed range description is outdated.**
  Step 3 says `"¡hasta 2 veces más rápido!"`. The standard range is -1.0
  to 1.0; the 2× range only applies in extended CTM mode. Clarify this.

- [ ] **Minor — Stray closing code fence at end of file.**
  There is a lone ` ``` ` before "Dios te bendiga" that will render as an
  unclosed code block in some Markdown renderers. Remove it.

---

## `src/emucon-openclipart.org.txt`

- [ ] **Minor — `Licence:` field is blank.**
  The file documents the origin of `src/emucon.svg` but leaves the
  `Licence:` field empty. Fill it in to match `debian/copyright`:
  ```
  Licence: CC0-1.0
  ```

---

## `Launcher.sh`

- [ ] **Minor — `cd .` is a no-op.**
  The intent was probably `cd "$(dirname "$0")"` to ensure the script runs
  from its own directory. As written it only works if the user is already
  in the correct directory. Fix or document the limitation.

- [ ] **Minor — Not suitable for installation.**
  Once installed, the binary is `/usr/bin/xinput-plus`. `Launcher.sh` is a
  development convenience and should not be installed by the package (it is
  not, per `debian/rules` — this is already correct). Consider adding a
  comment at the top of the file making its development-only purpose clear.

---

## `.gitignore`

- [ ] **Minor — Comments are in Spanish.**
  All section comments are in Spanish. For an international open-source
  project, English is conventional.

- [ ] **Minor — `i18n/*.qm` is gitignored but `i18n/xinput-plus_es.qm` is
  already tracked.**
  The ignore rule has no effect on a file already committed. Decide on one
  of two approaches:
  - **Recommended (build-time):** Remove the `.qm` from git tracking
    (`git rm --cached i18n/xinput-plus_es.qm`) and let `debian/rules`
    build it from the `.ts` file. This is the standard Debian approach.
  - **Alternative:** Keep the `.qm` committed and remove the gitignore
    rule. This requires manually updating the `.qm` before each release.

---

## `i18n/xinput-plus_es.ts`

- [ ] **Minor — One `vanished` translation entry.**
  `<translation type="vanished">Modo extendido (CTM)</translation>` is a
  string removed from the source. Clean it up by re-running:
  ```bash
  pylupdate6 --ts i18n/xinput-plus_es.ts xinput-plus.py
  ```
  This will remove vanished entries and update line numbers.

---

## Summary — Items that will cause rejection

These must be fixed before submitting to the Debian NEW queue:

1. Duplicate `6.6.1-1` entry in `debian/changelog`
2. `UNRELEASED` in the top changelog entry (must be `unstable`)
3. Version mismatch: Python header (`v6.5`), changelog (`6.6.4`), metainfo
   (only lists up to `6.6`)
4. `debian/copyright` is not valid DEP-5: missing `Format:` header,
   inline comments on `Files:` lines, broken stanza indentation
5. Man page `.TH` macro is malformed (missing date and section title)
6. `debian/xinput-plus.metainfo.xml` does not list the current release
   version in `<releases>`
7. `README_ES.md` has the wrong config file path (`libinput-gui.json`)
