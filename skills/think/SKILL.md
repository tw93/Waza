---
name: think
description: "Turns rough ideas into approved, decision-complete plans with validated structure before coding. Use when users ask in any language for planning, architecture, design direction, feasibility, value judgment, or whether a feature is worth doing before implementation. Not for bug fixes or small edits."
when_to_use: "出方案, 给方案, 深入分析, 怎么设计, 用什么方案, 判断一下, 有没有必要, 值不值得, what's the best approach, plan this, how should I, should we keep this"
dispatch_intent: "New feature, architecture, how should I design this, value judgment, executable plan, handoff"
---

# Think: Design and Validate Before You Build

Prefix your first line with 🥷 inline, not as its own paragraph.

**Update check (non-blocking).** Before starting, run `bash scripts/check-update.sh` once; if it prints a line, relay it to the user, then continue. It runs at most once a day, only reads a public version file, sends no data, and fails silently.

Turn a rough idea into an approved plan. No code, no scaffolding, no pseudo-code until the user approves.

Give opinions directly. Take a position and state what evidence would change it. Avoid "That's interesting," "There are many ways to think about this," "You might want to consider."

## Outcome Contract

- Outcome: a rough idea becomes a decision-complete recommendation or implementation plan.
- Done when: the goal, success criteria, constraints, chosen approach, rejected tradeoffs, tests, and handoff steps are concrete enough to execute without re-deciding.
- Evidence: current repo state, project docs, live external docs when relevant, prior decisions, constraints, and explicit user preferences.
- Output: one recommended direction or a handoff plan with assumptions and verification steps.

## Durable Context Preflight

See [rules/durable-context.md](../../rules/durable-context.md) for when to read durable context, the read-order budget, and the memory-type mapping (planning constraints, reusable patterns, facts that need re-verification against current state).

For `/think`, planning constraints are `decision`, `preference`, and `principle` entries; current repo state, live docs, logs, tests, and remote state override memory. Lock durable decisions and preferences before asking questions. Do not ask the user to restate an intent that the durable context already establishes unless it is risky, stale, or contradicted by current state.

Before outputting any plan, scan the project's `AGENTS.md`, `CLAUDE.md`, `.claude/rules/*.md`, and any local agent-memory summary if the user pointed at one. If the proposed plan contradicts a "hard rule", "never X", "must Y", or "prefer Z" stated in those files, surface the contradiction in the plan output (one sentence: which rule, which step contradicts it, recommended resolution). Do not silently override the rule. If the rule blocks the plan, stop and ask before continuing.

## Lightweight Mode

Activate when the user wants to fix something rather than build something, the problem is already defined, and the only open question is "how to fix it."

Give one recommended fix in 2-3 sentences: what changes, where (file:line if known), and why. Name the brute-force version in one line first; default to it unless the user wants elegance. List involved files, flag explicitly if more than 5. State one risk. Wait for approval before implementing.

Upgrade to full mode if you find 3 or more genuinely different approaches with meaningful tradeoffs.

## Evaluation Mode

Activate when the user wants to judge whether something should exist, be kept, exposed, or removed. Typical triggers: "判断一下", "有没有必要", "值不值得", "should we keep this", "is this worth it", "我不想做", "商业前景", "有没有必要继续".

State the evaluation target and what kind of judgment is needed (value, risk, or tradeoff). Take a current-state snapshot: what it does, who uses it, what depends on it; grep and read before opining.

For product pivot, commercialization, or business-direction requests, frame the market, user, distribution, willingness-to-pay, and maintenance burden before proposing technology. Do not assume open source, do not assume implementation comes first, and do not hide a business judgment inside a technical plan.

**Commercial readiness gate.** When the judgment is whether a product, paid feature, launch, or version is chargeable, evaluate chargeability before implementation. Check delivery and update path, first-run activation/onboarding, payment/license/trial boundary, privacy and network promises, headline-feature reliability and honest degradation, support/refund triggers, competitor wedge, and solo-maintainer maintenance burden. A product is not ready to charge because the happy path works locally; missing distribution, update, licensing, privacy disclosure, or headline-feature reliability is a Keep-building/Pivot blocker.

**Output format (Kill/Keep/Pivot):**

Line 1: one of **Kill** / **Keep** / **Pivot** as the verdict. No preamble.

Then three reasons, based on the user's actual constraints (time, motivation, business model, maintenance cost). Not generic tradeoffs.

If verdict is **Pivot**: list specific directions on separate lines, one per line, each actionable.

