#!/bin/bash
# Install Waza statusline into Claude Code
set -euo pipefail

CLAUDE_DIR="$HOME/.claude"
DEST="$CLAUDE_DIR/statusline.sh"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
WAZA_REF="${WAZA_REF:-v3.42.0}"

case "$WAZA_REF" in
  main|v[0-9]*.[0-9]*.[0-9]*) ;;
  *)
    echo "Error: WAZA_REF must be main or a release tag like v3.24.0." >&2
    exit 1
    ;;
esac

RAW="https://raw.githubusercontent.com/tw93/Waza/${WAZA_REF}/scripts/statusline.sh"

if ! command -v curl &>/dev/null; then
  echo "Error: curl is required but not installed." >&2
  exit 1
fi

if ! command -v python3 &>/dev/null; then
  echo "Error: python3 is required but not installed." >&2
  exit 1
fi

if ! command -v jq &>/dev/null; then
  if command -v brew &>/dev/null; then
    echo "Installing jq via Homebrew..."
    brew install jq
  else
    echo "Error: jq is required but not installed." >&2
    echo "  macOS:  brew install jq" >&2
    echo "  Linux:  sudo apt-get install jq  or  sudo dnf install jq" >&2
    exit 1
  fi
fi

mkdir -p "$CLAUDE_DIR"

# A download that dies partway must not touch the installed script, so stage it
# into a sibling temp file and swap that in only once it is complete and
# executable. The trap covers what a return cannot: Ctrl-C or a kill mid-curl.
STAGED_DOWNLOAD=""
cleanup_staged_download() {
  if [ -n "$STAGED_DOWNLOAD" ]; then
    rm -f "$STAGED_DOWNLOAD"
  fi
  return 0
}
trap cleanup_staged_download EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

download_failed() {
  echo "Error: could not fetch $RAW (exit $1)." >&2
  echo "$DEST was left untouched." >&2
  exit "$1"
}

download_statusline_atomically() {
  STAGED_DOWNLOAD="$(mktemp "${DEST}.tmp.XXXXXX")" || return 1
  curl -fsSL --connect-timeout 10 --max-time 60 "$RAW" -o "$STAGED_DOWNLOAD" || return
  chmod +x "$STAGED_DOWNLOAD" || return
  mv -f "$STAGED_DOWNLOAD" "$DEST" || return
  STAGED_DOWNLOAD=""
}

# Refuse to modify an invalid settings file. Overwriting it would drop unrelated keys.
if [ -f "$SETTINGS_FILE" ]; then
  SETTINGS_FILE="$SETTINGS_FILE" python3 - <<'PYEOF'
import json
import os
import sys

path = os.environ["SETTINGS_FILE"]
try:
    with open(path) as f:
        json.load(f)
except Exception as exc:
    print(f"Error: {path} is not valid JSON. Refusing to modify it.", file=sys.stderr)
    print(f"Reason: {exc}", file=sys.stderr)
    sys.exit(1)
PYEOF
fi

# Check for existing statusLine (skip if already Waza)
EXISTING=$(SETTINGS_FILE="$SETTINGS_FILE" python3 -c "
import json, os
path = os.environ['SETTINGS_FILE']
if os.path.exists(path):
    d = json.load(open(path))
    sl = d.get('statusLine', {})
    cmd = sl.get('command', '')
    if cmd and cmd != 'bash ~/.claude/statusline.sh':
        print(cmd)
" 2>/dev/null)

if [ -n "$EXISTING" ]; then
  echo "Another statusline is already configured:"
  echo "  $EXISTING"
  ans=""
  prompted=0
  if [ -t 0 ]; then
    printf "Replace it with Waza statusline? [Y/n] "
    if read -r ans; then prompted=1; fi
  elif { printf "Replace it with Waza statusline? [Y/n] " >/dev/tty; } 2>/dev/null \
      && read -r ans </dev/tty 2>/dev/null; then
    prompted=1
  fi
  if [ "$prompted" -eq 0 ]; then
    echo "Non-interactive shell with no controlling TTY; keeping existing statusline."
    echo "Re-run interactively (or set WAZA_REPLACE_STATUSLINE=1) to replace it."
    if [ "${WAZA_REPLACE_STATUSLINE:-}" != "1" ]; then
      exit 0
    fi
    ans="y"
  fi
  if [ "$ans" = "n" ] || [ "$ans" = "N" ]; then
    echo "Skipped. Existing statusline kept."
    exit 0
  fi
fi

# Download statusline script (after any confirmation prompt).
download_statusline_atomically || download_failed $?

# Write statusLine into ~/.claude/settings.json
SETTINGS_FILE="$SETTINGS_FILE" python3 - <<'PYEOF'
import json
import os
import tempfile

path = os.environ["SETTINGS_FILE"]
d = {}
if os.path.exists(path):
    with open(path) as f:
        d = json.load(f)

d["statusLine"] = {"type": "command", "command": "bash ~/.claude/statusline.sh"}

directory = os.path.dirname(path)
fd, tmp_path = tempfile.mkstemp(prefix="settings.", suffix=".json.tmp", dir=directory)
with os.fdopen(fd, "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
os.replace(tmp_path, path)
PYEOF

echo "Waza statusline installed. Restart Claude Code to activate."
echo "Tip: if you see a 513 error after switching Claude accounts, remove the statusLine entry from ~/.claude/settings.json, restart Claude Code, then re-run this script."
