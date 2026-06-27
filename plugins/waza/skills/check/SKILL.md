---
name: check
description: "Reviews code diffs, PRs, issue queues, release readiness, commits, pushes, publishing, and project audits. Use when users ask in any language for code review, issue or PR triage, release gates, publishing follow-through, or project audits. Not for debugging root causes or prose review."
when_to_use: "review, 看看代码, 检查一下, 有没有问题, 是否需要优化, 合并前, 继续优化, 优化代码, 看看issue, 看看PR, release, publish, push, release reaction, GitHub reaction, 发布, 提交, 关闭issue, 发布表情, release表情, close issue, issue close, review my code, check changes, before merge, before release, code review, code-review, audit, project audit, 项目体检, 项目评分, 给项目打分, 深入分析项目代码, 评估项目质量, 代码质量评分, scorecard, linus review, rate this codebase, score this project"
dispatch_intent: "Code review, before merge, release gates, generated artifacts, safety sinks, publish/push/reaction follow-through, triage issues/PRs, project-wide code-quality audit scorecard"
---

# Check: Review Before You Ship

Prefix your first line with 🥷 inline, not as its own paragraph.

**Update check (non-blocking).** Before starting, run `bash scripts/check-update.sh` once; if it prints a line, relay it to the user, then continue. It runs at most once a day, only reads a public version file, sends no data, and fails silently.

> Note: `/review` is a built-in Anthropic plugin command for PR review. Waza uses `/check` (or the alias `code-review`) instead. Do not re-trigger `/review` from within this skill.

Read the diff, find the problems, fix what can be fixed safely, ask about the rest. Done means verification ran in this session and passed.

## Outcome Contract

- Outcome: a review, release decision, or maintainer action grounded in the current diff, project context, and live evidence.
- Done when: findings, fixes, shipped state, or blockers are stated with the commands, artifacts, or remote state that prove them.
- Evidence: worktree status, diff, public project docs, manifests, CI, package contents, release or registry state, and current command output.
- Output: concise findings first, then verification and shipped-state summary when applicable.

## Worktree Safety Preflight

Before any review, triage, ship, release, or PR operation, read the current worktree with:

```bash
git status --short --branch -uall
```

Treat modified, staged, and untracked files as user work. You may read them and include them in the review surface, but you must not move, hide, overwrite, clean, or discard them without explicit user approval in the current turn.

Do not run these commands as default review or PR setup: `git switch`, `git checkout`, `git reset --hard`, `git clean`, `git stash -u`, `git stash --include-untracked`, `git stash -a`, `git stash --all`, or `gh pr checkout`. If a branch change or cleanup is genuinely required, stop and ask for that exact operation.

Do not "protect" user work by moving untracked files, generated files, screenshots, or local scratch files into `/tmp` or another holding directory. Moving someone else's WIP out of the checkout is the same class of interference as stashing it. If a clean tree is required for generation, packaging, or verification, use a separate worktree from a known commit and copy only the artifact or patch you own back into the current checkout.

For commit or push follow-through in a dirty or multi-agent checkout, record `git rev-parse HEAD` before staging. Re-read `git status --short --branch -uall` and `git rev-parse HEAD` immediately before commit and again before push. If HEAD moved, unknown commits appeared, or the worktree changed outside your intended files, stop and report the mismatch instead of rebasing, recommitting, or pushing.

For PR inspection, prefer commands that do not switch the current working tree: `gh pr view`, `gh pr diff`, `git fetch origin pull/<n>/head:refs/tmp/pr-<n>`, and `git merge-tree`.

## Mode Picker

Pick the mode that matches the user's intent, then read that section in full. Modes layer on top of the shared review surface (Scope, Hard Stops, Autofix, Specialist Review, Verification, Sign-off) further down.

