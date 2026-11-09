#!/usr/bin/env bash
# Collect agent configuration data for health audit.
# Outputs labeled sections for each data source.
# Run from any directory; uses pwd as the project root.
# Owns bounded, redacted discovery and receipt assembly. Keep shell to orchestration and simple
# presence checks; structured parsing belongs in Python helpers.
#
# Known failure modes (for interpreting (unavailable) output):
#   trusted Python missing  -> conversation, MCP/hooks/allowedTools, and skill-security sections print "(unavailable)"
#   settings.local.json absent -> hooks, MCP, allowedTools all show "(unavailable)"; normal for global-settings-only projects
#   MEMORY.md path          -> built via sed on pwd; unusual chars produce wrong project key; verify manually if (none) seems wrong
#   Conversation scope      -> summary scans 3 recent previous project files across Claude/Codex; deep streams all previous project files; every file modified in the live window is excluded
#   MCP token estimate      -> assumes ~25 tools/server, ~200 tokens/tool; treat as directional, not precise
set -euo pipefail

P=$(pwd)
SETTINGS="$P/.claude/settings.local.json"
# The first argument is retained for launcher compatibility. It is an audit
# hint only; file, contributor, and skill counts never select requirements.
AUDIT_HINT="${1:-auto}"
MODE="${2:-summary}"
SCRIPT_PATH="${BASH_SOURCE[0]}"
case "$SCRIPT_PATH" in
  */*) SCRIPT_BASE="${SCRIPT_PATH%/*}" ;;
  *) SCRIPT_BASE="." ;;
esac
SCRIPT_DIR="$(cd "$SCRIPT_BASE" && pwd -P)"
unset WAZA_PYTHON DOC_REF_CHECKER GIT_INSTALL_ROOT BASH_ENV ENV
unset WAZA_HEALTH_MODE WAZA_HEALTH_DEEP

sanitize_health_path() {
  local target="$1"
  local entry physical safe=""
  local -a path_entries=()
  target=$(cd "$target" 2>/dev/null && pwd -P) || target=$(pwd -P)
  IFS=: read -r -a path_entries <<< "${PATH:-}"
  for entry in "${path_entries[@]}"; do
    [ -n "$entry" ] || continue
    case "$entry" in
      /*) ;;
      *) continue ;;
    esac
    [ -d "$entry" ] || continue
    physical=$(cd "$entry" 2>/dev/null && pwd -P) || continue
    case "$physical/" in
      "$target/"*) continue ;;
    esac
    safe="${safe:+$safe:}$physical"
  done
  printf '%s\n' "$safe"
}

canonical_health_executable() {
  local current="$1"
  local parent name link readlink_bin=""
  local depth=0
  case "$current" in
    /*) ;;
    *) return 1 ;;
  esac
  while [ "$depth" -lt 32 ]; do
    parent="${current%/*}"
    name="${current##*/}"
    [ -n "$parent" ] || parent="/"
    parent=$(cd "$parent" 2>/dev/null && pwd -P) || return 1
    if [ "$parent" = "/" ]; then
      current="/$name"
    else
      current="$parent/$name"
    fi
    if [ ! -L "$current" ]; then
      [ -f "$current" ] && [ -x "$current" ] || return 1
      printf '%s\n' "$current"
      return 0
    fi
    if [ -z "$readlink_bin" ]; then
      if [ -x /usr/bin/readlink ]; then
        readlink_bin=/usr/bin/readlink
      else
        readlink_bin=$(type -P readlink 2>/dev/null || true)
      fi
      [ -n "$readlink_bin" ] || return 1
    fi
    link=$("$readlink_bin" "$current") || return 1
    case "$link" in
      /*) current="$link" ;;
      *) current="$parent/$link" ;;
    esac
    depth=$((depth + 1))
  done
  return 1
}

HEALTH_TARGET=$(cd "$P" 2>/dev/null && pwd -P) || HEALTH_TARGET=$(pwd -P)
HEALTH_HOME=$(cd "$HOME" 2>/dev/null && pwd -P) || HEALTH_HOME="$HOME"
PATH="$(sanitize_health_path "$HEALTH_TARGET")"
export PATH
PYTHON_BIN=""
for candidate in python3 python; do
  resolved=$(type -P "$candidate" 2>/dev/null || true)
  [ -n "$resolved" ] || continue
  resolved=$(canonical_health_executable "$resolved" 2>/dev/null || true)
  [ -n "$resolved" ] || continue
  if [ "$HEALTH_TARGET" = "/" ]; then
    continue
  fi
  case "$resolved/" in
    "$HEALTH_TARGET/"*) continue ;;
  esac
  "$resolved" --version >/dev/null 2>&1 || continue
  "$resolved" -I -c 'import sys; raise SystemExit(sys.version_info < (3, 9))' \
    >/dev/null 2>&1 || continue
  PYTHON_BIN="$resolved"
  break
done

safe_health_text() {
  printf '%s' "$1" | LC_ALL=C tr '\000-\037\177' '_'
  printf '\n'
}

path_has_controls() {
  case "$1" in
    *$'\n'*|*$'\r'*) return 0 ;;
  esac
  printf '%s' "$1" | LC_ALL=C grep -q '[[:cntrl:]]'
}

if path_has_controls "$P" || path_has_controls "$HOME" || path_has_controls "$SCRIPT_DIR"; then
  echo "Health cannot audit roots whose paths contain control characters." >&2
  exit 2
fi

health_path_label() {
  local path="$1" label home_prefix='~'
  case "$path" in
    "$HEALTH_TARGET") label='project:/' ;;
    "$HEALTH_TARGET"/*) label="project:/${path#"$HEALTH_TARGET"/}" ;;
    "$HOME") label="${home_prefix}/" ;;
    "$HOME"/*) label="${home_prefix}/${path#"$HOME"/}" ;;
    "$HEALTH_HOME") label="${home_prefix}/" ;;
    "$HEALTH_HOME"/*) label="${home_prefix}/${path#"$HEALTH_HOME"/}" ;;
    *) label="external:/${path##*/}" ;;
  esac
  safe_health_text "$label"
}

