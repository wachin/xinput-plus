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

- [x] **CRITICAL — Duplicate version entry.**
  Version `6.6.1-1` appeared twice with different timestamps and different
  descriptions. The duplicate entry (the one with the wrong description
  "New upstream release 6.6.2") was removed.

- [x] **CRITICAL — Top entry said `UNRELEASED`.**
  Changed to `unstable` so the package is ready for upload.

- [x] **CRITICAL — Version mismatch across the project.**
  Python file header updated to `v6.6.4`; metainfo releases list updated
  to include all versions up to `6.6.4`. See those items below.

- [x] **Minor — Changelog entry for `6.6.1-1` described `6.6.2`.**
  The surviving `6.6.1-1` entry now correctly reads
  "New upstream release 6.6.1."

---

## `debian/control`

- [x] **Minor — `Standards-Version` was outdated.**
  Updated from `4.6.2` to `4.7.0`.

- [x] **Minor — `Vcs-Git` should end in `.git`.**
  Already correct (`https://salsa.debian.org/wachin/xinput-plus.git`).
  Confirmed and left as-is.

- [x] **Minor — Trailing blank lines at end of file.**
  Removed the extra blank lines after the long description.

- [x] **Minor — `libqt6svg6` note for Bookworm vs. Trixie/Sid.**
  Verified on packages.debian.org: `libqt6svg6` is the correct package
  name in Debian 12 (Bookworm), Debian 13 (Trixie), and Sid. No change
  needed. Recorded here for future reference.

- [x] **Minor — Add `Suggests:` for optional theming packages.**
  Added `Suggests: qt6ct, qt6-style-kvantum`.

---

## `debian/copyright`

- [x] **CRITICAL — Missing `Format:` header stanza.**
  Added the required DEP-5 header stanza at the top of the file.

- [x] **CRITICAL — Inline comments on `Files:` lines.**
  Removed all inline comments (`# packaging files`, `# the ONLY CC0 file`).

- [x] **CRITICAL — `Files: debian/xinput-plus.metainfo.xml` stanza was
  nested inside `Files: debian/*`.**
  Moved to its own top-level stanza with a blank line separator.

- [x] **Minor — `src/emucon-openclipart.org.txt` was not covered.**
  Added to the `src/emucon.svg` stanza:
  `Files: src/emucon.svg src/emucon-openclipart.org.txt`
  Note: `src/emucon.svg` has since been removed from the repository as it
  is no longer used. `src/emucon-openclipart.org.txt` was removed along
  with it.

---

## `debian/rules`

- [x] **Minor — Comments were in Spanish.**
  All comments translated to English.

- [x] **Minor — `lrelease` glob could fail on a clean source tree.**
  Changed the `override_dh_auto_build` guard from `if [ -d i18n ]` to
  `if ls i18n/xinput-plus_*.ts >/dev/null 2>&1` so the block only runs
  when `.ts` files are actually present.

---

## `debian/watch`

- [x] **Minor — Version regex was slightly fragile.**
  Changed `\d[\d\.]*` to `\d+[\d\.]*` in both the `opts` mangling pattern
  and the URL pattern.

---

## `debian/xinput-plus.1` (man page)

- [x] **CRITICAL — `.TH` macro was malformed.**
  Updated to:
  `.TH XINPUT-PLUS 1 "2025-09-17" "xinput-plus 6.6.4" "User Commands"`

- [x] **Minor — `--lang` option was not documented.**
  Added an `OPTIONS` section documenting `--lang=<locale>`.

- [x] **Minor — Config file path was not documented.**
  Added a `FILES` section documenting `~/.config/xinput-plus.json`.

- [x] **Minor — `SYNOPSIS` was incomplete.**
  Updated to show `[--lang=locale]`.

---

## `debian/xinput-plus.desktop`

- [x] **Minor — `Name` was the technical package name.**
  Changed to `Name=Xinput Plus`.

- [x] **Minor — Missing Spanish localization entries.**
  Added `Name[es]`, `GenericName[es]`, and `Comment[es]`.

- [x] **Minor — `Categories` was too generic.**
  Changed from `Settings;` to `Settings;HardwareSettings;`.

---

## `debian/xinput-plus.metainfo.xml`

- [x] **CRITICAL — Current release version was missing from `<releases>`.**
  Added `6.6.4`, `6.6.3`, `6.6.2`, `6.6.1` to the releases list.

