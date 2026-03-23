---
name: health
description: Run when Claude feels off, ignores rules, or hooks/MCP need auditing.
version: "1.5.1"
disable-model-invocation: true
---

# Claude Code Configuration Health Audit

Audit the current project's Claude Code setup with the six-layer framework:
`CLAUDE.md → rules → skills → hooks → subagents → verifiers`

The goal is to find violations and identify the misaligned layer, calibrated to project complexity.

**Output language:** Use the user's recent messages; fall back to the CLAUDE.md `## Communication` rule. Default to English.

**IMPORTANT:** Before the first tool call, output a progress block in the output language:

```
Step 1/3: Collecting configuration data
  · CLAUDE.md (global + local) · rules/ · settings.local.json · hooks
  · MCP servers · skills inventory + security scan
  · conversation history (up to 3 recent sessions)
```

## Step 0: Assess project tier

Pick tier:

| Tier | Signal | What's expected |
|------|--------|-----------------|
| **Simple** | <500 project files, 1 contributor, no CI | CLAUDE.md only; 0–1 skills; no rules/; hooks optional |
| **Standard** | 500–5K project files, small team or CI present | CLAUDE.md + 1–2 rules files; 2–4 skills; basic hooks |
| **Complex** | >5K project files, multi-contributor, multi-language, active CI | Full six-layer setup required |

**Apply only the detected tier's requirements.**


## Step 1: Collect all data (single bash block)

Run one block to collect data.