redact_health_stream() {
  if [ -z "$PYTHON_BIN" ]; then
    echo "(unavailable: trusted Python missing; content withheld)"
    return 0
  fi
  "$PYTHON_BIN" -I -c '
import re, sys
limit = 131072
raw = sys.stdin.buffer.read(limit + 1)
truncated = len(raw) > limit
text = raw[:limit].decode("utf-8", errors="replace")
text = re.sub(r"-----BEGIN [^-\r\n]+-----.*?(?:-----END [^-\r\n]+-----|\Z)", "[REDACTED PRIVATE KEY]", text, flags=re.I | re.S)
text = re.sub(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|github_pat_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[A-Z0-9]{16}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b", "[REDACTED]", text)
text = re.sub(r"(?<![A-Za-z0-9_-])(?P<name>-{0,2}(?P<quote>[\x22\x27]?)(?:[A-Za-z0-9]+[_-])*(?:secret[_-]access[_-]key|private[_-]?key|api[_-]?key|authorization|password|passwd|pwd|token|secret)(?P=quote))(?![A-Za-z0-9_-])(?P<separator>\s*[:=]\s*)(?:Bearer\s+|Basic\s+)?(?:\"(?:\\[^\r\n]|[^\"\\\r\n])*(?:\"|\\?(?=\r?\n|\Z))|\x27(?:\\[^\r\n]|[^\x27\\\r\n])*(?:\x27|\\?(?=\r?\n|\Z))|[^\s,;]+)", lambda m: m.group("name") + m.group("separator") + "[REDACTED]", text, flags=re.I)
text = re.sub(r"(?<![A-Za-z0-9_])(?:~[/\\]|/(?:Users|home|private|tmp|var|etc|opt|Volumes)/)[^\s`\"\x27<>]+", "[PATH]", text)
text = re.sub(r"(?<![A-Za-z0-9_])(?:[A-Za-z]:\\|\\\\)[^\s`\"\x27<>]+", "[PATH]", text)
text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
sys.stdout.write(text)
if text and not text.endswith("\n"):
    sys.stdout.write("\n")
if truncated:
    sys.stdout.write("content_truncated: yes\n")
'
}

print_redacted_file() {
  local file="$1" canonical
  canonical=$(canonical_health_file "$file" || true)
  if [ -z "$canonical" ]; then
    echo "(none)"
    return 0
  fi
  LC_ALL=C head -c 131073 "$canonical" 2>/dev/null | redact_health_stream
}

print_sensitive_file_summary() {
  local label="$1" file="$2" canonical
  canonical=$(canonical_health_file "$file" || true)
  if [ -z "$canonical" ]; then
    echo "${label}_present: no"
    return 0
  fi
  echo "${label}_present: yes"
  echo "${label}_lines: $(count_file_lines "$canonical")"
  echo "${label}_words: $(count_file_words "$canonical")"
  echo "${label}_bytes: $(wc -c < "$canonical" | tr -d ' ')"
}

case "$MODE" in
  summary|deep) ;;
  *) MODE="summary" ;;
esac
PROJECT_KEY=$(printf '%s' "$P" | sed 's|[/_]|-|g; s|^-||')
CONVO_DIR="$HOME/.claude/projects/-${PROJECT_KEY}"

resolve_health_helper() {
  local name="$1"
  [ -f "$SCRIPT_DIR/$name" ] || return 1
  printf '%s\n' "$SCRIPT_DIR/$name"
}

count_project_files() {
  local count
  count=$(git -c core.fsmonitor=false -C "$P" ls-files 2>/dev/null | wc -l | tr -d ' ' || true)
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
  count=$(git -c core.fsmonitor=false -C "$P" log -n 500 --format='%ae' 2>/dev/null | sort -u | wc -l | tr -d ' ' || true)
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
  count=$(for dir in "$P/skills" "$P/.claude/skills" "$P/.agents/skills" "$P/.codex/skills"; do
    [ -d "$dir" ] || continue
    list_skill_files "$dir"
  done | while IFS= read -r f; do
      canonical_skill_file "$f" || true
    done | sort -u | wc -l | tr -d ' ')
  printf '%s\n' "${count:-0}"
}

resolve_symlink() {
  readlink -f "$1" 2>/dev/null && return
  # macOS fallback: resolve symlink chain manually
  local target="$1"
  local depth=0
  while [ -L "$target" ] && [ "$depth" -lt 32 ]; do
    local dir
    dir=$(cd "$(dirname "$target")" && pwd -P)
    target=$(readlink "$target")
    case "$target" in /*) ;; *) target="$dir/$target" ;; esac
    depth=$((depth + 1))
  done
  if [ -d "$target" ]; then
    (cd "$target" 2>/dev/null && pwd -P) || return 1
  elif [ -e "$target" ]; then
    local parent base
    parent=${target%/*}
    base=${target##*/}
    parent=$(cd "$parent" 2>/dev/null && pwd -P) || return 1
    printf '%s/%s\n' "$parent" "$base"
  else
    return 1
  fi
}

count_file_lines() {
  local file="$1" canonical
  canonical=$(canonical_health_file "$file" || true)
  if [ -n "$canonical" ]; then
    wc -l < "$canonical" | tr -d ' '
  else
    echo 0
  fi
}

count_file_words() {
  local file="$1" canonical
  canonical=$(canonical_health_file "$file" || true)
  if [ -n "$canonical" ]; then
    wc -w < "$canonical" | tr -d ' '
  else
    echo 0
  fi
}

count_file_bytes() {
  local file="$1" canonical
  canonical=$(canonical_health_file "$file" || true)
  if [ -n "$canonical" ]; then
    wc -c < "$canonical" | tr -d ' '
  else
    echo 0
  fi
}

count_file_cjk_chars() {
  local file="$1" canonical
  canonical=$(canonical_health_file "$file" || true)
  if [ -z "$canonical" ] || [ -z "$PYTHON_BIN" ]; then
    echo 0
    return
  fi
  "$PYTHON_BIN" -I -c 'import re,sys; from pathlib import Path; text=Path(sys.argv[1]).read_text(encoding="utf-8",errors="replace"); print(len(re.findall(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]", text)))' "$canonical" 2>/dev/null || echo 0
}

