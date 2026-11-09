# Project Review Context Template

Use this template to compress repository context before running Waza `/check`. The context must come from public project files, the diff, CI configuration, or explicit user instructions. Do not depend on private machine paths or unpublished project instructions.

## What Belongs In Project Context

The template below names most of it. Also capture:

- Protected files and directories.
- Packaging source of truth: whether archives are built from `git ls-files`, explicit allowlists, generated manifests, or source directories.
- Delivery surfaces: whether generated outputs are tracked, ignored, external release assets, registry uploads, appcasts, installer metadata, checksums, or site/download copy; how they are regenerated, inspected, staged, or uploaded.
- Runtime dependencies introduced by the diff: Python packages, CLIs, network services, package managers, or platform tools that are not already declared in CI/docs.
- Domain-specific safety rules.
- Known CI or test flakes documented by the project and how to distinguish them from real failures.

## What Does Not Belong In Public Context

- Credential paths, private key filenames, passwords, tokens, or secret values.
- Maintainer-only machine paths.
- One-off personal preferences that do not affect project behavior.
- One-off review reports, scorecards, or diagnostic snapshots copied as guidance instead of distilled into stable project rules.
- Raw memory, chat excerpts, screenshots, private support details, local paths, project-specific commands, issue/PR numbers, release tags, or commit hashes from another project.
- Full copies of Waza `/check` sections.

## Recommended Context Shape

```markdown
## Project Commands

- Format: `<command>`
- Fast check: `<command>`
- Full verification: `<command>`

## CLI Command Surface

- Entrypoints: `<command or bin>`.
- Command contract: help/version, subcommands, flags, exit codes, stdout/stderr, JSON/schema output.
- Runtime shape: TTY vs non-interactive behavior, env/config precedence, completion/manpage or shell integration.
- Install/run proof: built package, temp prefix, PATH shim, shebang/executable bit, or package-manager path checked with `<command>`.
- Mutating commands: dry-run/confirmation, operation log, rollback/retry behavior, signal/partial-failure handling.

## Skill Or Plugin Install Surface

- User install path: `<package manager / release archive / marketplace entry / plugin id / installer script>`.
- Source path and generated mirror: `<source dir>` -> `<installed dir>`.
- Package/archive inclusion: new scripts, references, templates, rules, manifests, and executable bits checked with `<command>`.
- Isolated install smoke: fresh temp home/config/cache plus `<install command>` and `<list or invoke command>`.
- Noise filtering: cache files, local logs, screenshots, and temp outputs excluded or intentionally shipped.

## Project Hard Stops

- Do not modify `<protected path>` unless explicitly requested.
- If `<artifact>` is generated from `<source>`, verify it was regenerated.
- If `<artifact>` is ignored by git but required for release, verify the regeneration and force-stage, upload, or registry publish path named by the project.
- If `<package script>` builds from tracked files or an allowlist, verify newly introduced helpers, references, templates, and scripts are included in `<archive>`.
- If an installer fetches remote content, verify the default ref is pinned to a release tag or checksum-protected; floating `main` must be an explicit override.
- If a helper introduces a non-stdlib package or external CLI, verify CI installs it or the helper fails with a clear setup path.
- If `<artifact>` is listed in release notes, verify it exists before sign-off.

## Project-Specific Risks

- `<risk>`: `<how to inspect it>`

## Public Replies

See `public-reply.md` for posting, edit-or-new-comment, read-back, and closure criteria; the reply body follows `/write` Public Reply Mode. Do not restate the rules here.

## Release Follow-through

- Version fields to check: `<manifest>`, `<app config>`, `<lockfile>`.
- Generated artifacts to check: `<artifact>` from `<source>`.
- Distribution lane: `<preview/beta/nightly/stable/etc.>` and which public surfaces it is allowed to touch.
- Dry-run command before publishing: `<command>`.
- Remote asset proof: `<download/readback command>` that checks content, manifest, digest, appcast, or registry state.
- GitHub release reactions to add after asset verification: `<+1/laugh/heart/hooray/rocket/eyes or none>`.
- Public state to re-read after publishing or closing: `<registry/release/issue URL or command>`.
```

Keep this context brief. It should guide the review, not replace the review method.

## Release Gate 2.0 Matrix

Fill this before claiming a change is release-ready. Use "n/a" only when the project clearly has no such surface.

| Surface | Evidence |
|---|---|
| Review base | Base branch, latest tag, and commit range reviewed |
| Worktree state | Dirty, staged, and untracked files accounted for |
| Remote state | `origin/main` or release branch sync checked |
| Version fields | Manifest, app config, changelog, appcast, and lockfile versions aligned |
| Distribution lane | Preview, beta, nightly, stable, registry, or app-store lane named, with unrelated lanes left untouched |
| Runtime dependencies | Newly introduced Python packages, CLIs, package managers, and network tools declared and available in CI |
| Generated artifacts | Tracked archives, ignored dist outputs, bundled/minified files, appcasts, installer metadata, checksums, and site/download copy regenerated or proven not needed |
| Package/archive contents | Built package inspected for required files, newly introduced helpers/references, and missing extras |
| Installed runtime | Package, skill, plugin, CLI, or marketplace install exercised from a clean environment when the diff changes installable surfaces |
| Release assets | GitHub release, appcast, download archive, checksum, or installer assets downloaded or read back and verified beyond page text or file size |
| Registry/appcast | npm/crates/Homebrew/appcast/App Store or equivalent state re-read after publish |
| CI status | Latest required checks passed or blocker named |
| Issue/PR state | Target issue or PR re-read before commenting, closing, merging, or saying shipped |

## Safety Sink Review

Any diff that touches one of these sinks needs explicit validation and rollback thinking:

- Deleting, moving, or overwriting user files, caches, history, preferences, or generated outputs.
- Building shell, AppleScript, SQL, URL, or filesystem paths from user input.
- Changing cwd handling, symlink resolution, path traversal guards, sandbox permissions, approval checks, or auth prompts.
- Changing signing, notarization, appcast, update, license, payment, or release asset generation.
- Changing CI workflows, release or publish scripts, installers, or anything that runs with elevated privilege.

Review the smallest entry point that reaches the sink, then the downstream call. If validation is missing or rollback is unclear, treat it as a hard stop.

### Risk tiers by path

The tier follows the paths a change touches, not its size or author. A one-line change to a workflow, updater, license check, installer, privilege helper, or deletion path gets the project's heaviest gate (its full or native test run, a security pass, and a human maintainer's review), and an agent's, bot's, or automated reviewer's approval never stands in for that human. Extract the project's tiers from its docs; when it keeps a table-driven script that prints the gates for the changed paths, run it and paste its lines. Such a script is advice, not a pass: the gates it names may run where this session cannot prove they ran. Commits and PRs in a tier also state how they were verified and how to revert them (`mode-ship.md` step 4).
