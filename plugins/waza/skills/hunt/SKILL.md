---
name: hunt
description: "Finds root cause before applying fixes for errors, crashes, regressions, failing tests, broken behavior, and screenshot-reported defects. Use when users report in any language errors, crashes, broken behavior, regressions, failing tests, screenshot evidence, or something that used to work and now fails. Not for code review or new features."
when_to_use: "排查, 查查, 报错, 崩溃, 不工作, 不对, 跑不通, 以前是好的, 回归, 截图回归, 判断错误原因, 判断为什么报错, 反复修不好, debug, regression, used to work, broke after update, why broken, not working, what's wrong, fix error, stack trace"
dispatch_intent: "Error, crash, regression, screenshot-reported defect, test failure, stale cache, runtime boundary, why broken"
---

# Hunt: Diagnose Before You Fix

Prefix your first line with 🥷 inline, not as its own paragraph.

A patch applied to a symptom creates a new bug somewhere else.

## Outcome Contract

- Outcome: the root cause is identified before any fix is applied.
- Done when: one sentence explains the cause, every observed symptom fits it, and the fix or handoff is verified against a reproducible check.
- Evidence: source trace, repro command or UI path, logs or state, targeted test/build output, and runtime evidence for UI or native defects.
- Output: root cause, fix or handoff, verification result, and any unswept sibling risks.

**Do not touch code until you can state the root cause in one sentence:**
> "I believe the root cause is [X] because [evidence]."

Name a specific file, function, line, or condition. "A state management issue" is not testable. "Stale cache in `useUser` at `src/hooks/user.ts:42` because the dependency array is missing `userId`" is testable. If you cannot be that specific, you do not have a hypothesis yet.

## Diagnosis Signals

Hypothesis quality gate: the hypothesis must explain every observable symptom, not just the one reported first; partial coverage is a symptom-level guess, not a root cause. For timing-dependent issues (flicker, intermittent failure, race), reproduce reliably before diagnosing.

Rationalization smells: "I'll just try this" = no hypothesis, write it first. "I'm confident" = run the instrument that proves it. "Probably the same issue" = re-read the execution path from scratch. "It works on my machine" = enumerate env differences before dismissing. "One more restart" = read the last error verbatim; never restart more than twice without new evidence.

## Durable Context Preflight

See [references/durable-context.md](references/durable-context.md) for when to read durable context, the read-order budget, and the memory-type mapping.

For `/hunt`: durable context is hypothesis fuel only, and current code, logs, and repro evidence override memory. It never replaces a fresh root-cause sentence or a reproducible symptom list.

## Hard Rules

