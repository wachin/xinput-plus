# How to compile and test the .deb package on your own computer

This guide is for developers who want to build the `xinput-plus` package
locally, install the resulting `.deb`, and test it on their own Debian
system before publishing it. You do not need to be a Debian Developer or
have any special account to do this.

**Debian 12 (Bookworm)** is assumed throughout. The commands are identical
on Debian 13 (Trixie) unless noted otherwise.

---

## What we are going to do

1. Install the build tools.
2. Clone the repository.
3. Enable source repositories and install build dependencies.
4. Build the package with `debuild`.
5. Check the package with `lintian`.
6. Install the `.deb` and test the program.
7. Uninstall when you are done.

---

## Step 1 — Install the build tools

Open a terminal and run:

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

What each package does:

| Package | Purpose |
|---------|---------|
| `build-essential` | C compiler and basic build tools |
| `devscripts` | Provides `debuild`, `dch`, `uscan`, and other helpers |
| `debhelper` | The build system used by `debian/rules` |
| `dh-python` | Python packaging support (`dh-sequence-python3`) |
| `pyqt6-dev-tools` | Provides `pylupdate6` to extract translation strings |
| `qt6-tools-dev-tools` | Provides `lrelease-qt6` to compile `.qm` translation files |
| `lintian` | Automated Debian policy checker |

---

## Step 2 — Clone the repository

If you do not have the source code yet:

```bash
git clone https://github.com/wachin/xinput-plus
cd xinput-plus
```

If you already have it cloned, make sure you are on the main branch and
up to date:

```bash
git checkout main
git pull
```

---

## Step 3 — Enable source repositories (recommended)

This step lets `apt` read your `debian/control` and install build
dependencies automatically. If you skip it, you will have to install them
by hand.

Edit `/etc/apt/sources.list` as root:

```bash
sudo nano /etc/apt/sources.list
```

Find the lines that start with `deb-src` and make sure they are **not**
commented out (no `#` at the beginning). They should look like this:

```
deb-src http://deb.debian.org/debian bookworm main
deb-src http://deb.debian.org/debian-security bookworm-security main
deb-src http://deb.debian.org/debian bookworm-updates main
```

Save the file and update:

```bash
sudo apt update
```

---

## Step 4 — Install the build dependencies

From the root of the repository (the directory that contains the `debian/`
folder):

```bash
sudo apt build-dep .
```

This command reads the `Build-Depends:` field in `debian/control` and
installs everything needed automatically.

> If you see the error `E: You must put some 'source' URIs in your
> sources.list`, go back to Step 3 and uncomment the `deb-src` lines.

If you prefer to install the dependencies manually without touching
`sources.list`:

```bash
sudo apt install \
  debhelper \
  dh-python \
  python3-all \
  pyqt6-dev-tools \
  qt6-tools-dev-tools
```

---

## Step 5 — Build the package

From the root of the repository, run:

```bash
debuild -us -uc -b
```

What those options mean:

- `-us` — "unsigned source": skips signing the source package (you do not
  need a GPG key for local testing).
- `-uc` — "unsigned changes": skips signing the `.changes` file.
- `-b` — builds only the binary package (the `.deb`), not the source.

You will see a lot of output in the terminal. If everything goes well, the
last lines will look something like:

```
dpkg-deb: building package 'xinput-plus' in '../xinput-plus_6.6.4-1_all.deb'.
...
dpkg-buildpackage: info: binary-only upload (no source included)
```

The `.deb` file is created **in the parent directory**, one level above the
repository:

```bash
ls ../xinput-plus_*.deb
# ../xinput-plus_6.6.4-1_all.deb
```

### What to do if the build fails

Read the error message carefully. The most common errors are:

**"command not found: lrelease-qt6"**
Install `qt6-tools-dev-tools`:
```bash
sudo apt install qt6-tools-dev-tools
```

**"dh: error: unable to load addon python3"**
Install `dh-python`:
```bash
sudo apt install dh-python
```

**"Makefile:X: \*\*\* missing separator. Stop."**
The `debian/rules` file has spaces where it should have tabs. Open it in
an editor that shows invisible characters and replace the leading spaces
with real tab characters.

**"dpkg-source: error: can't build with source format '3.0 (quilt)'"**
The file `debian/source/format` is missing. Create it:
```bash
echo "3.0 (quilt)" > debian/source/format
```

