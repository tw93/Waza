#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${WAZA_PYTHON:-python3}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || [ -x "$PYTHON_BIN" ] || exit 127
exec "$PYTHON_BIN" "$SCRIPT_DIR/check_agent_context.py" "$@"
