# Prune Mode

Load when the user asks to slim, prune, or trim agent guidance: global rules, user or project skills, `AGENTS.md` / `CLAUDE.md`, path-scoped rules, the memory index. The target is less context in every session with no lost constraint and no lost capability. When those pull apart, the order is: constraint kept > right layer > fewer words. Most bloat is guidance loaded at the wrong time, not guidance that should not exist.

## Outcome

- A ledger with one row per passage or group of lines: `file:line`, action (`fix`, `delete`, `move`, `edit`, `keep`), destination for a move, and the reason. Unverifiable usage, untestable behavior, and out-of-scope surfaces go in a separate gaps list.
- Always-loaded size before, and the estimate after, from the collector's `STARTUP CONTEXT ESTIMATE` (`local_agents_*`, `local_claude_*`, `rules_*`, `skill_desc_*`) and `PATH-SCOPED CONTEXT`, plus the memory index. In a project prune, `global:` rules and machine-wide skills are reported once as out of scope, not as ledger rows.
- Report-only until the user confirms the ledger. The repair phase applies only confirmed rows and ends with the checks under Moving and verifying.

## Inventory

- Separate what loads every session from what loads on demand. A file that is always present costs more than a larger one that loads rarely.
- Judge skill usage from real invocation records, never a name grep: the injected skill list contains every name. Freshly installed with zero calls is not unused. No records is a gap, not evidence.

## Decide each passage

- `fix` comes first and carries the least risk: a reference to a file, command, or option that no longer exists, two passages that contradict, a line that calls itself obsolete, a tool usage the vendor has changed. Check against current code and official docs, not memory.
- `delete` when removing it would not change behavior: defaults a capable model follows anyway (read before editing, run the tests, handle edge cases). A descriptive line often carries a constraint inside it ("never writes into `~/.config`", "uploads no user content", "stays silent on failure"); the description can go, the clause stays, because the code shows what it does, not what it must never do. A paragraph is judged clause by clause: keeping one trap from it does not license dropping the licensing or safety clause beside it.
- A rule that limits what the agent may touch or bundle is not a default, however generic it reads: files outside the repository need the change shown and confirmed first, and a user-visible change (UI, config field, default, permission) does not ride inside a cleanup patch. When unsure, keep it, or compare a clean session without the guidance. A one-step quiz proves knowledge, not retention over a long session, and a probe the task never triggers is no evidence.
- `keep` what the model cannot guess: user preferences, rejected approaches and why, product tradeoffs, machine and environment facts, and silent traps (exit 0 with an empty or wrong result, or expected behavior that looks like a failure, such as a first build that takes ten minutes). A loud trap with a clear error needs no always-on rule; at most a fix hint where the error surfaces.
- One-way doors are never compressed: deleting or moving user data, money, publishing, privilege, rewriting pushed history. Move them whole with the wording untouched, or keep them.
- Keep the cause, drop the story. "Because this loses data" stays; incident narrative, dates, and the size of the source artifact go. A dated maintainer mark (`(maintainer 2026-11-08)`) or a decision id (`D281`) is the authority a rule rests on, not story, and stays. A one-off report, scorecard, or diagnostic snapshot is evidence: extract the stable rule, then drop the report.

## Decide placement

| Content | Layer |
|---|---|
| Hard constraint across projects | global rules |
| Reusable workflow that needs judgment or follow-up | skill |
| Project commands, paths, release steps | project guide |
| Same input, same output: lookup, status, validation | script or hook |

- A lower layer restating a higher one is a `delete` only for the runtimes that load that higher layer; a project rule that repeats a global one stays when Cursor or another runtime that never reads the global file works in the project. One fact stored in several files is generated from one source or kept once.
- A sentence that also appears on a published surface (a site page, README, package listing, generated copy of the skill) is user-facing copy, not guidance: grep the whole tree, generated mirrors included, and leave its wording to the user.
- Keep one project guide. On Claude Code a root `CLAUDE.md` switches the project off `AGENTS.md`, nested guides included; when Claude-only lines are needed, a `CLAUDE.md` that starts with `@AGENTS.md`. This is version-dependent: confirm with the load probe below.
- The root keeps what a conversation can trigger without reading any file (commit, publish, reply, delete), because a path rule loads only when a matching file is read. For a release, the red lines and the entry point stay at the root and the parameters travel with the scripts.
- A move needs a destination that loads on its own: a path rule, or a nested `AGENTS.md`, which Claude Code (without a root `CLAUDE.md`), Codex, and Cursor read when they work in that folder. A file under `docs/` loads only when an agent opens it, so moving guidance there leaves a root line that names when to read it.
- `.claude/rules` with `paths:` reach Claude Code only. When Codex, Cursor, or another runtime that reads `AGENTS.md` is in use, a must-follow rule stays in the root `AGENTS.md` or a nested `AGENTS.md`, and a nested guide inside a deployed or packaged folder ships with it.
- A skill body carries what every run needs. Mutually exclusive modes and detail only some runs need move to `references/`, reached from a line that names the trigger. A description says what, when, and `Not for`; synonym lists and multilingual triggers stay out of it, since every session pays for it.

## Rewrite what stays

- Target over route: the outcome, what counts as done, the evidence, the output. A step is route when removing it lets the model reach the same result another way; keep it when the order is the constraint (verify before publish, confirm before delete).
- A quality restated three times collapses into one leading word the model already thinks with.
- Name the smell with a NO/OK pair instead of stating a `be X` goal. A new catalog row folds into the principle it instantiates; one name per concept.
- A text instruction of the form "read X before doing Y" is followed unreliably; it becomes a hook that injects X when Y happens. Injected context can arrive with the tool result, so an irreversible action is refused on its first attempt with the rule as the reason.

## Moving and verifying

- Move before compress. Rewriting is where constraints get lost while every mechanical gate stays green; a whole-line move keeps the wording.
- After the repair, run `python3 <skill-base-dir>/scripts/check_moved_lines.py <base-rev>` from the project root (`--include GLOB` for a destination outside the default instruction paths). Every missing line must match a confirmed `delete` or `edit` row.
- Re-run the collector: `path_rules_matching_nothing` must be 0, and each source file that deletes, moves, or uploads user data must still match the rule that governs it in `largest_effective_paths` or a direct selector check.
- After a split, grep the tree for the old file's name: pointers that still send readers to the old home go stale silently.
- Over-deletion audit, once the prune is committed: list what vanished with `check_moved_lines.py <base-rev> --head <prune-rev>` (one run per prune commit) and hand only that list and the repository to a reviewer that did not write the prune. For each lost line the reviewer greps the key nouns, not the sentence, in the current tree, flags it only when the meaning survives nowhere, and a flagged line is restored verbatim from the base revision.
- A new or moved file is checked against the publish scope: deployed site folders, package `files`, packaging allowlists.
- The load probe starts sessions, so it needs authorization: put a sentinel line in the moved file, ask a fresh session for it after reading a matching file, and once after a non-matching file. Then run one real task and the past failures the rules exist for, and hand the diff to a reviewer that did not write it.
