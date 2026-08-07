#!/usr/bin/env sh
set -eu
PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || { echo "HHC-KUR-001: python3 bulunamadı. Python 3.9+ kurup tekrar deneyin." >&2; exit 1; }
"$PYTHON" "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/scripts/install_global.py" --install
