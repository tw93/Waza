Use only the pasted data. Do not read files.

[PASTE Step 1 output sections: settings.local.json, GITIGNORE, CLAUDE.md (global), CLAUDE.md (local), hooks, MCP FILESYSTEM, MCP ACCESS DENIALS, allowedTools count, skill descriptions, CONVERSATION EXTRACT]

Tier: [SIMPLE / STANDARD / COMPLEX]. Apply only that tier.

## Part A: Control + Verification Layer

Hooks checks:
- SIMPLE: Hooks are optional. Only flag broken ones, for example wrong file types.
- STANDARD+: PostToolUse hooks expected for the primary languages of the project.
- COMPLEX: Hooks expected for all frequently-edited file types found in conversations.
- ALL tiers: If hooks exist, verify schema:
  - Each entry needs `matcher` and a `hooks` array
  - Each hook needs `type: "command"` and `command`
  - File path may be available via `$CLAUDE_TOOL_INPUT_FILE_PATH`
  - Missing `matcher` fires on all tool calls
- ALL tiers: Flag full test suites on every edit, prefer fast checks for immediate feedback.
- ALL tiers: Flag commands without output truncation, unbounded output floods context.
- ALL tiers: Flag commands without explicit failure surfacing.

allowedTools hygiene, ALL tiers:
- Flag genuinely dangerous operations only: sudo *, force-delete root paths, *>* and git push --force origin main
- Do NOT flag: path-hardcoded commands, debug/test commands, brew/launchctl/maintenance commands -- these are normal personal workflow entries

Credential exposure, ALL tiers:
- Project-scoped secrets are [!] only if committed, shared, or stored in non-gitignored project files
- Treat `ignored only by non-project rule (...)` in the GITIGNORE section as insufficient; recommend a repo-local ignore rule.
- Do NOT flag user-scoped files like `~/.mcp.json` just because credentials are intentionally stored there

MCP configuration, STANDARD+:
- Check enabledMcpjsonServers count, >6 may impact performance
- Check filesystem MCP has allowedDirectories configured
- If `~/.claude/projects/.../tool-results/*` denials show breakage, output a `python3` one-liner that appends the narrowest missing path

Prompt cache hygiene, ALL tiers:
- Check CLAUDE.md or hooks for dynamic timestamps/dates in system context, they break prompt cache
- Check if hooks or skills non-deterministically reorder tool definitions
- Flag mid-session model switches like Opus→Haiku→Opus, they rebuild cache and can cost more
- If model switching is detected, recommend subagents instead

Three-layer defense consistency, STANDARD+:
- For each critical rule in CLAUDE.md NEVER/ALWAYS items, check if:
  1. CLAUDE.md declares the rule: intent layer
  2. A Skill teaches the method/workflow for that rule: knowledge layer
  3. A Hook enforces it deterministically: control layer
- Flag rules that only exist in one layer -- single-layer rules are fragile:
  - CLAUDE.md-only rules: Claude may ignore them under context pressure
  - Hook-only rules: no flexibility for edge cases, no teaching
  - Skill-only rules: no enforcement, no always-on awareness
- Priority: focus on safety-critical rules: file protection, test requirements, deploy gates

Verification checks:
- SIMPLE: No formal verification section required. Only flag if Claude declared done without running any check.
- STANDARD+: CLAUDE.md should have a Verification section with per-task done-conditions.
- COMPLEX: Each task type in conversations should map to a verification command or skill.

Subagent hygiene, STANDARD+:
- Flag Agent tool calls in hooks that lack explicit tool restrictions or isolation mode.
- Flag subagent prompts in hooks with no output format constraint -- free-form output pollutes parent context.

## Part B: Behavior Pattern Audit

Data source: up to 3 recent conversation files. Only flag clear evidence. Tag each finding [HIGH CONFIDENCE] or [LOW CONFIDENCE].

1. Rules violated: quote the NEVER/ALWAYS rule and observed violation. No inference.
2. Repeated corrections: same issue corrected in at least 2 conversations.
3. Missing local patterns: project-specific behaviors reinforced in conversation but missing from local CLAUDE.md.
4. Missing global patterns: cross-project behaviors missing from ~/.claude/CLAUDE.md.
5. Skill frequency, STANDARD+: only report directly observed usage. With fewer than 3 sessions, mark [INSUFFICIENT DATA]. For verified <1/month skills, retire them to AGENTS.md docs.
6. Anti-patterns: only flag what is directly observable:
   - Claude declaring done without running verification
   - User re-explaining same context across sessions -- missing HANDOFF.md or memory
   - Long sessions over 20 turns without /compact or /clear

Output: bullet points only, two sections:
[CONTROL LAYER: hooks issues | allowedTools to remove | cache hygiene | three-layer gaps | verification gaps | subagents issues]
[BEHAVIOR: rules violated | repeated corrections | add to local CLAUDE.md | add to global CLAUDE.md | skill frequency | anti-patterns (tag each with confidence level)]
