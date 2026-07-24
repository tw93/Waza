---
name: waza
description: 'Dispatcher for Waza engineering skills: think (architecture/handoff), ui (artifact-grounded interface design), check (review/release gates), hunt (runtime debugging/regression), write (prose/release copy), learn (research), read (URL/PDF fetch), health (agent config and AI maintainability audit).'
---

# Waza: Engineering Skills Dispatcher

Prefix your first line with 🥷 inline, not as its own paragraph.

You have eight skills available. Match the user's intent to the right skill, read the matching section below, and execute it.

## Routing Table

<!-- routing-table:start -->
| Intent | Skill | File |
|--------|-------|------|
| Code review, before merge, release gates, generated artifacts, safety sinks, publish/push/reaction follow-through, triage issues/PRs, project-wide code-quality audit scorecard | check | `skills/check/SKILL.md` |
| Codex/Claude/Pi ignoring instructions, agent config audit, hooks/MCP broken, health token usage, AI coding code rot, hotspot ownership, unclear context, missing verification, stale verifier output | health | `skills/health/SKILL.md` |
| Error, crash, regression, screenshot-reported defect, test failure, stale cache, runtime boundary, why broken | hunt | `skills/hunt/SKILL.md` |
| Deep research, unfamiliar domain, compile sources into output | learn | `skills/learn/SKILL.md` |
| Any URL or PDF to fetch, read this, fetch this page | read | `skills/read/SKILL.md` |
| New feature, architecture, how should I design this, value judgment, executable plan, handoff | think | `skills/think/SKILL.md` |
| UI, component, page, visual interface, frontend, artifact-grounded screenshot aesthetic complaint | ui | `skills/ui/SKILL.md` |
| Writing, editing prose, polish, release notes, launch/social copy, remove AI tone | write | `skills/write/SKILL.md` |
<!-- routing-table:end -->

## How This Works

1. Read the user's message and match it to a skill from the table above.
2. Read the matched skill section in full.
3. Execute that skill's instructions exactly.

If the message could match multiple skills, use these disambiguation rules:

1. Most specific wins: `/ui` is more specific than `/think` for UI decisions.
2. URL in message: start with `/read`. If the content is research material, chain to `/learn`.
3. Code already done vs. code broken: done/PR -> `/check`; error/broken -> `/hunt`.
4. Config/maintainability vs. code: Codex/Claude misbehaving, hooks/MCP, `/health` token usage, AI coding code rot, unclear context, missing verification, or stale verifier output -> `/health`; user code errors -> `/hunt`.
5. Release action vs. release prose: commit/tag/publish/push/release reactions/close issue -> `/check`; write release notes/changelog text -> `/write`.
6. Screenshot taste vs. screenshot regression: visual taste complaint -> `/ui`; broken render/state/generated output or used-to-work evidence -> `/hunt`.
7. From scratch vs. editing: new long-form output -> `/learn`; existing draft to polish -> `/write`.
8. "Judge this" + error -> `/hunt`; "judge this" + should we keep it -> `/think`.
9. Still ambiguous: read both skills' "Not for" sections; use exclusion. If still unclear, ask the user.

## Path Resolution

In this distribution, sub-skill scripts live at `skills/{name}/scripts/`. Resolve all relative paths from this file's directory, not from a personal home-directory skill cache.

## Chaining

Skills chain manually, not automatically. Each skill completes and waits for the user's next action.

Common chains: `/think` -> implement approved plan -> `/check` | `/hunt` -> fix -> `/check` -> release/push/issue follow-through | `/read` -> `/learn` -> `/write`
