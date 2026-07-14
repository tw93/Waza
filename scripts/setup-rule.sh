#!/bin/bash
# Install a Waza rule into Claude Code (~/.claude/rules/<rule>.md) or Codex
# (~/.codex/AGENTS.md, wrapped in markers so re-runs replace the block).
#
# Usage:
#   setup-rule.sh <rule-name> [claude-code|codex|antigravity-cli]
#
# rule-name corresponds to a file at rules/<rule-name>.md in this repo. Marker
# label is derived from the rule slug (e.g. anti-patterns -> Anti-Patterns,
# english -> English Coaching), with explicit overrides for the established
# product names so existing AGENTS.md installs remain idempotent.
set -euo pipefail

RULE="${1:-}"
TARGET="${2:-claude-code}"
WAZA_REF="${WAZA_REF:-v3.31.2}"

if [ -z "$RULE" ]; then
  echo "Usage: setup-rule.sh <rule-name> [claude-code|codex|antigravity-cli]" >&2
  echo "Examples: setup-rule.sh anti-patterns" >&2
  echo "          setup-rule.sh english codex" >&2
  exit 1
fi

case "$RULE" in
  *[!a-z0-9-]* | -* | *- | "")
    echo "Error: rule-name must match [a-z0-9][a-z0-9-]*[a-z0-9]." >&2
    exit 1
    ;;
esac

case "$WAZA_REF" in
  main|v[0-9]*.[0-9]*.[0-9]*) ;;
  *)
    echo "Error: WAZA_REF must be main or a release tag like v3.24.0." >&2
    exit 1
    ;;
esac

RAW="https://raw.githubusercontent.com/tw93/Waza/${WAZA_REF}/rules/${RULE}.md"

# Marker label = how the block appears in ~/.codex/AGENTS.md. Established names
# kept verbatim so existing installs keep matching their original start/end
# markers; new rules fall back to a Title Case rendering of the slug. The
# waza-routing override avoids a double "Waza Waza Routing" in the marker.
case "$RULE" in
  english) MARKER_LABEL="English Coaching" ;;
  anti-patterns) MARKER_LABEL="Anti-Patterns" ;;
  waza-routing) MARKER_LABEL="Routing" ;;
  *)
    MARKER_LABEL="$(printf '%s' "$RULE" | tr '-' ' ' | awk '{ for (i=1;i<=NF;i++) $i = toupper(substr($i,1,1)) tolower(substr($i,2)); print }')"
    ;;
esac

if ! command -v curl >/dev/null 2>&1; then
  echo "Error: curl is required but not installed." >&2
  exit 1
fi

case "$TARGET" in
  claude-code|claude)
    mkdir -p "$HOME/.claude/rules"
    curl -fsSL --connect-timeout 10 --max-time 60 "$RAW" -o "$HOME/.claude/rules/${RULE}.md"
    echo "Waza ${MARKER_LABEL} installed for Claude Code."
    ;;

  codex)
    if ! command -v python3 >/dev/null 2>&1; then
      echo "Error: python3 is required but not installed." >&2
      exit 1
    fi

    mkdir -p "$HOME/.codex"
    tmp="$(mktemp)"
    trap 'rm -f "$tmp"' EXIT
    curl -fsSL --connect-timeout 10 --max-time 60 "$RAW" -o "$tmp"

    # Inline Python: this script is installed via `curl | bash` (no companion
    # .py file on the user's machine), so the AGENTS.md edit logic stays self-
    # contained here. py_compile cannot syntax-check it; bash -n catches
    # quoting bugs in the shell layer.
    MARKER_LABEL="$MARKER_LABEL" python3 - "$tmp" "$HOME/.codex/AGENTS.md" <<'PYEOF'
import os
import sys
from pathlib import Path

label = os.environ["MARKER_LABEL"]
source = Path(sys.argv[1]).read_text().strip()
target = Path(sys.argv[2])
start = f"<!-- Waza {label}: start -->"
end = f"<!-- Waza {label}: end -->"
block = f"{start}\n{source}\n{end}\n"
text = target.read_text() if target.exists() else ""

if start in text and end in text:
    before = text.split(start, 1)[0].rstrip()
    after = text.split(end, 1)[1].lstrip()
    text = f"{before}\n\n{block}\n{after}".rstrip() + "\n"
else:
    text = text.rstrip() + "\n\n" + block

target.write_text(text)
PYEOF
    echo "Waza ${MARKER_LABEL} installed for Codex."
    ;;

  antigravity-cli|antigravity|agy)
    mkdir -p "$HOME/.gemini/antigravity-cli/rules"
    curl -fsSL --connect-timeout 10 --max-time 60 "$RAW" -o "$HOME/.gemini/antigravity-cli/rules/${RULE}.md"
    echo "Waza ${MARKER_LABEL} installed for Antigravity."
    ;;

  *)
    echo "Usage: setup-rule.sh <rule-name> [claude-code|codex|antigravity-cli]" >&2
    exit 1
    ;;
esac
