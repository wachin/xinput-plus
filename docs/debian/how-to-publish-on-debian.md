# How to publish your program on packages.debian.org

A practical guide for independent developers who have never packaged for Debian before.

This guide uses `xinput-plus` as a concrete example throughout, so you can
see exactly what each step looks like in a real project. Replace every
occurrence of `xinput-plus`, `wachin`, and the author details with your own.

---

## What you are actually trying to do

When people say "get my package into Debian" they mean this chain of events:

1. You prepare your source code in a specific format Debian understands.
2. You upload it to a staging area called **mentors.debian.net**.
3. A **Debian Developer (DD)** reviews it and, if it passes, uploads it to
   the official Debian archive on your behalf. This person is called a
   **sponsor**.
4. The package enters the **NEW queue**, where the FTP Team checks it for
   legal and policy compliance.
5. Once accepted, it lands in **unstable** (also called **Sid**).
6. After roughly two days without critical bugs it migrates to **testing**.
7. When the next stable release is frozen and released, it becomes part of
   **stable**.

You cannot upload directly to Debian unless you are a Debian Developer.
Until then, you always need a sponsor. This is normal and expected — it is
not a rejection, it is the process.

---

## Part 1 — Prerequisites

### 1.1 Install the packaging tools

On Debian 12 (Bookworm):

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

`devscripts` gives you `debuild`, `dch`, `uscan`, and other helpers.
`lintian` is the automated policy checker — you must pass it before
asking for a sponsor. `pbuilder` lets you build in a clean environment.

### 1.2 Create a GPG key

Every upload to Debian must be signed with a GPG key. If you do not have
one yet:

```bash
gpg --full-generate-key
```

Choose **RSA and RSA**, key size **4096**, and set an expiry date (1–2 years
is fine; you can extend it later). Use the same email address you will put
in `debian/changelog` and `debian/control`.

To see your key ID:

```bash
gpg --list-secret-keys --keyid-format LONG
```

The output looks like:

```
sec   rsa4096/AABBCCDD11223344 2025-01-01 [SC]
```

`AABBCCDD11223344` is your key ID. You will need it in the next step.

### 1.3 Upload your key to a keyserver

```bash
gpg --keyserver keyserver.ubuntu.com --send-keys AABBCCDD11223344
```

Debian infrastructure uses the Ubuntu keyserver network. Your key must be
publicly reachable before a sponsor can verify your uploads.

### 1.4 Create a Salsa account

Salsa is Debian's GitLab instance at https://salsa.debian.org. You need an
account to host your packaging repository there (required by `Vcs-Git` and
`Vcs-Browser` in `debian/control`).

1. Register at https://salsa.debian.org/users/sign_up
2. Create a new project named after your package (e.g. `xinput-plus`).
3. Add your GPG key fingerprint to your Salsa profile under
   **Preferences → GPG Keys**.

---

## Part 2 — Structuring your source

### 2.1 What Debian expects

Debian uses the **3.0 (quilt)** source format. Your source tree must contain
a `debian/` directory with at minimum these files:

```
debian/
  changelog       — version history in a strict format
  control         — package metadata and dependencies
  copyright       — license information in DEP-5 format
  rules           — build instructions (a Makefile)
  source/
    format        — contains the text "3.0 (quilt)"
```

Additional files that are strongly recommended (and required for GUI apps):

```
debian/
  xinput-plus.desktop   — application menu entry
  xinput-plus.metainfo.xml — AppStream metadata
  xinput-plus.1         — man page
  watch                 — tells uscan where to find new upstream releases
```

### 2.2 `debian/source/format`

This file must contain exactly one line:

```
3.0 (quilt)
```

### 2.3 `debian/changelog`

This is the most strictly formatted file in the whole package. Every entry
must follow this exact layout — spacing, dashes, and all:

```
xinput-plus (6.6.4-1) unstable; urgency=medium

  * New upstream release 6.6.4.

 -- Washington Indacochea Delgado <wachin.id@gmail.com>  Wed, 17 Sep 2025 22:37:19 -0500
```

Rules:
- The version in parentheses is `<upstream-version>-<debian-revision>`.
  The first time you package something, the Debian revision is always `1`.
- The suite must be `unstable` when you are ready to upload. Use
  `UNRELEASED` while you are still working locally.
- The maintainer line starts with exactly one space, then ` -- `, then the
  name, email in angle brackets, two spaces, and the RFC 2822 date.
- Never edit this file by hand for new entries. Use `dch` instead:

```bash
# Start a new entry for a new upstream version:
dch -v 6.6.5-1 "New upstream release 6.6.5."

# Mark the top entry as ready to upload:
dch -r ""
```

