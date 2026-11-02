---
name: check
description: "Reviews diffs, PRs, release readiness, and publishing follow-through. Use when asked to review, triage issues or PRs, or ship. Not for debugging root causes or prose."
when_to_use: "review, 看看代码, 检查一下, 合并前, 看看issue, 看看PR, release, publish, push, 发布, 提交, close issue, 关闭issue, release reaction, 发布表情, before merge, 值得发布, code review, code-review, audit, 项目体检, 项目评分, scorecard"
dispatch_intent: "Code review, before merge, release gates, generated artifacts, safety sinks, publish/push/reaction follow-through, triage issues/PRs, project-wide code-quality audit scorecard"
---

# Check: Review Before You Ship

Prefix your first line with 🥷 inline, not as its own paragraph.

> Note: `/review` is a built-in Anthropic plugin command for PR review. Waza uses `/check` (or the alias `code-review`) instead. Do not re-trigger `/review` from within this skill.

Read the diff and find the problems. Review, audit, triage, and readiness requests are report-only; apply fixes only under explicit repair authorization still in force for the same task. Done means the requested review surface is covered and every verification claim comes from this session.

## Outcome Contract

- Outcome: a review, release decision, or maintainer action grounded in the current diff, project context, and live evidence.
- Done when: findings, fixes, shipped state, or blockers are stated with the commands, artifacts, or remote state that prove them.
- Evidence: worktree status, diff, public project docs, manifests, CI, package contents, release or registry state, and current command output.
- Output: concise findings first, then verification and shipped-state summary when applicable. Multi-step or ship-action runs, and any request with several items or screenshots, close with a numbered completion ledger (done / not applicable / remaining), never a narrative that leaves the user asking "is everything done".
- Authorization: read-only intent may inspect the worktree and remote state but may not edit files, apply autofixes, commit, push, publish, comment, close, merge, or change branches. Each write or public action needs authorization from the current request, or from an authorization still in force for the same unfinished task: one that named this action and goal and has not been withdrawn. A later turn that asks for progress or says "continue" does not revoke it and does not have to repeat it. A new action, a wider scope, a changed goal, or a risk the original authorization did not cover needs its own. Approval of a draft is not approval to commit, push, publish, or delete.

## Durable Context Preflight

See [references/durable-context.md](references/durable-context.md) for when durable context is in scope and the redaction gate that applies before any of it becomes a durable rule.

For `/check`: the current diff, CI, and remote state override memory. Durable memory can explain user intent and preferred follow-through, but public project rules still come from README files, manifests, CI workflows, release docs, and explicit instructions in the current thread. Never cite private memory as a public project requirement.


## Worktree Safety Preflight

Before any review, triage, ship, release, or PR operation, read the current worktree with:

```bash
git status --short --branch -uall
```

Treat modified, staged, and untracked files as user work. You may read them and include them in the review surface, but you must not move, hide, overwrite, clean, or discard them without explicit user approval in the current turn.

Do not run these commands as default review or PR setup: `git switch`, `git checkout`, `git reset --hard`, `git clean`, `git stash -u`, `git stash --include-untracked`, `git stash -a`, `git stash --all`, or `gh pr checkout`. If a branch change or cleanup is genuinely required, stop and ask for that exact operation.

Do not "protect" user work by moving untracked files, generated files, screenshots, or local scratch files into `/tmp` or another holding directory. Moving someone else's WIP out of the checkout is the same class of interference as stashing it. If a clean tree is required for generation, packaging, or verification, use a separate worktree from a known commit and copy only the artifact or patch you own back into the current checkout.

For PR inspection, prefer commands that do not switch the current working tree: `gh pr view`, `gh pr diff`, `git fetch origin pull/<n>/head:refs/tmp/pr-<n>`, and `git merge-tree`. Commit and push follow-through adds the HEAD re-read in `references/mode-ship.md`.

## Mode Picker

