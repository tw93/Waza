"""Validation checks for Waza skills.

Each function takes the repository root (and pre-discovered skill metadata
where useful) and either prints `ok:` lines or calls `fail()`. No side effects
beyond stdout/stderr. Driver lives in `verify_skills.py`.

Split out of verify_skills.py so the check functions can be imported and
exercised by pytest unit tests without invoking the argparse driver.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from skill_frontmatter import fail, parse_frontmatter, parse_when_to_use_keywords


REF_PATTERN = re.compile(r'(?<![/.])\b(?:references|agents|scripts)/[\w/.-]+\b')
SCRIPT_VAR_PATTERN = re.compile(r'\}/scripts/([\w/.-]+)')
LINK_RE = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
URL_PREFIXES = ("http://", "https://", "mailto:", "ftp://", "tel:", "data:")
SEP_RE = re.compile(r'^[\s|:\-]+$')
PERSONAL_PATH_PATTERN = re.compile(r'/(?:Users|home)/[A-Za-z0-9._-]+/')
SKILL_REF_RE = re.compile(r'skills/([a-z][a-z0-9_-]*)/SKILL\.md')
# Quoted user-utterance triggers in rules/waza-routing.md. Covers straight ("),
# curly (U+201C/D), and CJK corner brackets (「」 U+300C/D, 『』 U+300E/F) so a
# Chinese phrase in 「」 is checked just like one in straight quotes.
QUOTED_PHRASE_RE = re.compile(
    r'"([^"]+)"'
    r'|\u201c([^\u201d]+)\u201d'
    r'|\u300c([^\u300d]+)\u300d'
    r'|\u300e([^\u300f]+)\u300f'
)
PROJECT_RITUAL_RE = re.compile(r'\b(?:Sparkle|MAS|Homebrew tap|Xcode scheme)\b', re.IGNORECASE)
PRIVATE_CONTEXT_RE = re.compile(
    r'(?:\.codex/(?:sessions|memories)|rollout_summaries/|'
    r'thread_id|rollout_path|session_meta|owner/private-repo|'
    r'private[-_/](?:repo|project|tool)|internal[-_/](?:repo|project|tool))',
    re.IGNORECASE,
)
FORCED_GITHUB_TOOL_RE = re.compile(
    r'(?:Use\s+`?gh`?\s+CLI\s+for\s+all\s+GitHub\s+interactions|'
    r'for\s+all\s+GitHub\s+interactions,\s+not\s+MCP\s+or\s+raw\s+API)',
    re.IGNORECASE,
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

DURABLE_CONTEXT_SKILLS = {"think", "check", "hunt", "design", "write", "health"}

NINJA_PREFIX = "Prefix your first line with 🥷 inline, not as its own paragraph."
OUTCOME_CONTRACT_FIELDS = ("Outcome:", "Done when:", "Evidence:", "Output:")

# Attribution strings that indicate AI co-authorship leaked into tracked files.
ATTRIBUTION_PATTERNS = (
    "Co-Authored-By: Claude",
    "Co-authored-by: Cursor",
    "noreply@anthropic.com",
    "cursoragent@cursor.com",
)
CODEX_MIRROR_IGNORED_DIRS = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
CODEX_MIRROR_IGNORED_NAMES = {
    ".DS_Store",
}
CODEX_MIRROR_IGNORED_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def pipe_count(s: str) -> int:
    n, tick, i = 0, False, 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            i += 2
            continue
        if s[i] == "`":
            tick = not tick
        elif s[i] == "|" and not tick:
            n += 1
        i += 1
    return n


def should_include_codex_mirror_file(path: Path) -> bool:
    if any(part in CODEX_MIRROR_IGNORED_DIRS for part in path.parts):
        return False
    if path.name in CODEX_MIRROR_IGNORED_NAMES:
        return False
    return path.suffix not in CODEX_MIRROR_IGNORED_SUFFIXES


def check_skill_files(root: Path):
    skill_files = sorted((root / "skills").glob("*/SKILL.md"))
    if not skill_files:
        fail("NO SKILLS FOUND: expected skills/*/SKILL.md")
    skill_descriptions: dict[str, str] = {}
    skill_keywords: dict[str, set[str]] = {}
    for path in skill_files:
        skill_dir = path.parent.name
        fields = parse_frontmatter(path)
        if fields["name"] != skill_dir:
            fail(f"NAME MISMATCH: {path} frontmatter name={fields['name']} dir={skill_dir}")
        if NINJA_PREFIX not in path.read_text():
            fail(
                f"MISSING NINJA PREFIX INSTRUCTION: {path}\n"
                f"  Every SKILL.md must carry this exact line:\n"
                f"  {NINJA_PREFIX}"
            )
        if not fields["dispatch_intent"]:
            fail(
                f"MISSING dispatch_intent: in {path}\n"
                f"  Every skill needs a dispatch_intent line. It feeds the dispatcher "
                f"routing table emitted by scripts/build_metadata.py."
            )
        skill_descriptions[skill_dir] = fields["description"]
        skill_keywords[skill_dir] = parse_when_to_use_keywords(fields["when_to_use"])
        print(f"ok: {path.as_posix()}")
    return skill_files, skill_descriptions, skill_keywords


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


def check_references(root: Path, skill_files: list[Path]):
    for path in skill_files:
        skill_dir = path.parent.name
        text = path.read_text()
        refs = set(REF_PATTERN.findall(text))
        refs |= {"scripts/" + s for s in SCRIPT_VAR_PATTERN.findall(text)}
        for ref in sorted(refs):
            expected = root / "skills" / skill_dir / ref
            if not expected.exists():
                fail(f"BROKEN REFERENCE: {path} references {ref} but file does not exist")
            print(f"ok: reference {skill_dir}/{ref}")


def check_description_conformance(skill_descriptions: dict[str, str]):
    """Every skill needs a triggerable opening, a 'Use when' cue, a 'Not for' exclusion, and a sane length.

    Locks the convention so new skills can't drift into vague descriptions that
    agent resolvers can't match before they read when_to_use.
    """
    for skill, description in sorted(skill_descriptions.items()):
        clean = description.strip().strip('"')
        length = len(clean)
        if length < 40:
            fail(f"DESCRIPTION TOO SHORT: {skill} ({length} chars); need >=40 for reliable resolver matching")
        if length > 500:
            fail(f"DESCRIPTION TOO LONG: {skill} ({length} chars); trim to <=500 to keep the resolver index light")
        first_word = clean.split()[0].lower() if clean.split() else ""
        if first_word in ("the", "a", "an", "this", "it"):
            fail(
                f"DESCRIPTION STARTS WITH ARTICLE: {skill}\n"
                f"  Start with a verb or action phrase (third-person). Got: {clean[:60]!r}"
            )
        if "use when" not in clean.lower():
            fail(
                f"DESCRIPTION MISSING USE-WHEN CUE: {skill}\n"
                f"  Description must include a 'Use when ...' trigger phrase because "
                f"some agent runtimes see description before when_to_use. Got: {clean[:120]!r}"
            )
        if "not for" not in clean.lower():
            fail(
                f"DESCRIPTION MISSING EXCLUSION CLAUSE: {skill}\n"
                f"  Must contain a 'Not for ...' clause so the resolver learns when NOT to fire. Got: {clean[:120]!r}"
            )
        if CJK_RE.search(clean):
            fail(
                f"DESCRIPTION CONTAINS CJK: {skill}\n"
                f"  Keep public-facing description metadata English-only. Put multilingual trigger phrases in when_to_use."
            )
        print(f"ok: description {skill} ({length} chars)")


def check_outcome_contract(skill_files: list[Path]):
    """Keep skill entrypoints outcome-first instead of process-heavy."""
    for path in skill_files:
        text = path.read_text()
        if "## Outcome Contract" not in text:
            fail(
                f"MISSING OUTCOME CONTRACT: {path}\n"
                f"  Skill entrypoints must name outcome, done state, evidence, and output before detailed workflow."
            )
        section = text.split("## Outcome Contract", 1)[1]
        section = section.split("\n## ", 1)[0]
        missing = [field for field in OUTCOME_CONTRACT_FIELDS if field not in section]
        if missing:
            fail(
                f"INCOMPLETE OUTCOME CONTRACT: {path}\n"
                f"  Missing fields: {', '.join(missing)}"
            )
        print(f"ok: outcome contract {path.parent.name}")


def check_durable_context_and_paths(root: Path, skill_files: list[Path]):
    """Durable context rules must stay portable and evidence-bound.

    Each skill in DURABLE_CONTEXT_SKILLS links to rules/durable-context.md for the
    shared preamble (when to read, read order, type mapping) and then adds
    skill-specific guidance with current-state override evidence. The shared
    rules file itself is checked once for the "raw transcripts" guard.
    """
    rules_path = root / "rules" / "durable-context.md"
    if not rules_path.exists():
        fail(
            f"MISSING SHARED RULE: {rules_path}\n"
            f"  Durable context preamble must live at rules/durable-context.md."
        )
    rules_text = rules_path.read_text().lower()
    if "raw transcripts" not in rules_text:
        fail(
            f"SHARED RULE MAY OVERREAD: {rules_path}\n"
            f"  rules/durable-context.md must forbid reading raw transcripts by default."
        )
    print("ok: rules/durable-context.md forbids raw transcripts")

    for path in skill_files:
        skill = path.parent.name
        text = path.read_text()
        if PERSONAL_PATH_PATTERN.search(text):
            fail(
                f"PERSONAL ABSOLUTE PATH IN SKILL: {path}\n"
                f"  Skill docs must not hard-code personal home-directory paths. "
                f"Use user-provided paths, project-relative paths, or resolver commands instead."
            )

        has_section = "## Durable Context Preflight" in text
        if skill in DURABLE_CONTEXT_SKILLS and not has_section:
            fail(
                f"MISSING DURABLE CONTEXT PREFLIGHT: {path}\n"
                f"  This skill must explain how to consume optional memory/preview context."
            )
        if not has_section:
            continue

        section = text.split("## Durable Context Preflight", 1)[1]
        section = section.split("\n## ", 1)[0]
        section_lower = section.lower()
        if "rules/durable-context.md" not in section:
            fail(
                f"DURABLE CONTEXT MISSING SHARED REFERENCE: {path}\n"
                f"  Section must link to rules/durable-context.md for the shared preamble."
            )
        if "current" not in section_lower or "override" not in section_lower:
            fail(
                f"DURABLE CONTEXT NOT EVIDENCE-BOUND: {path}\n"
                f"  Skill-specific paragraph must name what current state overrides memory."
            )
        print(f"ok: durable context preflight for {skill}")


def check_portable_skill_surface(root: Path, markdown_paths: list[Path]):
    """Guard Waza's public skill surface against private/project-specific drift.

    Waza skills should teach transferable workflow behavior. Project-specific
    release rituals and platform products are warning signals, while
    one-machine paths and platform-forcing commands are hard portability failures.
    """
    scan_paths = list(markdown_paths)
    scan_paths.extend(sorted((root / "rules").glob("*.md")))
    agents = root / "AGENTS.md"
    if agents.exists():
        scan_paths.append(agents)

    seen: set[Path] = set()
    warning_paths: list[str] = []
    for path in scan_paths:
        if path in seen or not path.exists():
            continue
        seen.add(path)
        rel = path.relative_to(root)
        text = path.read_text()
        if "~/Downloads" in text:
            fail(
                f"NON-PORTABLE DEFAULT SAVE PATH: {rel}\n"
                f"  Use a user-specified directory, project scratch path, or session temp directory."
            )
        if FORCED_GITHUB_TOOL_RE.search(text):
            fail(
                f"FORCED GITHUB TOOLING IN GENERIC SURFACE: {rel}\n"
                f"  GitHub projects may prefer gh, but Waza must derive platform tools from project context."
            )
        if PRIVATE_CONTEXT_RE.search(text):
            fail(
                f"PRIVATE PROJECT OR SESSION CONTEXT IN PORTABLE SURFACE: {rel}\n"
                f"  Public skills and rules must not copy private project names, session paths, "
                f"memory paths, rollout metadata, support vendors, or thread identifiers."
            )
        if PROJECT_RITUAL_RE.search(text):
            warning_paths.append(rel.as_posix())
    if warning_paths:
        print(
            "warn: project-specific names or platform products in portable surface "
            f"({', '.join(warning_paths[:8])})"
        )
    print("ok: portable skill surface")


def check_resolver(root: Path, skill_names: set[str]):
    """Every skill must be referenced from skills/RESOLVER.md.

    Keeps the human-readable index in lock-step with the SKILL.md descriptions
    the model actually sees.
    """
    resolver_path = root / "skills" / "RESOLVER.md"
    if not resolver_path.exists():
        fail(f"MISSING RESOLVER: expected {resolver_path}")
    resolver_text = resolver_path.read_text()
    for skill in sorted(skill_names):
        token = f"skills/{skill}/SKILL.md"
        if token not in resolver_text:
            fail(
                f"RESOLVER GAP: {skill} has no entry in {resolver_path}\n"
                f"  Add a row to a triggers table that references {token!r}."
            )
        print(f"ok: resolver entry for {skill}")

    referenced_skills = set(SKILL_REF_RE.findall(resolver_text))
    stale = sorted(referenced_skills - skill_names)
    if stale:
        fail(f"RESOLVER REFERENCES MISSING SKILL: {', '.join(stale)}")
    print("ok: resolver has no stale skill references")
    return resolver_path


def collect_all_md(root: Path, skill_names: set[str], resolver_path: Path) -> list[Path]:
    all_md: list[Path] = [resolver_path]
    for skill in sorted(skill_names):
        skill_root = root / "skills" / skill
        all_md.append(skill_root / "SKILL.md")
        for sub in ("references", "agents"):
            sub_dir = skill_root / sub
            if sub_dir.is_dir():
                all_md.extend(sorted(sub_dir.rglob("*.md")))
    return all_md


def check_markdown_links(root: Path, all_md: list[Path]):
    for path in all_md:
        if not path.exists():
            continue
        in_code = False
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            for m in LINK_RE.finditer(line):
                raw = m.group(1).strip()
                if not raw or raw.startswith(("#", "/")):
                    continue
                if raw.startswith(URL_PREFIXES) or "://" in raw:
                    continue
                target = raw.split("#", 1)[0].split("?", 1)[0]
                if target and not (path.parent / target).resolve().exists():
                    fail(f"BROKEN MARKDOWN LINK: {path}:{lineno} -> {raw}")
        print(f"ok: markdown links {path.relative_to(root)}")


# Unescaped | in data cells breaks GitHub rendering (#35).
def check_table_pipes(root: Path, all_md: list[Path]):
    for path in all_md:
        if not path.exists():
            continue
        in_fence = False
        sep_pipes = None
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                sep_pipes = None
                continue
            if in_fence:
                sep_pipes = None
                continue
            if SEP_RE.match(stripped) and "---" in stripped and "|" in stripped:
                sep_pipes = pipe_count(stripped)
                continue
            if sep_pipes is not None and stripped.startswith("|"):
                if pipe_count(stripped) > sep_pipes:
                    fail(
                        f"UNESCAPED PIPE IN TABLE: {path}:{lineno}\n"
                        f"  Use '\\|' or wrap the cell text in backticks."
                    )
                continue
            sep_pipes = None
        print(f"ok: table pipes {path.relative_to(root)}")


def check_no_root_skill(root: Path):
    """A root SKILL.md would make `npx skills add tw93/Waza` stop scanning nested
    skills, so the direct coding install path would expose only `/waza`. Claude
    Desktop's single-root SKILL.md is generated by scripts/package-skill.sh
    during release packaging.
    """
    root_skill = root / "SKILL.md"
    if root_skill.exists():
        fail("ROOT SKILL DISALLOWED: generate the Desktop dispatcher during packaging instead")
    print("ok: no root SKILL.md")


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


def check_skill_update_scripts(root: Path, skill_names: set[str]):
    """Direct `npx skills add` installs copy each skill directory, not the repo
    root, so each skill must carry the update checker it asks agents to run.
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
    print(f"ok: skill-local update checkers present ({len(skill_names)} skills)")


