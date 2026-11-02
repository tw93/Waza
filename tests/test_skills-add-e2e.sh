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
# The isolated HOME keeps the real npm cache, so a run does not refetch every
# package cold, and each attempt is bounded: npm's own fetch timeout is five
# minutes per request with retries, and a stalled registry once held this smoke
# for over half an hour. One retry absorbs transient registry hiccups. Locally a
# registry that never answers skips the smoke as an environment problem; in CI
# it still fails, so a real packaging regression cannot hide behind it.
npm_cache="${npm_config_cache:-$HOME/.npm}"
attempt_seconds="${WAZA_SKILLS_ADD_TIMEOUT:-240}"
timeout_bin=$(command -v timeout || command -v gtimeout || true)
install_skills() {
  if [ -n "$timeout_bin" ]; then
    HOME="$test_home" npm_config_cache="$npm_cache" "$timeout_bin" "$attempt_seconds" \
      npx --yes skills add "$tmpdir/repo" -a claude-code -g -y >"$tmpdir/install.out" 2>&1
  else
    HOME="$test_home" npm_config_cache="$npm_cache" \
      npx --yes skills add "$tmpdir/repo" -a claude-code -g -y >"$tmpdir/install.out" 2>&1
  fi
}
install_status=0
install_skills || install_status=$?
if [ "$install_status" -ne 0 ]; then
  sleep 5
  install_status=0
  install_skills || install_status=$?
fi
if [ "$install_status" -eq 124 ] && [ -z "${CI:-}" ]; then
  echo "skills add e2e smoke: skipped (npx did not finish within ${attempt_seconds}s twice; registry unreachable?)"
  exit 0
fi
if [ "$install_status" -ne 0 ]; then
  echo "skills add e2e smoke: install failed after retry (exit $install_status)"
  cat "$tmpdir/install.out" >&2
  exit 1
fi

# All 8 SKILL.md files landed under ~/.claude/skills/.
expected=(check health hunt learn read think ui write)
for skill in "${expected[@]}"; do
  target="$test_home/.claude/skills/$skill/SKILL.md"
  if [ ! -f "$target" ]; then
    echo "skills add e2e smoke: missing $target after install"
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