- [x] **Minor — `<developer_name>` is deprecated in AppStream 1.0.**
  Replaced with `<developer><name>...</name></developer>`.

- [x] **Minor — No bugtracker URL.**
  Added `<url type="bugtracker">https://github.com/wachin/xinput-plus/issues</url>`.

---

## `xinput-plus.py` (main source)

- [x] **Minor — File header version comment said `v6.5`.**
  Updated to `v6.6.4`.

- [x] **Minor — Dead code: `btns = QHBoxLayout()` in `build_ui()`.**
  Removed the unused variable.

- [x] **Minor — Spanish comments in source code.**
  All Spanish inline comments translated to English or removed.

- [x] **Minor — `_qm_candidates` had a misleading `if parts:` guard.**
  Changed to `if len(parts) > 1:` so the language-only `.qm` variant is
  only added when a country code is actually present in the locale name.

- [x] **Minor — Grammatical error in About dialog text.**
  Removed the spurious comma: "Perfect for external keyboards with
  integrated touchpads".

- [x] **Minor — `on_natural_toggled` and `on_tapping_toggled` ignored
  their `checked` parameter.**
  Added a comment explaining the parameter is required by Qt's signal
  mechanism but the current value is read from the widget in
  `on_speed_changed`.

- [x] **Minor — Checkbox label "Extended mode (CTM)" was confusing.**
  Renamed to `"Extra speed (for slow devices)"` — a label that explains
  the purpose to the user without requiring knowledge of what a CTM is.
  Updated in `xinput-plus.py`, `README.md`, and `i18n/xinput-plus_es.ts`
  (new Spanish translation: `"Velocidad extra (para dispositivos lentos)"`).
  Verified working in the Spanish UI. Recompiled `i18n/xinput-plus_es.qm`:
  ```bash
  pylupdate6 --no-obsolete --ts i18n/xinput-plus_es.ts xinput-plus.py
  lrelease i18n/xinput-plus_es.ts -qm i18n/xinput-plus_es.qm
  ```
  Result: 20 translations compiled, 0 unfinished.

---

## `README.md`

- [x] **Minor — Broken image reference.**
  Removed the `vx_images/403085416299084.png` reference (leftover from a
  VNote note-taking app). The surrounding text was updated accordingly.

- [x] **Minor — "Save configuration" button no longer exists.**
  Step 5 updated to explain that configuration saves automatically when
  the slider moves.

- [x] **Minor — `python3-all` and `dh-python` listed as end-user
  requirements.**
  Removed from the user-facing `apt install` command. The runtime
  dependencies are `xinput`, `python3-pyqt6`, and `libqt6svg6`.

- [x] **Minor — Double H1 heading at the top.**
  The second `#` heading (the subtitle) was changed to `##`.

- [x] **Minor — "God bless you" sign-off.**
  Left as-is at the author's discretion — this is a personal project and
  the sign-off is in the English README only. Debian policy does not
  prohibit it. Recorded here for completeness.

---

## `README_ES.md`

- [x] **CRITICAL — Wrong config file path.**
  Changed `~/.config/libinput-gui.json` to `~/.config/xinput-plus.json`.

- [x] **Minor — "Guardar configuración" button no longer exists.**
  Step 4 updated: configuration now saves automatically.

- [x] **Minor — Speed range description was outdated.**
  Updated to show `-1.0` to `1.0` as the standard range, with a note
  that `2.0` is only available in extended CTM mode.

