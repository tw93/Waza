# Release Worthiness And Ship Follow-through

Loaded from `check` Mode Picker for "is this worth a release" and for commit / push / publish / tag / issue-closure follow-through. Ship extends review; it does not replace it.

## Release Worthiness Analysis

Activate when the user asks "深入分析 X 是不是值得发新版本", "is this worth a new release", "值不值得发版", or similar.

Classify every commit since the last published tag (the tag is the baseline, not a local VERSION file), then output:

- **Commit summary**: N feat, N fix, N chore since last release
- **Verdict**: release / skip (one line)
- **Recommended version bump**: patch (fixes only), minor (feat present), major (breaking change)
- **Key risk**: one sentence on the biggest risk in this batch

If the verdict is "release", offer to transition into Ship mode.

## Ship / Release Follow-through

Activate when the user asks to commit, tag, release, publish, push, reply on an issue/PR, or close an issue after a change is ready.

Treat an explicitly authorized chain such as review, fix, verify, commit, push, and public follow-through as one delivery ledger. Do not return control between its internal stages while safe authorized work remains. A local commit is not completion when push was included, and a no-op push is not completion when intended local changes remain uncommitted. Do not create an empty commit when the intended scope is already clean; prove the clean/up-to-date state instead.

This mode extends review; it does not skip review. Select every delivery surface the authorized request covers before running gates, and apply the union of their steps:

- **Commit/push:** inspect the intended diff, run its required checks, synchronize tracked generated outputs, and follow steps 4-5. Verify the remote SHA and relevant CI after push. Do not require a tag, release notes, registry publication, or uploaded assets unless the change or project rules make them part of this task.
- **Release readiness, packaging, or publication:** apply steps 1-3, then the authorized delivery steps.
- **Public replies, issue closure, or reactions:** apply the matching steps 6-7 against the actual delivery channel. Commit/push authorization alone does not authorize these actions.

Apply only the steps of the selected surfaces; step 8 applies whenever a network or API operation fails:

1. Extract release rules from public project context: README, manifests, CI workflows, release notes, package scripts, changelogs, and explicit user instructions in the current thread.
2. Fill the Release Gate 2.0 matrix from `references/project-context.md`. Seed the deterministic rows with `python3 <skill-base-dir>/scripts/release_gate.py --root <project>` (worktree state, remote sync, tag baseline, version field sync, changelog mention) and paste its status lines as evidence; the remaining rows (generated artifacts, package/archive contents, release assets, registry/appcast/CI, public issue/PR state) stay judgment calls with their own evidence.
3. Verify generated or bundled outputs, version fields, release notes, package contents, and required artifacts are in sync. Prefer dry-run commands when the ecosystem provides them. When drafting release notes or update-feed copy, follow `/write` and its release-note mode; for Chinese copy, load its zh release-notes rules before the first draft, not after a tone complaint -- translation-flavored Chinese notes are a defect, not a polish item.
   Before drafting release notes, read the repo's previous published release (`gh release view` the latest tag) and preserve its title convention, per-item length, and language layout. Treat its item count as history, not a target: use the smallest complete set of distinct user outcomes in the candidate artifact.
   Generated deliverables include tracked archives, ignored dist files, appcasts, site/download copy, registry packages, checksums, and release assets. If project docs require them, regenerate, inspect, and stage or upload them explicitly even when they are ignored by git; do not infer readiness from source-only tests. For remote assets, prefer downloading or reading back the published artifact and comparing entries, checksums, or manifest contents; release page text, file size, or workflow success alone is not artifact proof.
   If the project has preview, beta, nightly, stable, or App Store lanes, name the lane explicitly. Do not use a preview or beta artifact to claim stable release readiness, and do not touch stable appcast, registry, or download surfaces when the requested lane is preview-only unless project docs require it.
   Classify each change by deployment surface before concluding what is live: code that ships inside a packaged artifact (app binary, bundled CLI, release archive) reaches users only at the next release, while sites, serverless functions, CDN config, and infrastructure deploy automatically when the default branch updates. One batch of changes can be unreleased on the first surface and already in production on the second; state each surface separately instead of letting "not released yet" cover auto-deployed code.
4. Commit only intended files under the Worktree Safety Preflight in `SKILL.md`, and serialize git operations so index locks or overlapping adds do not corrupt the workflow. In a dirty or multi-agent checkout, record `git rev-parse HEAD` before staging, then re-read `git status --short --branch -uall` and `git rev-parse HEAD` immediately before commit and again before push. If HEAD moved, unknown commits appeared, or the worktree changed outside your intended files, stop and report the mismatch instead of rebasing, recommitting, or pushing.
5. Push, publish, tag, or create a release only when the user has explicitly approved that action. Before the first push in a project, check `git remote -v`, the current branch, and the authenticated identity; when the user names an exact account, verify the authenticated service identity immediately before the first remote write and stop on mismatch; never substitute another account silently. If auth, OTP, CI, registry, or network state blocks the operation, pause and report the exact blocker.
6. For issue/PR follow-through, confirm the item identity with the host's read command before posting. On GitHub, use `gh issue view` or `gh pr view`; on other hosts, use the CLI/API named by project docs or the current request. Use `references/public-reply.md` for posting, editing, read-back, and closure criteria; the reply body follows `/write` Public Reply Mode.
7. For GitHub release reaction follow-through, only do it when project context or the current thread asks for it. After the release exists and required assets are verified, resolve the release id from the tag, POST every positive release reaction to `repos/<owner>/<repo>/releases/<id>/reactions` with `gh api` or the available GitHub tool, and re-read reactions to confirm. Positive release reactions are `+1`, `laugh`, `heart`, `hooray`, `rocket`, and `eyes`.
8. After network or API failures, re-read the end state instead of assuming success or failure. For an at-most-once operation (publish, tag, release create, payment), a verification timeout is unknown, not failed: a registry can gate a successful upload behind a scan that delays visibility for tens of minutes. Use bounded read-only checks within the project's retry policy; if visibility remains unknown, report the exact unresolved state and stop. Never re-run the publish to make the check pass.

Before handoff, reconcile every authorized item as `done`, `not applicable`, or `blocked`, then re-read the local `HEAD`, target remote ref/SHA, worktree status, CI or published artifact lane, and any public thread changed in this run. Never collapse source, CI, package, deployed channel, and public-thread state into one "done" claim.

### Reworked Or Cancelled Release Gate

Activate this gate when a release candidate was cancelled, a preview or beta had repeated bug-fix churn, or the user asks whether a delayed release is finally safe. Load `references/release-surfaces.md` (Reworked Or Cancelled Release Gate): review from the last public stable tag through `HEAD` by shipped risk surface, and output two decisions, whether the preview keeps taking user testing and whether stable release prep can start.

Lead the verdict with an explicit go / no-go (ship, or the named blockers), then the concrete shipped state: commit hash, tag, release URL, registry/version result, pushed branch, release asset state, release reaction state, issue/PR state, and any remaining blockers. Omit fields that do not apply.