```bash
P=$(pwd)
SETTINGS="$P/.claude/settings.local.json"

echo "=== TIER METRICS ==="
echo "project_files: $(find "$P" -type f -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/dist/*" -not -path "*/build/*" | wc -l)"
echo "contributors: $(git -C "$P" log --format='%ae' 2>/dev/null | sort -u | wc -l)"
echo "ci_workflows:  $(ls "$P/.github/workflows/"*.yml "$P/.github/workflows/"*.yaml 2>/dev/null | wc -l)"
echo "skills:        $(find "$P/.claude/skills" -name "SKILL.md" 2>/dev/null | grep -v '/health/SKILL.md' | wc -l)"
echo "claude_md_lines: $(wc -l < "$P/CLAUDE.md" 2>/dev/null)"

echo "=== CLAUDE.md (global) ===" ; cat ~/.claude/CLAUDE.md 2>/dev/null || echo "(none)"
echo "=== CLAUDE.md (local) ===" ; cat "$P/CLAUDE.md" 2>/dev/null || echo "(none)"
echo "=== settings.local.json ===" ; cat "$SETTINGS" 2>/dev/null || echo "(none)"
echo "=== rules/ ===" ; find "$P/.claude/rules" -name "*.md" 2>/dev/null | while IFS= read -r f; do echo "--- $f ---"; cat "$f"; done
echo "=== skill descriptions ===" ; { [ -d "$P/.claude/skills" ] && grep -r "^description:" "$P/.claude/skills" 2>/dev/null; grep -r "^description:" ~/.claude/skills 2>/dev/null; } | sort -u
echo "=== STARTUP CONTEXT ESTIMATE ==="
echo "global_claude_words: $(wc -w < ~/.claude/CLAUDE.md 2>/dev/null | tr -d ' ' || echo 0)"
echo "local_claude_words: $(wc -w < "$P/CLAUDE.md" 2>/dev/null | tr -d ' ' || echo 0)"
echo "rules_words: $(find "$P/.claude/rules" -name "*.md" 2>/dev/null | while IFS= read -r f; do cat "$f"; done | wc -w | tr -d ' ')"
echo "skill_desc_words: $({ [ -d "$P/.claude/skills" ] && grep -r "^description:" "$P/.claude/skills" 2>/dev/null; grep -r "^description:" ~/.claude/skills 2>/dev/null; } | wc -w | tr -d ' ')"
echo "=== hooks ===" ; python3 -c "import json,sys; d=json.load(open('$SETTINGS')); print(json.dumps(d.get('hooks',{}), indent=2))" 2>/dev/null || echo "(unavailable: settings.local.json missing or malformed)"
echo "=== MCP ===" ; python3 -c "
import json
try:
    d=json.load(open('$SETTINGS'))
    s = d.get('mcpServers', d.get('enabledMcpjsonServers', {}))
    names = list(s.keys()) if isinstance(s, dict) else list(s)
    n = len(names)
    print(f'servers({n}):', ', '.join(names))
    est = n * 25 * 200  # ~200 tokens/tool, ~25 tools/server
    print(f'est_tokens: ~{est} ({round(est/2000)}% of 200K)')
except: print('(no MCP)')
" 2>/dev/null || echo "(unavailable: settings.local.json missing or malformed)"
echo "=== MCP FILESYSTEM ===" ; python3 -c "
import json
try:
    d=json.load(open('$SETTINGS')); s=d.get('mcpServers', d.get('enabledMcpjsonServers', {}))
    if isinstance(s, list):
        print('filesystem_present: (array format -- check .mcp.json)'); print('allowedDirectories: (not detectable)')
    else:
        fs=s.get('filesystem') if isinstance(s, dict) else None; a=[]
        if isinstance(fs, dict):
            a = fs.get('allowedDirectories') or (fs.get('config', {}).get('allowedDirectories') if isinstance(fs.get('config'), dict) else [])
            if not a and isinstance(fs.get('args'), list):
                args=fs['args']
                for i, v in enumerate(args):
                    if v in ('--allowed-directories', '--allowedDirectories') and i+1<len(args): a=[args[i+1]]; break
                if not a: a=[v for v in args if v.startswith('/') or (v.startswith('~') and len(v)>1)]
        print('filesystem_present:', 'yes' if fs else 'no'); print('allowedDirectories:', a or '(missing or not detected)')
except: print('(unavailable)')
" 2>/dev/null || echo "(unavailable)"
echo "=== allowedTools count ===" ; python3 -c "import json; d=json.load(open('$SETTINGS')); print(len(d.get('permissions',{}).get('allow',[])))" 2>/dev/null || echo "(unavailable)"
echo "=== NESTED CLAUDE.md ===" ; find "$P" -name "CLAUDE.md" -not -path "$P/CLAUDE.md" -not -path "*/.git/*" -not -path "*/node_modules/*" 2>/dev/null || echo "(none)"
echo "=== GITIGNORE ===" ; (git -C "$P" check-ignore -q .claude/settings.local.json 2>/dev/null && echo "settings.local.json: gitignored") || echo "settings.local.json: NOT gitignored -- risk of committing tokens/credentials"
echo "=== HANDOFF.md ===" ; cat "$P/HANDOFF.md" 2>/dev/null || echo "(none)"
echo "=== MEMORY.md ===" ; cat "$HOME/.claude/projects/-$(pwd | sed 's|[/_]|-|g; s|^-||')/memory/MEMORY.md" 2>/dev/null | head -50 || echo "(none)"

echo "=== CONVERSATION FILES ==="
PROJECT_PATH=$(pwd | sed 's|[/_]|-|g; s|^-||')
CONVO_DIR=~/.claude/projects/-${PROJECT_PATH}
ls -lhS "$CONVO_DIR"/*.jsonl 2>/dev/null | head -10

echo "=== CONVERSATION EXTRACT (up to 3 most recent, confidence improves with more files) ==="
# Skip the active session, it may still be incomplete.
_PREV_FILES=$(ls -t "$CONVO_DIR"/*.jsonl 2>/dev/null | tail -n +2 | head -3)
if [ -n "$_PREV_FILES" ]; then
  echo "$_PREV_FILES" | while IFS= read -r F; do
    [ -f "$F" ] || continue
    echo "--- file: $F ---"
    jq -r '
      if .type == "user" then "USER: " + ((.message.content // "") | if type == "array" then map(select(.type == "text") | .text) | join(" ") else . end)
      elif .type == "assistant" then
        "ASSISTANT: " + ((.message.content // []) | map(select(.type == "text") | .text) | join("\n"))
      else empty
      end
    ' "$F" 2>/dev/null | grep -v "^ASSISTANT: $" | head -300 || echo "(unavailable: jq not installed or parse error)"
  done
else
  echo "(no conversation files)"
fi

echo "=== MCP ACCESS DENIALS ==="
ls -t "$CONVO_DIR"/*.jsonl 2>/dev/null | head -10 | while IFS= read -r F; do
  grep -nEm 2 'Access denied - path outside allowed directories|tool-results/.+ not in ' "$F" 2>/dev/null
done | head -20

# --- Skill scan ---
# Exclude self by frontmatter name, stable across install paths.
SELF_SKILL=$( (grep -rl '^name: health$' "$P/.claude/skills" "$HOME/.claude/skills" 2>/dev/null || true) | grep 'SKILL.md' | head -1)
[ -z "$SELF_SKILL" ] && SELF_SKILL="health/SKILL.md"

echo "=== SKILL INVENTORY ==="
for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  find -L "$DIR" -name "SKILL.md" 2>/dev/null | grep -v "$SELF_SKILL" | while IFS= read -r f; do
    WORDS=$(wc -w < "$f" | tr -d ' ')
    IS_LINK="no"; LINK_TARGET=""
    SKILL_DIR=$(dirname "$f")
    if [ -L "$SKILL_DIR" ]; then
      IS_LINK="yes"; LINK_TARGET=$(readlink -f "$SKILL_DIR")
    fi
    echo "path=$f words=$WORDS symlink=$IS_LINK target=$LINK_TARGET"
  done
done

echo "=== SKILL SECURITY SCAN ==="
for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  find -L "$DIR" -name "SKILL.md" 2>/dev/null | grep -v "$SELF_SKILL" | while IFS= read -r f; do
    echo "--- SCANNING: $f ---"
    # Split dangerous literals to avoid false positives in static security scanners
    _ev='eva''l'; _b64='base6''4'; _rmrf='rm\s+-rf'; _net='cu''rl|wget'
    # Prompt injection
    grep -inE 'ignore (previous|above|all) (instructions|prompts|rules)' "$f" && echo "[!] PROMPT_INJECTION: $f"
    grep -inE '(you are now|pretend you are|act as if|new persona)' "$f" && echo "[!] ROLE_HIJACK: $f"
    # Data exfiltration
    grep -inE "(${_net}).+(-X\s*POST|--data|-d\s).+https?://" "$f" && echo "[!] DATA_EXFIL: $f"
    grep -inE "${_b64}"'.*encode.*(secret|key|token)' "$f" && echo "[!] DATA_EXFIL_B64: $f"
    # Destructive commands
    grep -nE "${_rmrf}"'\s+[/~]' "$f" && echo "[!] DESTRUCTIVE: $f"
    grep -nE 'git push --force\s+origin\s+main' "$f" && echo "[!] DESTRUCTIVE_GIT: $f"
    grep -nE 'chmod\s+777' "$f" && echo "[!] DESTRUCTIVE_PERM: $f"
    # Hardcoded credentials
    grep -nE '(api_key|secret_key|api_secret|access_token)\s*[:=]\s*["'"'"'][A-Za-z0-9+/]{16,}' "$f" && echo "[!] HARDCODED_CRED: $f"
    # Obfuscation
    grep -nE "${_ev}"'\s*\$\(' "$f" && echo "[!] OBFUSCATION_EVAL: $f"
    grep -nE "${_b64}"'\s+-d' "$f" && echo "[!] OBFUSCATION_B64: $f"
    grep -nE '\\x[0-9a-fA-F]{2}' "$f" && echo "[!] OBFUSCATION_HEX: $f"
    # Safety override
    grep -inE '(override|bypass|disable)\s*(the\s+)?(safety|rules?|hooks?|guard|verification)' "$f" && echo "[!] SAFETY_OVERRIDE: $f"
  done
done

echo "=== SKILL FRONTMATTER ==="
for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  find -L "$DIR" -name "SKILL.md" 2>/dev/null | grep -v "$SELF_SKILL" | while IFS= read -r f; do
    if head -1 "$f" | grep -q '^---'; then
      echo "frontmatter=yes path=$f"
      sed -n '2,/^---$/p' "$f" | head -10
    else
      echo "frontmatter=MISSING path=$f"
    fi
  done
done

echo "=== SKILL SYMLINK PROVENANCE ==="
for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
  [ -d "$DIR" ] || continue
  find "$DIR" -maxdepth 1 -type l 2>/dev/null | while IFS= read -r link; do
    TARGET=$(readlink -f "$link")
    echo "link=$(basename "$link") target=$TARGET"
    if [ -d "$TARGET/.git" ]; then
      REMOTE=$(git -C "$TARGET" remote get-url origin 2>/dev/null || echo "unknown")
      COMMIT=$(git -C "$TARGET" rev-parse --short HEAD 2>/dev/null || echo "unknown")
      echo "  git_remote=$REMOTE commit=$COMMIT"
    fi
  done
done

echo "=== SKILL FULL CONTENT (sample: up to 5 skills, 80 lines each) ==="
{ for DIR in "$P/.claude/skills" "$HOME/.claude/skills"; do
    [ -d "$DIR" ] || continue
    find -L "$DIR" -name "SKILL.md" 2>/dev/null | grep -v "$SELF_SKILL"
  done
} | head -5 | while IFS= read -r f; do
  echo "--- FULL: $f ---"
  head -80 "$f"
done
```

