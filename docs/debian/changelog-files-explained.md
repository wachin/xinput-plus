# The two changelog files explained

This project has two changelog files. They serve different purposes and
both must be updated when a new version is released.

---

## `src/CHANGELOG.md` — upstream changelog

This is the **program's own history**, written for users and developers
who want to know what changed in each version of xinput-plus itself.

- Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- Installed by `debian/rules` as:
  `/usr/share/doc/xinput-plus/changelog`
- Update it when: you add features, fix bugs, remove files, or change
  the program's behaviour.

Example entry:

```markdown
## [6.6.5] - 2026-05-06
### Added
- Translations for German, Russian, Japanese, and nine other languages.

### Removed
- `src/emucon.svg` (old joystick icon, no longer used).
```

---

## `debian/changelog` — Debian packaging history

This is the **packaging history**, written for Debian tools and reviewers.
It records every change made to the Debian package, not just the program.

- Format: strict Debian format (managed with `dch`, never edited by hand
  for new entries)
- Read by: `dpkg`, `apt`, `lintian`, Debian sponsors, and the NEW queue
  reviewers
- Update it when: you change anything in `debian/`, bump Standards-Version,
  add/remove files, or release a new upstream version.

Example entry:

```
xinput-plus (6.6.5-1) unstable; urgency=medium

  * Remove unused src/emucon.svg and src/emucon-openclipart.org.txt;
    remove their stanza from debian/copyright.
  * i18n: add translations for 12 languages.

 -- Washington Indacochea Delgado <linuxfrontier@proton.me>  Wed, 06 May 2026 10:00:00 -0500
```

To add a new entry use `dch`, never edit the file directly:

```bash
# New upstream version:
dch -v 6.6.6-1 "New upstream release 6.6.6."

# Packaging-only change (same upstream, new Debian revision):
dch -v 6.6.5-2 "Fix lintian warning."

# Mark the top entry as ready to upload (changes UNRELEASED to unstable):
dch -r ""
```

---

## Rule of thumb

| Question | File to update |
|---|---|
| Did the program change? | `src/CHANGELOG.md` |
| Did the Debian packaging change? | `debian/changelog` |
| New upstream release? | **Both** |