`dch -r` changes `UNRELEASED` to `unstable` and updates the timestamp.

### 2.4 `debian/control`

This file has two stanzas: one for the **source package** and one for each
**binary package** it produces. For a simple single-binary package:

```
Source: xinput-plus
Section: x11
Priority: optional
Maintainer: Washington Indacochea Delgado <wachin.id@gmail.com>
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

Key points:
- `Standards-Version` must match the current Debian Policy version. Check
  https://www.debian.org/doc/debian-policy/ for the latest. As of early
  2026 it is `4.7.3`.
- `Architecture: all` means the package is architecture-independent (pure
  Python, shell scripts, etc.). Use `any` for compiled binaries.
- `${python3:Depends}` and `${misc:Depends}` are substitution variables
  filled in automatically by `dh-python` and `debhelper` at build time.
  Always include them for Python packages.
- `Vcs-Git` and `Vcs-Browser` must point to your Salsa repository.
- The long description (indented lines) must not have trailing spaces.
  Blank lines within the description are represented by a single ` .`
  (space then dot).

### 2.5 `debian/copyright` (DEP-5 format)

This is the file most beginners get wrong. It must follow the
**DEP-5** machine-readable format exactly. The most common mistakes are:

- Missing the `Format:` header at the very top.
- Putting `#` comments on the same line as a field (`Files: foo # comment`
  is invalid — comments must be on their own line).
- Indenting stanzas (each stanza must start at column 0).

A correct minimal example:

```
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: xinput-plus
Upstream-Contact: Washington Indacochea Delgado <wachin.id@gmail.com>
Source: https://github.com/wachin/xinput-plus

Files: *
Copyright:
  2024-2025 Washington Indacochea Delgado <wachin.id@gmail.com>
License: GPL-3+
 On Debian systems, the full text of the GNU General Public License
 version 3 can be found in /usr/share/common-licenses/GPL-3.

Files: debian/*
Copyright:
  2025 Washington Indacochea Delgado <wachin.id@gmail.com>
License: GPL-3+
 On Debian systems, the full text of the GNU General Public License
 version 3 can be found in /usr/share/common-licenses/GPL-3.
```

If your project includes files under different licenses (icons, bundled
libraries, etc.), each group of files needs its own `Files:` stanza.
Every file in the source tree must be covered by at least one stanza.

### 2.6 `debian/rules`

This is a Makefile that tells `debhelper` how to build your package. For
most modern packages, the entire file is just:

```makefile
#!/usr/bin/make -f
export DH_VERBOSE=1

%:
	dh $@
```

The `dh $@` line delegates everything to `debhelper`, which handles
compilation, installation, stripping, and more automatically.

If you need to customise a step, add an `override_dh_<step>` target:

```makefile
override_dh_auto_install:
	install -D -m0755 xinput-plus.py \
	  debian/xinput-plus/usr/bin/xinput-plus
```

Important: the indentation in `debian/rules` must use **tabs**, not spaces.
This is a Makefile requirement. If you use spaces, the build will fail with
a cryptic error.

### 2.7 `debian/watch`

This file tells `uscan` (and the Debian QA tools) where to find new
upstream releases automatically. For a GitHub project:

```
version=4
opts=filenamemangle=s%.*archive/refs/tags/v?(\d+[\d\.]*)\.tar\.gz%xinput-plus-$1.tar.gz% \
  https://github.com/wachin/xinput-plus/tags \
  .*/archive/refs/tags/v?(\d+[\d\.]*)\.tar\.gz
```

### 2.8 Man page (`debian/xinput-plus.1`)

Every program that installs a binary into `/usr/bin` must have a man page.
The minimum required sections are `NAME`, `SYNOPSIS`, `DESCRIPTION`, and
`SEE ALSO`. The `.TH` macro at the top must include the date and version:

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

## Part 3 — Building and testing locally

### 3.1 Build with `debuild`

From the root of your source tree (the directory that contains `debian/`):

```bash
debuild -us -uc
```

`-us -uc` means "unsigned source, unsigned changes" — you skip signing
during local testing. This produces several files one directory up:

```
../xinput-plus_6.6.4-1.dsc
../xinput-plus_6.6.4.orig.tar.gz
../xinput-plus_6.6.4-1.debian.tar.xz
../xinput-plus_6.6.4-1_all.deb
../xinput-plus_6.6.4-1_amd64.changes
```

If the build fails, read the output carefully — `debhelper` is verbose and
usually tells you exactly what went wrong.

### 3.2 Run `lintian`

`lintian` is the automated policy checker. You must have zero errors and
ideally zero warnings before asking for a sponsor:

```bash
lintian --pedantic ../xinput-plus_6.6.4-1_amd64.changes
```

