"""Validation checks for Waza skills: facade over the domain modules.

Check implementations live in three sibling modules, split by surface:
  - checks_content.py       skill files, prose, references, catalogs
  - checks_distribution.py  marketplaces, Codex mirror, packaging, npm
  - checks_routing.py       RESOLVER.md and waza-routing sync

Import checks from here (verify_skills.py and the pytest unit layer do) so
the full check inventory stays visible in one place. Each function takes the
repository root (and pre-discovered skill metadata where useful) and either
prints `ok:` lines or calls `fail()`. No side effects beyond stdout/stderr.
"""

from __future__ import annotations

from checks_content import (  # noqa: F401
    REF_PATTERN,
    SCRIPT_VAR_PATTERN,
    LINK_RE,
    URL_PREFIXES,
    SEP_RE,
    PERSONAL_PATH_PATTERN,
    PROJECT_RITUAL_RE,
    PRIVATE_CONTEXT_RE,
    FORCED_GITHUB_TOOL_RE,
    CJK_RE,
    DURABLE_CONTEXT_SKILLS,
    NINJA_PREFIX,
    OUTCOME_CONTRACT_FIELDS,
    ATTRIBUTION_PATTERNS,
    CONTEXT_CLASSIFIER_PATTERNS,
    pipe_count,
    check_skill_files,
    check_references,
    check_description_conformance,
    check_outcome_contract,
    check_context_classifier_literals,
    check_durable_context,
    check_personal_paths,
    check_portable_skill_surface,
    collect_all_md,
    check_markdown_links,
    check_table_pipes,
    check_no_root_skill,
    BARE_INVOCATION_RE,
    check_portable_invocations,
    check_anti_patterns_contract,
    check_english_coaching_guard,
    check_attribution_leak,
    check_trigger_overlap,
)
from checks_distribution import (  # noqa: F401
    check_marketplace,
    check_claude_marketplace,
    check_codex_plugin,
    check_codex_plugin_manifest,
    check_codex_plugin_mirror,
    check_codex_marketplace,
    check_rules_files_present,
    check_no_automatic_update_checks,
    check_readme_install_command,
    check_release_workflow_npm_surface,
)
from checks_routing import (  # noqa: F401
    QUOTED_PHRASE_RE,
    check_resolver,
    check_waza_routing_skills,
    check_waza_routing_triggers,
)
