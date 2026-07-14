"""Distribution-surface checks: marketplaces, Codex plugin mirror, packaging, npm, shared assets.

Split from skill_checks.py; import through skill_checks (the facade) so the
check inventory stays visible in one place.
"""

from __future__ import annotations

import json
from pathlib import Path

from skill_frontmatter import fail, should_include_codex_mirror_file


def check_marketplace(root: Path, expected_version: str, skill_names: set[str], skill_descriptions: dict[str, str]):
    """Validate generated Claude Code and Codex marketplace metadata."""
    check_claude_marketplace(root, expected_version, skill_names, skill_descriptions)
    check_codex_plugin(root, expected_version)
    check_codex_marketplace(root)


def check_claude_marketplace(root: Path, expected_version: str, skill_names: set[str], skill_descriptions: dict[str, str]):
    """Validate Claude Code marketplace.json shape:

    - One bundle entry: name == "waza", source == "./".
    - Per-skill entries: name == "waza-<skill>", source == "./skills/<skill>".
    - All versions in marketplace march in lock-step with the top-level VERSION
      file. Source of truth is VERSION; per-skill SKILL.md no longer carries a
      version field (codegen + this check guarantee marketplace stays correct).
    """
    market_path = root / ".claude-plugin" / "marketplace.json"
    marketplace = json.loads(market_path.read_text())
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        fail("INVALID MARKETPLACE: plugins must be a list")

    market_versions: dict[str, str] = {}
    market_descriptions: dict[str, str] = {}
    seen_names: set[str] = set()
    bundle_version = ""
    for entry in plugins:
        if not isinstance(entry, dict):
            fail("INVALID MARKETPLACE: plugin entry must be an object")
        name = entry.get("name")
        version = entry.get("version")
        source = entry.get("source")
        description = (entry.get("description") or "").strip().strip('"')
        if not name or not version:
            fail("INVALID MARKETPLACE: every plugin needs name and version")
        if not description:
            fail(f"MISSING DESCRIPTION: marketplace plugin {name}")
        if name in seen_names:
            fail(f"DUPLICATE MARKETPLACE ENTRY: {name}")
        seen_names.add(name)

        if name == "waza":
            if source != "./":
                fail(f"WRONG BUNDLE SOURCE: source={source!r} expected='./'")
            bundle_version = version
            continue

        if not name.startswith("waza-"):
            fail(
                f"INVALID PLUGIN NAME: {name!r} must be 'waza' (bundle) or "
                f"'waza-<skill>' (per-skill entry)"
            )
        skill_name = name.removeprefix("waza-")
        if not skill_name:
            fail(
                f"INVALID PLUGIN NAME: {name!r} has an empty <skill> suffix; "
                f"per-skill entries must be named 'waza-<skill>' with a non-empty skill name"
            )
        expected_source = f"./skills/{skill_name}"
        if source != expected_source:
            fail(f"WRONG SOURCE: {name} source={source!r} expected={expected_source!r}")
        market_versions[skill_name] = version
        market_descriptions[skill_name] = description

    if "waza" not in seen_names:
        fail(
            "MISSING BUNDLE ENTRY: marketplace.json must include a 'waza' bundle entry "
            "(name=\"waza\", source=\"./\") so /plugin install waza@waza registers "
            "all skills under the waza namespace"
        )

    missing_from_market = sorted(skill_names - set(market_versions))
    if missing_from_market:
        fail("NOT IN MARKETPLACE: " + ", ".join(missing_from_market))
    extra_in_market = sorted(set(market_versions) - skill_names)
    if extra_in_market:
        fail("MISSING SKILL DIRECTORY: " + ", ".join(extra_in_market))

    for skill in sorted(skill_names):
        market_version = market_versions[skill]
        if market_version != expected_version:
            fail(
                f"VERSION DRIFT: marketplace waza-{skill} version={market_version!r} "
                f"!= VERSION file {expected_version!r}.\n"
                f"  All marketplace entries march in lock-step. "
                f"Update .claude-plugin/marketplace.json to match VERSION."
            )
        if not market_descriptions[skill].startswith(skill_descriptions[skill]):
            fail(
                f"DESCRIPTION MISMATCH: {skill}\n"
                f"  SKILL.md:    {skill_descriptions[skill]}\n"
                f"  marketplace: {market_descriptions[skill]}\n"
                f"  marketplace description must start with the SKILL.md description"
            )
        print(f"ok: marketplace waza-{skill} pinned to {market_version}")

    if bundle_version and bundle_version != expected_version:
        fail(
            f"VERSION DRIFT: waza bundle version={bundle_version!r} "
            f"!= VERSION file {expected_version!r}.\n"
            f"  Update the 'waza' entry in .claude-plugin/marketplace.json to match VERSION."
        )
    print(f"ok: all versions in lock-step with VERSION={expected_version}")


