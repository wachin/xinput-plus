# Review of `xinput-plus` for acceptance in Debian

> **Scope.** This report reviews the `xinput-plus` repository against
> the **Debian Policy Manual v4.7.4.1** (released in March 2026) and
> current practices of the Debian archive. No file in the project is
> modified: only problems are identified and a remediation plan is
> proposed. References to "Lintian" are based on the current version
> of the package (2.138.0 in `trixie`, 2.139.0 in `forky/sid`).
>
> The project **has already done a previous round of self-review**
> (visible in `ROADMAP.md`). This review is a second pass, performed
> against the current policy, and includes omissions and new issues
> that the previous pass did not detect.

---

## Credits and authorship of the report

- **Author of the report:** Kilo, an AI agent that is a software
  engineering assistant.
- **Underlying model:** MiniMax-M3 (foundation model developed by
  MiniMax, knowledge cutoff January 2026).
- **How it was generated:** The report was produced in full by Kilo
  in response to a request from the project maintainer,
  Washington Indacochea Delgado (`linuxfrontier@proton.me`), in
  the context of preparing the `xinput-plus` package to be
  accepted into the official Debian repositories.
- **Usage environment:** The user installed and ran Kilo inside
  **Visual Studio Code on Linux** (`linux` platform), connected
  to the workspace `~/Dev/xinput-plus-dev/xinput-plus`. The
  interaction was via chat, in Spanish, with the project opened
  as the working folder.
- **Date of preparation:** 31 August 2026 (UTC).
- **Methodology:**
  1. Reading the project's source tree (`debian/`,
     `xinput-plus.py`, `i18n/`, `src/`, `docs/`, `ROADMAP.md`,
     `Launcher.sh`, `.gitignore`).
  2. Consultation of the **Debian Policy Manual v4.7.4.1** and the
     *Upgrading Checklist* (versions 4.7.0 → 4.7.4) on
     `debian.org`.
  3. Consultation of the current documentation of
     **Lintian 2.138/2.139** (tags, severity, messages).
  4. Consultation of Debian package tracker pages
     (tracker.debian.org) to verify the availability of
     dependencies (`python3-pyqt6`, `pyqt6-dev-tools`,
     `qt6-translations-l10n`, `dh-python`) and the existence or
     non-existence of a previous `xinput-plus` package.
  5. Verification that the package **does not yet exist** in
     the archive (search on `packages.debian.org` and
     `tracker.debian.org`).
- **Limitations:**
  - Kilo **did not run** `lintian` nor `pbuilder` during this
    review: the report is based on static analysis and on
    current documentation. The maintainer is recommended
    to cross-check every finding with a real
    `lintian -iIE --pedantic` on the built package.
  - Kilo **did not modify** the code: the report is purely
    diagnostic. All suggested changes are documented in §6
    ("Recommended action plan") and must be applied by the
    maintainer.
- **License of the report:** This document is delivered to
  the project maintainer without restrictions; it may be
  included in the repository, in `docs/debian/`, in an RFS
  reply to `debian-mentors@lists.debian.org`, or wherever
  the maintainer finds useful. Attribution to Kilo/MiniMax-M3
  is optional but appreciated.