def check_anti_patterns_contract(root: Path):
    """Keep shared anti-pattern rules generic and mechanically sane."""
    path = root / "rules" / "anti-patterns.md"
    if not path.exists():
        fail(f"MISSING ANTI-PATTERNS: expected {path}")

    text = path.read_text()
    if re.search(r"\bWaza\b", text):
        fail(
            "ANTI-PATTERN PROJECT NAME LEAK: rules/anti-patterns.md\n"
            "  Anti-pattern rules are shared behavior. Keep row wording generic, "
            "without repo or product names."
        )

    stale_terms = (
        "Private rule leak",
        "Project fact promoted to global skill",
        "public Waza rules",
        "reusable Waza skill",
        "Keep Waza generic",
    )
    for term in stale_terms:
        if term in text:
            fail(
                f"ANTI-PATTERN STALE SPECIALIZATION: {term!r}\n"
                "  Merge private-context and project-fact cases into one generic public-surface rule."
            )

    rows: list[tuple[int, str]] = []
    for line in text.splitlines():
        if not line.startswith("| ") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or not cells[0].isdigit():
            continue
        rows.append((int(cells[0]), cells[1] if len(cells) > 1 else ""))

    expected_numbers = list(range(1, len(rows) + 1))
    actual_numbers = [number for number, _pattern in rows]
    if actual_numbers != expected_numbers:
        fail(
            "ANTI-PATTERN NUMBERING DRIFT: rules/anti-patterns.md\n"
            f"  Expected contiguous numbering {expected_numbers}; got {actual_numbers}."
        )

    pattern_names: dict[str, int] = {}
    for number, pattern in rows:
        key = pattern.lower()
        if key in pattern_names:
            fail(
                "ANTI-PATTERN DUPLICATE NAME: rules/anti-patterns.md\n"
                f"  Rows {pattern_names[key]} and {number} both use {pattern!r}."
            )
        pattern_names[key] = number

    print("ok: anti-patterns contract")


