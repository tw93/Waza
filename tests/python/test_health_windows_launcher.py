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
GITATTRIBUTES = ROOT / ".gitattributes"
POWERSHELL = shutil.which("powershell.exe") or shutil.which("pwsh")
WINDOWS_ONLY = pytest.mark.skipif(os.name != "nt", reason="Windows launcher test")

ACTION_SCRIPTS = {
    "collect": "collect-data.sh",
    "agent-context": "check-agent-context.sh",
    "maintainability": "check-maintainability.sh",
    "doc-refs": "check-doc-refs.sh",
    "verifier-output": "check-verifier-output.sh",
}


def run_launcher(
    launcher: Path,
    action: str,
    *script_args: str,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    assert POWERSHELL
    return subprocess.run(
        [
            POWERSHELL,
            "-NoLogo",
            "-NoProfile",
            "-File",
            str(launcher),
            action,
            *script_args,
        ],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=30,
    )


def copy_launcher_fixture(tmp_path: Path) -> Path:
    scripts = tmp_path / "skill with spaces" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(LAUNCHER, scripts / LAUNCHER.name)
    for action, script_name in ACTION_SCRIPTS.items():
        (scripts / script_name).write_text(
            f"printf '{action}:%s\\n' \"$*\"\n",
            encoding="utf-8",
        )
    return scripts / LAUNCHER.name


def clean_windows_env(tmp_path: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join(
        [
            str(Path(POWERSHELL).parent),
            str(Path(os.environ["SystemRoot"]) / "System32"),
            str(Path(shutil.which("git")).parent),
        ]
    )
    env["XDG_CACHE_HOME"] = str(tmp_path / "cache")
    return env


def git_install_root() -> Path:
    current = Path(shutil.which("git")).resolve().parent
    while current != current.parent:
        if (current / "bin" / "bash.exe").is_file() and (current / "usr" / "bin").is_dir():
            return current
        current = current.parent
    raise AssertionError("Git for Windows root not found")


@WINDOWS_ONLY
def test_derives_git_root_and_builds_child_path_without_mutating_parent(tmp_path: Path):
    launcher = copy_launcher_fixture(tmp_path)
    env = clean_windows_env(tmp_path)
    parent_path = os.environ["PATH"]

    result = run_launcher(launcher, "collect", cwd=tmp_path, env=env)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "collect:\n"
    assert os.environ["PATH"] == parent_path


@WINDOWS_ONLY
def test_accepts_install_root_when_git_is_reached_through_a_shim(tmp_path: Path):
    launcher = copy_launcher_fixture(tmp_path)
    env = clean_windows_env(tmp_path)
    env["PATH"] = os.pathsep.join(
        [
            str(Path(POWERSHELL).parent),
            str(Path(os.environ["SystemRoot"]) / "System32"),
        ]
    )
    env["GIT_INSTALL_ROOT"] = str(git_install_root())

    result = run_launcher(launcher, "collect", cwd=tmp_path, env=env)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "collect:\n"


@WINDOWS_ONLY
@pytest.mark.parametrize(("action", "script_name"), ACTION_SCRIPTS.items())
def test_routes_every_health_action_through_git_bash(
    tmp_path: Path, action: str, script_name: str
):
    launcher = copy_launcher_fixture(tmp_path)
    env = clean_windows_env(tmp_path)

    result = run_launcher(
        launcher,
        action,
        "target project",
        "deep",
        cwd=tmp_path,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == f"{action}:target project deep\n"
    assert script_name in LAUNCHER.read_text(encoding="utf-8")
    assert "not found" not in result.stderr.lower()


@WINDOWS_ONLY
def test_real_collector_runs_deep_from_clean_windows_path(tmp_path: Path):
    env = clean_windows_env(tmp_path)
    target = tmp_path / "target project"
    target.mkdir()

    result = run_launcher(
        LAUNCHER,
        "collect",
        "auto",
        "deep",
        cwd=target,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert "=== AI MAINTAINABILITY DETAIL ===" in result.stdout
    assert "not found" not in result.stderr.lower()


@WINDOWS_ONLY
def test_missing_git_bash_has_one_actionable_diagnostic(tmp_path: Path):
    launcher = copy_launcher_fixture(tmp_path)
    env = os.environ.copy()
    env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")

    result = run_launcher(launcher, "collect", cwd=tmp_path, env=env)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr.count("Health requires Git for Windows") == 1


def test_skill_routes_windows_commands_through_launcher():
    text = SKILL.read_text(encoding="utf-8")

    assert "pwsh " not in text
    for action in ACTION_SCRIPTS:
        assert f'run-health.ps1" {action}' in text
    assert 'bash "$HEALTH_SCRIPT"' in text


def test_health_shell_scripts_are_pinned_to_lf():
    result = subprocess.run(
        ["git", "check-attr", "eol", "--", "skills/health/scripts/collect-data.sh"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    )

    assert result.stdout.rstrip().endswith("eol: lf")
    assert "*.sh text eol=lf" in GITATTRIBUTES.read_text(encoding="utf-8")