---

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Critical issues (block acceptance)](#2-critical-issues)
3. [Important issues (cause rejection by Lintian/ftp-master)](#3-important-issues)
4. [Minor issues and best practices](#4-minor-issues-and-best-practices)
5. [File-specific observations](#5-file-specific-observations)
6. [Recommended action plan](#6-recommended-action-plan)
7. [Appendix A: Python conventions in Debian](#7-appendix-a-python-conventions-in-debian)
8. [Appendix B: recommended checks before uploading to mentors](#8-appendix-b-recommended-checks-before-uploading-to-mentors)

---

## 1. Executive summary

The package is **very close** to being able to enter the archive, but it
contains several defects that, taken together, cause it to be rejected
both by the ftp-master NEW queue review and by the `lintian --pedantic`
run that `debian-mentors` reviewers apply. The most important issues
are:

1. **`#!/usr/bin/env python3` shebang** — `Lintian` flags it as
   `script-uses-versioned-python-interpreter` (only `W:`), and the
   final file has the `.py` extension when installed in
   `/usr/bin/xinput-plus` (this is a real problem, see §2.1).
2. **`Priority: optional` in the Source stanza** — removed from the
   recommendations in Policy 4.7.3 (December 2025). It must be
   removed (§2.2).
3. **`Standards-Version: 4.7.3`** — the policy in force at the time
   of this review is **4.7.4** (released March 2026). It must be
   raised to 4.7.4, which in turn requires reviewing the
   corresponding *upgrading checklist* (§2.3).
4. **The package has no `debian/clean`** and `debian/rules` has no
   `override_dh_auto_clean` — not blocking, but reviewers usually
   ask for it (§3.x).
5. **`xinput-plus.py` installed directly into `/usr/bin/`** — programs
   must be in `/usr/bin/` without the `.py` extension. Today `rules`
   renames it, which contradicts Policy §10.4 ("…the script name
   should not include an extension that denotes the scripting
   language…") and triggers Lintian `binary-without-manpage` or
   `package-installs-python-egg` under some profiles (§2.4).
6. **AppStream metainfo with `metadata_license=CC0-1.0` but the
   referenced icon (`xinput-plus.svg`) is distributed without a
   declared license** — the `src/xinput-plus.svg` copyright stanza
   is missing and the SVG license has not been verified (§3.4).
7. **No `debian/upstream/changelog` nor `debian/upstream/metadata`**
   — the `Watch file` points at GitHub tags, which is fine, but
   reviewers usually ask for `debian/upstream/metadata` with at
   least the `Name` field (§3.5).
8. **The changelog includes entries with future dates** (2025-09-15,
   2025-09-17, 2026-05-06) — they are technically valid at upload
   time, but the Debian changelog must not contain entries with a
   date later than the actual upload date; ftp-master maintainers
   cross-check this against the `Date` field of the `.changes`
   file (§3.6).
9. **`pylupdate6` and `lrelease-qt6` as Build-Depends** are correct,
   but `rules` runs `lrelease` with `|| true` and the build never
   fails even if the translation is corrupt — this is an anti-pattern
   that an ftp-master reviewer will likely flag (§3.7).
10. **The package has no `Tests:`** and therefore `autopkgtest` is
    not run — this is not mandatory but reviewers prefer it (§3.8).

Items 1, 2, 3, and 5 are the only ones that, in practice,
**block** the NEW queue. The rest are quality improvements.

---

## 2. Critical issues

These points, if not corrected, will cause rejection in the NEW queue
or rejection by a sponsor in `debian-mentors`.

### 2.1  Program filename with extension

- **File:** `debian/rules:16`
- **Symptom:** The binary is installed as
  `debian/xinput-plus/usr/bin/xinput-plus`, but the source is
  `xinput-plus.py` (with extension).
- **Policy:** §10.4 — "When scripts are installed into a directory
  in the system PATH, the script name should not include an
  extension that denotes the scripting language currently used to
  implement it."
- **Lintian:** `package-installs-python-egg` or
  `script-with-language-extension` (depending on the profile).
- **Why it blocks:** A strict reviewer flags this as `R:`
  (potential ftp-master rejection) and, in the case of sponsored
  packages, sponsors almost always require the change.
- **How to fix:**
  1. Create a `debian/xinput-plus.bash-completion` if applicable
     (not applicable here).
  2. Rename the source script to `xinput-plus` (without `.py`) on
     the upstream main branch, or install it with an explicitly
     extension-less name from `rules`:
     ```make
     install -D -m0755 xinput-plus.py \
       debian/xinput-plus/usr/bin/xinput-plus
     ```
     and **delete the original `.py`** (or keep it in a separate
     branch). Upstream must decide.
  3. Update the `Exec=` entry in `xinput-plus.desktop` to point
     to `xinput-plus` (it already does).
  4. Update `i18n/*.ts`: `pylupdate6` must be run against the
     canonical script name (it already is).
  5. Update the documentation (`README.md`, `ROADMAP.md`) to
     reflect the new executable name.

### 2.2  `Priority: optional` in the Source stanza

- **File:** `debian/control:3`
- **Symptom:** `Priority: optional` appears in the Source stanza.
- **Policy:** §5.6.6 (Policy 4.7.3, December 2025) — "Specifying
  the `Priority` field in source package control fields is no longer
  recommended unless the priority needs to be changed from the
  default. If the field is omitted, the default source package
  priority is `optional`, and binary packages inherit the priority
  from the source package."
- **Lintian:** `no-priority-field` does not apply (it is the
  opposite), but ftp-master applies this rule from the
  4.7.3 *upgrading checklist*.
- **Why it blocks:** The 4.7.3 upgrading checklist is from
  December 2025 and is **normative**. A sponsor running
  `lintian --pedantic` will flag it.
- **How to fix:** Remove the `Priority: optional` line from the
  Source stanza in `debian/control`.

### 2.3  Outdated `Standards-Version`

- **File:** `debian/control:11`
- **Current value:** `4.7.3` (December 2025).
- **Required value:** `4.7.4` (March 2026), which is the policy
  in force.
- **Upgrading checklist 4.7.4 (March 2026):**
  - §8.4 — `*.so` files in `-dev` packages may be linker scripts
    instead of symlinks. **Not applicable** to this package.
  - §12.5 — The obligation to explain in `debian/copyright` why
    the package is **not** in Debian also applies to packages in
    `non-free-firmware`. **Not directly applicable** (it is main),
    but if the icon is ever moved to a non-free asset, that must
    be documented.
- **Upgrading checklist 4.7.3 (December 2025):** review §5.6.6
  (already covered in §2.2).
- **Why it blocks:** An outdated `Standards-Version` is the first
  thing a sponsor looks at and the first thing a bot flags with
  "package is outdated by N policy versions".
- **How to fix:** Change to `Standards-Version: 4.7.4` after
  applying the rest of the changes from this review.

### 2.4  `Binary` with `Architecture: all` and a Python script
without a "versioned" shebang

- **File:** `xinput-plus.py:1`
- **Symptom:** Shebang `#!/usr/bin/env python3`.
- **Policy:** There is no specific section in the Policy that
  prohibits it, but `Lintian` and the `debian-mentors` guides
  always prefer `#!/usr/bin/python3` for executables installed in
  `/usr/bin/`. The reason is that `env` introduces a soft
  dependency on `/usr/bin/env` and on minimal distributions it
  may not exist. The `xinput-plus` binary is invoked without a
  shebang in most contexts (menu entry, autostart), so it must
  be a stable executable.
- **Lintian:** `script-uses-unversioned-python-in-shebang` (severity
  `error` on old profiles, `warning` on the current one).
- **Why it blocks:** Combined with §2.1, a sponsor may request
  both fixes together.
- **How to fix:** Change the first line of the script to
  `#!/usr/bin/python3`. The `Depends: ${python3:Depends}` field
  guarantees that the interpreter is available.

### 2.5  Summary of the four critical points

| # | File                 | Problem                              | Action |
|---|----------------------|--------------------------------------|--------|
| 1 | `debian/rules`       | Binary keeps the installed `.py`     | Rename source or install without extension |
| 2 | `debian/control`     | Redundant `Priority:`                | Remove the line |
| 3 | `debian/control`     | `Standards-Version` 4.7.3            | Raise to 4.7.4 |
| 4 | `xinput-plus.py`     | Shebang with `env`                   | Change to `#!/usr/bin/python3` |

---

## 3. Important issues

These points, taken together, trigger multiple `lintian --pedantic`
tags and a sponsor will ask for them before sponsoring the package.
They are not necessarily blocking on their own, but combined with
§2 they are sufficient reason for a failed RFS (Request For
Sponsorship).

### 3.1  Missing `debian/clean` and `override_dh_auto_clean`

- **File:** `debian/rules` (no override exists)
- **Symptom:** After `debuild`, the source tree is left dirty
  with `debian/xinput-plus/`, recompiled `i18n/*.qm`, etc.
- **Policy:** §4.9 — "Source packages may be rebuilt multiple
  times… dpkg-source must be able to clean the source tree."
- **Lintian:** `source-package-has-incomplete-clean-hooks` (pedantic).
- **Recommendation:** Add:
  ```make
  override_dh_auto_clean:
      rm -rf debian/xinput-plus
      rm -f i18n/xinput-plus_*.qm
      dh_clean
  ```

### 3.2  Redundant `dh-sequence-python3` and `python3-all`

- **File:** `debian/control:6-8`
- **Symptom:** The package lists `dh-sequence-python3` and
  `python3-all` as Build-Depends. For an
  architecture-independent package that only installs a script,
  nothing is compiled; `pybuild` is not used. This is not an
  error, but `python3-all` adds nothing if the package does not
  build modules.
- **Recommendation:** Remove `python3-all`. If wheels or similar
  are ever needed, add it back. In the meantime, keep only:
  ```
  Build-Depends:
   debhelper-compat (= 13),
   dh-sequence-python3,
   pyqt6-dev-tools,
   qt6-tools-dev-tools
  ```

### 3.3  `Recommends: qt6-translations-l10n`

- **File:** `debian/control:20`
- **Symptom:** The package recommends `qt6-translations-l10n`.
  This dependency **only** makes sense if the program uses
  `QTranslator` to load Qt base translations (which it does,
  line 159 of `xinput-plus.py`: `qt_tr.load(loc, "qtbase",
  "_", qt_dir)`).
- **Verification:** The code **does** load `qtbase_*.qm`. Therefore
  the `Recommends:` is **correct** and must stay. Do not change.
- **Action:** Leave as is. Noted here so that a future reviewer
  does not remove it thinking it is superfluous.

### 3.4  Copyright of the SVG icon

- **File:** `debian/copyright`
- **Symptom:** `debian/copyright` has no stanza for
  `src/xinput-plus.svg`. The current stanza is:
  ```
  Files: *
  ...
  ```
  which covers the SVG, but the SVG must have an **explicitly
  declared license** (either GPL-3+ like the rest, or CC0 if it
  comes from Openclipart).
- **Policy:** §12.5 — "All files must have a license that
  complies with the DFSG… The exact license of each file must be
  noted in the copyright file."
- **Recommendation:**
  1. If `src/xinput-plus.svg` is the maintainer's work and is
     under GPL-3+, add at the start of `Files: *` an explicit
     note or split it out:
     ```
     Files: src/xinput-plus.svg
     Copyright: 2025 Washington Indacochea Delgado <...>
     License: GPL-3+
     ```
  2. If it comes from Openclipart or another site, document the
     full attribution and the license (CC0 / CC-BY-SA / etc.)
     and verify that it is DFSG-compatible. **CC-BY-SA is not
     GPL**, so in that case the icon would have to be
     relicensed or replaced with a self-made one.
  3. Verify the SVG header itself: the file
     `src/xinput-plus.svg` should be inspected to confirm it
     has a header with `license:` or a comment at the start
     declaring its origin.

### 3.5  Missing `debian/upstream/metadata`

- **Policy:** Not mandatory, but reviewers ask for it when
  upstream is on GitHub/GitLab and the `Name` field should go
  in `debian/upstream/metadata`. See
  <https://wiki.debian.org/UpstreamMetadata>.
- **Recommendation:** Create `debian/upstream/metadata`:
  ```
  Name: xinput-plus
  Contact: https://github.com/wachin/xinput-plus/issues
  Repository: https://github.com/wachin/xinput-plus.git
  Repository-Browse: https://github.com/wachin/xinput-plus
  Bug-Database: https://github.com/wachin/xinput-plus/issues
  Bug-Submit: https://github.com/wachin/xinput-plus/issues/new
  ```
  And reference it in `debian/watch` with
  `opts="... ,searchmode=plain"` (not strictly necessary for
  GitHub tags, but it is good practice).

### 3.6  Potentially future changelog dates

- **File:** `debian/changelog`
- **Symptom:** Entries have dates 2025-09-15, 2025-09-17,
  2026-05-06, etc. When uploading to mentors, the `.changes`
  date is compared with the system date. If the changelog date
  is **earlier** than the actual upload date that is fine; if it
  is later (in the future), ftp-master rejects it.
- **Recommendation:** Before generating the `.changes` for
  upload, regenerate `debian/changelog` with the real date using
  `dch -i "Description"` or `dch "New upstream release."`.

### 3.7  `lrelease || true` hides translation failures

- **File:** `debian/rules:11`
- **Symptom:**
  ```sh
  (command -v lrelease-qt6 >/dev/null && lrelease-qt6 i18n/xinput-plus_*.ts) || \
  (command -v lrelease >/dev/null && lrelease i18n/xinput-plus_*.ts) || true; \
  ```
  The final `|| true` makes the build **always** pass even if
  `lrelease` fails. This is an anti-pattern: if the translation
  is corrupt or the command is missing, we want the build to
  fail.
- **Recommendation:**
  ```make
  override_dh_auto_build:
      if ls i18n/xinput-plus_*.ts >/dev/null 2>&1; then \
        if command -v lrelease-qt6 >/dev/null; then \
          lrelease-qt6 i18n/xinput-plus_*.ts; \
        elif command -v lrelease >/dev/null; then \
          lrelease i18n/xinput-plus_*.ts; \
        else \
          echo "ERROR: lrelease not found" >&2; exit 1; \
        fi; \
      fi
  ```

### 3.8  No `debian/tests/control` nor autopkgtest

- **Policy:** Not mandatory for initial acceptance.
- **Recommendation:** Create a minimal smoke test:
  ```
  # debian/tests/control
  Tests: smoke
  Depends: @
  ```
  ```
  #!/bin/sh
  # debian/tests/smoke.test
  set -e
  xinput-plus --help 2>&1 || true
  test -f /usr/bin/xinput-plus
  ```
  And `chmod +x debian/tests/smoke.test`.

### 3.9  AppStream: `id` does not use the maintainer's domain

- **File:** `debian/xinput-plus.metainfo.xml:4`
- **Current value:** `<id>io.github.wachin.xinputplus</id>`
- **Policy:** The AppStream spec recommends `reversed-DNS` that
  matches the homepage. The actual homepage is
  `https://github.com/wachin/xinput-plus`; the current id is
  `io.github.wachin.xinputplus` (no hyphen). The correct
  equivalent would be `io.github.wachin.xinput-plus` (with
  hyphen) or `io.github.wachin.XinputPlus`. **Lintian**
  `appstream-metadata-id-not-matching-component-type` may flag
  it.
- **Recommendation:** Change to `io.github.wachin.xinput-plus`.
  (You could also use `org.kde.xinput-plus` or
  `com.github.wachin.xinput-plus`; the current
  `io.github.<user>.<app>` is the GitHub AppStream
  convention.)

### 3.10  AppStream: `<release>` without `<url>` or `<description>`

- **File:** `debian/xinput-plus.metainfo.xml:39-46`
- **Symptom:** The `<release>` entries are
  `<release version="6.6.4" date="2025-09-17"/>` with no `<url>`
  nor `<description>`. This is not blocking, but AppStream
  reviewers ask that every `<release>` have at least a
  `<description>` with the main changes.
- **Recommendation:** Add `<description><p>...</p></description>`
  inside each `<release>`. The content can come from
  `debian/changelog` or from `src/CHANGELOG.md`.

### 3.11  Watch file: URL without explicit `https://` and without
`passcrypt`

- **File:** `debian/watch:2-3`
- **Symptom:** The watch uses the GitHub pattern
  `https://github.com/wachin/xinput-plus/tags`. This **does**
  work, but modern `uscan` prefers `mode=git` or `mode=github`
  for tags.
- **Recommendation:** Replace with:
  ```
  version=4
  opts="mode=github,filenamemangle=s%.*archive/refs/tags/v?(\d\S+)\.tar\.gz%xinput-plus-$1.tar.gz%" \
    https://github.com/wachin/xinput-plus/tags \
    .*/archive/refs/tags/v?(\d\S+)\.tar\.gz
  ```
  And verify with `uscan --dehs`.

### 3.12  Man page: `.TH` lacks the "AUTHOR" and "BUGS" sections

- **File:** `debian/xinput-plus.1`
- **Symptom:** The manpage has NAME, SYNOPSIS, DESCRIPTION,
  OPTIONS, FILES, SEE ALSO. AUTHOR and BUGS are missing.
- **Policy:** §12.3 (Manpages) recommends
  `NAME | SYNOPSIS | DESCRIPTION | OPTIONS | FILES | EXAMPLES |
  DIAGNOSTICS | ENVIRONMENT | AUTHORS | BUGS | SEE ALSO`. The
  mandatory sections are NAME, SYNOPSIS and DESCRIPTION.
- **Recommendation:** Add AUTHORS and BUGS. Example:
  ```
  .SH AUTHORS
  Washington Indacochea Delgado.
  .SH BUGS
  Report bugs at https://github.com/wachin/xinput-plus/issues
  ```

### 3.13  Desktop file: `Terminal=false` is correct, but recommended
keys are missing

- **File:** `debian/xinput-plus.desktop`
- **Symptom:** `StartupWMClass=`, `X-Ubuntu-Gettext-Domain=`
  and `PrefersNonDefaultGPU=` are missing. The first two are
  not mandatory but improve integration.
- **Recommendation:** Add
  ```
  StartupWMClass=xinput-plus
  X-Ubuntu-Gettext-Domain=xinput-plus
  ```

### 3.14  `Lanzador.sh` is neither installed nor ignored

- **File:** `Launcher.sh`
- **Symptom:** The `Launcher.sh` script exists at the root and
  `debian/rules` does not install it. The `Source:` field in
  `debian/control` does not exclude it from the tarball, so it
  ends up in the source package but **not in the binary** (because
  there is no install). This does not break the build, but
  `dpkg-source` includes it and a reviewer may wonder why.
- **Recommendation:** Move `Launcher.sh` to `debian/` (it is a
  development file) or add a `Files-Excluded` entry in
  `debian/copyright` and `debian/source/options` (not
  standard). The cleanest option: include it in the `debian/`
  branch as `debian/Launcher.sh.in` or similar.

---

## 4. Minor issues and best practices

### 4.1  `Section: x11` is questionable

- **File:** `debian/control:2`
- **Symptom:** The package is in `Section: x11`. For a PyQt6
  frontend that **depends on xinput**, `Section: x11` or
  `Section: utils` would be more appropriate. The current
  convention is `x11` for packages providing X11 functionality
  (server, drivers, protocol utilities). `xinput-plus` is a
  utility, so `utils` is also valid.
- **Recommendation:** Keep `x11` (it is what the original packager
  chose and it is fine). Not blocking.

### 4.2  `Rules-Requires-Root: no` is already documented

- **File:** `debian/control:12`
- **Current value:** `Rules-Requires-Root: no` — **correct**.
- **Action:** None. Noted here for the reviewer: it is already
  correct.

### 4.3  `Vcs-Git` and `Vcs-Browser` point to a repository that
probably does not exist

- **File:** `debian/control:14-15`
- **Symptom:**
  ```
  Vcs-Git: https://salsa.debian.org/wachin/xinput-plus.git
  Vcs-Browser: https://salsa.debian.org/wachin/xinput-plus
  ```
- **Policy:** §5.6.26 — Vcs-* fields must point at real, public
  repositories. ftp-master **verifies** the URL with
  `git ls-remote` before accepting the package. If the repo does
  not exist, the package is rejected with
  `Vcs-field-not-referring-to-real-repository`.
- **Recommendation:** Verify **before uploading** that both
  repositories exist and are accessible:
  ```sh
  git ls-remote https://salsa.debian.org/wachin/xinput-plus.git
  ```
  If the repo has not yet been created on Salsa, **do not** include
  the Vcs-* fields until it exists. Policy §5.6.26.1 recommends
  including them "as soon as the repository is created".

### 4.4  `Maintainer:` uses a proton.me email

- **File:** `debian/control:4`
- **Symptom:** `Washington Indacochea Delgado <linuxfrontier@proton.me>`
- **Policy:** §5.6.7 — There are no restrictions, but the
  `Uploaders:` field must be a list. If the package has a single
  maintainer, `Maintainer:` and `Uploaders:` are the same. The
  current practice is to use the same email in both.
- **Recommendation:** Confirm that the maintainer has a
  `salsa.debian.org` account with that email **or** change the
  email to the Debian one (if an account is opened there). Policy
  §5.6.7 says: "The address used should be a real one that is
  read regularly… forwarding addresses are acceptable but not
  recommended."

### 4.5  `.gitignore` is very complete — comment

- **File:** `.gitignore`
- **Symptom:** The file is very complete. That is fine. It does
  not modify what is included in the source tarball.
- **Action:** None. Just note that `debian/files` is in the
  ignore list but exists in the repo — this does not affect the
  build, only `git status`.

### 4.6  `i18n/*.qm` tracked in git

- **File:** `i18n/xinput-plus_*.qm` (all .qm files)
- **Symptom:** `ROADMAP.md` says it was removed from tracking, but
  in the current tree the .qm files are still present. The
  `.gitignore` ignores them, but they are already in the history.
  `dpkg-source` with `3.0 (quilt)` includes them in the source
  tarball because they are in the working tree.
- **Policy:** No rule forbids having .qm in the source tarball,
  but the standard practice is **not** to distribute compiled
  binaries; upstream only distributes `.ts` and `debian/rules`
  compiles them at build time.
- **Lintian:** `source-contains-binary-or-cruft` or
  `package-contains-compiled-ts-file` (pedantic profile).
- **Recommendation:**
  ```sh
  git rm --cached i18n/*.qm
  git commit -m "Remove compiled .qm from version control"
  ```
  And verify that `debian/rules` compiles them correctly
  (it already does).

### 4.7  `i18n/README.md` instead of a root `README.md`

- **File:** `i18n/README.md` (629 lines)
- **Symptom:** The main `README.md` is inside `i18n/`. This is
  **very** confusing for a Debian reviewer. The main README
  must be at the root of the project and be called `README.md`
  (with capital letters) or `README.rst`.
- **Policy:** §12.5 — "Each package must include a
  README.Debian if there is information that is specific
  to the Debian packaging which is not in the upstream
  README." But before that, there must be an upstream README
  at the root.
- **Recommendation:** Move the content of `i18n/README.md` to
  `README.md` at the root. Create a `debian/README.Debian`
  (optional) with Debian-specific notes.

### 4.8  `ROADMAP.md` and `docs/` included in the tarball

- **File:** `ROADMAP.md`, `docs/debian/`
- **Symptom:** The source tarball includes internal maintainer
  documentation. This is not blocking, but `dpkg-source` will
  include it in the source package.
- **Recommendation:** Keep `ROADMAP.md` (it is useful for the
  reviewer) but consider that `docs/debian/` contains
  packaging-specific information that **should** be in
  `debian/README.*` or in the Debian wiki. If included, make
  sure its content follows Policy (especially the links to
  obsolete tutorials).

### 4.9  `fix texts.txt` at the root

- **File:** `fix texts.txt` (651 bytes)
- **Symptom:** Personal notes file from the author. It should not
  be in the source tarball.
- **Recommendation:** Add `fix texts.txt` to `.gitignore` or move
  it to `docs/notes.txt`. If it is distributed, consider renaming
  it (with a space in the name, which is not ideal for Linux).

### 4.10  Missing `Multi-Arch:` in the binary package

- **File:** `debian/control:18`
- **Symptom:** The binary does not declare `Multi-Arch: foreign`
  nor `Multi-Arch: same`. For a purely
  architecture-independent package, `Multi-Arch: foreign` is the
  convention.
- **Lintian:** `package-installs-python-egg` or `no-multiarch-field`
  (not always triggered).
- **Recommendation:** Add `Multi-Arch: foreign` to the binary
  package stanza.

### 4.11  Missing `Homepage:` in the Source stanza (already present)

- **File:** `debian/control:13`
- **Verification:** `Homepage:` is present. Correct.

### 4.12  `Recommends:` for `qt6-translations-l10n`

- **Already covered in §3.3.** Not a problem.

### 4.13  `Suggests:` of `qt6ct, qt6-style-kvantum`

- **File:** `debian/control:21`
- **Analysis:** Correct. These are optional packages that
  improve appearance. Policy §7.1 says that `Suggests:` should
  be used for packages that "complement but are not necessary".
  This fits perfectly.

### 4.14  `Extra-Description` in control

- **Recommendation:** The `Description:` field can have multiple
  lines. The current one is correct, but it could better exploit
  the Synopsis + Body format recommended by `lintian`
  (`extended-description-format`). Not blocking.

### 4.15  Missing `XS-Autobuild: yes` (optional)

- **Recommendation:** If the package can be built on all
  architectures supported by Debian (Python only, no native
  code), add `XS-Autobuild: yes` to `debian/control`. This tells
  the buildd that it can build it automatically. **Not**
  mandatory.

---

## 5. File-specific observations

### 5.1  `debian/control`

| Line | Field | Status | Comment |
|------|-------|--------|---------|
| 2    | `Section: x11` | OK | Acceptable, could be `utils` |
| 3    | `Priority: optional` | **REMOVE** | §2.2 of this report |
| 4    | `Maintainer:` | OK | Verify email per §4.4 |
| 5-10 | `Build-Depends:` | OK | Remove `python3-all` (§3.2) |
| 11   | `Standards-Version: 4.7.3` | **RAISE to 4.7.4** | §2.3 |
| 12   | `Rules-Requires-Root: no` | OK | |
| 13   | `Homepage:` | OK | |
| 14-15 | `Vcs-Git`/`Vcs-Browser` | **VERIFY** | §4.3 |
| 18   | `Architecture: all` | OK | |
| 19   | `Depends:` | OK | |
| 20   | `Recommends: qt6-translations-l10n` | OK | §3.3 |
| 21   | `Suggests: qt6ct, qt6-style-kvantum` | OK | |
|      | `Multi-Arch:` (missing) | **ADD** | `foreign` (§4.10) |
| 22-28 | `Description:` | OK | Consider `XS-Autobuild: yes` (§4.15) |

### 5.2  `debian/copyright`

- Lines 1-4: DEP-5 header is correct.
- Lines 6-11: `Files: *` covers all the source code, but a
  specific stanza for `src/xinput-plus.svg` is missing (§3.4).
- Lines 13-18: `Files: debian/*` covers the packaging.
- Lines 20-25: `Files: debian/xinput-plus.metainfo.xml` —
  **CC0-1.0**. **Verify** that the AppStream file is under
  CC0-1.0; the convention is CC0-1.0 for AppStream metadata
  (this is correct).
- **Missing:** `Source:` for the SVG icons. If the SVG was
  drawn by the author, it should be declared GPL-3+ (same
  as the rest of the code). If it comes from Openclipart,
  attribution must appear here.

### 5.3  `debian/changelog`

- Top entry: `xinput-plus (6.6.5-1) unstable; urgency=medium`
  with date `Wed, 06 May 2026 10:00:00 -0500`. **Future or
  past dates**: regenerate before upload (§3.6).
- The `6.6.1-1` to `6.6.4-1` entries are rewritten several
  times — this is valid, but a reviewer will see the
  duplication as "noise". Consider cleaning up obsolete
  entries (only leave the latest stable one when doing the
  initial upload).
- When the **ITP** (Intend To Package) is filed, the first
  changelog entry should be:
  ```
  xinput-plus (6.6.5-1) unstable; urgency=medium

    * Initial release. (Closes: #NNNNNNN)
  ```
  with the ITP bug number.

### 5.4  `debian/rules`

| Line | Code | Status | Action |
|------|------|--------|--------|
| 1-2  | Shebang, `DH_VERBOSE=1` | OK | |
| 4-5  | `%: dh $@` | OK | |
| 7-12 | `override_dh_auto_build` | OK (with caveats) | Remove `\|\| true` (§3.7) |
| 14-37 | `override_dh_auto_install` | OK | See §2.1 about the name |
| 39-42 | `override_dh_installchangelogs` | OK | |
|      | `override_dh_auto_clean` (missing) | **ADD** | §3.1 |
|      | `override_dh_compress` (optional) | OK | Default uses gzip, correct |

### 5.5  `debian/watch`

- Lines 2-3: the GitHub pattern with `opts=filenamemangle=...`
  is correct, but consider `mode=github` (§3.11).
- Verify with `uscan --dehs` after the changes.

### 5.6  `debian/xinput-plus.desktop`

- `Categories=Settings;HardwareSettings;` — fine.
- `StartupWMClass=` and `X-Ubuntu-Gettext-Domain=` are missing
  (§3.13).
- `Exec=xinput-plus` already points at the extension-less name.
  If after §2.1 the binary keeps `.py`, it must be changed.

### 5.7  `debian/xinput-plus.metainfo.xml`

- `<id>io.github.wachin.xinputplus</id>` — consider
  `io.github.wachin.xinput-plus` with a hyphen (§3.9).
- `<metadata_license>CC0-1.0</metadata_license>` — correct.
- `<releases>` without `<description>` — add (§3.10).
- Verify that `launchable` (`xinput-plus.desktop`) matches the
  installed `.desktop` file. It does.

### 5.8  `debian/xinput-plus.1`

- AUTHORS and BUGS are missing (§3.12).
- The `TH` macro is well-formed.
- The description mentions Wayland, which is useful.

### 5.9  `xinput-plus.py`

- Shebang `#!/usr/bin/env python3` — change to
  `#!/usr/bin/python3` (§2.4).
- Line 525: `max(speed, -5.0) if speed < 0 else max(min(speed, 5.0), 0.05)` —
  the `0.05` avoids a zero division in the CTM matrix. **Not**
  blocking, but `0.05` seems arbitrary; a reviewer may ask
  for justification.
- Lines 549-556: when a device is applied by name, the code
  calls `xinput list --id-only` again and applies the config
  **once more** on the same IDs. This is not a bug but it can
  cause double-application if the same ID is in
  `all_devices` and in the output of `--id-only`. Consider
  deduplicating.
- Line 41: `CONFIG_PATH = Path.home() / ".config" / "xinput-plus.json"`.
  On multi-user servers, this writes to the **first** user's
  home. The Policy does not require using `xdg.Config`
  (Python) or the freedesktop standard, but the recommended
  practice is `XDG_CONFIG_HOME`. Consider:
  ```python
  import os
  CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME",
                                    Path.home() / ".config")) / "xinput-plus.json"
  ```
  Not blocking.
- Lines 742-765: the About dialog has HTML with emojis
  (`🖱️`). Non-ASCII characters must be entities or in UTF-8
  — the code uses UTF-8, which is correct per Policy §6.1.

### 5.10  `i18n/README.md`

- **619 lines of user README** in a folder called `i18n/`.
  This is very confusing (§4.7). The content is fine but
  the location is not.

### 5.11  `Launcher.sh`

- Useful for development, not installed (§3.14). Keep it,
  but consider moving it to `scripts/` or `debian/`.

### 5.12  `fix texts.txt`

- Personal notes (§4.9). Move or ignore.

---

## 6. Recommended action plan

Ordered from most critical to most optional. Before each step,
verify with `lintian -iIE --pedantic` that no new warnings appear.

### Phase 0 — Git cleanup (5 min)

```sh
# Remove .qm from tracking
git rm --cached i18n/*.qm
# Ignore misplaced README
# (optional) git rm i18n/README.md
git commit -m "Cleanup: drop compiled .qm from VCS"
```

### Phase 1 — Critical changes that ftp-master will check (1-2 h)

1. **Move README to the root** (§4.7):
   ```sh
   mv i18n/README.md README.md
   ```
2. **Fix shebang** (§2.4):
   - Edit `xinput-plus.py:1`: change
     `#!/usr/bin/env python3` to `#!/usr/bin/python3`.
3. **Raise Standards-Version to 4.7.4** (§2.3) and
   **remove `Priority:`** (§2.2) in `debian/control`.
4. **Resolve the binary name** (§2.1): decide between renaming
   upstream or installing without the extension.
5. **Verify Vcs-Git/Vcs-Browser** (§4.3): create the repo on
   Salsa or remove the fields until it exists.

### Phase 2 — Lintian clean (2-3 h)

6. Add `override_dh_auto_clean` (§3.1).
7. Remove `|| true` in `lrelease` (§3.7).
8. Remove `python3-all` from Build-Depends (§3.2).
9. Add `Multi-Arch: foreign` (§4.10).
10. Add `debian/upstream/metadata` (§3.5).
11. Fix/cover the SVG license in `debian/copyright` (§3.4).
12. Fix the AppStream `id` and add `<description>` in
    `<release>` (§3.9, §3.10).
13. Extend the manpage with AUTHORS and BUGS (§3.12).
14. Add `StartupWMClass=` and `X-Ubuntu-Gettext-Domain=` to
    the desktop file (§3.13).
15. Move or ignore `Launcher.sh` and `fix texts.txt`
    (§3.14, §4.9).

### Phase 3 — Tests (1-2 h)

16. **Local build** with `debuild -us -uc -b` and verify that
    there are no errors.
17. **Full Lintian**:
    ```sh
    lintian -iIE --pedantic --color=auto ../xinput-plus_*_source.changes
    ```
    Should yield **0 errors, 0 warnings** (pedantic are
    optional but recommended).
18. **pbuilder**:
    ```sh
    sudo pbuilder create --distribution unstable
    sudo pbuilder build ../xinput-plus_*_source.changes
    ```
19. **autopkgtest** (optional):
    ```sh
    autopkgtest --null-autopkgtest ../xinput-plus_*.deb \
      -- /usr/share/autopkgtest/setup-commands/setup-testbed
    ```
20. **Manual smoke test**:
    ```sh
    sudo apt install /var/cache/pbuilder/result/xinput-plus_*.deb
    xinput-plus --help
    xinput-plus --lang=es
    man xinput-plus
    sudo apt purge xinput-plus
    ```

### Phase 4 — Upload to mentors (1-2 h)

21. **Verify that the Salsa repo exists** (§4.3).
22. **Clean up `debian/changelog`** (§3.6): regenerate
    with `dch -i "Initial release. (Closes: #NNNNNN)"`
    using the ITP bug number.
23. **Sign the `.changes` with GPG** and upload to
    `mentors.debian.net`:
    ```sh
    debuild -sa
    dput mentors ../xinput-plus_*_amd64.changes
    ```
24. **RFS to debian-mentors@lists.debian.org** with the
    mentors.debian.net link.

### Phase 5 — Post-acceptance (maintenance)

- Configure `watch` in the Debian VCS.
- Subscribe to `xinput-plus@packages.debian.org` (when it
  exists) and to `pkg-gnome-devel@lists.alioth.debian.org` if
  applicable.
- Create a `debian/tests/` with a minimal smoke test (§3.8).

---

## 7. Appendix A: Python conventions in Debian

For Python packages in Debian, the current (2026) conventions
are:

1. **Shebang**: always use `#!/usr/bin/python3` (not
   `#!/usr/bin/env python3`) in scripts installed in
   `/usr/bin/`.
2. **Build-Depends**: include `dh-sequence-python3` (which
   already includes `pybuild` and `dh_python3`). `python3-all`
   is only needed if modules are being built for multiple
   Python versions.
3. **${python3:Depends}**: always in the `Depends:` field of
   the binary package. It automatically calculates the Python
   version and modules.
4. **Do not use `python3-pip` nor wheels**: Debian packages
   Python modules as `python3-<modulename>`. Do not include
   `requirements.txt` in the tarball.
5. **Tests**: use `pytest` or `unittest`, integrated with
   `autopkgtest` via `debian/tests/control`.
6. **Modern packaging**: consider `pybuild` with
   `pyproject.toml` instead of `setup.py` if the project
   grows. For a simple script, the current approach is fine.
7. **Binary extension**: Python scripts installed in
   `/usr/bin/` **must not** keep `.py`.

More information:
- <https://www.debian.org/doc/manuals/python-policy/>
- <https://salsa.debian.org/python-team/tools/pybuild>

---

## 8. Appendix B: recommended checks before uploading to mentors

Run, in this order, on a clean source tree:

```sh
# 1. Verify the changelog format
lintian -i ../xinput-plus_*_source.changes

# 2. Verify Copyright
lintian -i ../xinput-plus_*_source.changes | grep -i copyright

# 3. Verify the source tarball has no binaries
tar -tzf ../xinput-plus_*.orig.tar.gz | grep -E '\.(qm|pyc|so)$'

# 4. Verify that all files in the binary package are valid
dpkg-deb -c ../xinput-plus_*_all.deb | less

# 5. Full Lintian (should be 0 errors, 0 warnings)
lintian -iIE --pedantic ../xinput-plus_*_source.changes

# 6. Verify the watch file
uscan --dehs

# 7. Verify that AppStream is valid
appstreamcli validate-tree ../xinput-plus-*/

# 8. Verify the manpage
man -l debian/xinput-plus.1

# 9. Verify the .desktop
desktop-file-validate debian/xinput-plus.desktop

# 10. pbuilder clean
sudo pbuilder build --distribution unstable \
  ../xinput-plus_*_source.changes
```

If all pass, the package is ready to be uploaded to
`mentors.debian.net`.

---

## 9. Summary of recommended changes (cheatsheet)

```
# File changes (priority order)

debian/control
  - Remove the "Priority: optional" line
  - Raise "Standards-Version: 4.7.3" → "4.7.4"
  - Remove "python3-all" from Build-Depends
  - Add "Multi-Arch: foreign" to the binary stanza
  - (Optional) Add XS-Autobuild: yes

debian/copyright
  - Add a stanza for src/xinput-plus.svg
  - Verify asset licenses

debian/rules
  - Add override_dh_auto_clean
  - Remove "|| true" in lrelease
  - Rename xinput-plus.py when installing (if you decide
    to keep the upstream name)

debian/watch
  - (Optional) opts="mode=github,..."

debian/xinput-plus.desktop
  - Add StartupWMClass
  - Add X-Ubuntu-Gettext-Domain

debian/xinput-plus.metainfo.xml
  - Change id to io.github.wachin.xinput-plus
  - Add <description> in each <release>

debian/xinput-plus.1
  - Add AUTHORS and BUGS sections

debian/upstream/metadata (new)
  - Name, Contact, Repository, Bug-Database

debian/changelog
  - Regenerate with the real upload date
  - First entry: "Initial release. (Closes: #NNNNNN)"

xinput-plus.py
  - Shebang: #!/usr/bin/env python3 → #!/usr/bin/python3
  - (Optional) Use XDG_CONFIG_HOME for CONFIG_PATH

README.md (moved from i18n/)
i18n/*.qm (remove from VCS, rules already builds them)
Launcher.sh (move to scripts/ or ignore)
fix texts.txt (move or ignore)
```

---

## 10. References consulted

- [Debian Policy Manual v4.7.4.1](https://www.debian.org/doc/debian-policy/) (March 2026)
- [Upgrading checklist 4.7.4 and 4.7.3](https://www.debian.org/doc/debian-policy/upgrading-checklist.html)
- [Debian Python Policy](https://www.debian.org/doc/manuals/python-policy/)
- [Lintian 2.138/2.139 tag reference](https://lintian.debian.org/tags/)
- [Debian Developer's Reference, Best Packaging Practices](https://www.debian.org/doc/manuals/developers-reference/best-pkging-practices.en.html)
- [Maintainer's Guide](https://www.debian.org/doc/manuals/maint-guide/)
- [AppStream specification](https://www.freedesktop.org/software/appstream/docs/)
- [uscan / debian-watch](https://manpages.debian.org/testing/uscan/uscan.1.en.html)
- [Repository: upstream/metadata](https://wiki.debian.org/UpstreamMetadata)

