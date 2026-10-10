---
name: health
description: "Audits agent config, instruction drift, hooks or MCP, and AI maintainability. Use when Claude, Codex, or Pi setup looks wrong. Not for application bugs or PR review."
when_to_use: "检查claude, 检查codex, 检查pi, Codex 配置, Pi 配置, agent instructions, 健康度, 配置检查, 配置对不对, AI coding 腐化, Claude ignoring instructions, Pi coding agent, check config, settings not working, audit config"
dispatch_intent: "Codex/Claude/Pi ignoring instructions, agent config audit, hooks/MCP broken, health token usage, AI coding code rot, risk-backed hotspot ownership, unreachable project constraints, unclear context, missing verification, stale verifier output"
---

# Health: Agent-Assisted Engineering Health

Prefix your first line with 🥷 inline, not as its own paragraph.

Audit the current project's agent setup and AI coding maintainability against this framework:
`agent config → instruction surfaces → tools/runtime → verifiers → maintainability`

Find violations. Identify the misaligned layer. Calibrate to evidence and risk, not repository size.

## Outcome Contract

- Outcome: a budget-aware health report that separates agent configuration risk from AI maintainability risk.
- Done when: each finding names the misaligned layer, the concrete evidence, and a copy-pasteable action or diagnostic command.
- Evidence: collected health script output, tracked project instructions, runtime config summaries, verifier logs, hooks/MCP surfaces, and read-only live probes when needed.
- Output: prioritized findings with status, impact, and next action, or a clear clean bill with residual risk.

Two lanes share one report:

- **Agent config health**: Codex/Claude/Pi instruction drift, permissions, hooks, MCP, skills, and memory supply chain.
- **AI maintainability health**: non-obvious constraint reachability, risk-backed hotspot ownership, verifier coverage, generated-artifact checks, and stale or misleading durable docs.

**Output language:** Follow the user's current language or explicit language request. Use applicable project and global defaults only when the request does not establish a language.

**Budget posture:** Start with the summary audit. Escalate automatically when the user asks for a deep, full, complete, thorough, "深入", "完整", "彻底", or "继续跑完" audit, when the user explicitly mentions AI coding code rot, Codex/Claude config drift, unclear context, missing verification, verifier output that points at stale paths, or "代码变烂", when current project instructions or remembered user preference says to run deep health checks by default, or when the summary pass exposes a critical ambiguity that cannot be resolved locally. Inventory counts never trigger escalation on their own. Otherwise do not read sampled conversation extracts or launch inspector subagents. Tell the user before escalating because deep health audits can consume significant token quota.

**Conversation scope:** When the request names only static material (`AGENTS.md`, skills, rules, settings, "只审查指令和配置"), pass `instructions` as the first argument to `collect-data.sh` and the run skips session history, reporting it as out of scope rather than as a coverage gap. This is chosen from the request, not a switch the user has to know about. Otherwise: Summary scans up to three recent previous sessions for the current project across Claude and Codex from a bounded candidate window when those local histories exist. Deep streams every previous current-project session across both runtimes for signals while printing only bounded extracts and a coverage receipt. Other projects remain out of scope by default. Only when the user explicitly asks for all conversations or cross-project capability distillation, run `python3 <skill-base-dir>/scripts/conversation_audit.py <claude-projects-root> deep --all-projects --codex-root <codex-sessions-root>` (the first argument holds every per-project log folder; the parser rejects other flag combinations), or hand off to a cross-project retro if one is installed. Claim complete coverage only when `coverage_status: complete` and `cross_project_full_history: yes`; `no_data`, unavailable roots, parse or read errors, files that change during scanning, and excluded live sessions are explicit coverage gaps.

## Durable Context Preflight

See [references/durable-context.md](references/durable-context.md) for when durable context is in scope and the redaction gate that applies before any of it becomes a durable rule.

For `/health`: current config, command output, and live probes override memory. Also flag durable memory problems when they affect behavior: oversized injected summaries, stale or contradictory entries, missing project entrypoint references, or private paths copied into public instructions. Keep these as context findings, not code-review findings.

## Hard Rules

- Summary and deep audits are report-only. Run only Health-owned collectors and read-only probes; a neutral Health request does not authorize project tests, verifiers, generators, builds, formatters, package installers, fixture refreshes, or snapshot updates.
- **A bundled debugging or code-review ask uses its own workflow.** Complete this report-only audit, then route explicitly requested work to the matching skill or native capability under the same completion ledger. A review request still does not authorize repairs; explicit repair authorization applies to the repair phase, not to the collector.
- Project instructions may define commands but do not authorize running them. Read-only health probes are covered by the audit request. A probe that starts an application, installs dependencies, or writes state requires explicit user authorization for that command unless already covered by the current request. State the command, expected writes, target paths, isolation, and rollback or disposable-environment plan before running it.

