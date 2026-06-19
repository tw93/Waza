#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

tmpdir=$(make_tmpdir)
copy_repo "$tmpdir/repo"

version=$(cat "$tmpdir/repo/VERSION")
test "$(jq -r '.name' "$tmpdir/repo/package.json")" = "@tw93/waza"
test "$(jq -r '.version' "$tmpdir/repo/package.json")" = "$version"
test "$(jq -r '.pi.skills[0]' "$tmpdir/repo/package.json")" = "./skills"
test "$(jq -r '.keywords[]' "$tmpdir/repo/package.json" | grep -c '^pi-package$')" -eq 1
test "$(jq -r '.keywords[]' "$tmpdir/repo/package.json" | grep -c '^antigravity$')" -eq 1
test "$(jq -r '.keywords[]' "$tmpdir/repo/package.json" | grep -c '^opencode$')" -eq 1
test "$(jq -r '.publishConfig.access' "$tmpdir/repo/package.json")" = "public"

if ! command -v npm >/dev/null 2>&1; then
  echo "package-json smoke: skipped npm pack --dry-run (npm not installed)"
  exit 0
fi

(cd "$tmpdir/repo" && npm pack --dry-run --json > "$tmpdir/npm-pack.json")

python3 - "$tmpdir/npm-pack.json" <<'PY'
import json
import sys

data = json.load(open(sys.argv[1]))
files = {item["path"] for item in data[0]["files"]}

required = {
    "package.json",
    "README.md",
    "LICENSE",
    "rules/anti-patterns.md",
    "scripts/check-update.sh",
    "scripts/statusline.sh",
    "skills/check/SKILL.md",
    "skills/check/scripts/check-update.sh",
}
missing = sorted(required - files)
if missing:
    raise SystemExit(f"missing expected npm package files: {missing}")

forbidden = {
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    "plugins/waza/.codex-plugin/plugin.json",
    ".github/workflows/test.yml",
    "dist/waza.zip",
    "tests/test_package.sh",
    "packaging.allowlist",
}
leaked = sorted(forbidden & files)
if leaked:
    raise SystemExit(f"forbidden npm package files leaked: {leaked}")

pycache = sorted(path for path in files if "__pycache__" in path or path.endswith(".pyc"))
if pycache:
    raise SystemExit(f"python cache files leaked into npm package: {pycache[:5]}")
PY

echo "package-json smoke: ok"
