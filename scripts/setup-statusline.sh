#!/bin/bash
# Install Waza statusline into Claude Code
set -e

CLAUDE_DIR="$HOME/.claude"
DEST="$CLAUDE_DIR/statusline.sh"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
RAW="https://raw.githubusercontent.com/tw93/Waza/main/scripts/statusline.sh"

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
  printf "Replace it with Waza statusline? [Y/n] "
  read -r ans
  if [ "$ans" = "n" ] || [ "$ans" = "N" ]; then
    echo "Skipped. Existing statusline kept."
    exit 0
  fi
fi

# Download statusline script (after any confirmation prompt)
curl -fsSL "$RAW" -o "$DEST"
chmod +x "$DEST"

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
