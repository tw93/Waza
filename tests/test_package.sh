#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

tmpdir=$(make_tmpdir)
"$ROOT/scripts/package-skill.sh" "$tmpdir/waza.zip" >/dev/null
zipinfo -1 "$tmpdir/waza.zip" >"$tmpdir/manifest"

# Root SKILL.md is present; nested SKILL.md files are inlined, never re-shipped.
grep -qx 'SKILL.md' "$tmpdir/manifest"
test "$(zipinfo -1 "$tmpdir/waza.zip" | grep -ciE '(^|/)skill\.md$')" -eq 1

# Required helper scripts are bundled.
for required in \
  scripts/check-update.sh \
  skills/check/scripts/check-update.sh \
  skills/read/scripts/fetch.sh \
  skills/health/scripts/check-agent-context.sh \
  skills/health/scripts/check-doc-refs.sh \
  skills/health/scripts/check-maintainability.sh \
  skills/health/scripts/check-verifier-output.sh \
  skills/health/agents/inspector-maintainability.md; do
  grep -qx "$required" "$tmpdir/manifest"
done

# Allowlist contract: build-only files and dev metadata never ship.
for forbidden in \
  .gitignore \
  Makefile \
  VERSION \
  package.json \
  packaging.allowlist \
  scripts/verify_skills.py \
  scripts/verify-skills.sh \
  scripts/build_metadata.py \
  scripts/package-skill.sh \
  scripts/packaging_filter.py; do
  if grep -qx "$forbidden" "$tmpdir/manifest"; then
    echo "forbidden file leaked into package: $forbidden"; exit 1
  fi
done
if grep -qE '^(docs|tests|\.github|\.claude-plugin|\.codex-plugin|\.agents|plugins)/' "$tmpdir/manifest"; then
  echo "forbidden directory leaked into package"; exit 1
fi

# Root SKILL.md inlines every skill body and rewrites cross-refs. Read the
# bundled file once into memory; bash string matching avoids the SIGPIPE that
# `unzip -p | grep -q` would raise under `set -o pipefail`.
root_skill=$(unzip -p "$tmpdir/waza.zip" SKILL.md)
[[ "$root_skill" == *"SKILL: check"* ]] || { echo "expected 'SKILL: check' section in root SKILL.md"; exit 1; }
if [[ "$root_skill" == *"skills/check/SKILL.md"* ]]; then
  echo "package root should not reference nested SKILL.md"; exit 1
fi

echo "package smoke: ok"
