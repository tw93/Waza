#!/usr/bin/env bash
# Collect Claude Code configuration data for health audit.
# Outputs labeled sections for each data source.
# Run from any directory; uses pwd as the project root.
set -euo pipefail

P=$(pwd)
SETTINGS="$P/.claude/settings.local.json"
TIER="${1:-auto}"
PROJECT_KEY=$(printf '%s' "$P" | sed 's|[/_]|-|g; s|^-||')
CONVO_DIR="$HOME/.claude/projects/-${PROJECT_KEY}"

count_project_files() {
  local count
  count=$(git -C "$P" ls-files 2>/dev/null | wc -l | tr -d ' ' || true)
  if [ -z "$count" ] || [ "$count" = "0" ]; then
    count=$(find "$P" -type f \
      -not -path "*/.git/*" \
      -not -path "*/node_modules/*" \
      -not -path "*/dist/*" \
      -not -path "*/build/*" \
      2>/dev/null | wc -l | tr -d ' ')
  fi
  printf '%s\n' "${count:-0}"
}

count_contributors() {
  local count
  count=$(git -C "$P" log -n 500 --format='%ae' 2>/dev/null | sort -u | wc -l | tr -d ' ' || true)
  printf '%s\n' "${count:-0}"
}

count_ci_workflows() {
  local count=0
  if [ -d "$P/.github/workflows" ]; then
    count=$(find "$P/.github/workflows" -maxdepth 1 -type f \( -name "*.yml" -o -name "*.yaml" \) 2>/dev/null | wc -l | tr -d ' ')
  fi
  printf '%s\n' "${count:-0}"
}

count_local_skills() {
  local count=0
  if [ -d "$P/.claude/skills" ]; then
    count=$(find -L "$P/.claude/skills" -maxdepth 4 -name "SKILL.md" 2>/dev/null | while IFS= read -r f; do
      grep -q '^name: health$' "$f" 2>/dev/null && continue
      echo "$f"
    done | wc -l | tr -d ' ')
  fi
  printf '%s\n' "${count:-0}"
}