count_file_context_units() {
  local file="$1" canonical
  canonical=$(canonical_health_file "$file" || true)
  if [ -z "$canonical" ] || [ -z "$PYTHON_BIN" ]; then
    count_file_words "$file"
    return
  fi
  "$PYTHON_BIN" -I -c 'import re,sys; from pathlib import Path; text=Path(sys.argv[1]).read_text(encoding="utf-8",errors="replace"); cjk=re.compile(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]"); print(len(cjk.sub(" ", text).split()) + len(cjk.findall(text)))' "$canonical" 2>/dev/null || count_file_words "$file"
}

context_units_from_stream() {
  if [ -z "$PYTHON_BIN" ]; then
    wc -w | tr -d ' '
    return
  fi
  "$PYTHON_BIN" -I -c 'import re,sys; text=sys.stdin.read(); cjk=re.compile(r"[\u3400-\u9fff\u3040-\u30ff\uac00-\ud7af]"); print(len(cjk.sub(" ", text).split()) + len(cjk.findall(text)))'
}

list_rule_files() {
  local rule_dir file canonical
  for rule_dir in "$P/.claude/rules" "$HOME/.claude/rules"; do
    [ -d "$rule_dir" ] || continue
    while IFS= read -r -d '' file; do
      path_has_controls "$file" && continue
      canonical=$(canonical_health_file "$file" || true)
      [ -n "$canonical" ] || continue
      printf '%s\n' "$canonical"
    done < <(find "$rule_dir" -type f -name "*.md" -print0 2>/dev/null || true)
  done | LC_ALL=C sort -u
}

print_rule_files() {
  local found=0 shown=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    found=1
    shown=$((shown + 1))
    if [ "$shown" -gt 50 ]; then
      continue
    fi
    echo "--- $(health_path_label "$f") ---"
    print_redacted_file "$f"
  done < <(list_rule_files)
  [ "$found" -eq 1 ] || echo "(none)"
  [ "$shown" -le 50 ] || echo "rule_files_truncated: $((shown - 50))"
}

print_file_summary() {
  local label="$1"
  local file="$2"
  local canonical

  canonical=$(canonical_health_file "$file" || true)
  if [ -z "$canonical" ]; then
    echo "${label}_present: no"
    return
  fi

  echo "${label}_present: yes"
  echo "${label}_lines: $(count_file_lines "$canonical")"
  echo "${label}_words: $(count_file_words "$canonical")"

  local headings
  headings=$(grep -nE '^[[:space:]]*#{1,3}[[:space:]]+' "$canonical" 2>/dev/null | head -8 || true)
  if [ -n "$headings" ]; then
    echo "${label}_headings:"
    printf '%s\n' "$headings" | sed 's/^/  /'
  fi
}

print_settings_summary() {
  local file="$1" canonical
  canonical=$(canonical_health_file "$file" || true)
  if [ -z "$canonical" ]; then
    echo "settings_local_json: no"
    return
  fi

  echo "settings_local_json: yes"
  echo "settings_local_json_lines: $(count_file_lines "$canonical")"
  echo "settings_local_json_bytes: $(wc -c < "$canonical" | tr -d ' ')"
}

print_rule_file_summary() {
  local files count=0 shown=0
  files=$(list_rule_files)
  if [ -z "$files" ]; then
    echo "rule_files: 0"
    return
  fi

  count=$(printf '%s\n' "$files" | wc -l | tr -d ' ')
  echo "rule_files: $count"
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    shown=$((shown + 1))
    [ "$shown" -le 50 ] || continue
    echo "path=$(health_path_label "$f") lines=$(count_file_lines "$f") words=$(count_file_words "$f")"
  done <<EOF
$files
EOF
  [ "$count" -le 50 ] || echo "rule_file_summaries_truncated: $((count - 50))"
}

rule_has_paths_frontmatter() {
  local file="$1"
  awk '
    NR == 1 && $0 == "---" { frontmatter = 1; next }
    frontmatter && $0 == "---" { exit(found ? 0 : 1) }
    frontmatter && $0 ~ /^paths:[[:space:]]*$/ { found = 1 }
    END { if (!frontmatter) exit 1 }
  ' "$file"
}

rules_word_count() {
  local scope="${1:-all}" words=0
  if [ -d "$P/.claude/rules" ] || [ -d "$HOME/.claude/rules" ]; then
    words=$(while IFS= read -r f; do
      [ -n "$f" ] || continue
      if [ "$scope" = "scoped" ] && ! rule_has_paths_frontmatter "$f"; then
        continue
      fi
      if [ "$scope" = "always" ] && rule_has_paths_frontmatter "$f"; then
        continue
      fi
      cat "$f"
    done < <(list_rule_files) | wc -w | tr -d ' ')
  fi
  printf '%s\n' "${words:-0}"
}

rules_context_unit_count() {
  local scope="${1:-all}"
  if [ ! -d "$P/.claude/rules" ] && [ ! -d "$HOME/.claude/rules" ]; then
    echo 0
    return
  fi
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    if [ "$scope" = "scoped" ] && ! rule_has_paths_frontmatter "$f"; then
      continue
    fi
    if [ "$scope" = "always" ] && rule_has_paths_frontmatter "$f"; then
      continue
    fi
    cat "$f"
  done < <(list_rule_files) | context_units_from_stream
}

collect_skill_descriptions_raw() {
  local f description helper
  helper=$(resolve_health_helper read_skill_description.py || true)
  [ -n "$helper" ] && [ -n "$PYTHON_BIN" ] || return 0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    description=$("$PYTHON_BIN" -I "$helper" "$f" 2>/dev/null || true)
    [ -n "$description" ] && printf '%s:description: %s\n' "$(health_path_label "$f")" "$description"
  done < <(list_direct_skill_files)
}