## Step 0: Establish the evidence basis

Record four evidence classes:

| Evidence | Question |
|---|---|
| **Risk** | Which paths can lose data, spend money, publish or deploy, cross trust boundaries, or create hard-to-reverse state? |
| **Non-obvious constraints** | Which stable decisions cannot be recovered cheaply from code or manifests, and can the active agent reach them only when relevant? |
| **Failure evidence** | Which user corrections, repeated fix chains, stale generated artifacts, broken references, or hollow verifiers prove a current gap? |
| **Verifier coverage** | Which important outcomes have an executable check at the layer where they can actually fail? |

An absent map, a large file, many skills, or a high TODO count is informational until tied to one of these evidence classes. Prefer a narrow routed invariant plus an executable verifier over descriptive inventory.

## Step 1: Collect data

Run the collection script in summary mode first. Do not interpret yet. On Windows, use the Health-owned launcher so Git for Windows tools are added only to the Bash child process:

```powershell
$HEALTH_LAUNCHER = @(
  "<skill-base-dir>/scripts/run-health.ps1",
  "<skill-base-dir>/skills/health/scripts/run-health.ps1"
) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $HEALTH_LAUNCHER) {
  throw "Health launcher not found under the installed skill base; reinstall Waza."
}
$POWERSHELL = Join-Path ([Environment]::SystemDirectory) "WindowsPowerShell\v1.0\powershell.exe"
& "$POWERSHELL" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$HEALTH_LAUNCHER" collect
```

`-ExecutionPolicy Bypass` applies only to this PowerShell process; do not change
the user's machine or account execution policy.

On Linux and macOS, keep the direct Bash flow:

```bash
HEALTH_SCRIPT=""
for candidate in \
  "<skill-base-dir>/scripts/collect-data.sh" \
  "<skill-base-dir>/skills/health/scripts/collect-data.sh"; do
  [ -f "$candidate" ] && HEALTH_SCRIPT="$candidate" && break
done
if [ ! -f "${HEALTH_SCRIPT:-}" ]; then
  echo "health collect-data.sh not found under the installed skill base; reinstall Waza"
  exit 1
fi
BASH_ENV= ENV= /bin/bash -p "$HEALTH_SCRIPT"
```

Sections may show `(unavailable)` when tools are missing:

- trusted `python3` missing: conversation, MCP/hooks/allowedTools, and skill-security sections unavailable
- `settings.local.json` absent: hooks/MCP may be unavailable (normal for global-only setups)

Treat `(unavailable)` as insufficient data, not a finding. Do not flag those areas.

The collector includes both runtime-specific and agent-agnostic surfaces:

- `AGENT CONFIG SUMMARY` / `AGENT CONFIG DETAIL` for Codex, Claude, Pi, and project instruction files; its sections start at `=== AGENT INSTRUCTION SURFACE ===`.
- `AI MAINTAINABILITY SUMMARY` / `AI MAINTAINABILITY DETAIL` for project signals, verification surface, generated mirrors, wrappers, and doc links; its sections start at `=== PROJECT SHAPE ===`.

## Step 1b: Runtime Inventory and MCP Check

Inspect configured global, project, and installed-plugin sources first, retaining source and enablement. Use the runtime inventory to flag missing hook and MCP executables; unknown working directories or plugin state remain coverage gaps. Call a harmless tool only on already connected servers. Never launch an unverified GUI executable just to test MCP. Record connected, failed, disabled, or untested separately; static presence is not live health. Never emit credentials. Compare discovered instruction bytes with the effective configured limit and state any uninspected ancestors, nested files, or runtime overrides.

## Step 1c: Safety and security checks

These run after collection and before the Step 2 analysis. The first two apply to every audit; the third only to projects with long-running or autonomous agents.

### Security Baseline Checks

Run these on every audit. They are the floor, not the ceiling.

