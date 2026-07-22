"""Windows runtime tests for the Health-owned launcher."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "health" / "SKILL.md"
LAUNCHER = ROOT / "skills" / "health" / "scripts" / "run-health.ps1"
PWSH = shutil.which("pwsh")
WINDOWS_ONLY = pytest.mark.skipif(os.name != "nt", reason="Windows launcher test")


def run_launcher(
    launcher: Path,
    action: str,
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    assert PWSH
    return subprocess.run(
        [PWSH, "-NoLogo", "-NoProfile", "-File", str(launcher), action],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def copy_launcher_fixture(tmp_path: Path, update_body: str) -> Path:
    scripts = tmp_path / "skill with spaces" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(LAUNCHER, scripts / LAUNCHER.name)
    (scripts / "check-update.sh").write_text(update_body, encoding="utf-8")
    (scripts / "collect-data.sh").write_text("printf 'collector-ok\\n'\n", encoding="utf-8")
    return scripts / LAUNCHER.name


def clean_windows_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(
        [
            str(Path(PWSH).parent),
            str(Path(os.environ["SystemRoot"]) / "System32"),
            str(Path(shutil.which("git")).parent),
        ]
    )
    env["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    return env


@WINDOWS_ONLY
def test_derives_git_root_and_builds_child_path_without_mutating_parent(tmp_path: Path):
    launcher = copy_launcher_fixture(tmp_path, "printf '%s\\n' \"$PATH\"\n")
    env = clean_windows_env(tmp_path)
    parent_path = os.environ["PATH"]

    first = run_launcher(launcher, "update", cwd=tmp_path, env=env)
    second = run_launcher(launcher, "update", cwd=tmp_path, env=env)

    assert first.returncode == 0, first.stderr
    assert first.stdout == second.stdout
    child_path = first.stdout.lower().replace("\\\\", "/")
    assert "/usr/bin" in child_path
    assert "/mingw64/bin" in child_path
    assert "program files" in child_path
    assert os.environ["PATH"] == parent_path


@WINDOWS_ONLY
def test_update_check_is_silent_when_network_is_unavailable(tmp_path: Path):
    launcher = copy_launcher_fixture(
        tmp_path,
        (ROOT / "skills" / "health" / "scripts" / "check-update.sh").read_text(),
    )
    env = clean_windows_env(tmp_path)
    env["WAZA_UPDATE_URL"] = "https://127.0.0.1:1/unavailable"
    project = tmp_path / "target project"
    project.mkdir()

    result = run_launcher(launcher, "update", cwd=project, env=env)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert (tmp_path / "cache" / "waza" / "last-check").is_file()
    assert list(project.iterdir()) == []


@WINDOWS_ONLY
def test_main_collector_starts_from_clean_windows_path(tmp_path: Path):
    launcher = copy_launcher_fixture(tmp_path, "exit 0\n")
    env = clean_windows_env(tmp_path)

    result = run_launcher(launcher, "collect", cwd=tmp_path, env=env)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "collector-ok\n"
    assert "not found" not in result.stderr.lower()


@WINDOWS_ONLY
def test_missing_git_bash_has_one_actionable_diagnostic(tmp_path: Path):
    launcher = copy_launcher_fixture(tmp_path, "exit 0\n")
    env = os.environ.copy()
    env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")

    result = run_launcher(launcher, "update", cwd=tmp_path, env=env)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.count("Health requires Git for Windows") == 1


def test_non_windows_collection_command_remains_direct_bash():
    text = SKILL.read_text(encoding="utf-8")

    assert 'bash "$HEALTH_SCRIPT"' in text
