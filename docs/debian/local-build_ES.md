# Build & install the binary package locally

## 0) Make sure `deb-src` is enabled (optional but recommended)

This allows `apt build-dep` to read your local `debian/control` and install build-deps automatically.

Edit `/etc/apt/sources.list` and ensure the lines with `deb-src` are **uncommented** for your Debian release, e.g.:

```
deb-src http://deb.debian.org/debian bookworm main
deb-src http://deb.debian.org/debian-security bookworm-security main
deb-src http://deb.debian.org/debian bookworm-updates main
```

Then:

```bash
sudo apt update
```

## 1) Install build tools (once)

```bash
sudo apt install build-essential devscripts debhelper dh-python \
                 pyqt6-dev-tools qt6-tools-dev-tools
```

> `dh-python` provides `dh-sequence-python3`.
> `qt6-tools-dev-tools` provides `lrelease-qt6` and `linguist-qt6`.

## 2) (Optional) Install build-dependencies from your control file

This step reads your local `debian/control` and installs `Build-Depends:` automatically.

```bash
# Either one works (depends on APT version)
sudo apt-get build-dep ./
# or
sudo apt build-dep .
```

If you get “no source entries”, double-check step 0.

## 3) Clean the tree

```bash
debian/rules clean || true
```

## 4) Build the **binary** package (no signing)

From the project root (where `debian/` lives):

```bash
debuild -us -uc -b
# (equivalente) dpkg-buildpackage -us -uc -b
```

This will produce `../xinput-plus_6.6.2-1_all.deb` (path is parent directory).

## 5) Install the .deb and test

Use `apt` (recommended – resolves deps) or `dpkg`:

```bash
# Recommended:
sudo apt install ../xinput-plus_6.6.2-1_all.deb

# Or with dpkg + fix-deps:
# sudo dpkg -i ../xinput-plus_6.6.2-1_all.deb || sudo apt -f install
```

Run it:

```bash
xinput-plus --lang=es   # or --lang=en
```

If you want to remove it later:

```bash
sudo apt remove xinput-plus          # keep config files
# or
sudo apt purge xinput-plus           # remove config files too
```

---

## Tips (nice-to-have)

* If you rebuild often, just bump the Debian revision in `debian/changelog`:

  ```bash
  dch -v 6.6.2-2 "Local test rebuild."
  dch -r
  debuild -us -uc -b
  ```

* For *really clean* builds matching Debian buildds, consider `sbuild` or `pbuilder` later. For now, local `debuild -b` is perfect to test on your own machine.

* Keep personal files (e.g. `.dput.cf`) **outside** the repo; add them to `.gitignore` so they never interfere with the build.

That’s it — you’ll get a reproducible `.deb` you can install and test on your Debian 12 system.