skill_description_inventory_status() {
  local helper
  if [ -z "$PYTHON_BIN" ]; then
    echo "unavailable_python"
    return
  fi
  helper=$(resolve_health_helper read_skill_description.py || true)
  if [ -z "$helper" ]; then
    echo "unavailable_helper"
  else
    echo "available"
  fi
}

print_skill_descriptions() {
  local out count status
  status=$(skill_description_inventory_status)
  echo "skill_description_inventory_status: $status"
  if [ "$status" != "available" ]; then
    echo "(unavailable: skill description parser)"
    return
  fi
  out=$(printf '%s\n' "$HEALTH_SKILL_DESCRIPTIONS" | sort -u | awk 'NR <= 101')
  if [ -n "$out" ]; then
    count=$(printf '%s\n' "$out" | wc -l | tr -d ' ')
    printf '%s\n' "$out" | awk 'NR <= 100' | redact_health_stream
    [ "$count" -le 100 ] || echo "skill_descriptions_truncated: yes"
  else
    echo "(none)"
  fi
}

print_skill_description_summary() {
  local out count status
  status=$(skill_description_inventory_status)
  echo "skill_description_inventory_status: $status"
  if [ "$status" != "available" ]; then
    echo "skill_descriptions: unavailable"
    return
  fi
  out=$(printf '%s\n' "$HEALTH_SKILL_DESCRIPTIONS" | sort -u)
  if [ -z "$out" ]; then
    echo "skill_descriptions: 0"
    return
  fi

  count=$(printf '%s\n' "$out" | wc -l | tr -d ' ')
  echo "skill_descriptions: $count"
  printf '%s\n' "$out" | awk 'NR <= 20 {
    marker=":description: "
    position=index($0, marker)
    if (!position) next
    path=substr($0, 1, position - 1)
    description=substr($0, position + length(marker))
    printf "path=%s description_chars=%d\n", path, length(description)
  }'
  if [ "$count" -gt 20 ]; then
    echo "skill_descriptions_truncated: yes"
  fi
}

skill_description_word_count() {
  local words
  words=$(printf '%s\n' "$HEALTH_SKILL_DESCRIPTIONS" | wc -w | tr -d ' ')
  printf '%s\n' "${words:-0}"
}

skill_description_context_unit_count() {
  printf '%s\n' "$HEALTH_SKILL_DESCRIPTIONS" | context_units_from_stream
}

list_skill_files() {
  local dir="$1" link target file relative
  [ -d "$dir" ] || return 0
  path_has_controls "$dir" && return 0
  path_is_sensitive "$dir" && return 0
  while IFS= read -r -d '' file; do
    path_has_controls "$file" && continue
    printf '%s\n' "$file"
  done < <(find "$dir" -maxdepth 4 \
    \( -type d \( -iname 'secrets' -o -iname '.env' -o -iname '.env.*' -o -iname '*credential*' \) -prune \) \
    -o -name "SKILL.md" -print0 2>/dev/null || true)
  while IFS= read -r -d '' link; do
    [ -n "$link" ] || continue
    path_has_controls "$link" && continue
    target=$(resolve_symlink "$link" || true)
    if [ -z "$target" ] || [ ! -d "$target" ]; then
      continue
    fi
    path_has_controls "$target" && continue
    path_is_sensitive "$target" && continue
    if is_project_skill_path "$link" && ! path_is_within "$target" "$HEALTH_TARGET"; then
      continue
    fi
    if [ -f "$target/SKILL.md" ]; then
      printf '%s/SKILL.md\n' "$link"
    elif [ -d "$target/skills" ]; then
      while IFS= read -r -d '' file; do
        relative=${file#"$target"/}
        path_has_controls "$file" && continue
        printf '%s/%s\n' "$link" "$relative"
      done < <(find "$target/skills" -maxdepth 2 -name "SKILL.md" -print0 2>/dev/null || true)
    fi
  done < <(find "$dir" -mindepth 1 -maxdepth 1 -type l -print0 2>/dev/null || true)
}

direct_skill_roots() {
  printf '%s\n' \
    "$P/.claude/skills" \
    "$P/.agents/skills" \
    "$P/.codex/skills" \
    "$HOME/.claude/skills" \
    "$HOME/.agents/skills" \
    "$HOME/.codex/skills"
}

source_skill_roots() {
  printf '%s\n' "$P/skills"
}

list_direct_skill_files() {
  local dir
  while IFS= read -r dir; do
    [ -d "$dir" ] || continue
    list_skill_files "$dir"
  done < <(direct_skill_roots) | while IFS= read -r file; do
    canonical_skill_file "$file" || true
  done | sort -u
}

codex_plugin_candidate_skill_roots() {
  local cache="$HOME/.codex/plugins/cache" dir
  [ -d "$cache" ] || return 0
  while IFS= read -r -d '' dir; do
    path_has_controls "$dir" && continue
    printf '%s\n' "$dir"
  done < <(find "$cache" -mindepth 4 -maxdepth 4 -type d -name skills -print0 2>/dev/null || true) \
    | LC_ALL=C sort
}

skill_roots() {
  local plugin_roots
  plugin_roots=$(codex_plugin_candidate_skill_roots)
  source_skill_roots
  direct_skill_roots
  [ -n "$plugin_roots" ] && printf '%s\n' "$plugin_roots"
}

path_is_within() {
  local path="$1" root="$2"
  [ "$path" = "$root" ] || case "$path/" in "$root/"*) return 0 ;; *) return 1 ;; esac
}

is_project_skill_path() {
  local path="$1"
  case "$path/" in
    "$P/skills/"*|"$P/.claude/skills/"*|"$P/.agents/skills/"*|"$P/.codex/skills/"*) return 0 ;;
    *) return 1 ;;
  esac
}

is_declared_skill_path() {
  local path="$1"
  case "$path/" in
    "$P/skills/"*|"$P/.claude/skills/"*|"$P/.agents/skills/"*|"$P/.codex/skills/"*|\
    "$HOME/.claude/skills/"*|"$HOME/.agents/skills/"*|"$HOME/.codex/skills/"*|\
    "$HOME/.codex/plugins/cache/"*) return 0 ;;
    *) return 1 ;;
  esac
}

