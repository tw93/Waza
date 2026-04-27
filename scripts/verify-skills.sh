#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python3 - <<'PYEOF'
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text().splitlines()
    if not lines or lines[0] != "---":
        fail(f"INVALID FRONTMATTER: {path} must start with ---")

    try:
        end = lines.index("---", 1)
    except ValueError:
        fail(f"INVALID FRONTMATTER: {path} missing closing ---")

    frontmatter = lines[1:end]
    fields: dict[str, str] = {}
    in_metadata = False

    for line in frontmatter:
        if line.startswith("name:"):
            fields["name"] = line.split(":", 1)[1].strip()
            in_metadata = False
        elif line.startswith("description:"):
            raw_value = line.split(":", 1)[1].strip()
            if not raw_value.startswith('"') and ": " in raw_value:
                fail(
                    f"UNQUOTED DESCRIPTION WITH COLON: {path}\n"
                    f"  Description contains ': ' and must be wrapped in double quotes, "
                    f"otherwise YAML plain-scalar parsing truncates the field."
                )
            fields["description"] = raw_value.strip('"')
            in_metadata = False
        elif line.startswith("when_to_use:"):
            raw_value = line.split(":", 1)[1].strip()
            fields["when_to_use"] = raw_value.strip('"')
            in_metadata = False
        elif line == "metadata:":
            in_metadata = True
        elif in_metadata and line.startswith("  version:"):
            fields["version"] = line.split(":", 1)[1].strip().strip('"')
        elif line and not line.startswith(" "):
            in_metadata = False

    for field in ("name", "description", "version"):
        if not fields.get(field):
            fail(f"MISSING {field}: in {path}")

    return fields


root = Path(".")
skill_files = sorted((root / "skills").glob("*/SKILL.md"))
if not skill_files:
    fail("NO SKILLS FOUND: expected skills/*/SKILL.md")

skill_versions: dict[str, str] = {}
skill_descriptions: dict[str, str] = {}
for path in skill_files:
    skill_dir = path.parent.name
    fields = parse_frontmatter(path)
    if fields["name"] != skill_dir:
        fail(f"NAME MISMATCH: {path} frontmatter name={fields['name']} dir={skill_dir}")
    expected_prefix = "Prefix your first line with 🥷 inline, not as its own paragraph."
    if expected_prefix not in path.read_text():
        fail(
            f"MISSING NINJA PREFIX INSTRUCTION: {path}\n"
            f"  Every SKILL.md must carry this exact line:\n"
            f"  {expected_prefix}"
        )
    skill_versions[skill_dir] = fields["version"]
    skill_descriptions[skill_dir] = fields["description"]
    print(f"ok: {path.as_posix()}")

marketplace = json.load(open(root / ".claude-plugin" / "marketplace.json"))
plugins = marketplace.get("plugins")
if not isinstance(plugins, list):
    fail("INVALID MARKETPLACE: plugins must be a list")

market_versions: dict[str, str] = {}
market_descriptions: dict[str, str] = {}
for entry in plugins:
    if not isinstance(entry, dict):
        fail("INVALID MARKETPLACE: plugin entry must be an object")
    name = entry.get("name")
    version = entry.get("version")
    source = entry.get("source")
    description = entry.get("description", "").strip().strip('"')
    if not name or not version:
        fail("INVALID MARKETPLACE: every plugin needs name and version")
    if not description:
        fail(f"MISSING DESCRIPTION: marketplace plugin {name}")
    if name in market_versions:
        fail(f"DUPLICATE MARKETPLACE ENTRY: {name}")
    expected_source = f"./skills/{name}"
    if source != expected_source:
        fail(f"WRONG SOURCE: {name} source={source!r} expected={expected_source!r}")
    market_versions[name] = version
    market_descriptions[name] = description

missing_from_market = sorted(set(skill_versions) - set(market_versions))
if missing_from_market:
    fail("NOT IN MARKETPLACE: " + ", ".join(missing_from_market))

extra_in_market = sorted(set(market_versions) - set(skill_versions))
if extra_in_market:
    fail("MISSING SKILL DIRECTORY: " + ", ".join(extra_in_market))