Pick the mode that matches the user's intent, then read it in full before acting. Modes layer on top of the shared review surface (Scope, Hard Rules, Hard Stops, Autofix, Specialist Review, Verification, Sign-off) further down, which applies in every mode. Load a mode file only when its row matches; the default review path needs none of them.

| User intent | Mode |
|---|---|
| "implement this plan", `/think` output handed off | [Plan Execution](#plan-execution-mode) |
| Diff or PR ready, "review", "看看代码", "合并前" | Default review (start at [Get the Diff](#get-the-diff)) |
| "look at issues", "review PRs", "triage", "批量处理", "all repos' issues", "其他仓库也扫一遍" | load `references/mode-triage.md` |
| "is this worth a release", "值不值得发版" | load `references/mode-ship.md` (Release Worthiness Analysis) |
| "commit", "push", "publish", "release", "close issue", "发布表情" | load `references/mode-ship.md` (Ship / Release Follow-through) |
| "audit", "项目体检", "项目评分", "给项目打分", "深入分析项目代码", "scorecard", "linus review" | load `references/mode-audit.md` |
| A review prompt, skill, persona, or model changed; "is review still catching bugs" | load `references/incident-ledger.md` (Replay eval) |
| Document, PDF, prose review | Delegate to `/write` Document Review Mode, keeping it in the same completion ledger; without `/write`, use the available prose capability and name the limitation |

Before any mode, run [Project Context Extraction](#project-context-extraction) and (if memory is in scope) [Durable Context Preflight](#durable-context-preflight).

## Project Context Extraction

This is Waza's public, standalone code-review capability; it never depends on private machine paths or unpublished instructions. Learn the project from the diff and its public context (manifests, CI workflows, AGENTS/CLAUDE files, release notes) until you know its verification commands, generated or protected files, release artifacts, and domain risks. The shape is in `references/project-context.md`.

- Where project context and this skill overlap and both can be met, satisfy the stricter one. An explicit project exception wins and the report names it; stricter is not a licence to overrule a written decision or reorder the host's instruction precedence.
- Prefer a verification command the project names, and read the workflow rather than the sentence describing it. A doc claiming CI enforces something is a claim; a check that runs on only one side (local or CI) means a green run there predicts nothing about the other.

For release readiness or publication, also fill the Release Gate 2.0 matrix from `references/project-context.md`. It covers review base, dirty/staged/untracked state, latest tag, origin sync, version fields, generated artifacts, package/archive contents, release assets, registry/appcast/CI, and public issue/PR state. Missing matrix evidence is a blocker for a "ready to release" claim. A commit/push-only task uses the source-delivery checks in `references/mode-ship.md`; unrelated release assets and registry state are out of scope.

## Plan Execution Mode

Activate when the message starts with "Implement the following plan", "按计划实施", "按照计划", "整", "可以干", or "直接改" followed by a plan body, or links to a `/think` output. Skip the code review: name the plan, check `git status --short --branch -uall` for drift that makes it unsafe (name the conflict and stop), execute, then run the project's verification command.

Review-then-ship: when `AGENTS.md` or the current thread asks to "commit after review", "ship if green", or equivalent, load `references/mode-ship.md` after a clean review or finished plan, state "proceeding to ship", and do not ask again.

## Get the Diff

Derive the review baseline from the user's words and current repository state. Do not ask for commits when the scope is already inferable:

- **All local or uncommitted changes**: inventory staged, unstaged, and untracked files, plus local commits ahead of the configured upstream. Being on the base branch does not make this scope ambiguous.
- **PR or branch review**: use the merge base through the reviewed head, then add any dirty files in that checkout as a separate surface.
- **Since the last release**: resolve the latest stable from the delivery channel the product actually uses (feed, registry, store, or release host), map it to a source ref, and review through `HEAD`, then add dirty files. A stale release-host listing is not the baseline when another channel ships the product; a missing artifact-to-ref mapping stays an explicit gap.
- **Recent N days or an explicit ref**: resolve that time/ref boundary through `HEAD`, then add dirty files.
- **Known-good or previous working version**: compare that ref through `HEAD`; route to `/hunt` Bisect Mode only when the regression point itself is unknown.
- **Whole-project audit**: use Audit Mode rather than pretending one diff is the repository.

Freeze the resolved base, `HEAD`, worktree inventory, generated/distribution surfaces, and delegated scopes before review. For a large inventory, reconcile the union of reviewed paths against that frozen set, including root files and cross-domain consumers; assignment alone is not coverage. Repeated locale or generated files may share a semantic check only when it accounts for every member, otherwise name the sampled and unread remainder separately. Ask one narrow question only when two plausible baselines would materially change the verdict. If review fixes are applied or repository state moves, the old verdict expires: re-read `HEAD`, status, and the full resolved diff before signing off.

## Scope

Measure the diff and classify depth:

| Depth | Criteria | Reviewers |
|-------|----------|-----------|
| **Quick** | Under 100 lines, 1-5 files | Base review only |
| **Standard** | 100-500 lines, or 6-10 files | Base + conditional specialists |
| **Deep** | 500+ lines, 10+ files, or touches auth/payments/data mutation | Base + all specialists + adversarial pass |

State the depth before proceeding.

Depth measures size; risk tier follows paths. A diff touching CI workflows, release or signing, the updater, auth, billing or license, installers, privilege, or deletion paths gets the project's heaviest gate and a human maintainer's review whatever its size or author; an agent's, bot's, or automated reviewer's approval never replaces that review. The method is the Risk tiers section of `references/project-context.md`.

Explicit depth language overrides the size thresholds. "All", "全部", "deep", "深入", or "仔细" means whole-scope coverage of the resolved inventory, even when the textual diff is small; it does not permit skipping untracked files, generated mirrors, required artifacts, or pending reviewers.

Static content diffs can stay quick even when they touch several generated files: version strings, dates, release-copy mirrors, sitemap dates, or one-for-one localization copy changes usually need line-by-line readback plus grep consistency, not a specialist fleet. Escalate only when the diff changes logic, generation rules, public distribution behavior, or user-facing semantics beyond the literal text replacement.

## Did We Build What Was Asked?

Before reading code, check scope drift: do the diff and the stated goal match? Label: **on target** / **drift** / **incomplete**.

Every changed file and new public surface must trace to the stated goal in one sentence; a file, dependency, config knob, abstraction, generated artifact, workflow permission, or release behavior that cannot is drift until proven necessary. Any one of these is enough: a file unrelated to the goal, pure refactoring or unrelated deletion inside a fix or feature, an unmentioned dependency or helper, or a cleanup that quietly adds user-visible UI, default config, workflow permissions, or release behavior. For every new public setting, flag, environment variable, command, or service, ask who will change it and why one correct default cannot serve them; with no evidenced user split, treat the knob as drift and fix the default path instead.

Every review, unasked, runs an over-design pass: for each new file, option, fallback, layer, or abstraction, ask whether the change would still hold with it removed, and report each one that would as removable.

## Question the Approach, Not Just the Diff

Scope drift checks the diff against the stated goal; this checks the goal against the approach. Skip when the user declares the route settled or the repo's design docs record the decision -- do not re-litigate deliberate trade-offs.

When findings cluster on one root cause -- the same bug class patched repeatedly, permission or state problems that follow from the architecture itself, a simple problem made complex -- stop listing patches and state the route verdict first: keep / adjust / replace / insufficient information. Compare a real alternative only when it eliminates the problem class at an acceptable migration cost; never manufacture one to fill the report. No patch list before the verdict.

## Pattern-Fix Completeness

When the diff fixes one instance of a class-of-bug, grep the repo for the same shape (hunt's Scope Blast Mode) and confirm the other instances were handled. List any unswept sibling: a hard stop when it carries the same risk, advisory when lower-risk.

When the diff contains a recurring or hard-to-observe bug, captured output or asynchronous completion, simplification or deletion, history-sensitive normalization, non-atomic replacement of user files, broad destructive matchers, duplicated derivations, test-surface fidelity, never-shipped migrations, or unknown identifiers, load the matching section of `references/review-patterns.md`. Do not load that catalog for unrelated diffs.

## Command And Install Surfaces

When a diff touches a CLI entrypoint, installer, config/env handling, or a mutating command (cleanup, update, uninstall, migration, cache removal), work the CLI Command Surface section of `references/release-surfaces.md`; when it touches a skill, plugin, marketplace entry, package manifest, generated mirror, or published archive, work its Packaged Install Surface section. The lesson behind both: library tests and manifest JSON never prove installed-runtime behavior, and every mutating command is a safety sink. Terminal output is a rendered surface too; after changing CLI-facing text or layout, re-run the command and read the real output.

## Hard Rules

- **No unverified claims.** Do not write "I verified X", "I ran Y", "tests pass", or "this fixes Z" unless the shell output is in this turn's transcript. If you reason about behavior without running, say "based on reading the code" instead of "I verified". Every verification claim in the sign-off must point to a command that actually ran in this session, or be labelled as reused evidence naming the commit and inputs it came from and what was re-checked to confirm it still applies. Reuse the project allows is fine; presenting it as this session's run is not.
- **Re-read source-of-truth facts.** Refresh line numbers, worktree state, fallback behavior, locale coverage, artifact state, and the identity of any issue, PR, or thread in the current turn before citing or posting to it. Earlier context and reviewer notes are leads, not evidence.
- **Public replies**: the body follows `/write` Public Reply Mode; posting, editing, read-back, and closure follow `references/public-reply.md`.

## Hard Stops (fix before merging)

Examples, not exhaustive -- flag any diff that could cause irreversible harm if merged unreviewed.

- **Destructive auto-execution**: any task marked "safe" or "auto-run" that modifies user-visible state (history files, config, preferences, installed software) must require explicit confirmation.
- **Source and distribution out of sync**: everything the source change implies downstream must be regenerated, tracked, uploaded, and version-consistent before declaring done: generated or bundled outputs rebuilt and included, every artifact named in release notes or workflows actually uploaded, every new helper module, reference file, or script present in the built archive, and version fields synchronized across manifests, package metadata, changelogs, tags, and lockfiles.
- **Verifier failure layer unclear**: if a verifier fails before assertions or due to missing optional dependencies, bootstrap noise, transient build-service crashes, unavailable simulators, or tool setup, classify setup versus product failure. Retry only with new evidence or a narrower environment. Do not call the repo broken until the intended test body or artifact check actually ran. The inverse is the same stop: a verifier that passes without running the real path -- a skipped optional-dependency job that still prints OK, a function that early-returns leaving output empty so a true-on-empty assertion passes, a render reported fixed but never opened -- is a hollow green. A pass counts only when at least one non-skipped, non-empty case exercised the path and the assertions fail on emptiness.
- **Publishing over your own open findings**: when the same run produced review findings and then reaches a ship action, every finding must be fixed, or restated as "known, shipping anyway" with its user impact and confirmed, before the release proceeds. A standing release authorization does not cover problems discovered after it was given.
- **Injection and validation**: SQL, command, path injection at system entry points. Credentials hardcoded, logged, committed, or copied into public docs.
- **Dependency changes**: unexpected additions or version bumps in package.json, Cargo.toml, go.mod, requirements.txt. Flag any new dependency not obviously required by the diff. The inverse is a finding too: a declared dependency or linked SDK with zero imports across the repo gets flagged to the maintainer, not silently removed (it may be staged for an upcoming feature, and unused analytics/telemetry SDKs still drag app review and privacy manifests). Removal needs the maintainer's go-ahead in the current turn, a grep proving zero references first, and a full build after. For lockfiles, automated security PRs, or version pins, load `references/review-patterns.md` (Dependency changes).
- **Safety sinks**: destructive file operations, shell or AppleScript construction, cwd/path/symlink traversal, approval or sandbox boundary changes, signing/appcast flows, and auth prompts need explicit review of validation, rollback, and user-confirmation behavior.

## Finding Quality Gate

Every finding needs the exact file:line, the specific input or state that triggers the bad outcome, a read of upstream callers and downstream consumers rather than the function in isolation, and a severity a senior reviewer would raise at that level in a real PR; missing any of these, drop it or downgrade it to advisory. Before calling a change a regression, read its commit message and author intent: a deliberate maintainer change is a decision, not a finding. Vague findings train the reader to ignore real ones.

**A clean review is a valid review.** Do not manufacture findings to justify the invocation. Zero findings with a stated review surface is a complete output. Padding the report with low-confidence noise is a worse outcome than reporting nothing.

**HIGH and CRITICAL** also need why existing guards (validation, type system, upstream catch, framework default) do not already prevent it. Cannot show that? Downgrade to MEDIUM, or drop. "This *might* break under some condition" is not a HIGH.

**Report shape.** Group findings by bug class, highest severity first, each class listing every same-class site with its file:line, then give the total; with none, write `no issues found` against the stated surface. Issues the diff did not introduce go in a separate `pre-existing` list and do not count toward the verdict.

**Rounds converge.** One task gets at most three review/fix rounds. From round two, review only the new diff plus the re-checks Autofix Routing requires, and never re-report a finding already reported. A third round that still finds new problems stops the patch loop: return to [Question the Approach](#question-the-approach-not-just-the-diff). A class that comes back in a second round or a second review is fixed at its source (lint, source gate, type, routed rule), not site by site.

## Knowledge Sync

If the diff introduces an invariant the project docs do not hold yet (a safety gate, a UI constraint, a release step, a cross-file sync requirement), it belongs in the narrowest tracked guidance every intended runtime reads, usually AGENTS.md. A review report or scorecard in the diff is evidence, not a durable doc: extract its stable rule instead of committing the snapshot. Apply a clear doc update as `safe_auto` or flag it as `doc debt`; with nothing new, sign-off says `doc debt: none`.

## Specialist Review (Standard and Deep only)

Load `references/persona-catalog.md` for activation, parallel or sequential review, and finding verification.

Before a whole-scope verdict, reconcile a completion ledger for every delegated review: assigned scope, returned status, and uncovered remainder. Wait for every active reviewer, or name its scope as unreviewed. Never say "all read", "full audit complete", or "no issues" while any reviewer or required verification is still pending.

## Autofix Routing

| Class | Definition | Action |
|-------|------------|--------|
| `safe_auto` | Unambiguous, risk-free: typos, missing imports, style inconsistencies | Apply only after explicit write authorization; otherwise report it |
| `gated_auto` | Behavior fixes with a clear intended result: null checks, error handling additions | Apply within explicit repair authorization; ask only for scope expansion or an unresolved user choice |
| `manual` | Architecture or security tradeoffs with no settled intended result | Resolve from project context; present any remaining user decision |
| `advisory` | Informational only | Note in sign-off |

Write authorization covers necessary fixes within its scope, including behavior changes needed for the requested result. A routing class does not create another approval step. In report-only mode, do not modify the worktree.

Any fix made during review invalidates the pre-fix verdict. Re-freeze the baseline, re-run the check that exposed the finding, refresh the sibling sweep, and complete the final adversarial pass required by the review depth before declaring ready.

## Adversarial Pass (Deep only)

Run the four attack angles in `references/persona-catalog.md`. Convergence from independent angles raises confidence; singleton findings face the same per-finding skeptic verification as specialist claims. Suppress findings below 0.60 confidence.

## Platform Operations

Derive the host CLI/API from public project docs; do not force GitHub commands onto other hosts, and confirm CI passes before merging. Poll CI as structured state, not streamed text: `gh run view <id> --json status,conclusion` (or the host's equivalent). Piping `gh run watch`, test output, or build output through `tail`/`head` swallows the real exit code and can report a failed or still-running run as green.

## Verification

Use the project's known verification command appropriate to the changed surface. Otherwise, `bash <skill-base-dir>/scripts/run-tests.sh` from the target project root can discover a candidate command. Report the exit status and summary, with relevant failure output rather than full passing logs.

A failed check needs diagnosis; no detected command is a discovery gap, not proof of failure or of no verification surface. Inspect project docs, manifests, and CI for an appropriate check. Complete a read-only review with explicit evidence limits when no check is available. Block a fix or readiness claim only when required evidence is missing or failing, and ask for a command only if it cannot be recovered from project context.

For bug fixes: a regression test that fails on the old code must exist before the fix is done, run red on that code (hunt's Regression guard rule). When the defect reached users or a published build and the project keeps an incident ledger, the same change adds its row; load `references/incident-ledger.md`. Establish expected behavior independently of the implementation: updating a snapshot does not prove it is correct. For agent instructions, keyword checks prove text retention only; behavior checks inspect tool actions and resulting files or artifacts, including forbidden side effects. Exercise a known-good and a known-bad case before relying on a new checker or a changed reviewer, and compare baseline and candidate under the same runtime and inputs; for a reviewer, the incident ledger's pre-fix code is the known-bad set and known-clean changes measure its noise.

In a dirty or multi-agent checkout, a passing local build or test run is not proof your change is sound: unrelated WIP already in the tree can supply missing symbols, mask a break, or fail for reasons unrelated to you. Verify in isolation -- `git worktree add --detach <known-good-commit>`, `git apply` only the diff of the files you own, then build/test there. The clean isolated pass is the real signal; the contaminated local pass is not.

## Gotchas

| What happened | Rule |
|---|---|
| New file name duplicated a locale, platform, or suffix convention | Check the target directory's existing naming convention before creating or renaming files |
| Deployed without provider runtime or env checks | Follow the project's public deployment docs and compare provider config with local required env and runtime settings |

## Sign-off

Open the final message with the `status` line as plain prose before any table or detail: exactly where the work stands now, with the hash, tag, or blocker. A verdict buried under verification tables reads as unfinished; the tables support the verdict, they do not replace it.

```
status:           [committed and pushed as <hash> / staged, not committed / released vX.Y.Z / blocked on <what>]
files changed:    N (+X -Y)
scope:            on target / drift: [what] / removable: [what]
user-visible delta: none / [entry, UI, copy, behavior added, removed, or changed]
review depth:     quick / standard / deep
risk tier:        [tier]: [gates], human review done / pending (only when a tier applies)
hard stops:       N found, N fixed, N deferred
sibling sweep:    N same-shape sites checked, N fixed / none found / not applicable
specialists:      [security, architecture] or none
new tests:        N
public actions:   replied #N, closed #N, reactions done / none pending
doc debt:         none / AGENTS.md needs X / rules need Y
verification:     [command] -> pass / fail
```

`public actions` lists every outward-facing step the task implied (issue replies, closures, release reactions) with its done or pending state; an external action the user has to ask about was not finished.

For a whole-scope or post-fix verdict, `scope` is backed by the frozen baseline and current inventory, not by the last patch viewed. For a ship action, the status line is incomplete until every currently authorized ledger item is `done`, `not applicable`, or `blocked` with evidence.

A turn that wrote files ends with the actual output of `git status --short --branch` and, when it pushed, the `status,conclusion` of the CI run for that sha; if either command was not run, the first line says which.
