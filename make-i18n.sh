#!/usr/bin/env bash
# make-i18n.sh — helper for PyQt6 translations
# Usage:
#   ./make-i18n.sh [path-to-py]
# Defaults:
#   - Python UI file: ./xinput-plus.py (or ./src/xinput-plus.py if present)
#   - TS/QM output directory: ./i18n

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PYFILE_DEFAULT_A="$ROOT/src/xinput-plus.py"
PYFILE_DEFAULT_B="$ROOT/xinput-plus.py"

if [[ $# -ge 1 ]]; then
  PYFILE="$1"
else
  if [[ -f "$PYFILE_DEFAULT_A" ]]; then
    PYFILE="$PYFILE_DEFAULT_A"
  elif [[ -f "$PYFILE_DEFAULT_B" ]]; then
    PYFILE="$PYFILE_DEFAULT_B"
  else
    echo "ERROR: Could not find xinput-plus.py (looked in ./src and .)."
    echo "Pass the path explicitly: ./make-i18n.sh path/to/your.py"
    exit 1
  fi
fi

I18NDIR="$ROOT/i18n"
mkdir -p "$I18NDIR"

# Try to locate appropriate tools
find_cmd() {
  for c in "$@"; do
    if command -v "$c" >/dev/null 2>&1; then
      echo "$c"
      return 0
    fi
  done
  return 1
}

PYLUPDATE="$(find_cmd pylupdate6 pylupdate lupdate || true)"
LRELEASE="$(find_cmd lrelease-qt6 lrelease || true)"

if [[ -z "${PYLUPDATE:-}" ]]; then
  echo "ERROR: pylupdate6 (or pylupdate/lupdate) not found. Install qt6-tools-dev-tools."
  exit 2
fi
if [[ -z "${LRELEASE:-}" ]]; then
  echo "ERROR: lrelease-qt6 (or lrelease) not found. Install qt6-tools-dev-tools."
  exit 3
fi

echo "Using: $PYLUPDATE"
echo "Using: $LRELEASE"
echo "Source: $PYFILE"
echo "Output dir: $I18NDIR"

# 1) Update/Generate TS files
"$PYLUPDATE" "$PYFILE" -ts "$I18NDIR/xinput-plus_es.ts" "$I18NDIR/xinput-plus_en.ts"

# 2) Compile to QM
"$LRELEASE" "$I18NDIR/xinput-plus_es.ts" -qm "$I18NDIR/xinput-plus_es.qm"
"$LRELEASE" "$I18NDIR/xinput-plus_en.ts" -qm "$I18NDIR/xinput-plus_en.qm"

echo "Done. Generated/updated:"
echo "  - $I18NDIR/xinput-plus_es.ts"
echo "  - $I18NDIR/xinput-plus_en.ts"
echo "  - $I18NDIR/xinput-plus_es.qm"
echo "  - $I18NDIR/xinput-plus_en.qm"
