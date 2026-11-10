import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "health" / "scripts" / "check_doc_refs.py"


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink support required")
def test_external_global_instruction_symlink_is_unverifiable_not_missing(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    project.mkdir()
    (home / ".claude").mkdir(parents=True)
    outside.mkdir()
    (project / "AGENTS.md").write_text(
        "Global rules: `~/.claude/CLAUDE.md`.\n", encoding="utf-8"
    )
    (outside / "CLAUDE.md").write_text("PRIVATE_EXTERNAL_CONTENT\n", encoding="utf-8")
    (home / ".claude" / "CLAUDE.md").symlink_to(outside / "CLAUDE.md")

    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), str(project)],
        env={**os.environ, "HOME": str(home)},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0
    assert "UNVERIFIED_EXTERNAL: AGENTS.md:1 -> ~/.claude/CLAUDE.md" in result.stdout
    assert "MISSING:" not in result.stdout
    assert "PRIVATE_EXTERNAL_CONTENT" not in result.stdout


def test_root_guide_reference_resolves_inside_a_skill_directory(tmp_path: Path):
    project = tmp_path / "project"
    references = project / "skills" / "kami" / "references"
    references.mkdir(parents=True)
    (project / "skills" / "kami" / "SKILL.md").write_text("---\nname: kami\n---\n", encoding="utf-8")
    (references / "design.md").write_text("design\n", encoding="utf-8")
    (project / "AGENTS.md").write_text(
        "Paths below are relative to `skills/kami/`.\n"
        "See `references/design.md` and `references/missing.md`.\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), str(project)],
        env={**os.environ, "HOME": str(tmp_path / "home")},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    assert "references/design.md" not in result.stdout
    assert "MISSING: AGENTS.md:2 -> references/missing.md" in result.stdout


def test_npm_scopes_are_not_directory_references(tmp_path: Path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "AGENTS.md").write_text(
        "Run `npx @redocly/cli lint`, test `@vela/<pkg>`, see `@missing/`.\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), str(project)],
        env={**os.environ, "HOME": str(tmp_path / "home")},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert "@redocly" not in result.stdout
    assert "@vela" not in result.stdout
    assert "MISSING: AGENTS.md:1 -> @missing/" in result.stdout