path_is_sensitive() {
  local path="$1" lower
  case "$path/" in
    "$HOME/.ssh/"*|"$HOME/.aws/"*|"$HOME/.gnupg/"*|"$HOME/.config/gh/"*|\
    "$HEALTH_HOME/.ssh/"*|"$HEALTH_HOME/.aws/"*|"$HEALTH_HOME/.gnupg/"*|"$HEALTH_HOME/.config/gh/"*) return 0 ;;
  esac
  lower=$(printf '%s' "/$path/" | tr '[:upper:]' '[:lower:]')
  case "$lower" in
    */.env/*|*/.env.*/*|*/secrets/*|*/*credential*/*) return 0 ;;
    *) return 1 ;;
  esac
}

canonical_health_file() {
  local file="$1" canonical scope_root
  path_has_controls "$file" && return 1
  case "$file/" in
    "$P/"*|"$HEALTH_TARGET/"*) scope_root="$HEALTH_TARGET" ;;
    "$HOME/"*|"$HEALTH_HOME/"*) scope_root="$HEALTH_HOME" ;;
    *) return 1 ;;
  esac
  canonical=$(resolve_symlink "$file" 2>/dev/null || true)
  [ -n "$canonical" ] && [ -f "$canonical" ] || return 1
  path_has_controls "$canonical" && return 1
  path_is_sensitive "$canonical" && return 1
  path_is_within "$canonical" "$scope_root" || return 1
  printf '%s\n' "$canonical"
}

canonical_skill_file() {
  local file="$1" dir base canonical
  path_has_controls "$file" && return 1
  is_declared_skill_path "$file" || return 1
  [ -L "$file" ] && return 1
  dir=${file%/*}
  base=${file##*/}
  dir=$(cd "$dir" 2>/dev/null && pwd -P) || return 1
  canonical="$dir/$base"
  path_is_sensitive "$canonical" && return 1
  if is_project_skill_path "$file" && ! path_is_within "$canonical" "$HEALTH_TARGET"; then
    return 1
  fi
  [ -f "$canonical" ] || return 1
  printf '%s\n' "$canonical"
}

list_all_skill_files() {
  local dir f
  while IFS= read -r dir; do
    [ -d "$dir" ] || continue
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      canonical_skill_file "$f"
    done < <(list_skill_files "$dir")
  done < <(skill_roots) | sort -u
}

list_security_skill_files() {
  local dir
  while IFS= read -r dir; do
    [ -d "$dir" ] || continue
    list_skill_files "$dir"
  done < <(skill_roots) | sort -u
}

print_skill_root_coverage() {
  local dir link target
  local direct_present=0 source_present=0 plugin_candidates=0 rejected_roots=0
  while IFS= read -r dir; do
    [ -d "$dir" ] && direct_present=$((direct_present + 1))
    [ -d "$dir" ] || continue
    while IFS= read -r -d '' link; do
      [ -n "$link" ] || continue
      path_has_controls "$link" && continue
      target=$(resolve_symlink "$link" || true)
      if [ -z "$target" ] || path_has_controls "$target" || path_is_sensitive "$target" || { is_project_skill_path "$link" && ! path_is_within "$target" "$HEALTH_TARGET"; }; then
        rejected_roots=$((rejected_roots + 1))
      fi
    done < <(find "$dir" -mindepth 1 -maxdepth 1 -type l -print0 2>/dev/null || true)
  done < <(direct_skill_roots)
  while IFS= read -r dir; do
    [ -d "$dir" ] && source_present=$((source_present + 1))
  done < <(source_skill_roots)
  plugin_candidates=$(codex_plugin_candidate_skill_roots | wc -l | tr -d ' ')
  echo "direct_skill_roots_declared: 6"
  echo "direct_skill_roots_present: $direct_present"
  echo "source_skill_roots_declared: 1"
  echo "source_skill_roots_present: $source_present"
  echo "codex_plugin_candidate_roots_scanned: ${plugin_candidates:-0}"
  echo "codex_plugin_activation_status: unknown"
  echo "codex_plugin_activation_gap: cache_presence_only_cannot_prove_active_routing"
  echo "rejected_sensitive_or_escaped_skill_roots: $rejected_roots"
}

