# Waza Agent Guide

This file is the canonical agent guide for the Waza repository. `CLAUDE.md` is a symlink to it, so Claude Code and Codex see identical content. Edit this file; do not edit `CLAUDE.md`.

## Project

Waza is a skill collection for engineering workflows. The repository contains eight skills: `think`, `design`, `check`, `hunt`, `write`, `learn`, `read`, and `health`.

## Repository Map

- `VERSION` - single source of truth for the lock-step version. Every `SKILL.md` frontmatter, marketplace entry, README install URL, and installer `WAZA_REF` default must agree with this file.
- `skills/RESOLVER.md` - trigger and routing table for the skill set.
- `skills/*/SKILL.md` - individual skill entrypoints.
- `skills/*/agents/` - specialist reviewer or inspector prompts.
- `skills/*/references/` - supporting references loaded only when needed.
- `skills/*/scripts/` - deterministic helper scripts.
- `rules/` - shared writing and behavior rules used by install and validation flows. `rules/durable-context.md` is the shared Durable Context Preflight preamble; the six skills with optional memory context link to it from their own preflight section.
- `.claude-plugin/marketplace.json` - **generated**. Edit `VERSION` or per-skill `SKILL.md` frontmatter and run `make regenerate`; never hand-edit.
- `.agents/plugins/marketplace.json` - **generated** Codex repo marketplace. Points Codex at `plugins/waza` for plugin installs; never hand-edit.
- `plugins/waza/` - **generated** Codex plugin tree. Mirrors `skills/` and `rules/` plus `plugins/waza/.codex-plugin/plugin.json`; edit source files and run `make regenerate`.
- `packaging.allowlist` - default-deny list of paths that ship in `waza.zip`. New shippable assets must be added here explicitly; everything else is excluded.
- `.github/workflows/` - public test and release automation. `release.yml` runs `make test` before `make package` so the tagged commit is gated by the same suite as PRs.
- `scripts/build_metadata.py` - codegen for Claude and Codex marketplace metadata, README install URLs, Codex plugin mirror files, skill-local update checkers, installer-script `WAZA_REF` defaults, and update-checker `LOCAL_VERSION`. Run via `make regenerate`; CI checks drift via `make verify-generated`.
- `scripts/verify_skills.py` - the only validator entrypoint. Covers frontmatter, references, marketplace, resolver, links, table pipes, trigger overlap, rule-file presence, README install string, English coaching guard, and AI-attribution leak detection.
- `scripts/package-skill.sh` + `scripts/packaging_filter.py` - build `dist/waza.zip` from `packaging.allowlist`.
- `scripts/setup-rule.sh` + `scripts/setup-statusline.sh` - public install helpers; `WAZA_REF` defaults are codegen-pinned to the current release tag.
- `Makefile` - smoke discovery and packaging entrypoints. Adding a `tests/test_<name>.sh` file is enough to create a `smoke-<name>` target automatically.
- `tests/test_*.sh` - one smoke per surface; sources `tests/test_helpers.sh` for tmpdir / repo-copy / stub-curl factories.

## Commands

```bash
make test             # verify-docs + verify-generated + verify-routing + verify-scripts + all smokes
make regenerate       # rewrite marketplace.json, README install URLs, update checker copies
make verify-generated # drift check used by CI; non-zero if regenerate would change anything
make package          # build dist/waza.zip from packaging.allowlist
```

Run `make test` before meaningful changes to skill behavior, packaging, scripts, marketplace metadata, or anything generated. If you edited only frontmatter or VERSION, also run `make regenerate` and commit the resulting `.claude-plugin/marketplace.json` / `README.md` / installer changes together with your source edits.

## Skill Design Rules

Before adding a capability, decide the layer deliberately:

| Question | Yes | No |
|---|---|---|
| Does the user need judgment, adaptation, or follow-up questions? | Skill | Script or rule |
| Does the same input always produce the same output? | Script or rule | Skill |
| Is it a lookup, list, status check, or invariant check? | Script or rule | Skill |
| Does behavior shift with conversation context? | Skill | Script or rule |

Examples: `verify_skills.py` is a script; `rules/english.md` and `rules/chinese.md` are rules; `/think`, `/hunt`, `/check`, and `/health` are skills.