## Step 2: Analyze with tier-adjusted depth

After Step 1 completes, output a summary line with the detected tier and key metrics, then the step progress:

```
Tier: {SIMPLE/STANDARD/COMPLEX}; {file_count} files · {contributor_count} contributors · {ci: present/absent}
Step 2/3: {SIMPLE: "Analyzing locally" | STANDARD/COMPLEX: "Launching parallel analysis agents"}
```

For STANDARD/COMPLEX, also list what each agent covers:
```
  · Agent 1: CLAUDE.md, rules, skills, MCP context + security scan
  · Agent 2: hooks, allowedTools, behavior patterns, three-layer defense
```

SIMPLE: do not launch subagents. Analyze locally from Step 1, prioritize core config checks, and skip conversation-heavy cross-validation unless the evidence is already obvious.

STANDARD/COMPLEX: launch **two subagents** in parallel. Paste the needed Step 1 sections inline. Fill in `[project]`, tier, and `(no conversation history)` when needed.

### Agent 1 -- Context + Security Audit (no conversation needed)

Read `agents/agent1-context.md` from this skill's directory for the full prompt.
Paste these Step 1 sections inline: CLAUDE.md (global), CLAUDE.md (local), NESTED CLAUDE.md, rules/, skill descriptions, STARTUP CONTEXT ESTIMATE, MCP, HANDOFF.md, MEMORY.md, SKILL INVENTORY, SKILL SECURITY SCAN, SKILL FRONTMATTER, SKILL SYMLINK PROVENANCE, SKILL FULL CONTENT.