- **Same symptom after a fix is a hard stop; so is "let me just try this."** Both mean the hypothesis is unfinished. Re-read the execution path from scratch before touching code again.
- **After three failed hypotheses, stop.** Use the Handoff format below to surface what was checked, what was ruled out, and what is unknown. Ask how to proceed.
- **Verify before claiming.** Never state versions, function names, or file locations from memory. Run `sw_vers` / `node --version` / grep first. No results = re-examine the path.
- **External tool failure: diagnose before switching.** When an MCP tool or API fails, determine why first (server running? API key valid? Config correct?) before trying an alternative.
- **System/tooling symptoms need a lower-layer baseline.** Before blaming the visible app, generated file, or top-level feature, measure the raw lower layer first: OS capture versus post-processing, runtime service versus UI, compiler/toolchain versus test assertion, network/API versus client handling. Retire hypotheses that the baseline disproves instead of circling them.
- **Pay attention to deflection.** When someone says "that part doesn't matter," treat it as a signal. The area someone avoids examining is often where the problem lives.
- **Visual/rendering bugs: static analysis first.** Trace paint layers, stacking contexts, and layer order in DevTools before adding console.log or visual debug overlays. Logs cannot capture what the compositor does. Only add instrumentation after static analysis fails.
- **Behavioral / lifecycle / async bugs: instrument first, not after failure.** Window lifecycle, event delivery, navigation, focus, timer, state-machine, and async-ordering bugs almost never yield to static reading alone. Do not wait for a failed fix to add logs. The moment your hypothesis involves "this callback fires before/after that one", "this state should be X when Y runs", or "this object should still be alive here", **add the log immediately as part of forming the hypothesis**, before writing any fix. A hypothesis without runtime evidence is a guess; two guesses in a row is the hard-stop signal. Distinguish from visual-rendering bugs (compositor behavior needs DevTools, not logs) and pure-logic bugs (wrong formula, off-by-one) where static analysis is sufficient.
- **Tuning magic numbers past round three: stop, unify.** When a spacing / sizing / threshold value has been adjusted three times and still looks wrong, the bug is structural, not numeric. Replace the N independent values with one named token (`Spacing.s4`, `--gap-content`, etc.) and verify the asymmetry was hiding a missing constraint. Asymmetry that survives tuning is structural; more tuning will not converge.
- **Performance complaints need numbers.** For "slow", "laggy", or memory-growth reports outside Native App Freeze Mode, measure the baseline first (wall-clock time, profile sample, memory footprint), fix, then re-measure and report before/after numbers. "Feels faster" is not evidence.
- **Fix the cause, not the symptom.** If the fix touches more than 5 files, pause and confirm scope with the user.

## Fix Scope Discipline

If the bug genuinely needs a refactor first (e.g. the cause cannot be addressed without changing a shared interface), pause, name the refactor explicitly, and ask. Do not silently bundle it. A bug fix that grew into a refactor is a separate PR.

## Bisect Mode

Activate when: "以前是好的", "之前是好的", "used to work", "上一次提交还是对的", "broke after update", or the user remembers a specific good commit or version.

- Protect the user's worktree first: `git status --short --branch -uall`. Any modified, staged, or untracked files mean no bisect in the current checkout: run it in a temporary detached worktree and remove that worktree when done. If a temporary worktree is impossible, stop and ask for explicit cleanup/stash approval.
- If the last-good version is only a few releases back, `git diff <last-good>..HEAD -- <suspect path>` and read the delta first. The regression is usually visible there at a fraction of a bisect's cost; fall through to bisect only when the diff is too large or the culprit is not obvious.
- Bisect only with a non-interactive pass/fail command defined up front, and keep the bookkeeping in git (`git bisect good/bad`), including when you test a suspect commit directly. When it names the culprit, read only that diff down to the specific line, then run `git bisect reset` before removing the temporary worktree.

## Repeated Regression / Screenshot Reference Mode

Activate when the user says the same issue is still wrong after a fix, provides a "good" screenshot/version/file, or describes a visual result as previously correct.

Treat the reference as evidence, not decoration: list every reported and visible symptom in the user's concrete words ("still slow", "尖刺", "先显示上一个内容"); identify the reference oracle (last-good commit, old build, fixture, screenshot, described expected state); define the pass/fail check before editing; then name the exact current-vs-reference delta. Do not generalize a visual defect into "style polish" when the evidence points to a broken render, race, font pipeline, or state path. If the same symptom survives one attempted fix, stop and rebuild the hypothesis from the evidence; do not stack patches onto a disproven explanation.

If the issue is purely subjective UI taste, route to `/ui`. If it is rendering, state, timing, build output, font generation, or a regression from a known-good version, stay in `/hunt`.

## Scope Blast Mode

Activate after fixing a root-cause pattern, before declaring the bug done; also when the user says "举一反三", "举一反三深入看看", or "其他地方有没有同样问题". The same shape often hides in N other places; one local fix that ignores the blast leaves N - 1 bugs in the tree.