- Put adaptive, judgment-heavy workflows in skills.
- Put deterministic checks, lookups, and table-driven validation in scripts.
- `rules/anti-patterns.md` owns cross-skill always-on behavioral guardrails (AI failure modes that apply regardless of active skill). Per-skill gotchas stay in each `skills/*/SKILL.md` Gotchas table; a gotcha belongs in `rules/anti-patterns.md` only when it applies identically across all eight skills.
- Catalogs consolidate, they do not accumulate. This covers `rules/anti-patterns.md` rows and every reference example list, banned-phrase list, and replacement table (`skills/write/references/*`, `skills/design/references/*`, and the like). Before adding a row, pattern, banned phrase, or example, find the existing row or principle it instantiates and fold it in; never append a near-synonym or a third encoding of a rule already stated above. Keep wording generic enough to ship outside this repo. A reference file that re-lists items it already covers under a numbered pattern is drift, not coverage.
- The no-op test prunes skill prose sentence by sentence: a line earns its place only if it changes behavior versus the model's default. A line that re-teaches what a capable model already does (`be thorough` to an already-thorough agent) is a no-op you pay context load to say nothing; delete the whole sentence, do not trim words from it. When unsure whether a line states a default, assume it does and cut.
- Leading words collapse a restated quality into one pretrained token the model already thinks with: `fast, deterministic, low-overhead` becomes a `tight` loop; `a repro you trust` becomes the loop that goes `red` on the bug. One token anchors a whole region of behavior and gives a sharper hook than the spelled-out triad, at fewer tokens. When a skill states the same quality three times, that is the passage to collapse into a leading word.
- Keep `skills/RESOLVER.md` in sync when a skill description, trigger, or scope changes.
- Keep each `description` concrete enough for automatic routing.
- Write skill entrypoints outcome-first: name the target result, what counts as done, which constraints and evidence matter, and what the final answer or artifact should look like. Keep detailed process in mode sections and references.
- Keep all eight `SKILL.md` on one skeleton so they read as a set: a `🥷` first line and one-line tagline, then Outcome Contract, then Durable Context Preflight (right after it, for skills that read memory), then modes, the must-obey list, Gotchas, and Output. Use one name per concept across skills (`Hard Rules` for a skill's must-obey constraints; `Hard Stops` is check's separate merge-blocker list). Tables are compact `| a | b |` with no hand-aligned spacing; a numbered step sequence stays contiguous, with side-checks grouped under a step rather than wedged between two.
- Avoid broad skills that mix unrelated workflows.
- Eight skills is the hard cap. Do not propose a 9th skill or split an existing one. Behavior additions land in `references/`, `rules/`, `scripts/`, or `rules/anti-patterns.md`, not as a new skill.
- Keep generic programmer capabilities in Waza. Project-specific constraints should be extracted from public repository context or user-provided task context.
- Treat `code-review` as an invocation alias for Waza `check`, not as a separate generic skill.
- Waza `check` must remain project-aware without depending on unpublished local files. It extracts commands, generated artifacts, risk areas, and release rules from the target diff, public docs, manifests, CI config, and user-provided context.
- Keep distribution files self-contained for Claude Desktop and plugin installs. The release ZIP may inline sub-skill bodies into a generated root `SKILL.md`; source-of-truth skill content remains under `skills/*/SKILL.md`.
- If a `templates/` directory is added, keep reusable public scaffolds there and include it in packaging/validation rules deliberately.
- Keep the README short: a new reader should understand Waza in 30 seconds. Detailed rules belong in `skills/<name>/SKILL.md`, `rules/*.md`, or this file. Do not stack promotional sections at the top.

## Adding Or Changing A Skill

Use this path for any new skill or meaningful behavior change:

1. Create or update `skills/<name>/SKILL.md`; keep the description concrete, triggerable, and include a `Not for ...` exclusion. Frontmatter `metadata.version` must match the top-level `VERSION` file.
2. Update `skills/RESOLVER.md` routing rows so the new skill or changed scope is reachable; never hand-edit `.claude-plugin/marketplace.json` (run `make regenerate` instead).
3. Keep Waza public: extract project-specific details from public repo context at runtime instead of hardcoding private paths, credentials, or one-machine workflow.
4. Put deterministic enforcement in `scripts/` or `rules/`; keep only adaptive judgment in the skill body.
5. If the new skill ships a new top-level asset (new dir under root, new helper script the user needs), add the path to `packaging.allowlist`. Default behavior is exclusion.
6. Run `make regenerate` after frontmatter / VERSION edits, then `make test` and `make package` before release handoff.

## Maintainability Invariants

- Prefer generation over drift lint when the same metadata appears in multiple distribution files. `VERSION` and `skills/*/SKILL.md` frontmatter are the source of truth for generated marketplace and install metadata.
- Keep executable programs as real files, not heredocs inside shell scripts or Makefile recipes. Shell wrappers may delegate to Python helpers, but large logic belongs in importable `.py` files with `py_compile` coverage.
- Keep smoke tests in `tests/test_*.sh`; `Makefile` should discover and run them, not embed large test bodies.
- Avoid hidden runtime dependencies. If a script needs a non-stdlib Python package, external CLI, or network resolver, declare it in CI/docs and add a smoke test that fails without it.
- Shipped skill scripts (`skills/*/scripts/`) stay self-contained: they import only the standard library and run from an arbitrary target project. Do not extract their shared-looking helpers (file walks, parsers) into a root `scripts/` module. That module is dev/CI-only and not on `packaging.allowlist`, so importing it would couple a standalone shipped tool to the install layout and can break `npx skills add` installs. Benign duplication across two shipped scripts is the correct trade; if drift matters, align the copies in place rather than sharing a module.
- Installer scripts that fetch remote content must default to a release tag. Use `WAZA_REF=main` only as an explicit bleeding-edge override.
- One-off review reports, scorecards, or diagnostic snapshots do not belong in durable docs. Extract the stable rule into `AGENTS.md`, `CLAUDE.md`, `rules/`, `skills/*/references/`, or a verifier script, then drop the report.
- Project case studies are inputs, not Waza policy. Only promote the transferable workflow rule; keep project-specific commands, paths, release rituals, and safety constraints in that project's public context.
- Strip provenance when distilling a lesson. A rule earns its place by what it prevents, not by the incident it came from. Drop framing like "this came from a 615-line / 40k-char article" or "from one real review round"; keep the rule, lose the origin story. The metrics of the source artifact are never load-bearing.
- Self-governing files must be collapsed, not just appended to. When a file's own header forbids monotonic growth (for example `rules/anti-patterns.md` and `skills/write/references/write-zh.md`), enforce it: fold new specifics back into existing principles and delete re-indexes, rather than treating the header as decoration.
- Local-only instruction overlays are not durable source of truth. If a rule must guide future contributors or packaged agents, put it in tracked public docs or shipped skill/rule files.
- Local review and health checks must account for modified, staged, and untracked files. New helpers, tests, references, and packaging allowlists are part of the review surface before they are committed.
- Runtime install contracts are part of the source of truth for agent surfaces. Marketplace metadata, plugin manifests, generated mirrors, and package archives are not done until the installed path works in a clean environment.