for skill, skill_version in sorted(skill_versions.items()):
    market_version = market_versions[skill]
    if skill_version != market_version:
        fail(f"VERSION MISMATCH: {skill} SKILL={skill_version} MARKET={market_version}")
    # marketplace description may append TRIGGER/SKIP lines after the
    # core SKILL.md description, so check prefix containment, not exact match.
    if not market_descriptions[skill].startswith(skill_descriptions[skill]):
        fail(
            f"DESCRIPTION MISMATCH: {skill}\n"
            f"  SKILL.md:    {skill_descriptions[skill]}\n"
            f"  marketplace: {market_descriptions[skill]}\n"
            f"  marketplace description must start with the SKILL.md description"
        )
    print(f"ok: {skill} {skill_version}")

import re
# Direct local references: `references/foo.md`, `agents/bar.md`, `scripts/baz.sh`
# Lookbehind excludes absolute path fragments like $HOME/.agents/skills/X
ref_pattern = re.compile(r'(?<![/.])\b(?:references|agents|scripts)/[\w/.-]+\b')
# Script references via runtime variable: ${SKILL_DIR}/scripts/foo.sh
script_pattern = re.compile(r'\}/scripts/([\w/.-]+)')
for path in skill_files:
    skill_dir = path.parent.name
    text = path.read_text()
    refs = set(ref_pattern.findall(text))
    refs |= {"scripts/" + s for s in script_pattern.findall(text)}
    for ref in sorted(refs):
        expected = root / "skills" / skill_dir / ref
        if not expected.exists():
            fail(f"BROKEN REFERENCE: {path} references {ref} but file does not exist")
        print(f"ok: reference {skill_dir}/{ref}")

# Description conformance: every skill needs a triggerable opening, a "Not for"
# exclusion clause, and a sane length. Locks the convention so new skills can't
# drift into vague descriptions that the Claude Code resolver can't match.
for skill, description in sorted(skill_descriptions.items()):
    clean = description.strip().strip('"')
    length = len(clean)
    if length < 40:
        fail(f"DESCRIPTION TOO SHORT: {skill} ({length} chars); need ≥40 for reliable resolver matching")
    if length > 500:
        fail(f"DESCRIPTION TOO LONG: {skill} ({length} chars); trim to ≤500 to keep the resolver index light")
    # Descriptions should be third-person (per Anthropic best practices).
    # Check for a verb in the first word rather than enforcing specific starters.
    first_word = clean.split()[0].lower() if clean.split() else ""
    passive_starters = ("the", "a", "an", "this", "it")
    if first_word in passive_starters:
        fail(
            f"DESCRIPTION STARTS WITH ARTICLE: {skill}\n"
            f"  Start with a verb or action phrase (third-person). Got: {clean[:60]!r}"
        )
    if "not for" not in clean.lower():
        fail(
            f"DESCRIPTION MISSING EXCLUSION CLAUSE: {skill}\n"
            f"  Must contain a 'Not for ...' clause so the resolver learns when NOT to fire. Got: {clean[:120]!r}"
        )
    print(f"ok: description {skill} ({length} chars)")

# RESOLVER.md coverage: every skill must be referenced from the central routing
# table at skills/RESOLVER.md. Keeps the human-readable index in lock-step with
# the SKILL.md descriptions the model actually sees.
resolver_path = root / "skills" / "RESOLVER.md"
if not resolver_path.exists():
    fail(f"MISSING RESOLVER: expected {resolver_path}")
resolver_text = resolver_path.read_text()
for skill in sorted(skill_versions):
    token = f"skills/{skill}/SKILL.md"
    if token not in resolver_text:
        fail(
            f"RESOLVER GAP: {skill} has no entry in {resolver_path}\n"
            f"  Add a row to a triggers table that references {token!r}."
        )
    print(f"ok: resolver entry for {skill}")