def check_codex_plugin(root: Path, expected_version: str):
    """Validate Codex plugin manifest shape."""
    plugin_root = root / "plugins" / "waza"
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        fail(
            "MISSING CODEX PLUGIN MANIFEST: expected "
            "plugins/waza/.codex-plugin/plugin.json "
            "so Codex can install Waza as a plugin from the repo marketplace"
        )
    manifest = json.loads(manifest_path.read_text())
    required = {
        "name": "waza",
        "version": expected_version,
        "skills": "./skills/",
        "license": "MIT",
        "homepage": "https://github.com/tw93/Waza",
        "repository": "https://github.com/tw93/Waza",
    }
    for key, expected in required.items():
        actual = manifest.get(key)
        if actual != expected:
            fail(
                f"CODEX PLUGIN FIELD DRIFT: plugins/waza/.codex-plugin/plugin.json {key}="
                f"{actual!r} expected {expected!r}"
            )
    if not (manifest.get("description") or "").strip():
        fail("CODEX PLUGIN DESCRIPTION: plugins/waza/.codex-plugin/plugin.json needs description")
    author = manifest.get("author")
    if not isinstance(author, dict) or not author.get("name"):
        fail("CODEX PLUGIN AUTHOR: plugins/waza/.codex-plugin/plugin.json needs author.name")
    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        fail("CODEX PLUGIN INTERFACE: plugins/waza/.codex-plugin/plugin.json needs interface object")
    interface_required = {
        "displayName": "Waza",
        "developerName": "Tw93",
        "category": "Developer Tools",
        "websiteURL": "https://github.com/tw93/Waza",
    }
    for key, expected in interface_required.items():
        actual = interface.get(key)
        if actual != expected:
            fail(
                f"CODEX PLUGIN INTERFACE DRIFT: plugins/waza/.codex-plugin/plugin.json "
                f"interface.{key}={actual!r} expected {expected!r}"
            )
    default_prompt = interface.get("defaultPrompt")
    if (
        not isinstance(default_prompt, list)
        or not default_prompt
        or len(default_prompt) > 3
        or any(not isinstance(item, str) or len(item) > 128 for item in default_prompt)
    ):
        fail(
            "CODEX PLUGIN DEFAULT PROMPTS: interface.defaultPrompt must contain "
            "1-3 strings, each <=128 chars"
        )
    if not (plugin_root / "skills").is_dir():
        fail(
            "CODEX PLUGIN SKILLS PATH: plugins/waza/.codex-plugin/plugin.json "
            "points at missing plugins/waza/skills/"
        )
    for source_name in ("skills", "rules"):
        source_root = root / source_name
        mirror_root = plugin_root / source_name
        for source_path in sorted(source_root.rglob("*")):
            if not source_path.is_file():
                continue
            source_rel = source_path.relative_to(source_root)
            if not should_include_codex_mirror_file(source_rel):
                continue
            mirror_path = mirror_root / source_rel
            if not mirror_path.exists():
                fail(
                    f"CODEX PLUGIN MIRROR MISSING: {mirror_path.relative_to(root)} "
                    f"must mirror {source_path.relative_to(root)}"
                )
            if mirror_path.read_bytes() != source_path.read_bytes():
                fail(
                    f"CODEX PLUGIN MIRROR DRIFT: {mirror_path.relative_to(root)} "
                    f"differs from {source_path.relative_to(root)}"
                )
        # Reverse direction: a mirror file with no source counterpart is stale
        # output that regeneration would delete; catch it here too so this
        # check stays symmetric with build_metadata --check.
        if mirror_root.exists():
            for mirror_path in sorted(mirror_root.rglob("*")):
                if not mirror_path.is_file():
                    continue
                mirror_rel = mirror_path.relative_to(mirror_root)
                if not should_include_codex_mirror_file(mirror_rel):
                    continue
                if not (source_root / mirror_rel).exists():
                    fail(
                        f"CODEX PLUGIN MIRROR EXTRA: {mirror_path.relative_to(root)} "
                        f"has no source under {source_name}/. "
                        f"Run scripts/build_metadata.py (no flags) to regenerate."
                    )
    print(f"ok: Codex plugin manifest pinned to {expected_version}")


