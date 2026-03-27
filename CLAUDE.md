# Claude Health

Configuration health audit skill for Claude Code.

## Communication

- Do not use em dashes (U+2014) in any output. Use commas, periods, colons, or semicolons instead.
- This also applies to skill templates, report examples, progress lines, and any example output embedded in `skills/health/`.

## Structure

```
.
├── skills/health/
│   └── SKILL.md              -- orchestration: tier detection, data collection, synthesis
├── agents/
│   ├── agent1-context.md     -- Agent 1 prompt: CLAUDE.md, rules, skills, MCP, security audit
│   └── agent2-control.md     -- Agent 2 prompt: hooks, behavior patterns, control layer audit
```

SKILL.md owns the flow. Agent files are loaded on demand by STANDARD/COMPLEX tier only; SIMPLE tier never reads them.

## Verification

```bash
# Syntax check: extract bash blocks from SKILL.md (macOS compatible)
awk '/^```bash$/{p=1;next} /^```$/{p=0} p' skills/health/SKILL.md | bash -n

# Word count: SKILL.md should stay under 3500 words; agent files under 750 words each
wc -w skills/health/SKILL.md agents/agent1-context.md agents/agent2-control.md

# Agent files must exist
test -f agents/agent1-context.md && test -f agents/agent2-control.md && echo "agent files: ok"

# Version: single source of truth is marketplace.json
grep '"version"' .claude-plugin/marketplace.json

# Claude Code install smoke test: project-local install should land in .claude/skills
TMP_HOME=$(mktemp -d) && TMP_PROJ=$(mktemp -d) && \
cd "$TMP_PROJ" && \
HOME="$TMP_HOME" XDG_CONFIG_HOME="$TMP_HOME/.config" npx skills add tw93/claude-health -a claude-code -s health -y --copy && \
test -f "$TMP_PROJ/.claude/skills/health/SKILL.md" && \
test -f "$TMP_PROJ/.claude/skills/health/agents/agent1-context.md" 2>/dev/null || \
test -f "$TMP_PROJ/.claude/skills/health/../../agents/agent1-context.md"
```

## Commit Convention

`{type}: {description}` -- types: feat, fix, refactor, docs, chore

## Release Convention (tw93/miaoyan style)

- Title: `V{version} {Codename} {emoji}` -- e.g., V1.3.0 Guardian
- Tag: `v{version}` (lowercase v)
- Body: HTML format, bilingual (English Changelog + 中文更新日志), one-to-one
- Each item: `<li><strong>Category</strong>: description.</li>` -- bold label summarizes the change, description is one concise sentence, no filler words
- Style: engineer-facing, no marketing language; lead with what changed, not why it matters
- Footer: update command `npx skills add tw93/claude-health@latest` + star + repo link