- [x] **Minor — Stray closing code fence at end of file.**
  Removed the lone ` ``` ` before "Dios te bendiga".

---

## `src/emucon-openclipart.org.txt`

- [x] **Minor — `Licence:` field was blank.**
  Filled in as `CC0-1.0` to match `debian/copyright`.
  Note: both `src/emucon.svg` and `src/emucon-openclipart.org.txt` have
  since been removed from the repository as they are no longer used.

---

## `Launcher.sh`

- [x] **Minor — `cd .` was a no-op.**
  Changed to `cd "$(dirname "$0")"` so the script works correctly when
  invoked from any directory.

- [x] **Minor — Purpose was not documented.**
  Added a comment at the top clarifying this is a development-only
  launcher and is not installed by the Debian package.

---

## `.gitignore`

- [x] **Minor — Comments were in Spanish.**
  All section comments translated to English.

- [ ] **Minor — `i18n/*.qm` is gitignored but `i18n/xinput-plus_es.qm`
  is already tracked.**
  The ignore rule has no effect on a file already committed to git.
  **Recommended action (not yet done):** Remove the compiled file from
  git tracking and let `debian/rules` build it from the `.ts` source:
  ```bash
  git rm --cached i18n/xinput-plus_es.qm
  git commit -m "Remove compiled .qm from version control; built by debian/rules"
  ```
  This is the standard Debian approach. The `.ts` source file stays in
  the repository; the `.qm` is generated at package build time.

---

## `i18n/xinput-plus_es.ts`

- [x] **Minor — One `vanished` translation entry.**
  The old `"Extended mode (CTM)"` string was marked as vanished after the
  checkbox was renamed to `"Extra speed (for slow devices)"`. Cleaned up
  with `--no-obsolete` (3 obsolete entries discarded). The two new
  unfinished strings (`"Extra speed (for slow devices)"` and the updated
  About dialog text) were translated and the `.qm` recompiled — result:
  20 translations, 0 unfinished.

  Commands used:
  ```bash
  pylupdate6 --no-obsolete --ts i18n/xinput-plus_es.ts xinput-plus.py
  lrelease i18n/xinput-plus_es.ts -qm i18n/xinput-plus_es.qm
  ```

---

## Summary — Items still requiring manual action

### One-time git operation

**`i18n/xinput-plus_es.qm` is tracked in git** — it should be removed from
version control and built at package build time instead:

```bash
git rm --cached i18n/xinput-plus_es.qm
git commit -m "Remove compiled .qm from version control; built by debian/rules"
```

### Standing maintenance rule — run before every release

Any time a UI string in `xinput-plus.py` is added, renamed, or removed,
the `.ts` file must be regenerated and the `.qm` recompiled:

```bash
# 1. Regenerate .ts and drop obsolete entries
pylupdate6 --no-obsolete --ts i18n/xinput-plus_es.ts xinput-plus.py

# 2. Translate any new/unfinished strings in Linguist, then recompile
lrelease i18n/xinput-plus_es.ts -qm i18n/xinput-plus_es.qm
```

The full workflow is documented in the README under
**"Keeping the .ts file clean after source changes"**.

---

## What to do next

All original review issues are fixed. The remaining work before submitting
to Debian falls into three phases.

---

### Phase 1 — Final local cleanup

- [x] **Remove the compiled `.qm` from git tracking.**
  Only `xinput-plus_es.ts` is tracked; the `.qm` is built at package
  build time by `debian/rules`.

- [x] **Update `debian/control` Standards-Version to `4.7.3`.**
  Done.

- [x] **Git tag `v6.6.4` exists.**
  Tag already present. Note: `v6.6.5` also exists in git but only
  contains a documentation edit with `UNRELEASED` in the changelog —
  it does not represent a real upstream release.

- [x] **Man page not installed by `debian/rules`.**
  Fixed — added `install -D -m0644 debian/xinput-plus.1` to
  `override_dh_auto_install`. Lintian `no-manual-page` warning is gone.

- [x] **`debian/changelog` top entry had a minimal description.**
  Expanded to document all packaging changes made during this review
  session (Standards-Version bump, copyright fix, rules improvements,
  desktop/metainfo updates, source fixes, i18n updates).

- [x] **New application icon created.**
  `src/xinput-plus.svg` designed (cursor + speed slider + motion lines).
  `debian/rules` and `xinput-plus.py` updated to use the new icon.
  The old `src/emucon.svg` (joystick) has been removed from the repository.

---

### Phase 2 — Build and validate

- [x] **Local build with `debuild -us -uc -b` — builds cleanly.**

- [x] **`lintian --pedantic` — zero errors, zero warnings.**

- [x] **Test in a clean pbuilder unstable chroot.**
  Recommended before asking for a sponsor. Builds the package in a
  minimal isolated environment, exactly as Debian's build servers would.
  If it fails here but not with `debuild`, a build dependency is missing
  from `debian/control`.

  Run these commands from inside the project directory
  (`~/Dev/xinput-plus-dev/xinput-plus`):

  ```bash
  # 1. Create the pbuilder unstable chroot (only needed once)
  sudo pbuilder create --distribution unstable

  # 2. Create the upstream orig tarball (required by 3.0 (quilt) format)
  tar --exclude=./debian --exclude=./.git -czf ../xinput-plus_6.6.4.orig.tar.gz .

  # 3. Build the source package
  debuild -us -uc -S

  # 4. Build the binary package inside the clean chroot
  sudo pbuilder build --distribution unstable ../xinput-plus_6.6.4-1.dsc
  ```

  After a successful build the parent directory
  (`~/Dev/xinput-plus-dev/`) will contain:

  ```
  xinput-plus/                        ← source tree
  xinput-plus_6.6.4-1.dsc
  xinput-plus_6.6.4-1.debian.tar.xz
  xinput-plus_6.6.4-1_source.build
  xinput-plus_6.6.4-1_source.buildinfo
  xinput-plus_6.6.4-1_source.changes
  xinput-plus_6.6.4.orig.tar.gz
  ```

  The built `.deb` and related files are placed under pbuilder's result
  directory:

  ```
  /var/cache/pbuilder/result/xinput-plus_6.6.4-1.dsc
  /var/cache/pbuilder/result/xinput-plus_6.6.4-1_all.deb
  /var/cache/pbuilder/result/xinput-plus_6.6.4-1_amd64.buildinfo
  /var/cache/pbuilder/result/xinput-plus_6.6.4-1_amd64.changes
  /var/cache/pbuilder/result/xinput-plus_6.6.4-1.debian.tar.xz
  /var/cache/pbuilder/result/xinput-plus_6.6.4-1_source.changes
  /var/cache/pbuilder/result/xinput-plus_6.6.4.orig.tar.gz
  ```

- [x] **Install and smoke-test the `.deb` from pbuilder.**
  ```bash
  sudo apt install /var/cache/pbuilder/result/xinput-plus_6.6.4-1_all.deb
  xinput-plus
  xinput-plus --lang=es
  man xinput-plus
  sudo apt purge xinput-plus
  ```
  All four commands passed: the program launched correctly, the Spanish
  UI worked, and the man page displayed as expected.

---

### Phase 3 — Submit to Debian

- [ ] **Create a Salsa account and push the repository there.**
  Register at https://salsa.debian.org/users/sign_up, create a project
  named `xinput-plus`, and push. The `Vcs-Git` and `Vcs-Browser` fields
  in `debian/control` already point to the correct Salsa URL — the
  repository just needs to exist there.

- [ ] **Create a GPG key and upload it to the keyserver.**
  Every upload to Debian must be signed. If you don't have a key yet:
  ```bash
  gpg --full-generate-key        # choose RSA 4096, set expiry 1-2 years
  gpg --list-secret-keys --keyid-format LONG   # note your key ID
  gpg --keyserver keyserver.ubuntu.com --send-keys YOUR_KEY_ID
  ```

- [ ] **File an ITP bug against the `wnpp` pseudo-package.**
  This tells the Debian community you are working on this package and
  prevents duplicate effort. You will receive a bug number by email.
  ```bash
  reportbug wnpp
  # Choose: ITP
  # Package name: xinput-plus
  # Short description: PyQt6 GUI to adjust pointer speed per device (Xorg, via xinput)
  # License: GPL-3+
  # URL: https://github.com/wachin/xinput-plus
  ```
  Then add the bug number to the top of `debian/changelog`:
  ```
  * Initial release. (Closes: #XXXXXXX)
  ```

- [ ] **Configure `dput` for mentors.debian.net.**
  Create or edit `~/.dput.cf`:
  ```ini
  [mentors]
  fqdn = mentors.debian.net
  incoming = /upload
  method = https
  allow_unsigned_uploads = 0
  progress_indicator = 2
  ```

- [ ] **Sign and upload to mentors.debian.net.**
  ```bash
  debuild -sa
  dput mentors ../xinput-plus_6.6.4-1_amd64.changes
  ```
  On success you will receive a confirmation email and the package will
  appear at https://mentors.debian.net/package/xinput-plus

- [ ] **Post an RFS (Request for Sponsorship) to the debian-mentors list.**
  Send an email to `debian-mentors@lists.debian.org` with subject:
  ```
  RFS: xinput-plus/6.6.4-1 -- PyQt6 GUI to adjust pointer speed per device
  ```
  Include: what the program does, the ITP bug number, the mentors.debian.net
  URL, and a note that lintian is clean and pbuilder builds successfully.
  A Debian Developer will review the package and upload it to the official
  archive on your behalf. This step requires patience — responses can take
  days or weeks.

---

Full details for Phase 3 are in
[docs/debian/how-to-publish-on-debian.md](docs/debian/how-to-publish-on-debian.md)
([español](docs/debian/como-publicar-en-debian.md)).