### Agent 2 -- Control + Behavior Audit (uses conversation evidence)

Read `agents/agent2-control.md` from this skill's directory for the full prompt.
Paste these Step 1 sections inline: settings.local.json, GITIGNORE, CLAUDE.md (global), CLAUDE.md (local), hooks, MCP FILESYSTEM, MCP ACCESS DENIALS, allowedTools count, skill descriptions, CONVERSATION EXTRACT.

Paste all data inline. Do not pass file paths.

## Gotchas

Known failure modes that produce misleading output. Check these before flagging as issues.

**Data collection silent failures**
- `jq` not installed: conversation extraction prints `(unavailable: jq not installed or parse error)` and continues. The BEHAVIOR section will be empty -- treat as [INSUFFICIENT DATA], not a finding.
- `python3` not on PATH: all MCP/hooks/allowedTools sections print `(unavailable)`. Do not flag MCP or hook issues when the data source itself failed.
- `settings.local.json` absent: hooks, MCP, and allowedTools all show `(unavailable)`. This is normal for projects that use global settings only -- not a misconfiguration.

**MEMORY.md path construction**
- The path is built with `sed 's|[/_]|-|g'` on `pwd`. Paths containing consecutive slashes or unusual characters produce the wrong project key. If MEMORY.md shows `(none)` but the user mentions prior sessions, verify the path manually before flagging missing memory as [!].

**Skill self-exclusion**
- The security scan excludes the health skill by frontmatter name. If the skill was installed with a non-default name, `SELF_SKILL` may be empty and the scan will include this skill's own content, producing false positives for patterns like `base64 -d` (used in the scan itself).

**Conversation extract scope**
- Only the 3 most recent `.jsonl` files are sampled, skipping the active session. Behavior findings from fewer than 3 files carry low signal -- always tag them [LOW CONFIDENCE].

**MCP token estimate**
- The estimate assumes ~25 tools/server and ~200 tokens/tool. Servers with many tools (e.g., filesystem MCP) or few tools (single-endpoint integrations) can cause large over/under-estimates. Treat the number as directional, not precise.

**Tier misclassification edge cases**
- Monorepos with many generated files (e.g., `dist/`, `node_modules/` not excluded from count) can falsely trigger COMPLEX tier. The bash block excludes common directories but not all generators. Recheck file count manually if the tier feels wrong.

## Step 3: Synthesize and present

Before writing the report, output a progress line in the output language:

```
Step 3/3: Synthesizing report
```

Aggregate the local analysis and any agent outputs into one report:

---

**Health Report: {project} ({tier} tier, {file_count} files)**

### ✓ Passing

Render a compact table of checks that passed. Include only checks relevant to the detected tier. Limit to 5 rows. Omit rows for checks that have findings.

| Check | Detail |
|-------|--------|
| settings.local.json gitignored | ok |
| No nested CLAUDE.md | ok |
| Skill security scan | no flags |

### ☻ Critical -- fix now

Rules violated, missing verification definitions, dangerous allowedTools, MCP overhead >12.5%, required-path `Access denied`, active cache-breakers, and security findings.

### ◎ Structural -- fix soon

CLAUDE.md content that belongs elsewhere, missing hooks, oversized skill descriptions, single-layer critical rules, model switching, verifier gaps, subagent permission gaps, and skill structural issues.

### ○ Incremental -- nice to have

New patterns to add, outdated items to remove, global vs local placement, context hygiene, HANDOFF.md adoption, skill invoke tuning, and provenance issues.

---

If all three issue sections are empty, output one short line in the output language like: `✓ All relevant checks passed. Nothing to fix.`

## Non-goals
- Never auto-apply fixes without confirmation.
- Never apply complex-tier checks to simple projects.
- Flag issues, do not replace architectural judgment.


**Stop condition:** After the report, ask in the output language:
> "Should I draft the changes? I can handle each layer separately: global CLAUDE.md / local CLAUDE.md / hooks / skills."

Do not make any edits without explicit confirmation.