# RESOLVER reverse parity: every skills/<name>/SKILL.md token cited in
# RESOLVER.md must point to a directory that actually exists. Forward parity
# (above) catches missing entries; this catches stale entries left over after a
# rename or deletion. Cheaper than parsing the markdown table.
referenced_skills = set(re.findall(r'skills/([a-z][a-z0-9_-]*)/SKILL\.md', resolver_text))
unknown_in_resolver = sorted(referenced_skills - set(skill_versions))
if unknown_in_resolver:
    fail(
        f"RESOLVER REFERENCES MISSING SKILL: {', '.join(unknown_in_resolver)}\n"
        f"  {resolver_path} cites these skills/<name>/SKILL.md tokens but no matching directory exists under skills/."
    )
print(f"ok: resolver has no stale skill references")

# Internal markdown link rot: every [text](path) link inside SKILL.md /
# references / agents content must resolve to an existing path under the
# owning skill directory. Skip URLs, mailto, anchors, and links inside
# fenced code blocks.
link_pattern = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
URL_PREFIXES = ("http://", "https://", "mailto:", "ftp://", "tel:", "data:")
link_targets: list[Path] = []
for skill in sorted(skill_versions):
    skill_root = root / "skills" / skill
    link_targets.append(skill_root / "SKILL.md")
    for sub in ("references", "agents"):
        sub_dir = skill_root / sub
        if sub_dir.is_dir():
            link_targets.extend(sorted(sub_dir.rglob("*.md")))

for path in link_targets:
    if not path.exists():
        continue
    text = path.read_text()
    in_code = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        for match in link_pattern.finditer(line):
            raw = match.group(1).strip()
            if not raw or raw.startswith("#"):
                continue
            if raw.startswith(URL_PREFIXES) or "://" in raw:
                continue
            target = raw.split("#", 1)[0].split("?", 1)[0]
            if not target:
                continue
            if target.startswith("/"):
                # Absolute paths are out of scope for this lint; left for a
                # future check if it becomes a recurring issue.
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                fail(
                    f"BROKEN MARKDOWN LINK: {path}:{lineno} -> {raw}\n"
                    f"  Link target does not exist at {resolved.relative_to(root.resolve())}."
                )
    print(f"ok: markdown links {path.relative_to(root)}")

# Pipe-in-table lint: a literal '|' inside a markdown table data cell
# terminates the column and breaks GitHub rendering (see upstream issue #35
# and commit 4fbf4bb). Detect data rows directly following a separator row
# and fail if the data row carries more unescaped pipes outside inline code
# than the separator does. Skips fenced code blocks and escaped pipes.
SEPARATOR_RE = re.compile(r'^[\s|:\-]+$')


def count_table_pipes(text: str) -> int:
    """Count unescaped '|' characters outside inline code spans."""
    count = 0
    in_inline = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            i += 2
            continue
        if ch == "`":
            in_inline = not in_inline
        elif ch == "|" and not in_inline:
            count += 1
        i += 1
    return count


pipe_targets: list[Path] = [resolver_path]
for skill in sorted(skill_versions):
    skill_root = root / "skills" / skill
    pipe_targets.append(skill_root / "SKILL.md")
    for sub in ("references", "agents"):
        sub_dir = skill_root / sub
        if sub_dir.is_dir():
            pipe_targets.extend(sorted(sub_dir.rglob("*.md")))

for path in pipe_targets:
    if not path.exists():
        continue
    in_fenced = False
    last_separator_pipes = None
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fenced = not in_fenced
            last_separator_pipes = None
            continue
        if in_fenced:
            last_separator_pipes = None
            continue
        is_separator = (
            bool(SEPARATOR_RE.match(stripped))
            and "---" in stripped
            and "|" in stripped
        )
        if is_separator:
            last_separator_pipes = count_table_pipes(stripped)
            continue
        if last_separator_pipes is not None and stripped.startswith("|"):
            if count_table_pipes(stripped) > last_separator_pipes:
                fail(
                    f"UNESCAPED PIPE IN TABLE: {path}:{lineno}\n"
                    f"  Cell carries an unescaped '|'. Use '\\|' or wrap the cell text in backticks."
                )
            continue
        last_separator_pipes = None
    print(f"ok: table pipes {path.relative_to(root)}")
PYEOF

# Rules files (outside skills/ so regex check above does not cover them)
test -f rules/english.md && \
test -f rules/chinese.md && echo "references: ok"
