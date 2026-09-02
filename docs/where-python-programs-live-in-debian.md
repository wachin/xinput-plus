# Where Do Python Programs Live in Debian? Two Ways Debian Installs Python Software

> A practical explanation for Linux users and new packagers: why you see
> some Python programs in `/usr/lib/python3/dist-packages/` and others
> installed directly as scripts in `/usr/bin/` — and why both are correct.

---

## Introduction — the mystery you find in Synaptic

If you like exploring your Debian system (for example, by right-clicking a
package in **Synaptic** and looking at its installed files), you have
probably noticed something curious about Python programs.

A program like **yt-dlp** seems to live in two places at once:

1. A **tiny launcher** in `/usr/bin/yt-dlp` (only a few lines), and
2. The **real code** in `/usr/lib/python3/dist-packages/yt_dlp/` — a folder
   with more than a hundred `.py` files.

If you open that little launcher, this is what you find inside:

```python
#! /usr/bin/python3
# -*- coding: utf-8 -*-
import re
import sys
from yt_dlp import main
if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    sys.exit(main())
```

And then a natural question appears: *"Most Python programs I see are
installed in `/usr/lib/python3/dist-packages/` with a launcher. Does that
mean a small Python program **cannot** be installed directly in `/usr/bin/`?
Is that even allowed?"*

**Short answer: yes, it is allowed — and it is very common.** Debian uses
**two different installation patterns** for Python software, and which one
a package uses depends on **how the program is structured**, not on a fixed
rule. Let's look at both.

---

## 1. Pattern A — module + thin launcher (the yt-dlp style)

This pattern is used when the program is a **Python package**: a folder
with an `__init__.py` file and many `.py` modules inside.

**What gets installed:**

- The whole package folder goes to
  `/usr/lib/python3/dist-packages/<package>/`
- A small entry-point script goes to `/usr/bin/<command>`

That launcher does only three things: it imports the real `main()` function
from the package, cleans up its own filename (the `re.sub` line just strips
suffixes like `.exe` on Windows — harmless on Linux), and calls it.

**Why Debian does it this way for these programs:**

- The code is **importable as a library**. yt-dlp is not only a command —
  other programs (GUI downloaders, scripts, extensions) `import yt_dlp`
  and use it as a Python module. Putting the code in `dist-packages/`
  makes that possible.
- The build system (setuptools / pybuild) **generates the launcher
  automatically** from an "entry point" declared by the upstream author.

**Real examples you can check on a Debian system today:**

| Program | Launcher in `/usr/bin` | Real code in `dist-packages` |
|---|---|---|
| `yt-dlp` | `yt-dlp` (entry-point script) | `yt_dlp/` package |
| `arandr` (screen layout GUI) | `arandr` (42 lines) | `screenlayout/` package |
| `catfish` (file search GUI) | `catfish` (45 lines) | `catfish/` + `catfish_lib/` |

You can verify it yourself:

```bash
dpkg -L arandr | grep -E "bin/|dist-packages"
```

---

## 2. Pattern B — the single-file script (installed directly in /usr/bin)

Now look at the other family: programs that are **one single Python
file**, with no package structure at all. For these, Debian installs the
script itself, directly and executable, in `/usr/bin/`:

| Program | What it is | Where it lives |
|---|---|---|
| `command-not-found` | a ~100-line helper | `/usr/bin/command-not-found` |
| `cppcheck-htmlreport` | a ~1000-line report generator | `/usr/bin/cppcheck-htmlreport` |
| `reportbug` | Debian's classic bug-reporting tool: one large Python script, installed this way for many years | `/usr/bin/reportbug` |

For this pattern there is no launcher and no `dist-packages` folder —
the script **is** the program. The only requirements Debian applies are:

1. **A proper shebang**: the first line must be `#!/usr/bin/python3`
   (not `#!/usr/bin/env python3`), because the interpreter on Debian is
   guaranteed to be exactly there.
2. **No language extension** in the file name inside `/usr/bin/` — the
   Debian Policy (§10.4) says commands in the PATH should not carry the
   extension of the language they are written in. So the installed name is
   `xinput-plus`, never `xinput-plus.py`.

So when you find a small program that is just one `.py` file, installing it
directly into `/usr/bin/` (with a good shebang, executable bit, and no
`.py` in the installed name) is not a hack — it is the standard Debian
approach for this kind of software.

---

## 3. How does Debian choose between the two patterns?

It is decided by the **structure of the program**, not by taste:

| Situation | Pattern Debian uses |
|---|---|
| The program is one `.py` file (an application, not a library) | **B** — script directly in `/usr/bin/` |
| The program is a folder with `__init__.py` and several modules | **A** — package in `dist-packages/` + launcher |
| Other programs are expected to `import` it as a library | **A** — the code must be in `dist-packages/` to be importable |
| The program is generated by setuptools/pip with entry points | **A** — the launcher is created by the build tools |