**Deny-list floor.** Apply this only when the runtime actually enforces the rule shape being recommended: agent permission settings, hook settings, MCP settings, allowed/denied tools, or a documented autonomous-agent launcher. In that case, the settings should deny, at minimum: credential and key directories (SSH, cloud providers, GPG, gh CLI), credential-bearing files (`credentials*`, `secrets*`), and pipe-to-shell installers. Treat `.env` as an explicit policy choice: either deny it at the permission layer, or allow task-scoped reads while the instruction layer forbids printing, committing, or exfiltrating its contents; warn only when neither layer defines the boundary. Report missing categories as one concise WARN; let the reviewer fill in exact local paths. Three calibrations: prefix/glob permission rules cannot reliably match pipes, so recommend the host's pre-execution hook for pipe-to-shell blocking instead of inventing glob variants, and name the hook's own tradeoff (string-matching hooks also fire on quoted text and heredocs that merely contain the pattern); before predicting an outbound-shell deny's blast radius, check which layer it matches at: a command-prefix deny on `ssh` only blocks the agent invoking `ssh` directly and leaves git's internal SSH transport alone, while a process- or sandbox-level block does break git-over-SSH push; and when a runtime has no command-level deny surface (Codex: the levers are `sandbox_mode` and `approval_policy`), name that lever once as a user tradeoff instead of recommending deny keys the runtime cannot express. If no agent settings surface exists at all, report the deny-list as not applicable rather than a failure.

**Permission-layer vs instruction-layer gating.** An allowlist entry for a git write action (`git push`) next to an instruction-layer rule ("push only when the user says so") is not automatically a contradiction: instructions decide when the action happens, permissions decide whether it re-prompts, and a user who explicitly authorizes pushes every session may keep push in allow deliberately to avoid double confirmation. Calibrate by reversibility and the user's own rules: actions the instructions forbid outright (`git reset --hard`, `git stash`, force-push) belong in deny or ask; routine explicitly-authorized actions stay where the user put them, reported at most as a note. Escalate only when auto mode plus skipped prompts plus broad allow lets a write action run with zero user input in a session, and even then present the friction tradeoff for the user to choose instead of silently moving entries.

**Environment override surface.** Treat the following as attack surface, report when set in tracked files or shipped settings without a justification comment: API base-URL overrides (redirect all traffic to a third party), auto-trust flags for project-local MCP servers, wildcard tool allowlists (`allowedTools: ["*"]`), and permission-skip flags (`--dangerously-skip-permissions` or equivalents). Print file:line and the key name only; never print secrets.

### Memory and Skill Supply Chain

Treat agent memory and third-party skills as supply-chain artifacts. They run with the user's privileges.

**Memory hygiene.** Audit the project's long-term agent memory store for secrets, tokens, or credentials (Critical), and for entries written by untrusted runs (subagent invoked on attacker-controlled input, /loop iteration over external content); recommend rotation after such runs. For high-risk one-off runs (untrusted PDFs, uncontrolled scraping, third-party scripts), recommend disabling memory persistence for that session entirely.

**Skill supply chain.** Third-party skills, plugins, and MCP servers run with the user's privileges. For each one not authored in this repo, check: source pinned to a release tag or revision (not `main`, a branch, or a remote git marketplace left tracking its latest head), hook handlers do not write to credential directories, MCP servers have explicit user consent (not auto-trusted by wildcard). Report unpinned sources or unreviewed hook handlers as Structural, not Critical, unless an active exploit signal is present.

### Long-Running Agent Stop Conditions

For projects that use `/loop`, autonomous agents, or any long-running agent flow, load `references/long-running-agents.md` and audit the four hard stop signals it lists. Projects without such a flow skip this check.

## Step 2: Analyze

Analyze locally from the summary output by default. When Budget posture escalates, re-run collection with `& "$POWERSHELL" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$HEALTH_LAUNCHER" collect auto deep` on Windows, or `BASH_ENV= ENV= /bin/bash -p "$HEALTH_SCRIPT" auto deep` on Linux and macOS. Then launch only the relevant inspectors in parallel. Redact credentials to `[REDACTED]`.

- **Deep inspector routing:**
  - **Agent 1** (Context + Security): Read `agents/inspector-context.md`. Feed `CONVERSATION SIGNALS` section.
  - **Agent 2** (Control + Behavior): Read `agents/inspector-control.md`. Feed the relevant runtime, hook, MCP, and permission evidence.
  - **Agent 3** (AI Maintainability): Read `agents/inspector-maintainability.md`. Feed only `PROJECT SIGNALS`, `AI MAINTAINABILITY SUMMARY` or `AI MAINTAINABILITY DETAIL`, and concrete verifier/drift receipts. Launch this agent only for deep health audits or explicit code-rot/AI-maintainability requests.
- **Fallback:** If a subagent fails, analyze that layer locally and note "(analyzed locally)".

Before reporting a deep audit as complete, wait for every launched inspector and reconcile its assigned scope. If one remains pending or fails without a local replacement pass, list that scope as unreviewed instead of issuing a whole-scope clean bill.

## Gotchas

