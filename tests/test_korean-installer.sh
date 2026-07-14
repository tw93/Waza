#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

tmpdir=$(make_tmpdir)
home_dir="$tmpdir/home"
bin_dir="$tmpdir/bin"
mkdir -p "$home_dir/.codex"
prepare_codex_installer_bin "$bin_dir"
write_stub_curl "$bin_dir" "## Korean\n\ntest rule\n"

PATH="$bin_dir" HOME="$home_dir" /bin/bash "$ROOT/scripts/setup-rule.sh" korean claude-code >"$tmpdir/claude.out"
grep -q 'test rule' "$home_dir/.claude/rules/korean.md"

# Idempotent for Codex target: two runs leave exactly one marker.
PATH="$bin_dir" HOME="$home_dir" /bin/bash "$ROOT/scripts/setup-rule.sh" korean codex >"$tmpdir/codex1.out"
PATH="$bin_dir" HOME="$home_dir" /bin/bash "$ROOT/scripts/setup-rule.sh" korean codex >"$tmpdir/codex2.out"
test "$(grep -c '<!-- Waza Korean: start -->' "$home_dir/.codex/AGENTS.md")" -eq 1
grep -q 'test rule' "$home_dir/.codex/AGENTS.md"

echo "Korean installer smoke: ok"
