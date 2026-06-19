#!/usr/bin/env bash
# End-to-end smoke for `npx skills add`. Catches packaging / frontmatter / path
# bugs that only surface on a real install, not on internal verify_skills.py
# runs. The marketplace v2.1.136+ regression in README.md is the exact class
# of bug this guards against.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

# Opt out when offline or for fast iteration loops:
#   WAZA_SMOKE_OFFLINE=1 make smoke-skills-add-e2e
if [ "${WAZA_SMOKE_OFFLINE:-0}" = "1" ]; then
  echo "skills add e2e smoke: skipped (WAZA_SMOKE_OFFLINE=1)"
  exit 0
fi

if ! command -v npx >/dev/null 2>&1; then
  echo "skills add e2e smoke: skipped (npx not available)"
  exit 0
fi

tmpdir=$(make_tmpdir)
copy_repo "$tmpdir/repo"
test_home="$tmpdir/home"
mkdir -p "$test_home"

# Install all 8 skills into an isolated HOME against the local repo copy.
HOME="$test_home" npx --yes skills add "$tmpdir/repo" -a claude-code -g -y \
  >"$tmpdir/install.out" 2>&1

# All 8 SKILL.md files landed under ~/.claude/skills/.
expected=(check design health hunt learn read think write)
for skill in "${expected[@]}"; do
  target="$test_home/.claude/skills/$skill/SKILL.md"
  if [ ! -f "$target" ]; then
    echo "skills add e2e smoke: missing $target after install"
    cat "$tmpdir/install.out" >&2
    exit 1
  fi
  checker="$test_home/.claude/skills/$skill/scripts/check-update.sh"
  if [ ! -f "$checker" ]; then
    echo "skills add e2e smoke: missing $checker after install"
    cat "$tmpdir/install.out" >&2
    exit 1
  fi
done

# Frontmatter survived the copy: re-run verify_skills.py against the installed
# skill root and confirm the same name/description/version contract holds.
python3 "$ROOT/scripts/verify_skills.py" --root "$test_home/.claude" --skills-only \
  >"$tmpdir/verify.out" 2>&1 || {
    echo "skills add e2e smoke: verify_skills failed against installed skills"
    cat "$tmpdir/verify.out" >&2
    exit 1
  }

echo "skills add e2e smoke: ok"