resolve_symlink() {
  readlink -f "$1" 2>/dev/null && return
  # macOS fallback: resolve symlink chain manually
  local target="$1"
  while [ -L "$target" ]; do
    local dir
    dir=$(cd "$(dirname "$target")" && pwd -P)
    target=$(readlink "$target")
    case "$target" in /*) ;; *) target="$dir/$target" ;; esac
  done
  printf '%s\n' "$target"
}

count_file_lines() {
  local file="$1"
  if [ -f "$file" ]; then
    wc -l < "$file" | tr -d ' '
  else
    echo 0
  fi
}

count_file_words() {
  local file="$1"
  if [ -f "$file" ]; then
    wc -w < "$file" | tr -d ' '
  else
    echo 0
  fi
}

list_rule_files() {
  if [ -d "$P/.claude/rules" ]; then
    find "$P/.claude/rules" -type f -name "*.md" 2>/dev/null | sort || true
  fi
}

print_rule_files() {
  local found=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    found=1
    echo "--- $f ---"
    cat "$f"
  done < <(list_rule_files)
  [ "$found" -eq 1 ] || echo "(none)"
}

rules_word_count() {
  local words=0
  if [ -d "$P/.claude/rules" ]; then
    words=$(while IFS= read -r f; do
      [ -n "$f" ] || continue
      cat "$f"
    done < <(list_rule_files) | wc -w | tr -d ' ')
  fi
  printf '%s\n' "${words:-0}"
}

collect_skill_descriptions_raw() {
  if [ -d "$P/.claude/skills" ]; then
    grep -r "^description:" "$P/.claude/skills" 2>/dev/null || true
  fi
  if [ -d "$HOME/.claude/skills" ]; then
    grep -r "^description:" "$HOME/.claude/skills" 2>/dev/null || true
  fi
}

print_skill_descriptions() {
  local out
  out=$(collect_skill_descriptions_raw | sort -u)
  if [ -n "$out" ]; then
    printf '%s\n' "$out"
  else
    echo "(none)"
  fi
}

skill_description_word_count() {
  local words
  words=$(collect_skill_descriptions_raw | wc -w | tr -d ' ')
  printf '%s\n' "${words:-0}"
}

list_skill_files() {
  local dir="$1"
  [ -d "$dir" ] || return 0
  find -L "$dir" -maxdepth 4 -name "SKILL.md" 2>/dev/null | sort || true
}

is_health_skill() {
  grep -q '^name: health$' "$1" 2>/dev/null
}

list_conversation_files() {
  [ -d "$CONVO_DIR" ] || return 0
  ls -1t "$CONVO_DIR"/*.jsonl 2>/dev/null || true
}

print_conversation_file_listing() {
  local out
  out=$(ls -lhS "$CONVO_DIR"/*.jsonl 2>/dev/null || true)
  if [ -n "$out" ]; then
    printf '%s\n' "$out" | head -10
  else
    echo "(no conversation files)"
  fi
}

previous_conversation_files() {
  list_conversation_files | tail -n +2 | head -2
}

sample_jsonl_prefix() {
  local file="$1"
  local limit="${2:-512000}"
  LC_ALL=C awk -v limit="$limit" '
    {
      line = $0 ORS
      next_bytes = bytes + length(line)
      if (next_bytes > limit) {
        exit
      }
      printf "%s", line
      bytes = next_bytes
    }
  ' "$file"
}

extract_messages_from_file() {
  local file="$1"
  sample_jsonl_prefix "$file" | jq -r '
    def flatten:
      if (.isMeta // false) or (.toolUseResult? != null) then
        empty
      else
        (.message.content // .content // .text // "")
        | if type == "array" then
            [ .[] | if type == "object" and .type == "text" then .text elif type == "string" then . else empty end ] | join(" ")
          elif type == "string" then .
          else empty
          end
        | gsub("[\\r\\n]+"; " ")
        | gsub("  +"; " ")
        | sub("^ "; "")
        | sub(" $"; "")
      end;
    (.type // .role // "") as $kind
    | (flatten) as $text
    | if ($text | length) == 0 then
        empty
      elif $kind == "user" then
        "USER: " + $text
      elif $kind == "assistant" then
        "ASSISTANT: " + $text
      elif $kind == "system" then
        "SYSTEM: " + $text
      else
        empty
      end
  ' 2>/dev/null
}

extract_signals_from_file() {
  local file="$1"
  sample_jsonl_prefix "$file" | jq -r '
    def flatten:
      if (.isMeta // false) or (.toolUseResult? != null) then
        empty
      else
        (.message.content // .content // .text // "")
        | if type == "array" then
            [ .[] | if type == "object" and .type == "text" then .text elif type == "string" then . else empty end ] | join(" ")
          elif type == "string" then .
          else empty
          end
        | gsub("[\\r\\n]+"; " ")
        | gsub("  +"; " ")
        | sub("^ "; "")
        | sub(" $"; "")
      end;
    def is_correction:
      test("(?i)(\\bdon'\''t\\b|\\bdo not\\b|\\bplease don'\''t\\b|\\binstead\\b|\\bnext time\\b|\\bremember\\b|\\buse\\b.*\\binstead\\b|\\bnot\\b.*\\bbut\\b)")
      or test("(不要再|请不要|不要|别再|下次|记得|改成|改为|而不是|别用|去掉|统一成)");
    (.type // .role // "") as $kind
    | (flatten) as $text
    | if ($text | length) == 0 then
        empty
      elif ($text | test("(?i)(conversation was compressed|context limit|context window|truncat|/compact|context management|token limit|window is full|compaction)")) then
        "CONTEXT SIGNAL: " + $text
      # Keep this conservative: false positives pollute enforcement-gap analysis.
      elif $kind == "user" and ($text | is_correction) then
        "USER CORRECTION: " + $text
      else
        empty
      end
  ' 2>/dev/null
}

print_conversation_signals() {
  local files file chunk found=0
  files=$(previous_conversation_files)
  if [ -z "$files" ]; then
    echo "(no conversation files)"
    return
  fi
  if ! command -v jq >/dev/null 2>&1; then
    echo "(unavailable: jq not installed or parse error)"
    return
  fi
  while IFS= read -r file; do
    [ -f "$file" ] || continue
    if ! chunk=$(extract_signals_from_file "$file"); then
      echo "(unavailable: jq not installed or parse error)"
      return
    fi
    chunk=$(printf '%s\n' "$chunk" | head -40 || true)
    if [ -n "$chunk" ]; then
      found=1
      echo "--- file: $file ---"
      printf '%s\n' "$chunk"
    fi
  done <<EOF
$files
EOF
  [ "$found" -eq 1 ] || echo "(no conversation signals detected)"
}

print_conversation_extract() {
  local files file chunk found=0
  files=$(previous_conversation_files)
  if [ -z "$files" ]; then
    echo "(no conversation files)"
    return
  fi
  if ! command -v jq >/dev/null 2>&1; then
    echo "(unavailable: jq not installed or parse error)"
    return
  fi
  while IFS= read -r file; do
    [ -f "$file" ] || continue
    found=1
    echo "--- file: $file ---"
    if ! chunk=$(extract_messages_from_file "$file"); then
      echo "(unavailable: jq not installed or parse error)"
      return
    fi
    chunk=$(printf '%s\n' "$chunk" | grep -v '^ASSISTANT: $' | head -150 || true)
    if [ -n "$chunk" ]; then
      printf '%s\n' "$chunk"
    else
      echo "(no extractable conversation messages)"
    fi
  done <<EOF
$files
EOF
  [ "$found" -eq 1 ] || echo "(no conversation files)"
}

print_mcp_access_denials() {
  local files file chunk found=0
  files=$(list_conversation_files | head -5)
  if [ -z "$files" ]; then
    echo "(no conversation files)"
    return
  fi
  while IFS= read -r file; do
    [ -f "$file" ] || continue
    chunk=$(head -c 1048576 "$file" | grep -Em 2 'Access denied - path outside allowed directories|tool-results/.+ not in ' 2>/dev/null || true)
    if [ -n "$chunk" ]; then
      found=1
      printf '%s\n' "$chunk"
    fi
  done <<EOF
$files
EOF
  [ "$found" -eq 1 ] || echo "(none found)"
}

PROJECT_FILES=$(count_project_files)
CONTRIBUTORS=$(count_contributors)
CI_WORKFLOWS=$(count_ci_workflows)

echo "[1/10] Tier metrics..."
echo "=== TIER METRICS ==="
echo "project_files: $PROJECT_FILES"
echo "contributors: $CONTRIBUTORS"
echo "ci_workflows:  $CI_WORKFLOWS"
echo "skills:        $(count_local_skills)"
echo "claude_md_lines: $(count_file_lines "$P/CLAUDE.md")"

# Auto-detect tier if not passed as argument.
# Matches SKILL.md definition: Simple = <500 files AND <=1 contributor AND no CI.
if [ "$TIER" = "auto" ]; then
  if [ "${PROJECT_FILES:-0}" -lt 500 ] && [ "${CONTRIBUTORS:-0}" -le 1 ] && [ "${CI_WORKFLOWS:-0}" -eq 0 ]; then
    TIER="simple"
  elif [ "${PROJECT_FILES:-0}" -lt 5000 ]; then
    TIER="standard"
  else
    TIER="complex"
  fi
fi
echo "detected_tier: $TIER"

echo "[2/10] CLAUDE.md (global + local)..."
echo "=== CLAUDE.md (global) ===" ; cat ~/.claude/CLAUDE.md 2>/dev/null || echo "(none)"
echo "=== CLAUDE.md (local) ===" ; cat "$P/CLAUDE.md" 2>/dev/null || echo "(none)"

echo "[3/10] Settings, hooks, MCP..."
echo "=== settings.local.json ===" ; cat "$SETTINGS" 2>/dev/null || echo "(none)"

echo "[4/10] Rules + skill descriptions..."
echo "=== rules/ ===" ; print_rule_files
echo "=== skill descriptions ===" ; print_skill_descriptions

echo "[5/10] Context budget estimate..."
echo "=== STARTUP CONTEXT ESTIMATE ==="
echo "global_claude_words: $(count_file_words "$HOME/.claude/CLAUDE.md")"
echo "local_claude_words: $(count_file_words "$P/CLAUDE.md")"
echo "rules_words: $(rules_word_count)"
echo "skill_desc_words: $(skill_description_word_count)"
if command -v python3 >/dev/null 2>&1; then
python3 - "$SETTINGS" <<'PYEOF' 2>/dev/null || echo "(unavailable)"
import json
import sys

path = sys.argv[1]
try:
    with open(path) as fh:
        d = json.load(fh)
except Exception:
    msg = '(unavailable: settings.local.json missing or malformed)'
    print('=== hooks ===')
    print(msg)
    print('=== MCP ===')
    print(msg)
    print('=== MCP FILESYSTEM ===')
    print(msg)
    print('=== allowedTools count ===')
    print(msg)
    sys.exit(0)

print('=== hooks ===')
print(json.dumps(d.get('hooks', {}), indent=2))

print('=== MCP ===')
servers = d.get('mcpServers', d.get('enabledMcpjsonServers', {}))
names = list(servers.keys()) if isinstance(servers, dict) else list(servers)
count = len(names)
print(f'servers({count}):', ', '.join(names))
est = count * 25 * 200
print(f'est_tokens: ~{est} ({round(est/2000)}% of 200K)')

print('=== MCP FILESYSTEM ===')
if isinstance(servers, list):
    print('filesystem_present: (array format -- check .mcp.json)')
    print('allowedDirectories: (not detectable)')
else:
    filesystem = servers.get('filesystem') if isinstance(servers, dict) else None
    allowed = []
    if isinstance(filesystem, dict):
        allowed = filesystem.get('allowedDirectories') or (
            filesystem.get('config', {}).get('allowedDirectories')
            if isinstance(filesystem.get('config'), dict)
            else []
        )
        if not allowed and isinstance(filesystem.get('args'), list):
            args = filesystem['args']
            for index, value in enumerate(args):
                if value in ('--allowed-directories', '--allowedDirectories') and index + 1 < len(args):
                    allowed = [args[index + 1]]
                    break
            if not allowed:
                allowed = [value for value in args if value.startswith('/') or (value.startswith('~') and len(value) > 1)]
    print('filesystem_present:', 'yes' if filesystem else 'no')
    print('allowedDirectories:', allowed or '(missing or not detected)')

print('=== allowedTools count ===')
print(len(d.get('permissions', {}).get('allow', [])))
PYEOF
else
  echo "=== hooks ==="
  echo "(unavailable)"
  echo "=== MCP ==="
  echo "(unavailable)"
  echo "=== MCP FILESYSTEM ==="
  echo "(unavailable)"
  echo "=== allowedTools count ==="
  echo "(unavailable)"
fi

echo "[6/10] Nested CLAUDE.md + gitignore..."
echo "=== NESTED CLAUDE.md ==="
_NESTED_CLAUDE=$(find "$P" -maxdepth 4 -name "CLAUDE.md" -not -path "$P/CLAUDE.md" -not -path "*/.git/*" -not -path "*/node_modules/*" 2>/dev/null || true)
if [ -n "$_NESTED_CLAUDE" ]; then
  printf '%s\n' "$_NESTED_CLAUDE"
else
  echo "(none)"
fi
echo "=== GITIGNORE ==="
_GITIGNORE_HIT=$(git -C "$P" check-ignore -v .claude/settings.local.json 2>/dev/null || true)
if [ -n "$_GITIGNORE_HIT" ]; then
  _GITIGNORE_SOURCE=${_GITIGNORE_HIT%%:*}
  case "$_GITIGNORE_SOURCE" in
    .gitignore|.claude/.gitignore)
      echo "settings.local.json: gitignored"
      ;;
    *)
      echo "settings.local.json: ignored only by non-project rule ($_GITIGNORE_SOURCE) -- add a repo-local ignore rule"
      ;;
  esac
else
  echo "settings.local.json: NOT gitignored -- risk of committing tokens/credentials"
fi

echo "[7/10] HANDOFF.md + MEMORY.md..."
echo "=== HANDOFF.md ===" ; cat "$P/HANDOFF.md" 2>/dev/null || echo "(none)"
echo "=== MEMORY.md ==="
if [ -f "$HOME/.claude/projects/-${PROJECT_KEY}/memory/MEMORY.md" ]; then
  head -50 "$HOME/.claude/projects/-${PROJECT_KEY}/memory/MEMORY.md"
else
  echo "(none)"
fi

echo "[8/10] Conversation signals + extract..."
echo "=== CONVERSATION FILES ==="
print_conversation_file_listing

echo "=== CONVERSATION SIGNALS ==="
print_conversation_signals

if [ "$TIER" != "simple" ]; then
echo "=== CONVERSATION EXTRACT ==="
print_conversation_extract
echo "=== MCP ACCESS DENIALS ==="
print_mcp_access_denials
else
  echo "=== CONVERSATION EXTRACT ===" ; echo "(skipped: simple tier)"
  echo "=== MCP ACCESS DENIALS ===" ; echo "(skipped: simple tier)"
fi

echo "[9/10] Skill inventory + frontmatter + provenance..."
echo "=== SKILL INVENTORY ==="
_SKILL_FOUND=0
for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    is_health_skill "$f" && continue
    _SKILL_FOUND=1
    WORDS=$(wc -w < "$f" | tr -d ' ')
    IS_LINK="no"; LINK_TARGET=""
    SKILL_DIR=$(dirname "$f")
    if [ -L "$SKILL_DIR" ]; then
      IS_LINK="yes"; LINK_TARGET=$(resolve_symlink "$SKILL_DIR")
    fi
    echo "path=$f words=$WORDS symlink=$IS_LINK target=$LINK_TARGET"
  done < <(list_skill_files "$DIR")
done
[ "$_SKILL_FOUND" -eq 1 ] || echo "(none)"

echo "=== SKILL FRONTMATTER ==="
_FRONTMATTER_FOUND=0
for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    is_health_skill "$f" && continue
    _FRONTMATTER_FOUND=1
    if head -1 "$f" | grep -q '^---'; then
      echo "frontmatter=yes path=$f"
      sed -n '2,/^---$/p' "$f" | head -10
    else
      echo "frontmatter=MISSING path=$f"
    fi
  done < <(list_skill_files "$DIR")
done
[ "$_FRONTMATTER_FOUND" -eq 1 ] || echo "(none)"

echo "=== SKILL SYMLINK PROVENANCE ==="
_PROVENANCE_FOUND=0
for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  find "$DIR" -maxdepth 1 -type l 2>/dev/null | while IFS= read -r link; do
    _PROVENANCE_FOUND=1
    TARGET=$(resolve_symlink "$link")
    echo "link=$(basename "$link") target=$TARGET"
    GIT_ROOT=$(git -C "$TARGET" rev-parse --show-toplevel 2>/dev/null || echo "")
    if [ -n "$GIT_ROOT" ]; then
      REMOTE=$(git -C "$GIT_ROOT" remote get-url origin 2>/dev/null || echo "unknown")
      COMMIT=$(git -C "$GIT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")
      echo "  git_remote=$REMOTE commit=$COMMIT"
    fi
  done
done
if ! { for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  find "$DIR" -maxdepth 1 -type l 2>/dev/null
done | grep -q .; }; then
  echo "(none)"
fi

echo "[10/10] Skill content sample + security scan..."
if [ "$TIER" != "simple" ]; then
echo "=== SKILL FULL CONTENT ==="
_CONTENT_COUNT=0
for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    is_health_skill "$f" && continue
    _CONTENT_COUNT=$((_CONTENT_COUNT + 1))
    [ "$_CONTENT_COUNT" -le 3 ] || break
    echo "--- FULL: $f ---"
    head -60 "$f"
  done < <(list_skill_files "$DIR")
  [ "$_CONTENT_COUNT" -ge 3 ] && break
done
[ "$_CONTENT_COUNT" -gt 0 ] || echo "(none)"
else
  echo "=== SKILL FULL CONTENT ===" ; echo "(skipped: simple tier)"
fi
