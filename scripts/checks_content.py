"""Skill-file and prose checks: frontmatter contracts, portability, references, catalogs.

Split from skill_checks.py; import through skill_checks (the facade) so the
check inventory stays visible in one place.
"""

from __future__ import annotations

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

DURABLE_CONTEXT_SKILLS = {"think", "check", "hunt", "ui", "write", "health"}

NINJA_PREFIX = "Prefix your first line with 🥷 inline, not as its own paragraph."

OUTCOME_CONTRACT_FIELDS = ("Outcome:", "Done when:", "Evidence:", "Output:")

# Attribution strings that indicate AI co-authorship leaked into tracked files.
ATTRIBUTION_PATTERNS = (
    "Co-Authored-By: Claude",
    "Co-authored-by: Cursor",
    "noreply@anthropic.com",
    "cursoragent@cursor.com",
)

# Direct adversarial instructions can trip provider-side classifiers when they
# live in Markdown that is injected into a model context. Keep the patterns
# lexical but do not reproduce the complete trigger strings in this source.
CONTEXT_CLASSIFIER_PATTERNS = (
    (
        "instruction-priority override",
        re.compile(
            r"\bignore\s+(?:all\s+)?(?:prior|previous)\s+instructions\b",
            re.IGNORECASE,
        ),
    ),
    (
        "role reassignment",
        re.compile(
            r"\byou\s+are\s+now\s+(?:x|an?\s+[a-z][a-z-]*|the\s+[a-z][a-z-]*)\b",
            re.IGNORECASE,
        ),
    ),
    ("false urgency", re.compile(r"\bact\s+now\b", re.IGNORECASE)),
    (
        "authority appeal",
        re.compile(r"\bthe\s+(?:ceo|founder|admin)\s+says\b", re.IGNORECASE),
    ),
    (
        "urgent imperative",
        re.compile(r"\burgent\s*:\s*do\s+.+?\s+immediately\b", re.IGNORECASE),
    ),
)


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


def check_context_classifier_literals(root: Path, skill_files: list[Path]):
    """Keep direct adversarial examples out of model-context Markdown."""
    paths: set[Path] = set()
    rules_dir = root / "rules"
    if rules_dir.is_dir():
        paths.update(rules_dir.rglob("*.md"))
    for skill_file in skill_files:
        paths.update(skill_file.parent.rglob("*.md"))
    for name in ("dispatcher-template.md", "dispatcher.md"):
        path = root / "scripts" / name
        if path.exists():
            paths.add(path)

    offenders: list[str] = []
    for path in sorted(paths):
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            for label, pattern in CONTEXT_CLASSIFIER_PATTERNS:
                if pattern.search(line):
                    offenders.append(f"{path.relative_to(root)}:{lineno}: {label}")

    if offenders:
        fail(
            "PROVIDER-SENSITIVE INSTRUCTION LITERAL IN MODEL CONTEXT:\n  "
            + "\n  ".join(offenders)
            + "\n  Describe adversarial behavior by semantic category; do not quote "
            "the executable instruction in always-loaded rules or skill prose."
        )
    print(f"ok: context classifier literals ({len(paths)} Markdown files)")


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
        if "references/durable-context.md" not in section:
            fail(
                f"DURABLE CONTEXT MISSING SHARED REFERENCE: {path}\n"
                f"  Section must link to references/durable-context.md (the "
                f"generated skill-local copy of rules/durable-context.md); "
                f"a rules/ link is dead in installed copies."
            )
        copy_path = path.parent / "references" / "durable-context.md"
        if not copy_path.exists() or copy_path.read_bytes() != rules_path.read_bytes():
            fail(
                f"DURABLE CONTEXT COPY DRIFT: {copy_path.relative_to(root)}\n"
                f"  Must be a byte-exact generated copy of rules/durable-context.md. "
                f"Run scripts/build_metadata.py (no flags) to regenerate."
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

# A bare repo-relative command in skill prose (`bash skills/...`, `python3
# scripts/...`) resolves against the agent's cwd, which in an installed copy is
# the target project, not the Waza checkout; the command exits 127. Every
# instruction must resolve through the skill's own install path instead:
# a `<skill-base-dir>` placeholder, a resolved variable such as
# `"$(dirname "$HEALTH_SCRIPT")"`, or a candidate cascade.
BARE_INVOCATION_RE = re.compile(
    r'\b(?:bash|sh|python3)\s+(?:\.\./)*(?:skills|scripts)/'
)


def check_portable_invocations(root: Path, skill_files: list[Path]):
    """No skill may tell the agent to run a bare repo-relative command."""
    offenders: list[str] = []
    for skill_md in skill_files:
        scan = [skill_md, *sorted((skill_md.parent / "references").glob("*.md"))]
        for path in scan:
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                if BARE_INVOCATION_RE.search(line) or "<waza>" in line:
                    offenders.append(
                        f"{path.relative_to(root)}:{lineno}: {line.strip()[:120]}"
                    )
    if offenders:
        fail(
            "NON-PORTABLE INVOCATION IN SKILL PROSE:\n  "
            + "\n  ".join(offenders)
            + "\n  Installed copies contain only the skill directory; resolve "
            "commands via <skill-base-dir>, a resolved variable, or a "
            "candidate cascade instead of a bare repo-relative path."
        )
    print(f"ok: skill invocations portable ({len(skill_files)} skills)")


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


def check_english_coaching_guard(root: Path):
    """rules/english.md must keep failure-mode guards intact:
    (1) silence on Chinese-only messages, (2) silence on Korean-only messages,
    (3) silence when English is fine.
    These guards were added after real misfires; do not let them rot."""
    english_rule = root / "rules" / "english.md"
    if not english_rule.exists():
        fail(f"MISSING {english_rule}")
    text = english_rule.read_text()
    missing = []
    if "Chinese-only messages" not in text:
        missing.append("'Chinese-only messages'")
    if "Korean-only messages" not in text:
        missing.append("'Korean-only messages'")
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
