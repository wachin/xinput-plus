# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.4] - 2025-09-09
### Added
- **Whitelist of visible devices** with UI to edit and a **“Show only whitelist”** toggle.
- **Profiles by ID** (in addition to by name). Per‑ID profiles take precedence when applying.
- New config schema with `by_name`, `by_id`, `_whitelist`, `_show_only_whitelist`.
- Button **Re‑apply all** to re‑enforce current profiles on connected devices.

### Changed
- Device list entries now display **`Name (id N)`** for clarity.
- Config is **auto‑migrated** from the old (flat) format to the new structure.
- README updated (EN): usage, whitelist, per‑ID profiles, CTM details.

## [6.3] - 2025-09-09
### Fixed
- Hardened all **multi‑line messages** to avoid Python `SyntaxError: unterminated string literal` when editors wrap lines.

## [6.0] - 2025-09-09
### Added
- **Icon restored** from `src/emucon.svg`.
- **Hide virtual/master/XTEST** pointers; only physical **slave pointers** are listed.
- **Disambiguation by ID**: the app resolves and stores the exact device ID; apply by ID.
- **Property check**: if `libinput Accel Speed` is missing, **fallback to CTM** safely.
- **Extended Mode (CTM)** with expanded range and clamping to prevent pointer freeze.
- **Auto‑apply** all saved configs on startup; **Refresh** button to rescan devices.

### Changed
- Better device matching: fallback to `pointer:<name>` when needed.
- UI sync improvements and safer command execution with debug logs.

## [5.0] - 2025-09-09
### Fixed
- Multi‑line **QMessageBox** string corrected using `\n` to prevent `SyntaxError` on some editors.

---

## Unreleased / Ideas
- Option to **skip applying** to non‑whitelisted devices.
- Per‑device **axis scaling/inversion**.
- Import/Export profiles.