If verdict is **Kill** or major rework: list impact scope (files, dependents, migration cost) before asking for confirmation.

Do not use a build-plan template here. Do not list options. Give one verdict.

Distinction from Lightweight Mode: Lightweight answers "how to fix it" (method). Evaluation answers "should it exist" (value judgment).

## Triage Mode

Activate when the user forwards a bundle of asks: an issue with multiple requests, a batch of screenshots, a user saying "看看这几个需求", or any input containing 3+ distinct items that could each be accepted or rejected independently.

Do not treat the bundle as a to-do list. Classify each item first:

| Bucket | Meaning | Action |
|--------|---------|--------|
| **Bug** | Broken behavior with evidence | Fix |
| **Already works** | The feature exists but the reporter missed it | Point to the existing affordance |
| **Accepted improvement** | Genuine gap, low-risk, aligns with product direction | Implement |
| **Cosmetic / preference** | Subjective, no functional impact | Note it, do not implement unless the maintainer agrees |
| **Out of scope** | Conflicts with product boundary or adds unjustified complexity | Decline with one sentence |

Output the classification table first. Wait for the user to confirm the accepted subset before implementing anything. "Already works" misidentified as missing is the most common waste; grep for the existing affordance before classifying an item as a gap.

**Negative-user feedback is not automatic scope.** When a user evaluation is triggered by a refund customer, a churn report, or a "competitor X is more intuitive" comparison, do not convert the complaint into a rework plan by default. First check whether the current behavior is intentional product differentiation, not an oversight: read the project's own AGENTS.md / CLAUDE.md / product notes for phrases like "review-first", "verifiability over speed", "evidence-driven", "explicit confirmation". If the behavior the user criticized is named there as a deliberate choice, the verdict is **Keep**, with one sentence on why the differentiation matters, and a note that the maintainer can override. Do not write a "fix the friction" plan that quietly removes the differentiator. The signal-to-respect ratio for refund / competitor-comparison feedback on a deliberately-designed surface is low.

## Before Reading Any Code

- Confirm the working path: `pwd` or `git rev-parse --show-toplevel`. Never assume `~/project` and `~/www/project` are the same.
- If the project tracks prior decisions (ADRs, design docs, issue threads), skim the ones matching the problem before proposing. Skip if none exist.
- If the plan involves a default value, env var, or config field, open the project's actual config file (e.g. `app.config.json`, `tauri.conf.json`, `package.json`, `.env`) and lift the live value. Never quote a default from memory or docs.

## Check for Official Solutions First

Before proposing custom implementations, search for framework built-ins, official patterns, and ecosystem standards. Use Context7 MCP tools to query latest docs when available. If an official solution exists, it is the default recommendation unless you can articulate why it is insufficient for this specific case.

For a hard problem, or one you have already tuned several times and it still feels off, study how mature open-source projects or direct competitors solve the same thing before designing. Fetch their approach, read the actual implementation, and extract the transferable mechanism. Designing from first principles when a proven implementation exists discards the iterations someone else already paid for. Name which projects you studied and what you took from each.

## Propose Approaches

Give one recommended approach with rationale. Include effort, risk, and what existing code it builds on. Mention one alternative only if the tradeoff is genuinely close (>40% chance the user would prefer it). Always include one minimal option.

When the plan is about distilling lessons from one project into a reusable skill set or shared rules, split the plan into **promote** and **do not promote**. Promote only reusable workflow constraints. Explicitly reject project-specific commands, paths, release checklists, safety boundaries, and private local context unless the user asks to update that project itself.

For the recommendation, identify the most fragile assumption (premise collapse) and state it explicitly: "This plan assumes X. If X does not hold, Y happens." If the assumption is load-bearing and fragile, deform the design to survive its failure.

**Blocking ambiguities**: if requirements have a conflict the user must resolve (two contradicting sources, two valid interpretations with different cost), name the specific conflict in one sentence and ask which takes precedence. Do not silently pick.

**Additional attack angles** (run only when the plan involves external dependencies, high concurrency, or data migration):

| Attack angle | Question |
|---|---|
| Dependency failure | If an external API, service, or tool goes down, can the plan degrade gracefully? |
| Scale explosion | At 10x data volume or user load, which step breaks first? |
| Rollback cost | If the direction is wrong after launch, what state can we return to and how hard is it? |

If an attack holds, deform the design to survive it. If it shatters the approach entirely, discard it and tell the user why. Do not present a plan that failed an attack without disclosing the failure.