Common lintian tags and what they mean:

| Tag | Meaning |
|-----|---------|
| `E:` | Error — will cause rejection. Must fix. |
| `W:` | Warning — should fix. Sponsors will ask about these. |
| `I:` | Info — minor issue. Fix if easy. |
| `P:` | Pedantic — style suggestion. Optional. |

To look up what any tag means:

```bash
lintian-explain-tags <tag-name>
# or online: https://lintian.debian.org/tags/<tag-name>
```

### 3.3 Test in a clean environment with `pbuilder`

Your machine has many packages installed that might hide missing build
dependencies. `pbuilder` builds in a minimal chroot so you catch those
problems before a sponsor does.

Set up pbuilder once:

```bash
sudo pbuilder create --distribution bookworm
```

Then build your package inside it:

```bash
sudo pbuilder build ../xinput-plus_6.6.4-1.dsc
```

The resulting `.deb` is placed in `/var/cache/pbuilder/result/`.

If you want to test against `unstable` (which is what Debian uses):

```bash
sudo pbuilder create --distribution unstable
sudo pbuilder build --distribution unstable ../xinput-plus_6.6.4-1.dsc
```

### 3.4 Install and test the `.deb` manually

```bash
sudo dpkg -i /var/cache/pbuilder/result/xinput-plus_6.6.4-1_all.deb
# Check it runs:
xinput-plus
# Check the man page installed correctly:
man xinput-plus
# Remove it:
sudo dpkg -r xinput-plus
```

---

## Part 4 — Filing an ITP (Intent to Package)

Before uploading anywhere, you must file an **ITP bug** against the
`wnpp` pseudo-package. This tells the Debian community you are working on
this package and prevents duplicate effort.

```bash
reportbug wnpp
```

When prompted:
- Choose **ITP** (Intent to Package).
- Package name: `xinput-plus`
- Short description: `PyQt6 GUI to adjust pointer speed per device (Xorg, via xinput)`
- License: `GPL-3+`
- URL: `https://github.com/wachin/xinput-plus`

`reportbug` will send an email to `submit@bugs.debian.org` and you will
receive a bug number back (e.g. `#1234567`). Add this number to your
`debian/changelog` entry:

```
xinput-plus (6.6.4-1) unstable; urgency=medium

  * Initial release. (Closes: #1234567)

 -- Washington Indacochea Delgado <wachin.id@gmail.com>  Wed, 17 Sep 2025 22:37:19 -0500
```

The `Closes: #NNNNNN` syntax automatically closes the ITP bug when your
package is accepted into the archive.

---

## Part 5 — Uploading to mentors.debian.net

`mentors.debian.net` is the staging area where non-DDs upload packages for
sponsors to review. It is not the official Debian archive — it is a
waiting room.

### 5.1 Sign your package

Now build with signing enabled:

```bash
debuild -sa
```

`-sa` means "include the original source tarball". You will be prompted for
your GPG passphrase. This produces a signed `.changes` file.

### 5.2 Configure `dput`

`dput` is the tool that uploads your package. Create or edit
`~/.dput.cf`:

```ini
[mentors]
fqdn = mentors.debian.net
incoming = /upload
method = https
allow_unsigned_uploads = 0
progress_indicator = 2
```

### 5.3 Upload

```bash
dput mentors ../xinput-plus_6.6.4-1_amd64.changes
```

If the upload succeeds, you will receive a confirmation email and your
package will appear at:
`https://mentors.debian.net/package/xinput-plus`

---

## Part 6 — Finding a sponsor

A sponsor is a Debian Developer who reviews your package and uploads it to
the official archive on your behalf. Finding one is often the hardest part
of the process — it requires patience.

### 6.1 Subscribe to the debian-mentors mailing list

```
https://lists.debian.org/debian-mentors/
```

This is the primary channel for sponsorship requests. Read the list for a
week before posting so you understand the tone and expectations.

### 6.2 Send a sponsorship request

Post to `debian-mentors@lists.debian.org` with a subject like:

```
RFS: xinput-plus/6.6.4-1 -- PyQt6 GUI to adjust pointer speed per device
```

RFS stands for **Request for Sponsorship**. Your email should include:
- A brief description of what the program does.
- The ITP bug number.
- The mentors.debian.net URL.
- A note that lintian is clean and pbuilder builds successfully.
- Any known issues or things you are unsure about.

Example:

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

### 6.3 Be patient and responsive

Sponsors are volunteers. A response may take days or weeks. When a sponsor
reviews your package and asks for changes, make them promptly, upload a new
version to mentors.debian.net, and reply to the thread.