def check_waza_routing_skills(root: Path, skill_names: set[str]):
    """rules/waza-routing.md routing table must enumerate exactly the skills
    under skills/. Structural drift only -- trigger phrases stay hand-tuned."""
    path = root / "rules" / "waza-routing.md"
    if not path.exists():
        return
    listed: set[str] = set()
    for line in path.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 3:
            continue
        name = cells[1]
        # Skip table header (literal "skill") and separator rows ("---").
        if name == "skill" or set(name) <= {"-", ":"}:
            continue
        if re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            listed.add(name)
    missing = skill_names - listed
    extra = listed - skill_names
    if missing:
        fail(
            "WAZA ROUTING MISSING SKILLS: rules/waza-routing.md table omits: "
            f"{', '.join(sorted(missing))}"
        )
    if extra:
        fail(
            "WAZA ROUTING STALE SKILLS: rules/waza-routing.md lists skills "
            f"not in skills/: {', '.join(sorted(extra))}"
        )
    print(f"ok: rules/waza-routing.md skills match ({len(listed)} skills)")


def check_waza_routing_triggers(root: Path):
    """Quoted user-utterance triggers in rules/waza-routing.md must be grounded.

    The routing table's prose stays hand-tuned, but any phrase in quotes is a
    claim about what a user literally types. Each quoted phrase (split on '/',
    whitespace-normalized) must appear in the matching skill's when_to_use, so
    the routing hint can never advertise a trigger no skill actually claims.
    Unquoted wording is intentionally free and is not checked here.
    """
    path = root / "rules" / "waza-routing.md"
    if not path.exists():
        return
    norm = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
    for line in path.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 3:
            continue
        skill = cells[1]
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", skill):
            continue
        skill_md = root / "skills" / skill / "SKILL.md"
        if not skill_md.exists():
            continue  # missing skill dir is check_waza_routing_skills' job
        when = norm(parse_frontmatter(skill_md)["when_to_use"])
        for match in QUOTED_PHRASE_RE.finditer(cells[2]):
            quoted = next(g for g in match.groups() if g is not None)
            for seg in quoted.split("/"):
                seg_norm = norm(seg)
                if seg_norm and seg_norm not in when:
                    fail(
                        f"WAZA ROUTING UNGROUNDED TRIGGER: rules/waza-routing.md "
                        f"row '{skill}' quotes {seg!r}, but it is absent from "
                        f"skills/{skill}/SKILL.md when_to_use.\n"
                        f"  Quote only phrases a user actually types; align the "
                        f"phrase with when_to_use or add it to when_to_use."
                    )
    print("ok: rules/waza-routing.md quoted triggers grounded")


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
    expected = "npx skills add tw93/Waza -a claude-code codex cursor -g -y"
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