Both patterns pass `lintian` (Debian's automatic policy checker) perfectly
when done correctly.

---

## 4. "But how does the package know Python is needed?"

This is the part that convinces most people. When you build a Debian
package, a helper called `dh_python3` **scans everything you install** —
including scripts placed in `/usr/bin/` — and it automatically adds the
Python dependency to the binary package.

Here is a real example. While packaging **xinput-plus** (a small
single-file PyQt6 application), the built package ended up with this
`Depends` line:

```
Depends: python3:any, python3-pyqt6, xinput, qt6-svg-plugins
```

Notice the first entry, `python3:any`. Nobody wrote that by hand: it means
"works with any Python 3 version", and it was **generated automatically**
by `dh_python3` when it found the Python script in `/usr/bin/`. So a
single-file script installed this way is perfectly protected: without a
Python 3 interpreter, the package simply cannot be installed.

---

## 5. Case study: packaging a small PyQt6 tool (xinput-plus)

xinput-plus is a good real-life example of Pattern B. It is a
**single-file application**: one Python file of roughly 800 lines that
provides a PyQt6 graphical interface to adjust pointer speed through
`xinput`.

How it is packaged:

- In the **source repository**, the file keeps its upstream name
  `xinput-plus.py`. This is important for the translation tools: PyQt's
  `pylupdate6` **only accepts files that end in `.py`**, so renaming the
  source file would break the translation workflow.
- In `debian/rules`, the install step copies it to its final, correct name:

  ```make
  install -D -m0755 xinput-plus.py debian/xinput-plus/usr/bin/xinput-plus
  ```

  One line, and the program is installed exactly where it belongs: as
  `/usr/bin/xinput-plus` — no extension, executable, with the
  `#!/usr/bin/python3` shebang.
- The build is **lintian-clean**, the translations (`.qm` files) are
  compiled during the package build, and `dh_python3` takes care of the
  Python dependency automatically.

If one day the program grows so much that it is split into several
modules, that would be the moment to switch to Pattern A (a real Python
package + launcher). Until then, Pattern B is simpler and one hundred
percent correct.

---

## 6. Explore it yourself

These commands are safe (read-only) and work on any Debian, MX Linux,
Ubuntu or derivative:

```bash
# Which package owns the yt-dlp command?
dpkg -S "$(command -v yt-dlp)"

# Where does arandr install its real code?
dpkg -L arandr | grep -E "bin/|dist-packages"

# Look at a thin launcher
head -5 /usr/bin/arandr

# List some Python libraries installed by apt
ls /usr/lib/python3/dist-packages/ | head -20

# Find single-file Python programs directly in /usr/bin
for f in /usr/bin/*; do head -1 "$f" 2>/dev/null | grep -q "^#!/usr/bin/python3" \
  && dpkg -S "$f" 2>/dev/null; done | head -10
```

---

## 7. FAQ

**Is `/usr/lib/python3/dist-packages/` the folder where `pip` installs things?**
No. That folder belongs to **apt**. When you install with `pip` as root,
things go to `/usr/local/lib/python3.X/dist-packages/` instead. Keeping
them separate is exactly what lets apt and pip coexist without breaking
each other.

**Can I keep the `.py` extension on a command in `/usr/bin/`?**
You should not. Debian Policy §10.4 asks that commands in the system PATH
do not carry the extension of the language they are written in, and
lintian flags it. The trick shown above (different name at install time)
solves it without renaming your source file.

**So a "small" program can be installed directly in `/usr/bin/`?**
Yes — as long as it is genuinely a single-file application. If it is (or
becomes) a package or a library, use the `dist-packages` + launcher
pattern instead.

---

## Conclusions

- Debian installs Python software using **two valid patterns**: a package
  in `/usr/lib/python3/dist-packages/` plus a thin launcher in `/usr/bin/`
  (yt-dlp, arandr, catfish), or a **single-file script** installed directly
  in `/usr/bin/` (command-not-found, cppcheck-htmlreport, reportbug).
- The pattern is chosen by the **structure** of the program, not by
  preference: libraries and multi-module programs need `dist-packages`;
  single-file applications go straight to `/usr/bin/`.
- Debian's tooling (`dh_python3`) **detects scripts in `/usr/bin/` and
  generates the Python dependency automatically**, so nothing is left to
  chance.
- When a single-file program grows into multiple modules, that is the
  moment to migrate to the package + launcher pattern — not before.

So the next time you browse Synaptic and see a lonely Python script
installed directly in `/usr/bin/`, you will know it is not an anomaly: it
is Debian doing exactly the right thing for that program.
