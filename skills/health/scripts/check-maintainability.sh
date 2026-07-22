#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Keep the override for existing callers; the Python default avoids resolving
# Windows' WSL bash from inside a native Python subprocess.
export DOC_REF_CHECKER="${DOC_REF_CHECKER:-$SCRIPT_DIR/check_doc_refs.py}"
PYTHON_BIN="${WAZA_PYTHON:-python3}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || [ -x "$PYTHON_BIN" ] || exit 127
exec "$PYTHON_BIN" "$SCRIPT_DIR/check_maintainability.py" "$@"