## Distribution Rules

- `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `plugins/waza/.codex-plugin/plugin.json`, `skills/RESOLVER.md`, and every `skills/*/SKILL.md` must agree on skill names, descriptions, versions, and source paths.
- `npx skills add tw93/Waza` should install the eight direct coding skills by default. Do not add a source-root `SKILL.md`; it prevents nested skill discovery.
- Codex marketplace entries must resolve to `plugins/waza`, not the repository root. After Codex marketplace, plugin manifest, or plugin mirror changes, verify an isolated install flow rather than only checking JSON shape.
- Plugin mirror generation must filter local cache and noise files in both generator and verifier paths, including `__pycache__`, `*.pyc`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`, and `.DS_Store`.
- Claude Desktop uses the release ZIP built by `scripts/package-skill.sh`.
- `scripts/package-skill.sh` builds a public archive with exactly one generated root `SKILL.md`; nested `skills/*/SKILL.md` files are inlined for packaged installs.
- Do not make packaged skills resolve scripts or references through personal home-directory caches or machine paths. Resolve relative to the installed Waza directory.
- Rules under `rules/` are shared public behavior, not project-private memory.

## Verification

- Skill behavior changes: run `python3 scripts/verify_skills.py` and the relevant smoke target.
- Packaging changes: run `make package` and inspect the generated archive.
- Marketplace, resolver, or root dispatcher changes: run `python3 scripts/verify_skills.py` and confirm every marketplace source points at an existing skill directory. For Codex plugin changes, also run a clean install smoke such as `CODEX_HOME=$(mktemp -d) codex plugin marketplace add <repo>` followed by `codex plugin add waza@waza` and `codex plugin list`.
- Non-trivial diffs: run the review workflow before release handoff.
- Documentation-only changes: check internal links and command names.

## Commit And Release

- Commit convention: `{type}: {description}` where type is `feat`, `fix`, `refactor`, `docs`, or `chore`.
- Keep commits atomic. A commit touching more than ~20 files should split into packaging / docs / scripts / per-skill units, unless every file is the same codegen output from `make regenerate`.
- Release tags use lowercase `v{version}`.
- Rebuild packaged artifacts before publishing release assets. Run `make package` before publishing; CI should upload the ZIP on published releases.
- Before saying a Waza release is ready or done, separate the evidence layers: source diff, CI, generated metadata, package contents, GitHub release assets, npm registry/dist-tag state, and installed-runtime smoke. Missing layers are explicit gaps, not implied passes.
- After a GitHub release is published and assets are verified, add every positive release reaction with `gh api`: `+1`, `laugh`, `heart`, `hooray`, `rocket`, and `eyes`. Resolve the release id from the tag, POST each reaction to `repos/<owner>/<repo>/releases/<id>/reactions`, then re-read reactions to confirm them.
- **Never add the `-1` or `confused` reactions**. Those are negative signals; adding them to one's own release reads as self-deprecation. Only the six positive reactions above.

### Release title and body template

- Title: `V{version} {Codename} {emoji}`, e.g. `V3.8.0 Forge 🔨`.
- Body: Markdown with the structure below.

```markdown
<div align="center">
  <img src="..." width="120" />
  <h1>Waza V{version}</h1>
  <p><em>tagline</em></p>
</div>

### Changelog

1. **SkillName**: One sentence on what changed and its user effect.
2. ...

### 更新日志

1. **技能名**: 一句话说清楚改了什么以及对用户的影响。
2. ...

Update: `npx skills update -g -y` · [Claude Desktop](https://github.com/tw93/Waza/releases/latest/download/waza.zip) · ⭐ [tw93/Waza](https://github.com/tw93/Waza)
```

- Each item: `**Label**: one sentence`. Bold label is the skill or module name; the description leads with what changed.
- Style: engineer-facing, no marketing language. English and Chinese items must map one-to-one by number, 5 to 8 items total, one sentence each.
- Footer: update command + star + repo link, separated by `·`.