| User intent | Mode |
|---|---|
| "implement this plan", `/think` output handed off | [Plan Execution](#plan-execution-mode) |
| Diff or PR ready, "review", "看看代码", "合并前" | Default review (start at [Get the Diff](#get-the-diff)) |
| "look at issues", "review PRs", "triage", "批量处理" | [Triage Mode](#triage-mode) |
| "is this worth a release", "值不值得发版" | [Release Worthiness Analysis](#release-worthiness-analysis) |
| "commit", "push", "publish", "release", "close issue", "发布表情" | [Ship / Release Follow-through](#ship--release-follow-through) |
| "audit", "项目体检", "项目评分", "给项目打分", "深入分析项目代码", "scorecard", "linus review" | [Project Audit](#project-audit-mode) |
| Document, PDF, prose review | Delegate to `/write` (see [Document Review](#document-review)) |

Before any mode, run [Project Context Extraction](#project-context-extraction) and (if memory is in scope) [Durable Context Preflight](#durable-context-preflight).

## Project Context Extraction

This is Waza's public, standalone code-review capability. It should not depend on private machine paths or unpublished project instructions.

Before reviewing, extract project constraints from repository context:

1. Read the diff and identify changed languages, frameworks, manifests, generated outputs, release files, and CI workflows.
2. Inspect public project files only as needed: README, AGENTS/CLAUDE instructions when present, package manifests, lockfiles, build configs, test configs, workflow files, and release notes.
3. Compress the findings into review context: verification commands, protected or generated files, release artifacts, domain risks, and public reply rules.
4. Apply the stricter rule when project context and this skill overlap.
5. If project docs or CI name a verification command, prefer that over auto-detection.

For the context shape, see `references/project-context.md`.

For release or maintainer work, also fill the Release Gate 2.0 matrix from `references/project-context.md`. It covers review base, dirty/staged/untracked state, latest tag, origin sync, version fields, generated artifacts, package/archive contents, release assets, registry/appcast/CI, and public issue/PR state. Missing matrix evidence is a blocker for a "ready to release" claim.

## Durable Context Preflight

See [rules/durable-context.md](../../rules/durable-context.md) for when to read durable context, the read-order budget, and the memory-type mapping.

For `/check`, private task constraints are `decision`, `preference`, and `principle` entries; review checklists are `pattern` and `learning`. Current code, diff, public docs, CI, tests, and remote state override memory. Durable memory can explain user intent and preferred follow-through, but public project rules still come from README files, manifests, CI workflows, release docs, the diff, and explicit instructions in the current thread. Never cite private memory as a public project requirement.

## Plan Execution Mode

Activate when the user's message starts with "Implement the following plan", "按计划实施", "按照计划", "整", "可以干", "直接改" followed by a plan body, or links to a `/think` output.

In this mode, do not run a code review. Instead:

1. State which plan is being executed (first heading or summary line).
2. Check for obvious repo drift: run `git status --short --branch -uall` and skim any changed files that contradict the plan. If drift makes the plan unsafe, name the specific conflict and stop.
3. Work through each plan item as a to-do. Mark each complete as you go.
4. After all items are done, run the project's verification command.
5. Transition automatically into Ship mode if the project context or current thread indicates review-then-ship.

## Default Continuation (review-then-ship)

When the project's `AGENTS.md` or the current thread explicitly asks to "commit after review", "ship if green", or equivalent, transition directly from review to the Ship flow after a clean review. Do not ask again. State "proceeding to ship" before acting.

## Get the Diff

Get the full diff between the current branch and the base branch. If unclear, ask. If already on the base branch, ask which commits to review.

## Triage Mode

Activate when the user mentions: issue, PR, "review all", triage, "batch", or "批量处理". Skip the diff flow and run this instead.

**Action-first rule:** Items with a clear disposition (already fixed, duplicate, already released) get acted on immediately without analysis paragraphs. When analyzing screenshots or images, state what you see and the suggested action in one message. Only ask the user when the disposition is genuinely ambiguous.

**Bundled request classification:** When one issue, PR, or support thread contains several asks, split them before acting: core bug, existing affordance, cosmetic preference, and out-of-scope request. Fix or close only the validated core bug; answer existing affordances with the current path; defer or decline cosmetic and out-of-scope asks instead of treating the whole report as a to-do list.

**Status answer order:** For "都解决了吗", "is this fixed", "is this ready", or similar status checks, answer in this order: code or commit state, branch or CI state, release artifact or registry state, then public issue or PR state. Do not collapse fixed-on-main, available in pre-release, next stable release, and already shipped.

**Flow:** First identify the project's issue/PR host from public context. For GitHub projects, pull open items with `gh issue list -R <repo> --state open --limit 20` and `gh pr list -R <repo> --state open`. For non-GitHub projects, use the platform CLI/API named by the project docs or user request; if none exists, stop and report the missing integration instead of pretending GitHub commands apply. For each item, check current state with the project's release boundary: latest public release, main branch, preview/nightly/beta channel, registry/appcast, and target issue/PR status. If the fix is already in the current public release or documented pre-release channel, close with that exact upgrade path. If fixed on `main` but unreleased, reply "已修复，等下一个版本 release" and close only when project convention or the current user request allows fixed-on-main closure; otherwise leave it open with the next-release note. If no fix exists, analyze and act. Fix now if possible (`fix: closes #N` commit); for valid-but-unreleased items acknowledge and leave open; for invalid items give one-two sentence reason and close.

Before final conclusions in a live queue, refresh the issue/PR list once more and re-read any item that changed during the run. If evidence is incomplete, hold the item instead of closing it on a guess.

**PR handling:** If the PR direction is accepted but the patch needs changes, prefer pushing the maintainer's fixes to the contributor's PR branch and then merging the PR. Check `maintainerCanModify` first, then confirm the push remote, target branch, and current HEAD immediately before pushing so you do not overwrite contributor work or push maintainer fixes to the wrong repository. If branch edits are not allowed, ask the contributor to enable maintainer edits or push the needed revision; only fall back to a separate maintainer commit when timing or release safety requires it, and say so in the PR. Close without merging only when the direction is rejected, unsafe, no longer needed, or explicitly not part of the project's scope. Do not silently absorb an accepted PR into `main` and close it.

**Public reply shape:** load `references/public-reply.md` for the full template (mention, single thanks, factual paragraphs, next-release step, editing rules, closure criteria). Ship Mode uses the same template; the file is the single source.

**Sign-off line (append to standard sign-off):**
```
triage:           N reviewed, N closed, N deferred
```

## Release Worthiness Analysis

Activate when the user asks "深入分析 X 是不是值得发新版本", "is this worth a new release", "值不值得发版", or similar.

1. Run `git log <last-tag>..HEAD --oneline` (find last tag with `git tag --sort=-version:refname | head -1`).
2. Count and classify commits: feat (new feature), fix (bug fix), chore/docs/refactor (internal).
3. Output:
   - **Commit summary**: N feat, N fix, N chore since last release
   - **Verdict**: release / skip (one line)
   - **Recommended version bump**: patch (fixes only), minor (feat present), major (breaking change)
   - **Key risk**: one sentence on the biggest risk in this batch
4. If verdict is "release", offer to transition into Ship mode.

## Ship / Release Follow-through

Activate when the user asks to commit, tag, release, publish, push, reply on an issue/PR, or close an issue after a change is ready.

This mode extends review; it does not skip review. Before any public or irreversible action:

1. Extract release rules from public project context: README, manifests, CI workflows, release notes, package scripts, changelogs, and explicit user instructions in the current thread.
2. Fill the Release Gate 2.0 matrix from `references/project-context.md`: review base, dirty/staged/untracked state, latest tag, origin sync, version fields, generated artifacts, package/archive contents, release assets, registry/appcast/CI, and public issue/PR state.
3. Verify generated or bundled outputs, version fields, release notes, package contents, and required artifacts are in sync. Prefer dry-run commands when the ecosystem provides them.
   Generated deliverables include tracked archives, ignored dist files, appcasts, site/download copy, registry packages, checksums, and release assets. If project docs require them, regenerate, inspect, and stage or upload them explicitly even when they are ignored by git; do not infer readiness from source-only tests. For remote assets, prefer downloading or reading back the published artifact and comparing entries, checksums, or manifest contents; release page text, file size, or workflow success alone is not artifact proof.
   If the project has preview, beta, nightly, stable, or App Store lanes, name the lane explicitly. Do not use a preview or beta artifact to claim stable release readiness, and do not touch stable appcast, registry, or download surfaces when the requested lane is preview-only unless project docs require it.
4. Commit only intended files. Preserve unrelated dirty work, serialize git operations so index locks or overlapping adds do not corrupt the workflow, and re-check HEAD/status before pushing so concurrent agent or maintainer commits are not swept into your ship action.
5. Push, publish, tag, or create a release only when the user has explicitly approved that action. If auth, OTP, CI, registry, or network state blocks the operation, pause and report the exact blocker.
6. For issue/PR follow-through, confirm the item identity with the host's read command before posting. On GitHub, use `gh issue view` or `gh pr view`; on other hosts, use the CLI/API named by project docs or the current request. Use `references/public-reply.md` for the maintainer reply template (mention, single thanks, facts, explicit next release or verification step) and its closure criteria.
7. For GitHub release reaction follow-through, only do it when project context or the current thread asks for it. After the release exists and required assets are verified, resolve the release id from the tag, POST every positive release reaction to `repos/<owner>/<repo>/releases/<id>/reactions` with `gh api` or the available GitHub tool, and re-read reactions to confirm. Positive release reactions are `+1`, `laugh`, `heart`, `hooray`, `rocket`, and `eyes`.
8. After network or API failures, re-read the end state instead of assuming success or failure.

### Reworked Or Cancelled Release Gate

Activate this gate when a release candidate was cancelled, a preview or beta had repeated bug-fix churn, or the user asks whether a delayed release is finally safe.

1. Lock the review base to the last public stable tag or release artifact, then review through current `HEAD`. Do not limit the review to recent commits or the latest local diff.
2. Record the exact base, `HEAD`, dirty state, origin sync, version fields, generated artifacts, release notes, package contents, CI, and remote distribution state. If any state changes mid-review, refresh the range and rerun the fast gates.
3. Review by shipped risk surface: user-reported regressions, crash or hang paths, destructive operations, privilege or permission boundaries, background workers, startup or first-frame work, update feeds, package contents, and public support claims.
4. Output two release decisions, not one: whether the preview or beta can keep taking user testing, and whether stable release prep can start.
5. Every conclusion must name blockers, deferrable maintenance, commands that ran, and runtime or user-smoke coverage. Source tests alone cannot prove a reworked UI/native release ready.

End with the concrete shipped state: commit hash, tag, release URL, registry/version result, pushed branch, release asset state, release reaction state, issue/PR state, and any remaining blockers. Omit fields that do not apply.

## Project Audit Mode

Activate when the user asks for a project-wide code-quality scorecard: "audit", "项目体检", "代码质量评分", "scorecard", "linus 风格 review". Distinct from Default Review (PR/diff scoped) and Triage (issue batching). Single-pass project-wide quality assessment.

**Flow**

1. Run `python3 <waza>/skills/check/scripts/audit_signals.py --root <project>` from the target repo. The script emits labelled blocks (`=== FILE SIZE HOTSPOTS ===` ... `=== DENYLIST IN BUILD ===`) each ending with `status: PASS|WARN|FAIL|N/A`.
2. Skim the largest source files surfaced by `FILE SIZE HOTSPOTS` (typically 3-5; stop sooner if the architecture is already clear).
3. Read `CLAUDE.md` / `AGENTS.md` / `README.md` to learn the project's own stated conventions before judging it against generic ones.
4. Apply the four-axis rubric below. Each axis is independently scored 0-10. Overall = arithmetic mean.
5. Surface 3-7 concrete findings per axis. Each finding: file:line citation when possible, severity (CRIT/STRUCT/INCR), one-line fix.
6. Output to **terminal only**. Do not create files in the target repo. If the user follows up with "save it", offer `./docs/<project>-audit.md` then; default is ephemeral.

**Rubric**

| Axis | What it covers |
|---|---|
| Architecture | Module boundaries, coupling, abstraction layers vs flat duplication, single source of truth |
| Code Quality | File size discipline, dedup, readability, comments on non-obvious behavior |
| Engineering | Tests, CI gates, version coordination, install URL pinning, packaging posture |
| Perf and Risk | Hazards, scope creep, distribution risk, privacy posture, third-party blast radius |

**Scoring anchors**

- 9-10: exceptional discipline, polish-only items
- 7-8.5: solid with clear targeted improvements
- 5-7: working but with structural debt
- below 5: significant rework recommended

A WARN that the project has explicitly justified (in its own docs or a comment) is not a finding; cite the justification and skip. Do not mechanically convert WARN to CRIT. A block with `status: N/A` means the surface does not exist (e.g. no packaging script); treat as silence, not as a positive signal.

**Output template (terminal)**

```
Project: <name>
Overall: X.X / 10

Architecture: X / 10 -- one-line summary
Code Quality: X / 10 -- one-line summary
Engineering:  X / 10 -- one-line summary
Perf & Risk:  X / 10 -- one-line summary

Findings
[CRIT] <file:line> -- <issue>
       why: <reason grounded in signal or read>
       fix: <concrete action>
[STRUCT] ...
[INCR] ...

Top 3 highest-leverage moves
1. ...
2. ...
3. ...
```

Stop after the report unless the user asks for follow-up implementation. Audit mode does not modify files in the target repo.

## Scope

Measure the diff and classify depth:

| Depth | Criteria | Reviewers |
|-------|----------|-----------|
| **Quick** | Under 100 lines, 1-5 files | Base review only |
| **Standard** | 100-500 lines, or 6-10 files | Base + conditional specialists |
| **Deep** | 500+ lines, 10+ files, or touches auth/payments/data mutation | Base + all specialists + adversarial pass |

State the depth before proceeding.

Static content diffs can stay quick even when they touch several generated files: version strings, dates, release-copy mirrors, sitemap dates, or one-for-one localization copy changes usually need line-by-line readback plus grep consistency, not a specialist fleet. Escalate only when the diff changes logic, generation rules, public distribution behavior, or user-facing semantics beyond the literal text replacement.

## Did We Build What Was Asked?

Before reading code, check scope drift: do the diff and the stated goal match? Label: **on target** / **drift** / **incomplete**.

Also check surgical traceability: every changed file and every new public surface must trace back to the user's stated goal. If a file, dependency, config knob, abstraction, generated artifact, workflow permission, or release behavior cannot be explained in one sentence from the request, label it drift until proven necessary.

Drift signals (examples, not exhaustive -- any one is enough to label drift):
- A changed file has no connection to the stated goal
- The diff includes pure refactoring (renames, formatting, restructuring) when the goal was a bug fix or feature
- A new dependency appears that the goal did not mention
- Code unrelated to the goal was deleted or commented out
- A new abstraction or helper was introduced that is not required by the goal
- A maintainability, review, or cleanup change quietly adds user-visible UI, default config, workflow permissions, or release behavior

## Pattern-Fix Completeness

When the diff fixes one instance of a class-of-bug (a missing validation, a wrong selector, an off-by-one, a missing lock), the same shape often lives elsewhere. Extract the pattern signature, `grep -rn` it across the repo (exclude generated dirs), and confirm sibling instances were also handled. List any unswept sibling: flag it as a hard stop when it carries the same risk, advisory when lower-risk. For a deeper sweep playbook, see hunt's Scope Blast Mode.

## Testability Seam For Recurring Bugs

When the diff fixes a visual, layout, timing, or stateful-UI bug that has recurred (the same area broke before, or the fix reads as "tune a number until it looks right"), a code change alone will let the regression return: the logic is entangled with mutable render or UI state, so there is nowhere to assert on it. Flag the fix as incomplete unless it pulls the decision into a pure function -- inputs in, value out, no mutable receiver -- and unit-tests the invariant that was violated (a width never collapses to zero, a hit region stays half-open, an offset stays in bounds). "Verified by running the app" confirms this one instance; only a pinned invariant stops the next one. Reserve this for classes that recur or that runtime checks cannot see; do not demand a seam for one-off logic that already has straightforward coverage. If no honest seam exists -- the only place to assert is past a shallow interface that never exercises the real failure at the call site -- do not fake a hollow test to satisfy the gate. Record "no correct test seam" as an architectural finding and surface it: the missing seam is the actual defect.

## CLI Command Surface

When a diff touches a CLI entrypoint, installer, completion, config/env handling, package wrapper, or a mutating command such as cleanup, update, uninstall, migration, or cache removal, fill the CLI Command Surface from `references/project-context.md` before sign-off.

Check command contract and installed-runtime behavior, not just library tests: help/version, subcommands/flags, exit codes, stdout/stderr, JSON/schema output, TTY/non-interactive paths, env/config precedence, shebang/executable bit, PATH shim, and package-manager install path when applicable.

For mutating CLI commands, also run the Safety Sink Review: dry-run or confirmation path, operation log or rollback story, retry/idempotency, signal/partial-failure handling, and test-mode guards for auth prompts or real system changes. For cleanup, uninstall, prune, reset, or cache-removal commands, add two checks before approval: can a normal user verify each selected item is safe, and is the deleted content locally rebuildable rather than a downloaded dependency or user data? If either answer is no, require narrower matching, explicit user selection, or leave the item visible but non-destructive.

## Skill, Plugin, And Packaged Install Surface

When a diff touches a skill, plugin, marketplace entry, installer, package allowlist, package manifest, generated mirror, or published archive, verify the installed runtime contract, not just the source tree:

1. Identify the install path a real user will get: package manager, release archive, marketplace entry, plugin source path, or installer script default ref.
2. Build or regenerate the package exactly as project docs require, then inspect the archive or generated mirror for every new script, reference, template, rule, manifest, and executable bit.
3. Run an isolated install smoke when the surface is installable: fresh temp home/config/cache, add the marketplace or package, install the skill or plugin, list it, and invoke the smallest command or entrypoint that proves scripts and references resolve from the installed path.
4. Filter generated mirrors and archives for cache/noise files such as `__pycache__`, `*.pyc`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, `.DS_Store`, local logs, and screenshots unless the project explicitly ships them.
5. If network, auth, or host tooling prevents the install smoke, state the missing layer as a blocker or gap. Do not replace installed-runtime proof with manifest JSON, source tests, or a successful local import.

## Hard Stops (fix before merging)

Examples, not exhaustive -- flag any diff that could cause irreversible harm if merged unreviewed.

- **No unverified claims.** Do not write "I verified X", "I ran Y", "tests pass", or "this fixes Z" unless the shell output is in this turn's transcript. If you reason about behavior without running, say "based on reading the code" instead of "I verified". Every verification claim in the sign-off must point to a command that actually ran in this session.
- **Re-read before citing source-of-truth facts.** Before writing a line number, dirty-file count, branch ahead/behind state, fallback behavior, locale coverage, or release artifact state into a handoff or review report, re-read the source in this turn (`git status`, `git diff`, file `Read`, `rg`, command output). Earlier chat context, prior agent's notes, and your own recall from a hundred turns ago are stale by default; restating "the catalog uses en fallback" or "the file is at line 310" without checking has been the recurring failure mode in long sessions. Cite the verification path inline (`per current Read of <file>` / `per `git status` this turn`) so reviewers know which facts are anchored.
- **String-matching on captured output?** When a diff branches on, greps, or classifies an error message or command output, verify what that string actually holds at runtime before approving. A subprocess spawned with `stdio: 'inherit'` (or any uncaptured pipe) streams its diagnostics to the terminal, not into `error.message` -- which then contains only the command line. Such a matcher silently matches the command, not the output: it can pass tests, fire on the wrong token, or be dead in production while looking correct. Probe the real `error.message` (a one-line repro) instead of assuming, and prefer driving behavior off a structured fact the caller already holds (build target, exit code) over re-parsing a string.
- **Magic-wait coupling**: a fixed `sleep`, `asyncAfter`, `setTimeout`, or "should be enough" timeout standing in for an unobserved async completion, or an animation, poll, or progress step tied to a frame count or fixed duration rather than wall-clock state. It passes on the author's machine and breaks on a slow CPU, a 120Hz display, or a proxied network. Flag it: drive the next step off the real completion signal (callback, navigation-done, frame-changed, state flag), and keep timing machine- and frame-rate-independent.
- **Destructive auto-execution**: any task marked "safe" or "auto-run" that modifies user-visible state (history files, config, preferences, installed software) must require explicit confirmation.
- **Release artifacts missing**: verify every artifact listed in release notes, release templates, or project workflows exists and has been uploaded before declaring done.
- **Generated artifact drift**: if source changes require generated or bundled outputs, verify the output was regenerated and included.
- **Verifier failure layer unclear**: if a verifier fails before assertions or due to missing optional dependencies, bootstrap noise, transient build-service crashes, unavailable simulators, or tool setup, classify setup versus product failure. Retry only with new evidence or a narrower environment. Do not call the repo broken until the intended test body or artifact check actually ran. The inverse is the same stop: a verifier that passes without running the real path -- a skipped optional-dependency job that still prints OK, a function that early-returns leaving output empty so a true-on-empty assertion passes, a render reported fixed but never opened -- is a hollow green. A pass counts only when at least one non-skipped, non-empty case exercised the path and the assertions fail on emptiness.
- **Tracked package omissions**: if a package script builds from tracked files, allowlists, or generated manifests, verify every new helper module, reference file, template, or script used by the diff is tracked and present in the built archive before sign-off.
- **Manifest-only install proof**: if a diff changes a skill, plugin, installer, marketplace entry, package wrapper, or installable archive, metadata and source tests are not enough. Build or install through the real user path in an isolated environment, or mark the install/runtime layer unverified.
- **Version skew**: release version fields across manifests, package metadata, app configs, changelogs, tags, or lockfiles must stay synchronized.
- **Unknown identifiers in diff**: any function, variable, or type introduced in the diff that does not exist in the codebase is a hard stop. Grep before writing or approving any reference: `grep -r "name" .` -- no results outside the diff = does not exist.
- **Dead-code or YAGNI deletion without proof**: any "zero callers" or "unused" claim must be checked across the whole repository, including top-level entrypoints, docs, tests, generated dispatch tables, scripts, CI, and dynamic lookup patterns. Treat sub-agent or tool reports as leads, not proof. Before deleting, batch-grep all candidates, classify test-only references separately from production references, and chase written variables or data tables that may become orphaned together. If the grep scope is partial, do not delete.
- **Injection and validation**: SQL, command, path injection at system entry points. Credentials hardcoded, logged, committed, or copied into public docs.
- **Dependency changes**: unexpected additions or version bumps in package.json, Cargo.toml, go.mod, requirements.txt. Flag any new dependency not obviously required by the diff.
- **Safety sinks**: destructive file operations, shell or AppleScript construction, cwd/path/symlink traversal, approval or sandbox boundary changes, signing/appcast flows, and auth prompts need explicit review of validation, rollback, and user-confirmation behavior.
- **Audit before restore**: when the diff re-adds a symbol, string, asset, or config field that recent history removed, grep the rest of the diff and the main branch to confirm anything still uses it. A rule file that names the symbol is not proof of life. If only a parity test references it, the rule is stale and the restore is wrong; reject the restore and flag the stale rule. Specifically suspicious: re-adding an enum case, xcstrings entry, dictionary key, or asset file that the prior commit deleted intentionally.
- **Intentional-divergence normalized**: a surface that deliberately breaks a house pattern -- omits a shared step, takes a conditional path the siblings avoid, leaves an asymmetry -- to dodge a known defect, then a later cleanup pass "tidies" it back into uniformity and reintroduces the bug. Before unifying an outlier to match its siblings, read the comment or commit that created it and confirm the defect it prevents survives your change.
- **AI-generated PR with broad matchers in destructive sinks**: any PR that introduces `find`-like recursion, mass-delete, sandbox/container traversal, ID-prefix wildcards, or fallback regex branches feeding a destructive sink, and was likely AI-generated, must be reviewed line-by-line for three things: matcher breadth in every branch (fallback paths often regress to broad globs even when the primary branch is correct), protected-path coverage (does the existing guard list include this new entry point?), and whether the change bypasses an existing user-confirmation step. Generic plausibility is not safety. When in doubt, ask the contributor to narrow the matcher to an exact constant (exact bundle ID, exact app name, exact path), not a prefix or wildcard; do not approve "this looks fine."
- **Migration code for features that did not ship before**: reject migration scaffolding, version-gated defaults, or "carry old key forward" logic when the underlying preference / schema / feature was introduced in this same release. `git show v<last-release>:<path>` is the gate: if the key is absent from the last tag, no migration is needed; ship the default. Migration code added for a never-shipped key is dead-on-arrival complexity.

## Finding Quality Gate

Before writing any finding into the report, run this gate:

**Pre-report self-check (four questions, every finding must pass):**
1. Can I cite the exact file:line?
2. Can I describe the specific input or state that triggers the bad outcome?
3. Have I read the upstream callers / downstream consumers, not just the function in isolation?
4. Is the severity defensible? Would a senior reviewer raise this at this level in a real PR?

If any answer is "no", drop the finding or downgrade it to advisory. Vague findings train the reader to ignore real ones.

**A clean review is a valid review.** Do not manufacture findings to justify the invocation. Zero findings with a stated review surface is a complete output. Padding the report with low-confidence noise is a worse outcome than reporting nothing.

**HIGH and CRITICAL require three pieces of evidence:**
1. The exact file:line where the bug lives.
2. The specific trigger: what input, state, or sequence produces the bad outcome.
3. Why existing guards (validation, type system, upstream catch, framework default) do not already prevent it.

Cannot supply all three? Downgrade to MEDIUM, or drop. "This *might* break under some condition" is not a HIGH.

## Knowledge Sync

After reviewing the diff, check whether it introduces invariants not yet captured in project docs:

- New safety gate or path-guard rule → AGENTS.md
- New UI constraint (layout rule, animation, overlay registration) → `.claude/rules/*.md`
- New deploy/release step or artifact → AGENTS.md or `docs/`
- New cross-file sync requirement (enum ↔ HTML anchors, Swift keys ↔ xcstrings) → AGENTS.md
- One-off review reports or diagnostic snapshots should not become durable docs as-is; extract the stable rule into AGENTS/CLAUDE/rules/references and drop the stale report from the commit.

### Snapshot Report Routing

Treat review reports, scorecards, and diagnostic snapshots as evidence, not as source-of-truth docs. Before approving one:

1. Re-read the current diff or repo surface named by the report. If the claim is stale, exclude the report from the commit or rewrite it into a stable rule.
2. Keep project-specific commands, paths, protected areas, release rituals, and safety constraints in that project's public context. Do not promote them into Waza.
3. Promote only transferable review behavior into Waza: e.g. "check untracked files before readiness", "inspect generated package contents", or "turn one-off reports into invariants."

If found, either apply the doc update as `safe_auto` (when the invariant is clear from the diff) or flag it in the sign-off as `doc debt`. When no new invariants exist, sign-off says `doc debt: none`.

## Specialist Review (Standard and Deep only)

Load `references/persona-catalog.md` to determine which specialists activate. Launch all activated specialists in parallel via the environment's agent or sub-agent facility when available, passing the full diff. If no parallel reviewer facility exists, run the specialist passes sequentially in the same session.

Merge findings: when two specialists flag the same code location, keep the higher severity and note cross-reviewer agreement. Findings on different code locations are never duplicates even if they share a theme.

Treat each specialist finding as a claim to verify, not a fact to act on. Before routing a finding to Autofix or sign-off, re-read the cited code this turn and confirm it is real and live: not already handled elsewhere, not consistent-by-design, not a latent-only risk labeled as a live bug. Parallel reviewers over-report from name-based inference and partial context; drop or downgrade what dissolves on direct read, and cite the verification path.

## Autofix Routing

| Class | Definition | Action |
|-------|------------|--------|
| `safe_auto` | Unambiguous, risk-free: typos, missing imports, style inconsistencies | Apply immediately |
| `gated_auto` | Likely correct but changes behavior: null checks, error handling additions | Batch into one user confirmation block |
| `manual` | Requires judgment: architecture, behavior changes, security tradeoffs | Present in sign-off |
| `advisory` | Informational only | Note in sign-off |

Apply all `safe_auto` fixes first. Batch all `gated_auto` into one confirmation block. Never ask separately about each one.

## Adversarial Pass (Deep only)

"If I were trying to break this system through this specific diff, what would I exploit?" Four angles (see `references/persona-catalog.md`): assumption violation, composition failures, cascade construction, abuse cases. Suppress findings below 0.60 confidence.

## Platform Operations

Use the platform tool that matches the project. For GitHub projects, prefer `gh` or the available GitHub integration and confirm CI passes before merging. For non-GitHub projects, derive the CLI/API from public project docs or the user's explicit platform context; do not force GitHub commands onto other hosts.

## Verification

Run `bash scripts/run-tests.sh` from this skill directory, or the project's known verification command from the target repository. Paste the full output.

If the script exits non-zero or prints `(no test command detected)`: halt. Do not claim done. Ask the user for the verification command before proceeding. If the user also cannot provide one, document this explicitly in the sign-off as `verification: none -- no command available` and flag it as a structural gap, not a pass.

For bug fixes: a regression test that fails on the old code must exist before the fix is done.

In a dirty or multi-agent checkout, a passing local build or test run is not proof your change is sound: unrelated WIP already in the tree can supply missing symbols, mask a break, or fail for reasons unrelated to you. Verify in isolation -- `git worktree add --detach <known-good-commit>`, `git apply` only the diff of the files you own, then build/test there. The clean isolated pass is the real signal; the contaminated local pass is not.

## Gotchas

| What happened | Rule |
|---------------|------|
| Posted a public reply to the wrong issue or PR thread | Re-read the target with `gh issue view N` or `gh pr view N` and confirm title, author, and current state before acting |
| PR comment sounded like a report | 1-2 sentences, natural, like a colleague. Not structured, not AI-sounding. |
| PR comment used bullet points | Write as short paragraphs, one thought per paragraph; thank the contributor first |
| New file name duplicated a locale, platform, or suffix convention | Check the target directory's existing naming convention before creating or renaming files |
| Deployed without provider runtime or env checks | Follow the project's public deployment docs and compare provider config with local required env and runtime settings |
| Push failed from auth mismatch | Check `git remote -v`, current branch, and auth identity before the first push in a new project |

## Document Review

For document, PDF, white paper, or prose review, route to `/write` (Document Review Mode). `/check` handles code diffs and release artifacts only.

## Sign-off

```
files changed:    N (+X -Y)
scope:            on target / drift: [what]
review depth:     quick / standard / deep
hard stops:       N found, N fixed, N deferred
specialists:      [security, architecture] or none
new tests:        N
doc debt:         none / AGENTS.md needs X / rules need Y
verification:     [command] -> pass / fail
```