---

## Step 6 — Check the package with lintian

`lintian` analyses the `.deb` for Debian policy violations. Run:

```bash
lintian --pedantic ../xinput-plus_6.6.4-1_all.deb
```

The output uses these letters to indicate severity:

| Letter | Meaning |
|--------|---------|
| `E:` | **Error** — serious problem; the package would be rejected |
| `W:` | **Warning** — should be fixed before asking for a sponsor |
| `I:` | **Info** — minor issue; fix if straightforward |
| `P:` | **Pedantic** — style suggestion; optional |

If you see any `E:` errors, fix them before continuing. To understand what
any tag means:

```bash
lintian-explain-tags tag-name-here
```

For example:

```bash
lintian-explain-tags no-upstream-changelog
```

You can also look up any tag at https://lintian.debian.org/tags/

The goal is a clean run with no `E:` or `W:` lines.

---

## Step 7 — Install the .deb and test the program

Install the package with `apt` (recommended because it resolves
dependencies automatically):

```bash
sudo apt install ../xinput-plus_6.6.4-1_all.deb
```

> If `apt` says it cannot find the file, make sure you are using the
> correct path. The `../` means the file is in the parent directory.

Now test the program:

```bash
# Launch normally:
xinput-plus

# Launch in Spanish:
xinput-plus --lang=es

# Launch in English:
xinput-plus --lang=en
```

Also check that the man page was installed correctly:

```bash
man xinput-plus
```

And verify that the program appears in your desktop application menu
(if you use one).

---

## Step 8 — Uninstall the package

When you are done testing:

```bash
# Remove the package but keep the user's configuration files:
sudo apt remove xinput-plus

# Remove the package and delete configuration files too:
sudo apt purge xinput-plus
```

---

## Workflow for making changes and rebuilding

When you modify the code and want to test a new version, the usual flow is:

**1. Make your changes to the code.**

**2. Add a changelog entry:**

```bash
dch -v 6.6.4-2 "Brief description of what you changed."
```

This opens your editor with the new entry ready to fill in. Save and close.

**3. Mark the entry as ready (changes UNRELEASED to unstable):**

```bash
dch -r ""
```

**4. Clean up artefacts from the previous build:**

```bash
debian/rules clean
```

**5. Rebuild:**

```bash
debuild -us -uc -b
```

**6. Install the new version:**

```bash
sudo apt install ../xinput-plus_6.6.4-2_all.deb
```

`apt` will detect that a version is already installed and upgrade it
automatically.

---

## Building in a clean environment with pbuilder (optional but recommended)

The method above builds on your own system, which has many packages
installed. This can hide missing dependencies that are not declared in
`debian/control`. `pbuilder` builds inside a minimal isolated chroot,
exactly as the official Debian build servers would.

### Set up pbuilder (once only)

```bash
sudo apt install pbuilder
sudo pbuilder create --distribution bookworm
```

This downloads a minimal Debian system and saves it as an image. It takes
a few minutes the first time.

### Build with pbuilder

You first need a source package, not just the binary. Build it like this:

```bash
debuild -us -uc -S
```

This creates a `.dsc` file in the parent directory. Then:

```bash
sudo pbuilder build ../xinput-plus_6.6.4-1.dsc
```

The resulting `.deb` appears in `/var/cache/pbuilder/result/`.

### Why use pbuilder?

If `pbuilder` fails but `debuild` succeeds, it means you are missing a
dependency declaration in `Build-Depends:` in `debian/control`. That is
exactly the kind of error the Debian team would catch when reviewing your
package, so it is much better to find it yourself first.

---

## Quick reference

```bash
# 1. Install tools (once)
sudo apt install build-essential devscripts debhelper dh-python \
                 pyqt6-dev-tools qt6-tools-dev-tools lintian

# 2. Clone the repository
git clone https://github.com/wachin/xinput-plus
cd xinput-plus

# 3. Install build dependencies
sudo apt build-dep .

# 4. Build
debuild -us -uc -b

# 5. Check with lintian
lintian --pedantic ../xinput-plus_6.6.4-1_all.deb

# 6. Install and test
sudo apt install ../xinput-plus_6.6.4-1_all.deb
xinput-plus

# 7. Uninstall when done
sudo apt purge xinput-plus
```