def check_english_coaching_guard(root: Path):
    """rules/english.md must keep two failure-mode guards intact:
    (1) silence on Chinese-only messages, (2) silence when English is fine.
    These guards were added after real misfires; do not let them rot."""
    english_rule = root / "rules" / "english.md"
    if not english_rule.exists():
        fail(f"MISSING {english_rule}")
    text = english_rule.read_text()
    missing = []
    if "Chinese-only messages" not in text:
        missing.append("'Chinese-only messages'")
    if "already-natural English, stay silent" not in text:
        missing.append("'already-natural English, stay silent'")
    if missing:
        fail(
            "ENGLISH COACHING GUARD: rules/english.md must suppress no-op output. "
            f"Missing markers: {', '.join(missing)}"
        )
    print("ok: English Coaching guard")


def check_attribution_leak(root: Path):
    """Scan tracked .sh and .json files for AI-attribution strings. This file
    legitimately owns the pattern list, so exclude itself from the scan.
    Markdown is excluded because rules/anti-patterns.md and similar docs may
    describe these strings as patterns to avoid."""
    self_path = Path(__file__).resolve()
    for suffix in (".sh", ".json"):
        for path in root.rglob(f"*{suffix}"):
            if ".git" in path.parts:
                continue
            try:
                if path.resolve() == self_path:
                    continue
            except OSError:
                continue
            try:
                text = path.read_text()
            except (UnicodeDecodeError, OSError):
                continue
            for pat in ATTRIBUTION_PATTERNS:
                if pat in text:
                    fail(
                        f"ATTRIBUTION LEAK: {path.relative_to(root)} contains {pat!r}"
                    )
    print("ok: no attribution leak")


def check_trigger_overlap(skill_keywords: dict[str, set[str]]):
    """Pairwise Jaccard >= 0.5 means more than half the combined keywords are shared."""
    names = sorted(skill_keywords)
    found_overlap = False
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            shared = skill_keywords[a] & skill_keywords[b]
            union = skill_keywords[a] | skill_keywords[b]
            if not union:
                continue
            jaccard = len(shared) / len(union)
            if jaccard >= 0.5:
                print(
                    f"TRIGGER OVERLAP: {a} vs {b} jaccard={jaccard:.2f} shared={sorted(shared)}",
                    file=sys.stderr,
                )
                found_overlap = True
    if found_overlap:
        raise SystemExit(1)
    print("ok: trigger keyword overlap below threshold")