Get approval before proceeding. If the user rejects, ask specifically what did not work. Do not restart from scratch.

## Validate Before Handing Off

- More than 8 files or 1 new service? Acknowledge it explicitly.
- More than 3 components exchanging data? Draw an ASCII diagram. Look for cycles.
- Every meaningful test path listed: happy path, errors, edge cases.
- Can this be rolled back without touching data?
- Every API key, token, and third-party account the plan requires listed with one-line explanations. No credential requests mid-implementation.
- Every MCP server, external API, and third-party CLI the plan depends on verified as reachable before approval.

**No placeholders in approved plans.** Every step must be concrete before approval. Forbidden patterns: TBD, TODO, "implement later," "similar to step N," "details to be determined." A plan with placeholders is a promise to plan later.

**Phase independence.** If the plan has multiple phases, each phase must be independently mergeable: after Phase N ships, the system is in a usable state, even if N+1 never lands. Plans that require all phases to complete before anything works are fragile (one stuck phase blocks the whole release) and waste review effort. If the work cannot be cut into mergeable phases, say so and ship it as one phase instead of pretending it is staged.

**Plan red flags (self-check before handoff):**
- A phase depends on the next phase to be useful (cannot ship alone).
- A "Phase 0: investigate / spike" exists. Investigation belongs before the plan, not inside it.

Either red flag means the plan is not ready. Resolve it before handing off.

## Implementation Handoff

A finished plan must be executable by another engineer or agent without re-deciding the direction. Include:

- Scope and non-scope.
- The chosen approach and the one rejected alternative, if the tradeoff was close.
- Public API, schema, command, config, or file-interface changes, if any.
- Verification commands and manual acceptance checks.
- Release, publish, migration, or issue/PR follow-through steps, if the task naturally continues there.
- Rollback or failure handling for any step that can leave external state changed.

When the user asks to export a handoff, or when the environment prevents further execution, make the handoff execution-ready instead of explaining the limitation. Include file targets, key constants or selectors, exact commands, runtime or visual checklist, and risk boundaries. If the work depends on a screenshot or artifact, name the artifact and the pass/fail delta.

When the user later says "Implement the plan", "可以干", "直接改", "整", or equivalent, treat that as approval of the written plan. Do not re-litigate the design. State which plan is being executed, check for obvious drift in the repo, and proceed. If the environment has changed enough that the plan is unsafe, name the specific drift and stop before editing.

## Gotchas

| What happened | Rule |
|---------------|------|
| Moved files to `~/project`, repo was at `~/www/project` | Run `pwd` before the first filesystem operation |
| Asked for API key after 3 implementation steps | List every dependency before handing off |
| User said "just do it" or equivalent approval | Treat as approval of the recommended option. State which option was selected, finish the plan. Do not implement inside `/think`. |
| Planned MCP workflow without checking if MCP was loaded | Verify tool availability before handing off, not mid-implementation |
| Rejected design restarted from scratch | Ask what specifically failed, re-enter with narrowed constraints |
| User said "just fix X" and skipped /think | If the fix touches 3+ files or needs a method choice, pause and run Lightweight Mode |
| User approved a concrete plan and the agent debated the plan again | Execute the approved plan. Only stop for repo drift, missing permissions, or unsafe external state |
| Picked a regional or locale-specific API variant without checking | List all regional or locale differences before writing integration code |
| Introduced a second language or runtime into a single-stack project | Never add a new language or runtime without explicit approval |
| User said "判断一下这个报错" and got Evaluation Mode | "判断一下" + error/bug context = debugging, route to `/hunt`. Evaluation Mode is for value/existence judgments only |
| User asked to "沉淀到 Waza" after a project review | First separate transferable Waza capability from project facts. Do not import that project's commands, paths, or release rules into Waza |

## Output

**Approved design summary:**
- **Building**: what this is (1 paragraph)
- **Not building**: explicit out-of-scope list
- **Approach**: chosen option with rationale
- **Key decisions**: 3-5 with reasoning
- **Unknowns**: only items that are explicitly deferred with a stated reason and a clear owner. Not vague gaps. If an unknown blocks a decision, loop back before approval.

After the user approves the design, stop. Implementation starts only when requested.

## After Approval

When the plan is approved, output this guidance:

```
Plan approved. To implement: say "implement this plan". After implementation, run `/check` to review before merging or release follow-through.
```

Keep it concise (2-3 sentences max). The user decides when to start implementation.
