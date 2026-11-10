import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "health" / "scripts" / "check_moved_lines.py"

GUIDE = (
    "# Guide\n\n"
    "- Never delete files under data/ without a backup.\n"
    "- Release notes follow the last published release.\n"
    "- The site uses one accent color.\n"
)


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        check=True,
        capture_output=True,
    )


def make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    (repo / "AGENTS.md").write_text(GUIDE, encoding="utf-8")
    (repo / "app.py").write_text("print('hi')\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def run(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "HEAD", str(repo), *extra],
        capture_output=True,
        text=True,
        check=False,
    )


def test_whole_line_move_into_path_rule_passes(tmp_path: Path):
    repo = make_repo(tmp_path)
    (repo / "AGENTS.md").write_text(
        "- Never delete files under data/ without a backup.\n"
        "- Release notes follow the last published release.\n",
        encoding="utf-8",
    )
    rules = repo / ".claude" / "rules"
    rules.mkdir(parents=True)
    (rules / "site.md").write_text(
        '---\npaths:\n  - "site/**"\n---\n-   The site uses one accent color.\n',
        encoding="utf-8",
    )

    result = run(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "moved_lines_status: PASS" in result.stdout
    assert "moved_lines_missing: 0" in result.stdout


def test_dropped_line_is_reported_with_its_base_location(tmp_path: Path):
    repo = make_repo(tmp_path)
    (repo / "AGENTS.md").write_text(
        "# Guide\n\n- Release notes follow the last published release.\n"
        "- The site uses one accent color.\n",
        encoding="utf-8",
    )

    result = run(repo)

    assert result.returncode == 1
    assert "moved_lines_missing: 1" in result.stdout
    assert "AGENTS.md:3 - Never delete files under data/ without a backup." in result.stdout


def test_line_moved_outside_instruction_files_counts_only_when_included(tmp_path: Path):
    repo = make_repo(tmp_path)
    (repo / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    docs = repo / "docs"
    docs.mkdir()
    (docs / "agent.md").write_text(GUIDE, encoding="utf-8")

    assert run(repo).returncode == 1
    included = run(repo, "--include", "docs/*.md")
    assert included.returncode == 0, included.stdout


def test_bad_revision_is_an_error_not_a_pass(tmp_path: Path):
    repo = make_repo(tmp_path)

    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "no-such-rev", str(repo)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "moved_lines_status: ERROR" in result.stderr


def test_head_compares_two_commits_regardless_of_the_working_tree(tmp_path: Path):
    repo = make_repo(tmp_path)
    (repo / "AGENTS.md").write_text(
        "- Release notes follow the last published release.\n", encoding="utf-8"
    )
    git(repo, "commit", "-q", "-am", "prune")
    (repo / "AGENTS.md").write_text(GUIDE, encoding="utf-8")

    working_tree = run(repo)
    committed = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "HEAD~1", str(repo), "--head", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert working_tree.returncode == 0, working_tree.stdout
    assert committed.returncode == 1
    assert "moved_lines_head: HEAD" in committed.stdout
    assert "moved_lines_missing: 2" in committed.stdout
    assert "Never delete files under data/ without a backup." in committed.stdout