Extract the pattern signature (the specific function, regex, API call, CSS selector, lock acquisition, validation skip, or input boundary that produced the bug) and `grep -rn` it across the repo, excluding generated dirs, build output, and vendored deps; for class-of-bug patterns ("any handler missing the lock"), grep the surrounding shape, not just the literal text. For every match, answer in writing: same bug / safe to leave (why) / unsure (ask the user). Do not silently skip a match, and do not claim "fixed" until the blast report is in the Output block. Unrelated bugs the sweep surfaces get listed, not fixed in this PR, unless the user agrees.

## Confirm or Discard

Run the one probe that would fail if the hypothesis were wrong, then read it. If the evidence contradicts the hypothesis, discard it completely and re-orient on what the probe just showed. Do not stack a fix onto a disproven hypothesis, and do not keep one just because the code "looks like" the cause.

## Runtime Evidence Ladder

Use this ladder before claiming a bug is fixed:

1. Source trace: name the exact function, state transition, file, line, or condition that can produce the symptom.
2. Deterministic repro: run or write the smallest command, fixture, UI path, or scenario that produces it.
3. Logs/state/cache: inspect the runtime state that proves the path was reached, including queues, DB rows, caches, temp files, generated outputs, or external tool logs.
4. Build/test: run the narrow test or build that exercises the fix.
5. Real runtime check: for UI, native app, browser, rendering, or visual bugs, open the app/page/artifact and verify the visible result with a screenshot or concrete checklist.

Compile-only is not enough for UI, native-app, visual, rendering, or generated-artifact bugs. If the runtime check is impossible in the environment, say why and hand off the exact screen, command, or artifact to verify.

For recurring classes of failures, load `references/failure-patterns.md` before adding a second fix.

## Native App Freeze Mode

Activate when a desktop or mobile native app reports beachball, not responding, tab-switch freeze, first-open lag, idle wake stall, overlay lockup, or a screenshot shows a frozen app.

Evidence to collect before changing code:

1. Exact user path and version: first launch versus warm launch, the tab or window transition, idle duration, permissions, display count, and any setting that makes the freeze disappear.
2. Runtime capture while frozen: `sample <process>`, recent app logs, CPU and memory footprint, thread count, and whether the main thread is blocked, spinning, or allocating.
3. First-frame surface: view body work, first `.task`, synchronous icon or metadata lookup, filesystem scans, URL parent walks, notification callbacks, and app/window wake handlers.
4. Blast search after the fix: grep the same API shape across the repo, especially path parent walks, synchronous icon loading, metadata reads in render paths, and callbacks that run on the main thread.

Common native freeze traps:

- Launch, terminate, permission, audio, display, or workspace notifications doing path walks, icon lookup, filesystem scans, or process enumeration on the main thread.
- First paint hydrating a full app list, directory tree, media thumbnail set, or system status table before showing an interactive shell.
- An input-lock or full-screen overlay without a guaranteed teardown path for Escape, app deactivation, permission denial, process termination, and window close.
- Timer or sampler work that survives hidden windows, long idle periods, sleep/wake, or app reactivation.

Compile-only and source-only checks are insufficient for this mode. The outcome must include the runtime capture, the root-cause frame or state transition, the focused regression guard, and any sibling matches that were fixed or explicitly left safe.

## Targeted Logging

Every log is a yes/no question: "if this prints X before Y, hypothesis A survives; otherwise A is dead." A log that cannot rule a hypothesis in or out is noise. Remove temporary logs before finishing; gate persistent diagnostics behind the project's debug flag. If adding a log changes the behavior, that is itself evidence of a timing, lifecycle, or concurrency problem. Full playbook: `references/logging-techniques.md`.

## Gotchas

