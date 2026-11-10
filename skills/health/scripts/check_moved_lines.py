#!/usr/bin/env python3
"""Check that slimming agent guidance moved lines instead of losing them.

Compares every line of the instruction files at a git base revision with the instruction
files in the working tree (tracked and untracked, ignored files excluded). A line counts as
kept when the same text, whitespace-normalized, still appears in any instruction file, so a
whole-line move into a path rule, a nested guide or a skill reference passes. Headings and
bare markup are not counted. Every line
reported missing must be an approved delete or edit in the prune ledger.

Run as: python3 check_moved_lines.py BASE [ROOT] [--head REV] [--include GLOB ...]

With --head, the comparison is BASE against the committed tree at REV instead of the
working tree, so a prune that was already committed can still be audited for lost lines.

Owns the line-conservation receipt for prune repairs. Read-only: it runs `git ls-tree`,
`git show` and `git ls-files` and never writes. Exit 0 when nothing is missing, 1 when
lines are missing, 2 on usage or git errors.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

INSTRUCTION_GLOBS = (
    "AGENTS.md",
    "*/AGENTS.md",
    "CLAUDE.md",
    "*/CLAUDE.md",
    "GEMINI.md",
    ".claude/rules/*.md",
    ".claude/skills/*.md",
    ".agents/*.md",
    ".cursor/rules/*",
    ".github/copilot-instructions.md",
    ".github/instructions/*.md",
    "skills/*.md",
)
MAX_FILE_BYTES = 2_000_000
MAX_REPORTED = 200
# Headings carry no constraint and vanish when a section moves to its own file.
MARKUP_ONLY = re.compile(r"^(?:#.*|---+|[|:\-\s]+|```\w*|[-*]|\d+\.)$")


def is_instruction(path: str, extra: list[str]) -> bool:
    # fnmatch's `*` crosses `/`, so `*/AGENTS.md` covers nested guides at any depth.
    return any(fnmatch.fnmatch(path, pattern) for pattern in (*INSTRUCTION_GLOBS, *extra))


def normalize(line: str) -> str:
    return " ".join(line.split())


def countable(text: str) -> bool:
    return len(text) >= 3 and not MARKUP_ONLY.match(text)


def git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, check=False
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args[:2])} failed: {detail}")
    return result.stdout


def tree_files(root: Path, base: str, extra: list[str]) -> dict[str, list[str]]:
    names = git(root, "ls-tree", "-r", "-z", "--name-only", base).split(b"\0")
    files: dict[str, list[str]] = {}
    for raw in names:
        name = raw.decode("utf-8", errors="replace")
        if name and is_instruction(name, extra):
            content = git(root, "show", f"{base}:{name}")[:MAX_FILE_BYTES]
            files[name] = content.decode("utf-8", errors="replace").splitlines()
    return files


def current_files(root: Path, extra: list[str]) -> dict[str, list[str]]:
    names = git(
        root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"
    ).split(b"\0")
    files: dict[str, list[str]] = {}
    resolved_root = root.resolve()
    for raw in names:
        name = raw.decode("utf-8", errors="replace")
        if not name or not is_instruction(name, extra):
            continue
        path = root / name
        if path.is_symlink() or not path.is_file():
            continue
        if resolved_root not in path.resolve().parents:
            continue
        with path.open("rb") as handle:
            content = handle.read(MAX_FILE_BYTES)
        files[name] = content.decode("utf-8", errors="replace").splitlines()
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base", help="git revision before the prune, e.g. HEAD or a commit")
    parser.add_argument("root", nargs="?", default=".", help="repo root (default: cwd)")
    parser.add_argument(
        "--head",
        metavar="REV",
        help="compare against this committed revision instead of the working tree",
    )
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="GLOB",
        help="extra instruction path glob, e.g. 'docs/agent/*.md' (repeatable)",
    )
    args = parser.parse_args()
    root = Path(args.root)
    if shutil.which("git") is None:
        print("moved_lines_status: ERROR\nmoved_lines_error: git not found", file=sys.stderr)
        return 2
    try:
        before = tree_files(root, args.base, args.include)
        after = tree_files(root, args.head, args.include) if args.head else current_files(root, args.include)
    except RuntimeError as error:
        print(f"moved_lines_status: ERROR\nmoved_lines_error: {error}", file=sys.stderr)
        return 2

    remaining = Counter(
        text for lines in after.values() for text in map(normalize, lines) if countable(text)
    )
    missing: list[tuple[str, int, str]] = []
    base_count = 0
    for name in sorted(before):
        for number, line in enumerate(before[name], 1):
            text = normalize(line)
            if not countable(text):
                continue
            base_count += 1
            if remaining[text] > 0:
                remaining[text] -= 1
            else:
                missing.append((name, number, text))

    print("=== MOVED LINES ===")
    print(f"moved_lines_status: {'WARN' if missing else 'PASS'}")
    print(f"moved_lines_base: {args.base}")
    print(f"moved_lines_head: {args.head or 'working tree'}")
    print(f"moved_lines_base_files: {len(before)}")
    print(f"moved_lines_current_files: {len(after)}")
    print(f"moved_lines_base_lines: {base_count}")
    print(f"moved_lines_missing: {len(missing)}")
    if missing:
        print("missing_lines (each must be an approved delete or edit in the prune ledger):")
        for name, number, text in missing[:MAX_REPORTED]:
            print(f"  {name}:{number} {text[:160]}")
        if len(missing) > MAX_REPORTED:
            print(f"  ... {len(missing) - MAX_REPORTED} more")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