sanitize_git_remote() {
  local remote="$1" scheme rest authority path host
  remote=$(safe_health_text "$remote")
  case "$remote" in
    *://*)
      scheme=${remote%%://*}
      rest=${remote#*://}
      rest=${rest%%\#*}
      rest=${rest%%\?*}
      authority=${rest%%/*}
      if [ "$authority" = "$rest" ]; then
        path=""
      else
        path="/${rest#*/}"
      fi
      authority=${authority##*@}
      [ -n "$authority" ] || { printf '%s\n' "redacted"; return; }
      printf '%s://%s%s\n' "$scheme" "$authority" "$path"
      ;;
    *@*:*)
      rest=${remote%%\#*}
      rest=${rest%%\?*}
      rest=${rest#*@}
      host=${rest%%:*}
      path=${rest#*:}
      if [ -z "$host" ] || [ -z "$path" ]; then
        printf '%s\n' "redacted"
        return
      fi
      printf 'ssh://%s/%s\n' "$host" "$path"
      ;;
    /*|./*|../*)
      printf '%s\n' "local"
      ;;
    *)
      rest=${remote%%\#*}
      rest=${rest%%\?*}
      rest=${rest##*@}
      printf '%s\n' "${rest:-redacted}"
      ;;
  esac
}

is_current_health_skill() {
  [ -f "$SCRIPT_DIR/../SKILL.md" ] && [ "$1" -ef "$SCRIPT_DIR/../SKILL.md" ]
}

list_conversation_files() {
  local file canonical mtime
  [ -d "$CONVO_DIR" ] || return 0
  while IFS= read -r -d '' file; do
    path_has_controls "$file" && continue
    canonical=$(canonical_health_file "$file" || true)
    [ -n "$canonical" ] || continue
    path_is_within "$canonical" "$CONVO_DIR" || continue
    mtime=$(stat -f '%m' "$canonical" 2>/dev/null || stat -c '%Y' "$canonical" 2>/dev/null || echo 0)
    printf '%s\t%s\n' "$mtime" "$canonical"
  done < <(find "$CONVO_DIR" -maxdepth 1 -type f -name '*.jsonl' -print0 2>/dev/null || true) \
    | sort -nr | cut -f2-
}

print_mcp_access_denials() {
  local files file canonical chunk found=0
  files=$(list_conversation_files | head -5)
  if [ -z "$files" ]; then
    echo "(no conversation files)"
    return
  fi
  while IFS= read -r file; do
    path_is_within "$file" "$CONVO_DIR" || continue
    canonical=$(canonical_health_file "$file" || true)
    [ -n "$canonical" ] || continue
    path_is_within "$canonical" "$CONVO_DIR" || continue
    chunk=$(head -c 1048576 "$canonical" | grep -Em 2 'Access denied - path outside allowed directories|tool-results/.+ not in ' 2>/dev/null || true)
    if [ -n "$chunk" ]; then
      found=1
      printf '%s\n' "$chunk" | redact_health_stream
    fi
  done <<EOF
$files
EOF
  [ "$found" -eq 1 ] || echo "(none found)"
}

PROJECT_FILES=$(count_project_files)
CONTRIBUTORS=$(count_contributors)
CI_WORKFLOWS=$(count_ci_workflows)

echo "[1/12] Project signals..."
echo "=== PROJECT SIGNALS ==="
echo "project_files: $PROJECT_FILES"
echo "contributors: $CONTRIBUTORS"
echo "ci_workflows:  $CI_WORKFLOWS"
echo "skills:        $(count_local_skills)"
echo "claude_md_lines: $(count_file_lines "$P/CLAUDE.md")"
echo "collection_mode: $MODE"
echo "audit_hint: $AUDIT_HINT"

echo "[2/12] CLAUDE.md (global + local)..."
echo "=== CLAUDE.md (global) ==="
if [ "$MODE" = "deep" ]; then
  print_redacted_file "$HOME/.claude/CLAUDE.md"
else
  print_file_summary "global_claude_md" "$HOME/.claude/CLAUDE.md"
fi
echo "=== CLAUDE.md (local) ==="
if [ "$MODE" = "deep" ]; then
  print_redacted_file "$P/CLAUDE.md"
else
  print_file_summary "local_claude_md" "$P/CLAUDE.md"
fi

echo "[3/12] Settings, hooks, MCP..."
echo "=== settings.local.json ==="
print_settings_summary "$SETTINGS"

echo "[4/12] Rules + skill descriptions..."
# One per-run snapshot keeps inventory and both budget estimates consistent.
HEALTH_SKILL_DESCRIPTIONS=$(collect_skill_descriptions_raw)
echo "=== rules/ ==="
if [ "$MODE" = "deep" ]; then
  print_rule_files
else
  print_rule_file_summary
fi
echo "=== skill descriptions ==="
if [ "$MODE" = "deep" ]; then
  print_skill_descriptions
else
  print_skill_description_summary
fi

echo "[5/12] Context budget estimate..."
echo "=== STARTUP CONTEXT ESTIMATE ==="
echo "global_claude_words: $(count_file_words "$HOME/.claude/CLAUDE.md")"
echo "global_claude_cjk_chars: $(count_file_cjk_chars "$HOME/.claude/CLAUDE.md")"
echo "global_claude_bytes: $(count_file_bytes "$HOME/.claude/CLAUDE.md")"
echo "global_claude_context_units: $(count_file_context_units "$HOME/.claude/CLAUDE.md")"
echo "local_claude_words: $(count_file_words "$P/CLAUDE.md")"
echo "local_claude_cjk_chars: $(count_file_cjk_chars "$P/CLAUDE.md")"
echo "local_claude_bytes: $(count_file_bytes "$P/CLAUDE.md")"
echo "local_claude_context_units: $(count_file_context_units "$P/CLAUDE.md")"
echo "rules_words: $(rules_word_count always)"
echo "rules_context_units: $(rules_context_unit_count always)"
echo "path_scoped_rules_words: $(rules_word_count scoped)"
echo "path_scoped_rules_context_units: $(rules_context_unit_count scoped)"
echo "skill_desc_words: $(skill_description_word_count)"
echo "skill_desc_context_units: $(skill_description_context_unit_count)"
echo "skill_description_inventory_status: $(skill_description_inventory_status)"
if [ -n "$PYTHON_BIN" ]; then
SAFE_SETTINGS=$(canonical_health_file "$SETTINGS" || true)
"$PYTHON_BIN" -I - "$SAFE_SETTINGS" "$MODE" <<'PYEOF' 2>/dev/null || echo "(unavailable)"
import json
import os
import re
import sys

path = sys.argv[1]
mode = sys.argv[2]
try:
    if os.path.getsize(path) > 1048576:
        raise ValueError('settings file exceeds 1 MiB collection limit')
    with open(path) as fh:
        d = json.load(fh)
except Exception:
    msg = '(unavailable: settings.local.json missing or malformed)'
    print('=== PROJECT-LOCAL hooks ===')
    print(msg)
    print('=== PROJECT-LOCAL MCP ===')
    print(msg)
    print('=== MCP FILESYSTEM ===')
    print(msg)
    print('=== allowedTools count ===')
    print(msg)
    sys.exit(0)

print('=== PROJECT-LOCAL hooks ===')
hooks = d.get('hooks', {})
if isinstance(hooks, dict):
    names = sorted(hooks.keys())
    print(f'hook_events: {len(names)}')
    print('hook_event_names:', ', '.join(names[:20]) if names else '(none)')
    if len(names) > 20:
        print('hook_event_names_truncated:', len(names) - 20)
    handler_count = 0
    matcher_count = 0
    for groups in hooks.values():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict):
                continue
            matcher_count += int(bool(group.get('matcher')))
            handlers = group.get('hooks')
            if isinstance(handlers, list):
                handler_count += len(handlers)
    print('hook_matchers_configured:', matcher_count)
    print('hook_handlers_configured:', handler_count)
else:
    print('hook_events: (unknown format)')

print('=== PROJECT-LOCAL MCP ===')
servers = d.get('mcpServers', d.get('enabledMcpjsonServers', {}))
names = list(servers.keys()) if isinstance(servers, dict) else list(servers)
count = len(names)
safe_names = [re.sub(r'[^A-Za-z0-9_.@+-]+', '_', str(name))[:80] for name in names[:20]]
print(f'servers({count}):', ', '.join(safe_names))
if count > 20:
    print('server_names_truncated:', count - 20)
print('coverage: project settings only; see RUNTIME CONFIGURATION for global sources')

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
    print('allowedDirectories_count:', len(allowed))

print('=== allowedTools count ===')
print(len(d.get('permissions', {}).get('allow', [])))
PYEOF
else
  echo "=== PROJECT-LOCAL hooks ==="
  echo "(unavailable)"
  echo "=== PROJECT-LOCAL MCP ==="
  echo "(unavailable)"
  echo "=== MCP FILESYSTEM ==="
  echo "(unavailable)"
  echo "=== allowedTools count ==="
  echo "(unavailable)"
fi

echo "[6/12] Nested CLAUDE.md + gitignore..."
echo "=== NESTED CLAUDE.md ==="
_NESTED_CLAUDE=()
while IFS= read -r -d '' f; do
  path_has_controls "$f" && continue
  f=$(canonical_health_file "$f" || true)
  [ -n "$f" ] || continue
  _NESTED_CLAUDE+=("$f")
done < <(find "$P" -maxdepth 4 -type f -name "CLAUDE.md" -not -path "$P/CLAUDE.md" -not -path "*/.git/*" -not -path "*/node_modules/*" -print0 2>/dev/null || true)
_NESTED_COUNT=${#_NESTED_CLAUDE[@]}
if [ "$_NESTED_COUNT" -gt 0 ]; then
  _NESTED_SHOWN=0
  for f in "${_NESTED_CLAUDE[@]}"; do
    _NESTED_SHOWN=$((_NESTED_SHOWN + 1))
    [ "$_NESTED_SHOWN" -le 50 ] || continue
    health_path_label "$f"
  done
  [ "$_NESTED_COUNT" -le 50 ] || echo "nested_claude_listing_truncated: $((_NESTED_COUNT - 50))"
else
  echo "(none)"
fi
echo "=== GITIGNORE ==="
_GITIGNORE_HIT=$(git -c core.fsmonitor=false -C "$P" check-ignore -v .claude/settings.local.json 2>/dev/null || true)
if [ -n "$_GITIGNORE_HIT" ]; then
  _GITIGNORE_SOURCE=${_GITIGNORE_HIT%%:*}
  case "$_GITIGNORE_SOURCE" in
    .gitignore|.claude/.gitignore)
      echo "settings.local.json: gitignored"
      ;;
    *)
      echo "settings.local.json: ignored only by non-project rule ($(safe_health_text "$_GITIGNORE_SOURCE")) -- add a repo-local ignore rule"
      ;;
  esac
else
  echo "settings.local.json: NOT gitignored -- risk of committing tokens/credentials"
fi

echo "[7/12] HANDOFF.md + MEMORY.md..."
echo "=== HANDOFF.md ==="
print_sensitive_file_summary "handoff" "$P/HANDOFF.md"
echo "=== MEMORY.md ==="
if [ -f "$HOME/.claude/projects/-${PROJECT_KEY}/memory/MEMORY.md" ]; then
  print_sensitive_file_summary "memory" "$HOME/.claude/projects/-${PROJECT_KEY}/memory/MEMORY.md"
else
  echo "memory_present: no"
fi

echo "[8/12] Conversation signals + extract..."
CONVERSATION_AUDIT_SCRIPT="$(resolve_health_helper conversation_audit.py || true)"
if [ "$AUDIT_HINT" = "instructions" ]; then
  # Out of scope, not unavailable: an instruction-and-config audit does not need
  # session history, and calling a deliberate skip a coverage gap would train the
  # reader to ignore real ones.
  echo "=== CONVERSATION COVERAGE ==="
  echo "(out of scope: instruction and config audit, session history not read)"
  echo "=== CONVERSATION FILES ==="
  echo "(out of scope)"
  echo "=== CONVERSATION SIGNALS ==="
  echo "(out of scope)"
elif [ -n "$CONVERSATION_AUDIT_SCRIPT" ] && [ -n "$PYTHON_BIN" ]; then
  "$PYTHON_BIN" -I "$CONVERSATION_AUDIT_SCRIPT" "$CONVO_DIR" "$MODE" \
    --codex-root "$HOME/.codex/sessions" --project-root "$P"
else
  echo "=== CONVERSATION COVERAGE ==="
  echo "(unavailable: conversation_audit.py or trusted Python missing)"
  echo "=== CONVERSATION FILES ==="
  echo "(unavailable)"
  echo "=== CONVERSATION SIGNALS ==="
  echo "(unavailable)"
  echo "=== CONVERSATION EXTRACT ==="
  echo "(unavailable)"
  echo "=== VERIFICATION RECEIPTS ==="
  echo "(unavailable)"
fi

if [ "$MODE" = "deep" ]; then
echo "=== MCP ACCESS DENIALS ==="
print_mcp_access_denials
else
  echo "=== MCP ACCESS DENIALS ===" ; echo "(skipped: summary mode; ask for a deep health audit or run collect-data.sh auto deep for access-denial scan)"
fi

echo "[9/12] Agent config..."
if [ "$MODE" = "deep" ]; then
  echo "=== AGENT CONFIG DETAIL ==="
else
  echo "=== AGENT CONFIG SUMMARY ==="
fi
AGENT_CONTEXT_SCRIPT="$(resolve_health_helper check_agent_context.py || true)"
if [ -n "$AGENT_CONTEXT_SCRIPT" ] && [ -n "$PYTHON_BIN" ]; then
  if ! "$PYTHON_BIN" -I "$AGENT_CONTEXT_SCRIPT" "$P" "$MODE"; then
    echo "(unavailable: check_agent_context.py failed)"
  fi
else
  echo "(unavailable: check_agent_context.py or trusted Python missing)"
fi

echo "[10/12] AI maintainability..."
if [ "$MODE" = "deep" ]; then
  echo "=== AI MAINTAINABILITY DETAIL ==="
else
  echo "=== AI MAINTAINABILITY SUMMARY ==="
fi
MAINTAINABILITY_SCRIPT="$(resolve_health_helper check_maintainability.py || true)"
if [ -n "$MAINTAINABILITY_SCRIPT" ] && [ -n "$PYTHON_BIN" ]; then
  if ! "$PYTHON_BIN" -I "$MAINTAINABILITY_SCRIPT" "$P" "$MODE"; then
    echo "(unavailable: check_maintainability.py failed)"
  fi
else
  echo "(unavailable: check_maintainability.py or trusted Python missing)"
fi

echo "[11/12] Skill inventory + frontmatter + provenance..."
echo "=== SKILL ROOT COVERAGE ==="
print_skill_root_coverage
echo "=== SKILL INVENTORY ==="
_SKILL_FOUND=0
_SKILL_SHOWN=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  _SKILL_FOUND=1
  _SKILL_SHOWN=$((_SKILL_SHOWN + 1))
  [ "$_SKILL_SHOWN" -le 200 ] || continue
  WORDS=$(wc -w < "$f" | tr -d ' ')
  echo "path=$(health_path_label "$f") words=$WORDS"
done < <(list_all_skill_files)
[ "$_SKILL_FOUND" -eq 1 ] || echo "(none)"
[ "$_SKILL_SHOWN" -le 200 ] || echo "skill_inventory_truncated: $((_SKILL_SHOWN - 200))"

echo "=== SKILL FRONTMATTER ==="
if [ "$MODE" = "deep" ]; then
  _FRONTMATTER_FOUND=0
  _FRONTMATTER_SHOWN=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    _FRONTMATTER_FOUND=1
    _FRONTMATTER_SHOWN=$((_FRONTMATTER_SHOWN + 1))
    [ "$_FRONTMATTER_SHOWN" -le 200 ] || continue
    if head -1 "$f" | grep -q '^---'; then
      echo "frontmatter=yes path=$(health_path_label "$f")"
    else
      echo "frontmatter=MISSING path=$(health_path_label "$f")"
    fi
  done < <(list_all_skill_files)
  [ "$_FRONTMATTER_FOUND" -eq 1 ] || echo "(none)"
  [ "$_FRONTMATTER_SHOWN" -le 200 ] || echo "skill_frontmatter_truncated: $((_FRONTMATTER_SHOWN - 200))"
else
  echo "(skipped: summary mode; use collect-data.sh auto deep to print skill frontmatter samples)"
fi

echo "=== SKILL SYMLINK PROVENANCE ==="
_PROVENANCE_FOUND=0
_PROVENANCE_SHOWN=0
while IFS= read -r DIR; do
  [ -d "$DIR" ] || continue
  while IFS= read -r -d '' link; do
    [ -n "$link" ] || continue
    path_has_controls "$link" && continue
    _PROVENANCE_FOUND=1
    _PROVENANCE_SHOWN=$((_PROVENANCE_SHOWN + 1))
    [ "$_PROVENANCE_SHOWN" -le 100 ] || continue
    TARGET=$(resolve_symlink "$link" || true)
    if [ -z "$TARGET" ] || path_has_controls "$TARGET"; then
      echo "link=$(safe_health_text "${link##*/}") target_scope=unresolved"
      continue
    fi
    echo "link=$(safe_health_text "${link##*/}") target_scope=$(health_path_label "$TARGET")"
    GIT_ROOT=$(git -c core.fsmonitor=false -C "$TARGET" rev-parse --show-toplevel 2>/dev/null || echo "")
    if [ -n "$GIT_ROOT" ]; then
      RAW_REMOTE=$(git -c core.fsmonitor=false -C "$GIT_ROOT" remote get-url origin 2>/dev/null || echo "unknown")
      REMOTE=$(sanitize_git_remote "$RAW_REMOTE")
      unset RAW_REMOTE
      COMMIT=$(git -c core.fsmonitor=false -C "$GIT_ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")
      echo "  git_remote=$REMOTE commit=$COMMIT"
    fi
  done < <(find "$DIR" -maxdepth 1 -type l -print0 2>/dev/null || true)
done < <(skill_roots)
[ "$_PROVENANCE_FOUND" -eq 1 ] || echo "(none)"
[ "$_PROVENANCE_SHOWN" -le 100 ] || echo "skill_provenance_truncated: $((_PROVENANCE_SHOWN - 100))"

echo "[12/12] Full skill security scan..."
if [ "$MODE" = "deep" ]; then
echo "=== SKILL SECURITY SCAN ==="
_SKILL_SCAN_FILES=()
while IFS= read -r f; do
  [ -n "$f" ] || continue
  _SKILL_SCAN_FILES+=("$f")
done < <(list_security_skill_files)
SKILL_SECURITY_SCRIPT="$(resolve_health_helper scan_skill_security.py || true)"
if [ -n "$SKILL_SECURITY_SCRIPT" ] && [ -n "$PYTHON_BIN" ] && [ "${#_SKILL_SCAN_FILES[@]}" -gt 0 ]; then
  "$PYTHON_BIN" -I "$SKILL_SECURITY_SCRIPT" \
    --project-root "$HEALTH_TARGET" \
    --health-entrypoint "$SCRIPT_DIR/../SKILL.md" \
    -- "${_SKILL_SCAN_FILES[@]}"
elif [ "${#_SKILL_SCAN_FILES[@]}" -eq 0 ]; then
  echo "(none)"
else
  echo "(unavailable: scan_skill_security.py or trusted Python missing)"
fi
else
  echo "=== SKILL SECURITY SCAN ===" ; echo "(skipped: summary mode; deep mode scans discovered direct skill roots plus Codex plugin-cache candidates with bounded metadata; cache presence does not prove active routing)"
fi
