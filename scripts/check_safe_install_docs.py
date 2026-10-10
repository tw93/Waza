#!/usr/bin/env python3
"""Reject remote-download-to-shell pipelines in public Markdown examples."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOOK = ROOT / "skills/health/scripts/block-pipe-to-shell.py"


def load_pipe_hook(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("waza_pipe_hook", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pipe-to-shell checker: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def markdown_files(root: Path) -> Iterator[Path]:
    candidates = [root / "README.md", *sorted(root.glob("README_*.md")), root / "AGENTS.md"]
    for directory in (root / "skills", root / "rules"):
        if directory.is_dir():
            candidates.extend(sorted(directory.rglob("*.md")))

    resolved_root = root.resolve()
    for candidate in candidates:
        if not candidate.is_file() or candidate.is_symlink():
            continue
        try:
            candidate.resolve().relative_to(resolved_root)
        except ValueError:
            continue
        yield candidate


def fenced_blocks(path: Path) -> Iterator[tuple[int, str]]:
    marker = ""
    marker_length = 0
    start_line = 0
    body: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if not marker:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                marker = stripped[0]
                marker_length = len(stripped) - len(stripped.lstrip(marker))
                start_line = line_number + 1
                body = []
            continue

        closing_length = len(stripped) - len(stripped.lstrip(marker))
        if closing_length >= marker_length and not stripped[closing_length:].strip():
            yield start_line, "\n".join(body)
            marker = ""
            marker_length = 0
            body = []
        else:
            body.append(line)
    if marker:
        yield start_line, "\n".join(body)


def unsafe_examples(root: Path, hook: ModuleType) -> list[tuple[Path, int]]:
    findings: list[tuple[Path, int]] = []
    for path in markdown_files(root):
        for line_number, block in fenced_blocks(path):
            if hook.pipes_download_to_shell(block):
                findings.append((path, line_number))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--hook", type=Path, default=DEFAULT_HOOK)
    args = parser.parse_args()

    try:
        hook = load_pipe_hook(args.hook)
        findings = unsafe_examples(args.root.resolve(), hook)
    except (OSError, UnicodeError, RuntimeError) as exc:
        print(f"safe install docs check failed: {exc}", file=sys.stderr)
        return 2

    for path, line_number in findings:
        print(f"{path}:{line_number}: remote download is piped to a shell", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
