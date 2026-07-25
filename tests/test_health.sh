#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

tmpdir=$(make_tmpdir)
project_key=$(printf '%s' "$ROOT" | sed 's|[/_]|-|g; s|^-||')
convo_dir="$tmpdir/.claude/projects/-${project_key}"
mkdir -p "$convo_dir"

# Two prior sessions: one ordinary build request, one explicit correction.
# The collector samples the older session (2-old) and ignores the active one
# (1-active) so we can deterministically assert what surfaces.
printf '%s\n' '{"type":"user","message":{"content":"Please build a dashboard for sales data."}}' > "$convo_dir/2-old.jsonl"
printf '%s\n' '{"type":"user","message":{"content":"Please do not use em dashes next time."}}' >> "$convo_dir/2-old.jsonl"
printf '%s\n' '{"type":"user","message":{"content":"active session placeholder"}}' > "$convo_dir/1-active.jsonl"

HOME="$tmpdir" bash "$ROOT/skills/health/scripts/collect-data.sh" auto > "$tmpdir/health.out"
grep -q '^=== CONVERSATION SIGNALS ===$' "$tmpdir/health.out"
grep -q '^=== AGENT CONFIG SUMMARY ===$' "$tmpdir/health.out"
grep -q '^=== AI MAINTAINABILITY SUMMARY ===$' "$tmpdir/health.out"
grep -q '^USER CORRECTION: Please do not use em dashes next time\.$' "$tmpdir/health.out"
if grep -q '^USER CORRECTION: Please build a dashboard for sales data\.$' "$tmpdir/health.out"; then
  echo "false positive correction detected"; exit 1
fi

# Repository-configured fsmonitor hooks are executable project code. Health
# collection must disable them rather than relying on a clean Git status.
fsmonitor_repo="$tmpdir/fsmonitor"
mkdir -p "$fsmonitor_repo"
(
  cd "$fsmonitor_repo"
  git init -q
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'printf executed > fsmonitor-marker' \
    "printf '2.0.0\\n'" \
    > fsmonitor.sh
  chmod +x fsmonitor.sh
  git config core.fsmonitor "$fsmonitor_repo/fsmonitor.sh"
  HOME="$tmpdir" bash "$ROOT/skills/health/scripts/collect-data.sh" auto > "$tmpdir/fsmonitor.out"
  test ! -e fsmonitor-marker
)

echo "health smoke: ok"