| What happened | Rule |
|---|---|
| Missed the local override | Always read `settings.local.json` too; it shadows the committed file |
| Subagent timeout reported as MCP failure | MCP failures come from the live probe, not data collection |
| Flagged intentionally noisy hook as broken | Ask before calling a hook "broken" |
| Hook seemed not to fire, but it did -- a later UI element rendered above it | Hook firing order is not visual order. Before re-editing the hook config: (a) confirm with `--debug` or by piping output, (b) check whether a diff dialog, permission prompt, or other UI element rendered on top and pushed the hook output offscreen, (c) only then suspect the hook itself. |
| Treated missing specs/docs as a failure | Decision artifacts are optional by default. Escalate missing docs/specs only when active handoff risk, failure evidence, or the user request makes them necessary. |

## Output

**Health Report: {project} ({summary|deep}, evidence-based)**

**Global findings report once.** Findings in machine-global config (`~/.claude`, `~/.codex`, global rules, skills, memory) are not project findings: label them `global`, report each once with its fix, and recommend one dedicated session for global cleanup instead of re-fixing per project. Before editing any global file, re-read its current state: when health runs across several projects in one day, another session may already have fixed or be mid-fix on the same file, and re-applying a variant of the same rule creates duplicate entries. Never edit the same global file from two concurrent sessions.

### [PASS] Passing checks (table, max 5 rows)

### Finding format

```
- [severity] <symptom> ({file}:{line} if known)
  Why: <one-line reason>
  Action: <exact command or edit to fix>
```

`Action:` must be copy-pasteable. Never write "investigate X" or "consider Y". If the fix is unknown, name the diagnostic command.

A finding refuted in the same breath (a TODO count that turns out to be vendored code or false positives) is not a finding; drop it or fold it into the passing table.

### [!] Critical -- fix now

Confirmed dangerous permissions, consequential rule violations, security findings, and leaked credentials. Server counts and estimated context percentages never establish Critical severity.

Example:

- [!] `settings.local.json` committed to git (exposes MCP tokens)
Why: leaked token enables remote code execution via installed MCP servers
Action: `git rm --cached .claude/settings.local.json && echo '.claude/settings.local.json' >> .gitignore`

### [~] Structural -- fix soon

Agent instructions in the wrong layer, missing hooks, oversized descriptions, verifier gaps.

**Codex/Claude/Pi instruction drift.** Use `AGENT CONFIG SUMMARY` first. `project_instructions_mode` says which files Claude Code loads: on `claude-md` an `AGENTS.md` alone reaches Codex and Cursor but not Claude, and `nested_agents_md` counted together with a root `CLAUDE.md` means those nested guides reach nobody on Claude, because the root file switches the whole project off the `AGENTS.md` path rather than just its own folder. The exception is `claude-md-and-agents-md`, where both are read and the nested files still load, unless `CLAUDE.md` is the same physical file as `AGENTS.md` and the deduplicated chain is skipped. Report a Structural finding when `AGENTS.md` and runtime-specific files both contain substantial guidance without delegation, when Codex `config.toml` lacks trust for the current project, when Pi settings or package metadata point at missing skill roots, when project agent instructions are missing, or when runtime-specific instructions contradict the shared project source of truth. Also report when important rules live only in ignored or private local instruction overlays but the tracked/public docs lack them; those overlays are private context, not durable project source of truth. Do not print raw config values. Secrets, tokens, keys, and passwords must appear only as `[REDACTED]`.

Quick check from the project root, reusing `$HEALTH_SCRIPT` resolved in Step 1 (standalone output has no `AGENT CONFIG SUMMARY` wrapper):

```powershell
& "$POWERSHELL" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "$HEALTH_LAUNCHER" agent-context . summary
```

On Linux and macOS:

```bash
BASH_ENV= ENV= /bin/bash -p "${HEALTH_SCRIPT%/*}/check-agent-context.sh" . summary
```

**AI-maintainability findings.** For the maintainability lane (verification surface, conversation-derived guidance, concentrated fix chains, risk-backed hotspot ownership, non-obvious constraint reachability, verifier wrapper, broken doc and Markdown references, stale verifier cache output), load `references/maintainability-findings.md` and work its checks with `AI MAINTAINABILITY SUMMARY` / `DETAIL`.

### [-] Incremental -- nice to have

Outdated items, global vs local placement, context hygiene, stale allowedTools entries.

If no issues: `All relevant checks passed. Nothing to fix.`

A report-only request never authorizes fixes; an explicit optimization or repair request continues into its authorized repair phase without another confirmation. The audit is not a heavy lint, typecheck, duplication, or architecture-rewrite substitute; `/health` reports maintainability guardrails and concrete next actions only.