| What happened | Rule |
|---------------|------|
| Patched client pane instead of local pane | Trace the execution path backward before touching any file |
| MCP not loading, switched tools instead of diagnosing | Check server status, API key, config before switching methods |
| Blamed the visible app before measuring the raw system/tooling layer | Measure the lower layer first, then retire ruled-out hypotheses explicitly |
| Orchestrator said RUNNING but TTS vendor was misconfigured | In multi-stage pipelines, test each stage in isolation |
| Race condition diagnosed as a stale-state bug | For timing-sensitive issues, inspect event timestamps and ordering before state |
| Added logs everywhere and still could not explain the bug | Rewrite each log as a yes/no question. Delete logs that do not rule a hypothesis in or out |
| Reproduced locally but failed in CI | Align the environment first (runtime version, env vars, timezone), then chase the code |
| Stack trace points deep into a library | Walk back 3 frames into your own code; the bug is almost always there, not in the dependency |
| Worked when launched from app, broke when opened via file association / drag-drop / deep link / external proxy | Reproduce using the exact entry point the user described. App-internal init differs from cold-launch-with-file init; state may not be ready when the document arrives. |
| Build passed but UI still looked wrong | Move up the Runtime Evidence Ladder and verify the real rendered surface or artifact. |
| Fix matched the reporter's setup but changed nothing for everyone else, or regressed the default | A defect report is evidence, not the full scope. State whether the fix changes the default experience for all users or only the reporter's configuration, and prefer fixing the default path. |
| Broke after toggling theme / mode / locale, fine after restart | State not re-applied on the toggle path. Trace the toggle's recompute or invalidation route first; do not tune styles pixel by pixel while the state path is broken. |
| Changed the algorithm but the output stayed wrong | The reader may be hitting persisted output written by the old code (scan results, analysis cache, snapshot with a TTL). Changing generated-then-persisted data requires invalidating or version-bumping the old cache in the same change; before re-diagnosing, confirm the runtime is not reading stale data. |
| Reporter reproduces, local machine is fine, agent patched blind | Produce one copy-paste diagnostic command first (single command, silent collection, one output file, a privacy note), diagnose from the returned evidence, then fix. |

## Rendering Bug Mode

Activate when: "PDF looks wrong", "page break issue", "font not rendering", broken PDF output, or print layout wrong.

Load `references/rendering-debug.md` for the full diagnosis checklist (WeasyPrint quirks, font loading, page overflow, browser print CSS). Static analysis first, then reproduce if needed.

## IME / Unicode Issues

For input method, character rendering, or text encoding bugs (IME state, cursor drift, emoji splitting, composition events), check `references/ime-unicode.md` first before forming a hypothesis.

## Output

### Success Format

Open the wrap-up with one plain line stating the outcome and whether the changes are committed; the block below supports that line, it does not replace it.

```
Root cause:        [what was wrong, file:line]
Fix:               [what changed, file:line]
Sibling sweep:     [N same-shape sites checked, N fixed / none found / not run, why]
Confirmed:         [evidence or test that proves the fix]
Tests:             [pass/fail count, regression test location]
Regression guard:  [test file:line] or [none, reason]
```

Status: **resolved**, **resolved with caveats** (state them), or **blocked** (state what is unknown).

**Regression guard rule**: for any bug that recurred or was previously "fixed", the fix is not done until:
1. A regression test exists that fails on the unfixed code and passes on the fixed code.
2. The test lives in the project's test suite, not a temporary file.
3. The commit message states why the bug recurred and why this fix prevents it.

### Handoff Format (after 3 failed hypotheses)

```
Symptom:
[Original error description, one sentence]

Hypotheses Tested:
1. [Hypothesis 1] → [Test method] → [Result: ruled out because...]
2. [Hypothesis 2] → [Test method] → [Result: ruled out because...]
3. [Hypothesis 3] → [Test method] → [Result: ruled out because...]

Evidence Collected:
- [Log snippets / stack traces / file content]
- [Reproduction steps]
- [Environment info: versions, config, runtime]

Ruled Out:
- [Root causes that have been eliminated]

Unknowns:
- [What is still unclear]
- [What information is missing]

Suggested Next Steps:
1. [Next investigation direction]
2. [External tools or permissions that may be needed]
3. [Additional context the user should provide]
```

Status: **blocked**
