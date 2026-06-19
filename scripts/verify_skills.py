#!/usr/bin/env python3
"""Validate Waza skill metadata, references, marketplace, and resolver invariants.

Driver only. Validation logic lives in two sibling modules so both can be
imported and unit-tested without invoking argparse:
  - `skill_frontmatter.py`  -- parse_frontmatter, parse_when_to_use_keywords, fail
  - `skill_checks.py`       -- all check_* functions

Run as: python3 scripts/verify_skills.py [--root PATH] [--skills-only]

Default --root is the repository root inferred from this file's location.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `from skill_frontmatter import ...` style imports when invoked as a
# standalone script. Tests and codegen import directly via sys.path tricks.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_frontmatter import fail  # noqa: E402
from skill_checks import (  # noqa: E402
    check_anti_patterns_contract,
    check_attribution_leak,
    check_description_conformance,
    check_durable_context_and_paths,
    check_english_coaching_guard,
    check_marketplace,
    check_markdown_links,
    check_no_root_skill,
    check_outcome_contract,
    check_portable_skill_surface,
    check_readme_install_command,
    check_release_workflow_npm_surface,
    check_references,
    check_resolver,
    check_rules_files_present,
    check_skill_files,
    check_skill_update_scripts,
    check_table_pipes,
    check_trigger_overlap,
    check_waza_routing_skills,
    check_waza_routing_triggers,
    collect_all_md,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--skills-only",
        action="store_true",
        help=(
            "Verify only per-skill frontmatter under <root>/skills/. Skips "
            "marketplace.json, RESOLVER.md, README, and root-level checks. "
            "Use when validating an installed copy that does not ship the "
            "build-only files."
        ),
    )
    args = parser.parse_args()
    root = args.root.resolve()

    skill_files, skill_descriptions, skill_keywords = check_skill_files(root)
    skill_names = set(skill_descriptions)
    check_description_conformance(skill_descriptions)
    check_outcome_contract(skill_files)
    if (root / "rules" / "durable-context.md").exists():
        check_durable_context_and_paths(root, skill_files)

    if args.skills_only:
        # Installed copies (e.g. ~/.claude/skills/) don't ship VERSION,
        # marketplace.json, RESOLVER.md, or the repo README. Stop here.
        print(f"ok: skills-only verification passed for {len(skill_files)} skills")
        return 0

    version_file = root / "VERSION"
    if not version_file.exists():
        fail("MISSING VERSION FILE: expected top-level VERSION with one line like '3.24.0'")
    expected_version = version_file.read_text().strip()
    if not expected_version:
        fail("EMPTY VERSION FILE: VERSION must contain one line like '3.24.0'")

    check_marketplace(root, expected_version, skill_names, skill_descriptions)
    check_references(root, skill_files)
    resolver_path = check_resolver(root, skill_names)
    all_md = collect_all_md(root, skill_names, resolver_path)
    check_portable_skill_surface(root, all_md)
    check_markdown_links(root, all_md)
    check_table_pipes(root, all_md)
    check_no_root_skill(root)
    check_trigger_overlap(skill_keywords)
    check_rules_files_present(root)
    check_skill_update_scripts(root, skill_names)
    check_anti_patterns_contract(root)
    check_waza_routing_skills(root, skill_names)
    check_waza_routing_triggers(root)
    check_readme_install_command(root)
    check_release_workflow_npm_surface(root)
    check_english_coaching_guard(root)
    check_attribution_leak(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