def check_codex_marketplace(root: Path):
    """Validate repo-local Codex marketplace shape."""
    marketplace_path = root / ".agents" / "plugins" / "marketplace.json"
    if not marketplace_path.exists():
        fail(
            "MISSING CODEX MARKETPLACE: expected .agents/plugins/marketplace.json "
            "so `codex plugin marketplace add tw93/Waza` can discover Waza"
        )
    marketplace = json.loads(marketplace_path.read_text())
    if marketplace.get("name") != "waza":
        fail("CODEX MARKETPLACE NAME: .agents/plugins/marketplace.json name must be 'waza'")
    interface = marketplace.get("interface")
    if not isinstance(interface, dict) or interface.get("displayName") != "Waza":
        fail(
            "CODEX MARKETPLACE DISPLAY NAME: .agents/plugins/marketplace.json "
            "must set interface.displayName to 'Waza'"
        )
    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or len(plugins) != 1:
        fail("CODEX MARKETPLACE PLUGINS: expected exactly one Waza plugin entry")
    entry = plugins[0]
    expected_entry = {
        "name": "waza",
        "source": {
            "source": "local",
            "path": "./plugins/waza",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": "Developer Tools",
    }
    if entry != expected_entry:
        fail(
            "CODEX MARKETPLACE ENTRY DRIFT: .agents/plugins/marketplace.json "
            f"plugins[0]={entry!r} expected {expected_entry!r}"
        )
    if not (root / "plugins" / "waza" / ".codex-plugin" / "plugin.json").exists():
        fail(
            "CODEX MARKETPLACE SOURCE: source.path './plugins/waza' must resolve to a plugin "
            "root containing .codex-plugin/plugin.json"
        )
    print("ok: Codex marketplace exposes waza plugin")


def check_rules_files_present(root: Path):
    """Required shared rule files outside skills/ that the per-skill ref check
    doesn't cover."""
    required = [
        "english.md",
        "chinese.md",
        "anti-patterns.md",
        "durable-context.md",
        "waza-routing.md",
    ]
    for name in required:
        path = root / "rules" / name
        if not path.exists():
            fail(f"MISSING RULE FILE: {path}")
    print(f"ok: rules/ files present ({', '.join(required)})")

# Canonical update-check instruction every SKILL.md must carry verbatim. The
# base-dir wording is load-bearing: agents that run the literal command from
# their own cwd hit exit 127 on any relative path (issue #71), so the line must
# tell them to resolve against the skill's install directory and to fail quiet.
UPDATE_CHECK_LINE = (
    "**Update check (non-blocking).** Once per conversation, run "
    "`bash <skill-base-dir>/scripts/check-update.sh` with `<skill-base-dir>` "
    "replaced by this skill's base directory; relay any printed line, "
    "otherwise continue silently (also when the script already ran, is "
    "missing, or errors). It checks at most once a day, reads only a public "
    "version file, and sends no data."
)


def check_skill_update_scripts(root: Path, skill_names: set[str]):
    """Direct `npx skills add` installs copy each skill directory, not the repo
    root, so each skill must carry the update checker it asks agents to run,
    and every surface that invokes it (each SKILL.md plus the Desktop
    dispatcher template) must use the exact canonical line.
    """
    source = root / "scripts" / "check-update.sh"
    if not source.exists():
        fail(f"MISSING UPDATE CHECKER: expected {source}")
    expected = source.read_bytes()
    for skill in sorted(skill_names):
        path = root / "skills" / skill / "scripts" / "check-update.sh"
        if not path.exists():
            fail(
                f"MISSING SKILL UPDATE CHECKER: {path.relative_to(root)}\n"
                "  Direct `npx skills add` installs only the skill folder, so "
                "the checker must be present inside every skill directory."
            )
        if path.read_bytes() != expected:
            fail(
                f"SKILL UPDATE CHECKER DRIFT: {path.relative_to(root)} "
                f"differs from {source.relative_to(root)}"
            )
        skill_md = root / "skills" / skill / "SKILL.md"
        if UPDATE_CHECK_LINE not in skill_md.read_text():
            fail(
                f"UPDATE CHECK LINE DRIFT: {skill_md.relative_to(root)}\n"
                "  The update-check instruction must match "
                "skill_checks.UPDATE_CHECK_LINE verbatim. Relative invocations "
                "like `bash ../../scripts/check-update.sh` break installed "
                "copies (issue #71)."
            )
    dispatcher_template = root / "scripts" / "dispatcher-template.md"
    if not dispatcher_template.exists():
        fail(f"MISSING DISPATCHER TEMPLATE: expected {dispatcher_template}")
    if UPDATE_CHECK_LINE not in dispatcher_template.read_text():
        fail(
            f"UPDATE CHECK LINE DRIFT: {dispatcher_template.relative_to(root)}\n"
            "  The Desktop ZIP root SKILL.md is generated from this template, "
            "so its update-check instruction must match "
            "skill_checks.UPDATE_CHECK_LINE verbatim."
        )
    print(f"ok: skill-local update checkers present ({len(skill_names)} skills)")


def check_readme_install_command(root: Path):
    """README must show the default install command users can copy-paste."""
    readme = root / "README.md"
    if not readme.exists():
        fail(f"MISSING README.md at {readme}")
    text = readme.read_text()
    # One command installs every skill to an explicit agent list, so the README
    # documents a single copy-paste line. The list is intentional: `-a '*'` (or
    # the no-`-a` auto-detect path) sweeps in agents like PromptScript and Eve
    # that lack global-install support and prints a "Failed to install" block.
    # Naming agents installs cleanly; codex and cursor share `~/.agents/skills`,
    # so other universal agents pick the skills up without being listed.
    expected = "npx skills add tw93/Waza -a claude-code codex cursor antigravity-cli -g -y"
    if expected not in text:
        fail(
            f"README INSTALL COMMAND: README.md must include {expected!r}\n"
            f"  Waza's public install path depends on this exact string."
        )
    expected_codex_marketplace = "codex plugin marketplace add tw93/Waza"
    if expected_codex_marketplace not in text:
        fail(
            "README CODEX MARKETPLACE COMMAND: README.md must include "
            f"{expected_codex_marketplace!r}\n"
            f"  Codex plugin installs should use the repo marketplace so users can "
            f"upgrade without rerunning npx skills add."
        )
    expected_codex_install = "codex plugin add waza@waza"
    if expected_codex_install not in text:
        fail(
            "README CODEX PLUGIN COMMAND: README.md must include "
            f"{expected_codex_install!r}\n"
            f"  The Codex marketplace entry must document the plugin install selector."
        )
    expected_pi = "pi install npm:@tw93/waza"
    if expected_pi not in text:
        fail(
            f"README PI INSTALL COMMAND: README.md must include {expected_pi!r}\n"
            f"  The Pi package install path depends on this exact string."
        )
    expected_installers = {
        "setup-rule": "https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh",
        "setup-statusline": "https://github.com/tw93/Waza/releases/latest/download/setup-statusline.sh",
    }
    for label, url in expected_installers.items():
        if url not in text:
            fail(
                f"README {label.upper()} URL: README.md must include {url!r}\n"
                f"  Installer snippets should follow the latest release asset "
                f"without per-release README churn."
            )
    print(
        "ok: README documents the universal skills install, Codex plugin "
        "marketplace, Pi package, and latest installer assets"
    )


def check_release_workflow_npm_surface(root: Path):
    """GitHub releases must publish the npm package that Pi consumes."""
    workflow = root / ".github" / "workflows" / "release.yml"
    if not workflow.exists():
        fail(f"MISSING RELEASE WORKFLOW: expected {workflow}")
    text = workflow.read_text()
    required = {
        "npm publish": "publishes @tw93/waza during release",
        "npm view @tw93/waza": "re-reads the npm registry after publish",
        "id-token: write": "allows npm trusted publishing through GitHub OIDC",
        "node-version: 24": "uses a Node/npm runtime that supports trusted publishing",
        "package-manager-cache: false": "keeps release publish jobs from caching credentials or package state",
        "github.event.release.tag_name": "checks the GitHub release tag",
        "package.json').pi.skills[0]": "checks Pi package metadata",
        "dist-tags.latest": "confirms the npm latest dist-tag",
        "scripts/setup-rule.sh": "uploads the rule installer as a latest release asset",
        "scripts/setup-statusline.sh": "uploads the statusline installer as a latest release asset",
    }
    missing = [label for label, reason in required.items() if label not in text]
    if missing:
        fail(
            "RELEASE WORKFLOW NPM SURFACE: .github/workflows/release.yml "
            "must publish and verify @tw93/waza for Pi installs.\n"
            + "\n".join(f"  missing {label!r}: {required[label]}" for label in missing)
        )
    print("ok: release workflow publishes npm package and installer assets")