Do not send the same RFS email repeatedly to the list. One post per
package version is the norm. If weeks pass with no response, you may post
again when you upload a new version.

---

## Part 7 — The NEW queue

When your sponsor uploads the package for the first time, it enters the
**NEW queue** at https://ftp-master.debian.org/new.html. The FTP Team
reviews it for:

- License compliance (every file must have a clear, DFSG-free license).
- Correct `debian/copyright` (DEP-5 format, all files covered).
- Appropriate section and priority.
- No name conflicts with existing packages.

The NEW queue can take anywhere from a few days to several months depending
on the FTP Team's workload. You cannot speed this up. Just wait.

When the package is accepted you will receive an email and it will appear
at `https://packages.debian.org/unstable/xinput-plus`.

---

## Part 8 — Maintaining the package after acceptance

Getting in is not the end — it is the beginning of an ongoing commitment.

### 8.1 Updating for a new upstream release

1. Update your source code.
2. Run `uscan` to verify the watch file works:
   ```bash
   uscan --verbose
   ```
3. Add a new changelog entry:
   ```bash
   dch -v 6.6.5-1 "New upstream release 6.6.5."
   dch -r ""
   ```
4. Build, run lintian, test with pbuilder.
5. Upload to mentors.debian.net and ask your sponsor to upload again.

Once you have a track record of clean packages, you can apply to become a
**Debian Maintainer (DM)**, which gives you upload rights for your own
packages without needing a sponsor every time.

### 8.2 Responding to bug reports

Users will file bugs against your package at `bugs.debian.org`. Subscribe
to your package's bug tracker:

```
https://bugs.debian.org/xinput-plus
```

Respond to bugs promptly. A package with many unaddressed bugs can be
removed from the archive.

### 8.3 Keeping `Standards-Version` current

Debian Policy is updated regularly. Check the current version at
https://www.debian.org/doc/debian-policy/ and update `Standards-Version`
in `debian/control` when you make a new upload. Read the upgrading checklist
at https://www.debian.org/doc/debian-policy/upgrading-checklist.html to
see what changed.

---

## Part 9 — From unstable to stable

You do not need to do anything to get your package into stable. The
migration happens automatically:

1. Your package lands in **unstable** (Sid).
2. After 2–10 days with no RC (release-critical) bugs, it migrates to
   **testing** automatically.
3. When the Debian Release Team freezes testing for a new stable release
   (roughly every two years), your package is included if it has no RC bugs.
4. The new stable release ships and your package is now on
   `packages.debian.org/stable/xinput-plus`.

The only thing you need to do is keep the package free of RC bugs during
the freeze period.

---

## Quick reference — files checklist

Before asking for a sponsor, verify every item:

```
[ ] debian/source/format        contains "3.0 (quilt)"
[ ] debian/changelog            top entry suite is "unstable", no duplicates,
                                 contains "Closes: #ITP-number"
[ ] debian/control              Standards-Version is current, Vcs-* fields
                                 point to Salsa, long description has no
                                 trailing spaces
[ ] debian/copyright            starts with Format: header, all files covered,
                                 no inline # comments on Fields: lines
[ ] debian/rules                uses tabs (not spaces), builds cleanly
[ ] debian/watch                uscan can find the latest upstream tarball
[ ] debian/<pkg>.1              man page exists for every binary in /usr/bin
[ ] debian/<pkg>.desktop        Name is human-readable, Categories correct
[ ] debian/<pkg>.metainfo.xml   current version in <releases>, no deprecated
                                 <developer_name> tag
[ ] lintian --pedantic          zero errors, ideally zero warnings
[ ] pbuilder build              succeeds in a clean unstable chroot
[ ] ITP filed                   bug number recorded in changelog
[ ] Salsa repository            Vcs-Git and Vcs-Browser URLs are reachable
[ ] GPG key                     on keyserver.ubuntu.com, same email as
                                 debian/changelog
```

---

## Useful links

| Resource | URL |
|----------|-----|
| Debian Policy Manual | https://www.debian.org/doc/debian-policy/ |
| Debian Developer's Reference | https://www.debian.org/doc/manuals/developers-reference/ |
| DEP-5 copyright format | https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/ |
| mentors.debian.net | https://mentors.debian.net/ |
| NEW queue | https://ftp-master.debian.org/new.html |
| lintian tag reference | https://lintian.debian.org/tags/ |
| ITP / WNPP | https://www.debian.org/devel/wnpp/ |
| debian-mentors mailing list | https://lists.debian.org/debian-mentors/ |
| Salsa | https://salsa.debian.org/ |
| Debian Maintainer process | https://wiki.debian.org/DebianMaintainer |
| Debian New Member process | https://nm.debian.org/ |
