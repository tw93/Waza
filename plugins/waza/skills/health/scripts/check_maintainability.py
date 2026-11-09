#!/usr/bin/env python3
"""AI maintainability audit: project shape, context surface, verification surface,
decision artifacts, drift markers, generated mirrors, and markdown links.

Run as: python3 check_maintainability.py [ROOT] [summary|deep]

Owns repository-signal, verifier, doc-link, generated-mirror, and drift receipts. Counts, missing maps, and large files stay informational unless tied to risk or real failure evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.parse
from collections import Counter
from pathlib import Path


# Mechanical definitions (excluded dirs, source extensions, marker regex,
# minified filter) are kept identical with skills/check/scripts/audit_signals.py
# by tests/python/test_auditor_alignment.py; thresholds stay per-product.
EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "dist", "build", ".next",
    "__pycache__", ".turbo", "target", ".venv", "venv", "vendor",
    "coverage", ".cache", ".parcel-cache", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "Pods", "Carthage", ".swiftpm", ".gradle",
}

SOURCE_EXTS = {
    ".bash", ".c", ".cc", ".cpp", ".cs", ".css", ".go", ".h", ".hpp",
    ".html", ".java", ".js", ".jsx", ".kt", ".lua", ".m", ".mjs", ".mm",
    ".md", ".php", ".py", ".rb", ".rs", ".scss", ".sh", ".swift", ".ts",
    ".tsx", ".vue", ".yaml", ".yml", ".zsh",
}

MARKER_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
MARKER_EXAMPLE_RE = re.compile(r"\b(example|placeholder|fixture|marker|taxonomy)\b", re.IGNORECASE)
MINIFIED_RE = re.compile(r"\.min\.[a-z]+$", re.IGNORECASE)
MAKE_RE = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(?![=])")
MAKE_CMD_RE = re.compile(r"\bmake\s+([A-Za-z0-9_.-]+)\b")
NPM_CMD_RE = re.compile(r"\b(?:npm|pnpm|yarn|bun)\s+run\s+([A-Za-z0-9:_-]+)\b")
COMMAND_LINE_RE = re.compile(r"^(?:make|npm|pnpm|yarn|bun)\s+")
VERIFIER_NAME_RE = re.compile(
    r"(?:^|[-_:.])(test|check|lint|type|build|package|verify|smoke)(?:$|[-_:.])",
    re.IGNORECASE,
)
HOLLOW_COMMAND_RE = re.compile(
    r"^(?:echo\b.*|printf\b.*|true|false|:|exit(?:\s+\d+)?|set\s+-[^\s]+|"
    r"cd\b.*|(?:export|readonly|local)\b.*|trap\b.*|umask\b.*|"
    r"(?:mkdir|touch|chmod|chown|cp|mv|rm)\b.*|"
    r"[A-Za-z_][A-Za-z0-9_]*=.*)$",
    re.IGNORECASE,
)
SHELL_OPTION_RE = re.compile(
    r"^set(?:\s+[-+][A-Za-z0-9_-]+)*(?:\s+[A-Za-z0-9_-]+)*$",
    re.IGNORECASE,
)
VERIFIER_COMMAND_RE = re.compile(
    r"(?:"
    r"^(?:test|\[)\s+|"
    r"\bgit\s+diff\s+--check\b|"
    r"^(?:sudo\s+)?(?:shellcheck|pytest|ruff|mypy|eslint|stylelint|biome|hadolint)\b|"
    r"\bpython(?:3)?\s+-m\s+(?:pytest|unittest|compileall|py_compile)\b|"
    r"\b(?:cargo|go|mvn|gradle|deno)\s+(?:test|check|build|verify|vet|clippy)\b|"
    r"\bswift\s+(?:build|test)\b|"
    r"\b(?:npm|pnpm|yarn|bun)\s+(?:test|check|lint|build|verify|pack)\b|"
    r"(?:^|[\s/])[A-Za-z0-9_.-]*(?:test|check|verify|lint|smoke|build)"
    r"[A-Za-z0-9_./-]*\.(?:sh|py)\b"
    r")",
    re.IGNORECASE,
)
SETUP_ONLY_COMMAND_RE = re.compile(
    r"(?:"
    r"\b(?:apt-get|apt|brew)\s+(?:install|update|upgrade)\b|"
    r"\bpython(?:3)?\s+-m\s+pip\s+install\b|"
    r"\bpip(?:3)?\s+install\b|"
    r"\b(?:npm|pnpm|yarn|bun)\s+(?:install|add|publish|view)\b|"
    r"\b(?:curl|wget)\b|"
    r"--version\b"
    r")",
    re.IGNORECASE,
)
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
URL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
RUSTDOC_LINK_RE = re.compile(
    r"(?:^|/)(?:constant|enum|fn|macro|mod|static|struct|trait|type|union)\."
    r"[^/]+\.html$"
)
ACTIONABLE_COMMAND_RE = re.compile(
    r"(?:"
    r"\b(?:run|execute|invoke)\s+$|"
    r"\b(?:build|check|package|test|verify)\s+(?:using|via|with)\s+$|"
    r"\b(?:command|verification|verifier)\s*:\s*$"
    r")",
    re.IGNORECASE,
)
MAX_TEXT_BYTES = 2_000_000
MAX_MIRROR_DIGEST_BYTES = 16_000_000
SECRET_TOKEN_RE = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|"
    r"github_pat_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
    r"AKIA[A-Z0-9]{16}|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\."
    r"[A-Za-z0-9_-]{10,})\b"
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?<![A-Za-z0-9_-])"
    r"(?P<name>-{0,2}(?P<quote>[\x22\x27]?)(?:[A-Za-z0-9]+[_-])*"
    r"(?:secret[_-]access[_-]key|private[_-]?key|api[_-]?key|"
    r"authorization|password|passwd|pwd|token|secret)(?P=quote))"
    r"(?![A-Za-z0-9_-])"
    r"(?P<separator>\s*[:=]\s*)"
    r"(?:Bearer\s+|Basic\s+)?(?:\"(?:\\[^\r\n]|[^\"\\\r\n])*(?:\"|\\?(?=\r?\n|\Z))|"
    r"\x27(?:\\[^\r\n]|[^\x27\\\r\n])*(?:\x27|\\?(?=\r?\n|\Z))|[^\s,;]+)",
    re.IGNORECASE,
)
PRIVATE_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:~[/\\]|/(?:Users|home|private|tmp|var)/)"
    r"[^\s`\"'<>]+"
)
WINDOWS_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z]:\\|\\\\)[^\s`\"'<>]+"
)


# The file-walk helpers below are deliberately duplicated in
# skills/check/scripts/audit_signals.py. Both scripts ship standalone
# (see packaging.allowlist) and run inside an arbitrary target project, so
# they import only stdlib. Do not hoist them into a shared scripts/
# module: it is dev-only, not on the ship allowlist, and would couple a
# standalone tool to the install layout.
def rel(path: Path, root: Path) -> str:
    try:
        value = path.resolve().relative_to(root).as_posix()
    except ValueError:
        value = path.as_posix()
    return safe_label(value)


def safe_label(value: str, limit: int = 500) -> str:
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        value = json.dumps(value, ensure_ascii=False)
    return value if len(value) <= limit else f"{value[: limit - 3]}..."


def redact_command_label(value: str) -> str:
    """Keep verifier inventory useful without emitting secrets or host paths."""
    value = SECRET_TOKEN_RE.sub("[REDACTED]", value)
    value = SECRET_ASSIGNMENT_RE.sub(
        lambda match: f"{match.group('name')}{match.group('separator')}[REDACTED]",
        value,
    )
    value = PRIVATE_PATH_RE.sub("[PATH]", value)
    return WINDOWS_PATH_RE.sub("[PATH]", value)


def is_excluded(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts if path.is_absolute() else path.parts
    if any(part in EXCLUDED_DIRS for part in parts):
        return True
    return bool(MINIFIED_RE.search(path.name))


def is_repo_file(path: Path, root: Path) -> bool:
    """Return true only for a regular file reached without any symlink hop."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    if not relative.parts:
        return False
    current = root
    try:
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                return False
        return current.is_file()
    except OSError:
        return False


def is_repo_dir(path: Path, root: Path) -> bool:
    """Return true only for a directory reached without any symlink hop."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    current = root
    try:
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                return False
        return current.is_dir()
    except OSError:
        return False


def is_safe_repo_reference(path: Path, root: Path) -> bool:
    """Allow documentation symlinks only when their final target stays in-repo."""
    try:
        path.relative_to(root)
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve())
        return resolved.is_file() or resolved.is_dir()
    except (OSError, RuntimeError, ValueError):
        return False


def read_text(path: Path, root: Path, limit: int | None = None) -> str:
    if not is_repo_file(path, root):
        return ""
    byte_limit = limit or MAX_TEXT_BYTES
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
    except OSError:
        return ""
    try:
        chunks: list[bytes] = []
        remaining = byte_limit
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
    except OSError:
        return ""
    finally:
        os.close(descriptor)
    return b"".join(chunks).decode("utf-8", errors="replace")


def file_digest(path: Path, root: Path) -> tuple[int, bytes] | None:
    """Hash a stable regular file without trusting a shared prefix."""
    if not is_repo_file(path, root):
        return None
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
    except OSError:
        return None
    try:
        before = os.fstat(descriptor)
        if before.st_size > MAX_MIRROR_DIGEST_BYTES:
            return None
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, 65_536)
            if not chunk:
                break
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            return None
        return before.st_size, digest.digest()
    except OSError:
        return None
    finally:
        os.close(descriptor)


def iter_files(root: Path) -> list[Path]:
    try:
        proc = subprocess.run(
            [
                "git",
                "-c",
                "core.fsmonitor=false",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            files = []
            for raw_path in proc.stdout.split(b"\0"):
                if not raw_path:
                    continue
                path = root / os.fsdecode(raw_path)
                if is_repo_file(path, root) and not is_excluded(path, root):
                    files.append(path)
            return files
    except OSError:
        pass

    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        dirnames[:] = [
            name for name in dirnames
            if name not in EXCLUDED_DIRS and is_repo_dir(current / name, root)
        ]
        if is_excluded(current, root):
            continue
        for filename in filenames:
            path = current / filename
            if is_repo_file(path, root) and not is_excluded(path, root):
                files.append(path)
    return files


def collapse_generated_mirrors(
    files: list[Path], root: Path
) -> tuple[list[Path], int, list[str], list[str]]:
    """Fold byte-identical Codex plugin mirrors into their source files."""
    file_set = set(files)
    digests: dict[Path, tuple[int, bytes] | None] = {}

    def digest(path: Path) -> tuple[int, bytes] | None:
        if path not in digests:
            digests[path] = file_digest(path, root)
        return digests[path]

    logical: list[Path] = []
    collapsed = 0
    drifted: list[str] = []
    coverage_gaps: list[str] = []
    for path in files:
        try:
            parts = path.relative_to(root).parts
        except ValueError:
            logical.append(path)
            continue
        source: Path | None = None
        if len(parts) >= 4 and parts[0] == "plugins" and parts[2] in {"skills", "rules"}:
            source = root.joinpath(*parts[2:])
        if source is not None and source in file_set:
            mirror_digest = digest(path)
            source_digest = digest(source)
            if mirror_digest is None or source_digest is None:
                coverage_gaps.append(
                    f"{rel(path, root)} -> {rel(source, root)}"
                )
            elif mirror_digest == source_digest:
                collapsed += 1
                continue
            else:
                drifted.append(f"{rel(path, root)} -> {rel(source, root)}")
        logical.append(path)
    return logical, collapsed, drifted, coverage_gaps


def line_count(path: Path, root: Path) -> int:
    if not is_repo_file(path, root):
        return 0
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as handle:
            return sum(1 for _ in handle)
    except OSError:
        return 0


def print_list(items: list[str], empty: str = "(none)", limit: int | None = None) -> None:
    shown = items if limit is None else items[:limit]
    if not shown:
        print(f"  {empty}")
        return
    for item in shown:
        print(f"  {safe_label(item)}")
    if limit is not None and len(items) > limit:
        print(f"  ... {len(items) - limit} more")


def instruction_paths(root: Path) -> list[Path]:
    candidates = [
        root / "AGENTS.md",
        root / "CLAUDE.md",
        root / ".github" / "copilot-instructions.md",
        root / "GEMINI.md",
    ]
    instructions_dir = root / ".github" / "instructions"
    if is_repo_dir(instructions_dir, root):
        candidates.extend(sorted(instructions_dir.glob("*.md")))
    rules_dir = root / ".claude" / "rules"
    if is_repo_dir(rules_dir, root):
        candidates.extend(sorted(rules_dir.glob("*.md")))
    return [
        path for path in candidates
        if is_repo_file(path, root) and not is_excluded(path, root)
    ]


def has_substantive_instruction_evidence(path: Path, root: Path) -> bool:
    """Reject empty/frontmatter/heading-only placeholders as context evidence."""
    in_frontmatter = False
    frontmatter_seen = False
    for raw_line in read_text(path, root, 200_000).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "---" and not frontmatter_seen:
            in_frontmatter = True
            frontmatter_seen = True
            continue
        if line == "---" and in_frontmatter:
            in_frontmatter = False
            continue
        if in_frontmatter or line.startswith("#") or line.startswith("<!--"):
            continue
        return True
    return False


def find_text_signal(paths: list[Path], patterns: list[str], root: Path) -> bool:
    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for path in paths:
        text = read_text(path, root, 200_000)
        if any(regex.search(text) for regex in regexes):
            return True
    return False


def parse_makefile(
    root: Path,
) -> tuple[set[str], list[str], dict[str, tuple[list[str], list[str]]]]:
    makefile = root / "Makefile"
    targets: set[str] = set()
    commands: list[str] = []
    specs: dict[str, tuple[list[str], list[str]]] = {}
    if not is_repo_file(makefile, root):
        return targets, commands, specs
    current_target: str | None = None
    for line in read_text(makefile, root).splitlines():
        match = MAKE_RE.match(line)
        if match:
            target = match.group(1)
            current_target = None
            if target.startswith("."):
                continue
            targets.add(target)
            remainder = line.split(":", 1)[1]
            dependencies_text, separator, inline_recipe = remainder.partition(";")
            dependencies = [
                item for item in dependencies_text.split()
                if not item.startswith("#") and not item.startswith("$")
            ]
            recipes = [inline_recipe.strip()] if separator and inline_recipe.strip() else []
            specs[target] = (dependencies, recipes)
            current_target = target
            if VERIFIER_NAME_RE.search(target):
                commands.append(f"make {target}")
            continue
        if current_target and line.startswith("\t"):
            dependencies, recipes = specs[current_target]
            recipes.append(line.strip())
        elif line.strip() and not line.lstrip().startswith("#"):
            current_target = None
    return targets, commands, specs


def parse_package_json(root: Path) -> tuple[set[str], list[str], dict[str, str]]:
    package = root / "package.json"
    script_names: set[str] = set()
    commands: list[str] = []
    script_specs: dict[str, str] = {}
    if not is_repo_file(package, root):
        return script_names, commands, script_specs
    try:
        data = json.loads(read_text(package, root))
    except json.JSONDecodeError:
        return script_names, commands, script_specs
    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        return script_names, commands, script_specs
    for name in sorted(scripts):
        script_names.add(name)
        value = scripts[name]
        if isinstance(value, str):
            script_specs[name] = value
        if VERIFIER_NAME_RE.search(name):
            commands.append(f"npm run {name}")
    return script_names, commands, script_specs


def parse_ci_commands(root: Path) -> list[tuple[str, str]]:
    workflows_dir = root / ".github" / "workflows"
    workflows = (
        sorted(path for path in workflows_dir.glob("*.yml") if is_repo_file(path, root))
        if is_repo_dir(workflows_dir, root) else []
    )
    workflows += (
        sorted(path for path in workflows_dir.glob("*.yaml") if is_repo_file(path, root))
        if is_repo_dir(workflows_dir, root) else []
    )
    commands: list[tuple[str, str]] = []
    for workflow in workflows:
        lines = read_text(workflow, root).splitlines()
        index = 0
        while index < len(lines):
            raw = lines[index]
            line = raw.strip()
            if line.startswith("- run:"):
                command = line.split("- run:", 1)[1].strip()
            elif line.startswith("run:"):
                command = line.split("run:", 1)[1].strip()
            else:
                index += 1
                continue
            if command in {"|", ">", "|-", ">-"}:
                base_indent = len(raw) - len(raw.lstrip())
                block: list[str] = []
                index += 1
                while index < len(lines):
                    candidate = lines[index]
                    candidate_indent = len(candidate) - len(candidate.lstrip())
                    if candidate.strip() and candidate_indent <= base_indent:
                        break
                    if candidate.strip():
                        block.append(candidate.strip())
                    index += 1
                command = "; ".join(block)
            else:
                if len(command) >= 2 and command[0] == command[-1] and command[0] in "'\"":
                    command = command[1:-1]
                index += 1
            if command:
                label = redact_command_label(f"{rel(workflow, root)}: {command}")
                commands.append((label, command))
    return commands


def shell_script_has_verifier_evidence(path: Path, root: Path) -> bool:
    """Reject scripts whose only behavior is setup, printing, or a fixed exit."""
    text = read_text(path, root, 200_000)
    meaningful: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#!") or line.startswith("#"):
            continue
        normalized = line.lstrip("@-+")
        normalized = re.split(r"\s+#", normalized, maxsplit=1)[0].rstrip()
        if (
            HOLLOW_COMMAND_RE.fullmatch(normalized)
            or SHELL_OPTION_RE.fullmatch(normalized)
            or SETUP_ONLY_COMMAND_RE.search(normalized)
        ):
            continue
        meaningful.append(line)
    return bool(meaningful)


def command_is_verifier_candidate(command: str) -> bool:
    """Return whether a command claims or resembles a verification entrypoint."""
    normalized = command.strip().lstrip("@-+").strip()
    if any(VERIFIER_NAME_RE.search(target) for target in MAKE_CMD_RE.findall(normalized)):
        return True
    if any(VERIFIER_NAME_RE.search(script) for script in NPM_CMD_RE.findall(normalized)):
        return True
    script_call = re.search(r"(?:^|\s)(?:bash\s+|sh\s+)?([^\s;&|]+)", normalized)
    if script_call and VERIFIER_NAME_RE.search(Path(script_call.group(1)).name):
        return True
    return bool(VERIFIER_COMMAND_RE.search(normalized))


def command_has_verifier_evidence(
    command: str,
    root: Path,
    make_specs: dict[str, tuple[list[str], list[str]]],
    package_specs: dict[str, str],
    visiting: frozenset[str] = frozenset(),
    trusted_entrypoint: bool = False,
) -> bool:
    """Return whether a discovered command can do more than print or exit."""
    normalized = command.strip().lstrip("@-+").strip()
    if not normalized:
        return False

    make_only = re.fullmatch(
        r"(?:make|\$\(MAKE\))\s+([A-Za-z0-9_.-]+)(?:\s+[^;&|]+)?", normalized
    )
    if make_only:
        target = make_only.group(1)
        if not trusted_entrypoint and not VERIFIER_NAME_RE.search(target):
            return False
        key = f"make:{target}"
        if key in visiting or target not in make_specs:
            return False
        dependencies, recipes = make_specs[target]
        next_visiting = visiting | {key}
        if any(
            command_has_verifier_evidence(
                recipe, root, make_specs, package_specs, next_visiting, True
            )
            for recipe in recipes
        ):
            return True
        return any(
            command_has_verifier_evidence(
                f"make {dependency}", root, make_specs, package_specs, next_visiting, True
            )
            for dependency in dependencies
            if dependency in make_specs
        )

    package_only = re.fullmatch(
        r"(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?([A-Za-z0-9:_-]+)(?:\s+[^;&|]+)?",
        normalized,
    )
    if package_only:
        script = package_only.group(1)
        builtin_verifier = script == "pack" and "--dry-run" in normalized
        if (
            not trusted_entrypoint
            and not builtin_verifier
            and not VERIFIER_NAME_RE.search(script)
        ):
            return False
        key = f"package:{script}"
        if key in visiting:
            return False
        if script in package_specs:
            return command_has_verifier_evidence(
                package_specs[script], root, make_specs, package_specs, visiting | {key}, True
            )
        if re.match(r"(?:npm|pnpm|yarn|bun)\s+run\s+", normalized):
            return False
        if not builtin_verifier:
            return False

    script_call = re.fullmatch(
        r"(?:(?:bash|sh)\s+)?(\.?\.?/[A-Za-z0-9_./-]+\.sh)(?:\s+.*)?",
        normalized,
    )
    if script_call:
        script_path = root / script_call.group(1)
        named_as_verifier = bool(VERIFIER_NAME_RE.search(script_path.name))
        return (trusted_entrypoint or named_as_verifier) and shell_script_has_verifier_evidence(
            script_path, root
        )

    fragments = [
        fragment.strip().lstrip("@-+").strip()
        for fragment in re.split(r"\s*(?:&&|\|\||;)\s*", normalized)
        if fragment.strip()
    ]
    substantive = [
        fragment for fragment in fragments
        if not HOLLOW_COMMAND_RE.fullmatch(fragment)
        and not SHELL_OPTION_RE.fullmatch(fragment)
        and not SETUP_ONLY_COMMAND_RE.search(fragment)
    ]
    if not substantive:
        return False
    return trusted_entrypoint or any(
        VERIFIER_COMMAND_RE.search(fragment) for fragment in substantive
    )


def scan_markdown_links(files: list[Path], root: Path) -> list[str]:
    missing: list[str] = []
    markdown_files = [path for path in files if path.suffix.lower() == ".md"]
    for path in markdown_files:
        fence: tuple[str, int] | None = None
        for lineno, line in enumerate(read_text(path, root).splitlines(), 1):
            fence_match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
            if fence_match:
                marker = fence_match.group(1)
                if fence is None:
                    fence = (marker[0], len(marker))
                elif marker[0] == fence[0] and len(marker) >= fence[1]:
                    fence = None
                continue
            if fence is not None:
                continue
            for raw in MARKDOWN_LINK_RE.findall(strip_markdown_inline_code(line)):
                target = raw.strip().split()[0].strip("<>")
                if not target or target.startswith("#") or URL_RE.match(target):
                    continue
                target = urllib.parse.unquote(target.split("#", 1)[0])
                if not target:
                    continue
                # A leading slash is a site-root route, not a filesystem-relative
                # Markdown reference. Its validity belongs to the site's route or
                # link checker; treating it as /path/on/the/audit-host is a false
                # broken-doc finding.
                if target.startswith("/"):
                    continue
                if is_rustdoc_generated_link(path, target, root):
                    continue
                full = path.parent / target
                if not is_safe_repo_reference(full, root):
                    missing.append(f"{rel(path, root)}:{lineno} -> {target}")
    return missing


def strip_markdown_inline_code(line: str) -> str:
    """Blank inline code spans while preserving non-code Markdown text."""
    output: list[str] = []
    open_ticks = 0
    index = 0
    while index < len(line):
        if line[index] != "`":
            output.append(line[index] if open_ticks == 0 else " ")
            index += 1
            continue
        end = index
        while end < len(line) and line[end] == "`":
            end += 1
        run = end - index
        if open_ticks == 0:
            open_ticks = run
        elif run == open_ticks:
            open_ticks = 0
        output.extend(" " * run)
        index = end
    return "".join(output)


def is_rustdoc_generated_link(source: Path, target: str, root: Path) -> bool:
    """Recognize links that Rustdoc resolves only in generated crate docs."""
    if not RUSTDOC_LINK_RE.search(target):
        return False
    current = source.parent
    while True:
        if is_repo_file(current / "Cargo.toml", root):
            return True
        if current == root:
            return False
        try:
            current.relative_to(root)
        except ValueError:
            return False
        current = current.parent


def actionable_inline_command_snippets(line: str) -> list[str]:
    snippets: list[str] = []
    for match in re.finditer(r"`([^`]+)`", line):
        if ACTIONABLE_COMMAND_RE.search(line[: match.start()]):
            snippets.append(match.group(1))
    return snippets


def verification_surface(
    root: Path, instruction_files: list[Path], files: list[Path]
) -> tuple[list[str], list[str], list[str], list[str], set[str], set[str]]:
    make_targets, make_commands, make_specs = parse_makefile(root)
    package_scripts, package_commands, package_specs = parse_package_json(root)
    ci_commands = parse_ci_commands(root)
    commands = make_commands + package_commands + [label for label, _ in ci_commands]
    evidence: list[str] = []
    hollow: list[str] = []

    for command in make_commands + package_commands:
        destination = evidence if command_has_verifier_evidence(
            command, root, make_specs, package_specs
        ) else hollow
        destination.append(command)
    for label, raw_command in ci_commands:
        if command_has_verifier_evidence(raw_command, root, make_specs, package_specs):
            evidence.append(label)
        elif command_is_verifier_candidate(raw_command):
            hollow.append(label)

    if is_repo_file(root / "Cargo.toml", root):
        commands.extend(["cargo test", "cargo check"])
        evidence.extend(["cargo test", "cargo check"])
    if is_repo_file(root / "go.mod", root):
        commands.append("go test ./...")
        evidence.append("go test ./...")
    if is_repo_file(root / "Package.swift", root):
        commands.append("swift test")
        evidence.append("swift test")
    pyproject = root / "pyproject.toml"
    pytest_configured = is_repo_file(root / "pytest.ini", root) or (
        is_repo_file(pyproject, root)
        and bool(re.search(r"\bpytest\b", read_text(pyproject, root, 200_000), re.IGNORECASE))
    )
    python_tests_present = any(
        path.suffix.lower() == ".py"
        and (
            path.name.startswith("test_")
            or path.name.endswith("_test.py")
            or any(
                part.lower() in {"test", "tests", "spec", "specs"}
                for part in path.relative_to(root).parts[:-1]
            )
        )
        for path in files
    )
    if pytest_configured:
        commands.append("pytest")
        if python_tests_present:
            evidence.append("pytest")
    if is_repo_file(root / "pom.xml", root):
        commands.append("mvn test")
        evidence.append("mvn test")
    if is_repo_file(root / "deno.json", root) or is_repo_file(root / "deno.jsonc", root):
        commands.append("deno test")
        evidence.append("deno test")

    missing: list[str] = []
    for path in instruction_files:
        text = read_text(path, root, 200_000)
        snippets: list[str] = []
        for raw_line in text.splitlines():
            snippets.extend(actionable_inline_command_snippets(raw_line))
            stripped = raw_line.strip().strip("`")
            if COMMAND_LINE_RE.match(stripped):
                snippets.append(stripped)
        for snippet in snippets:
            for target in MAKE_CMD_RE.findall(snippet):
                if target not in make_targets:
                    missing.append(f"{rel(path, root)} references missing make target: {target}")
            for script in NPM_CMD_RE.findall(snippet):
                if script not in package_scripts:
                    missing.append(f"{rel(path, root)} references missing package script: {script}")

    unique_commands = list(dict.fromkeys(commands))
    unique_evidence = list(dict.fromkeys(evidence))
    unique_hollow = list(dict.fromkeys(hollow))
    unique_missing = list(dict.fromkeys(missing))
    return (
        unique_commands,
        unique_evidence,
        unique_hollow,
        unique_missing,
        make_targets,
        package_scripts,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="Repo root (default: cwd)")
    parser.add_argument(
        "mode", nargs="?", default="summary", choices=("summary", "deep"),
        help="Output detail level",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    mode = args.mode

    if not root.is_dir():
        print(f"Repo root not found: {safe_label(root.as_posix())}", file=sys.stderr)
        return 2

    files = iter_files(root)
    (
        logical_files,
        generated_mirror_files_collapsed,
        generated_mirror_drift,
        generated_mirror_coverage_gaps,
    ) = collapse_generated_mirrors(files, root)
    tracked_count = len(files)
    extensions = Counter(path.suffix.lower() or "(none)" for path in files)
    detected_manifests = [
        name
        for name in [
            "Makefile", "package.json", "Cargo.toml", "go.mod", "Package.swift",
            "pyproject.toml",
            "pytest.ini", "pom.xml", "deno.json", "deno.jsonc",
        ]
        if is_repo_file(root / name, root)
    ]
    workflows_dir = root / ".github" / "workflows"
    workflow_count = 0
    if is_repo_dir(workflows_dir, root):
        workflow_count = sum(
            1
            for path in list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            if is_repo_file(path, root)
        )
    if workflow_count:
        detected_manifests.append(f".github/workflows ({workflow_count})")

    source_files = [path for path in logical_files if path.suffix.lower() in SOURCE_EXTS]
    implementation_files = [
        path
        for path in source_files
        if path.suffix.lower() not in {".css", ".html", ".md", ".scss", ".yaml", ".yml"}
    ]
    source_stats: list[tuple[int, int, Path]] = []
    for path in source_files:
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        source_stats.append((line_count(path, root), size, path))
    source_stats.sort(key=lambda item: (item[0], item[1]), reverse=True)

    dir_counts: Counter[str] = Counter()
    for path in files:
        relative_parts = Path(rel(path, root)).parts
        top = relative_parts[0] if len(relative_parts) > 1 else "."
        dir_counts[top] += 1

    instruction_files = instruction_paths(root)
    instruction_evidence_files = [
        path for path in instruction_files
        if has_substantive_instruction_evidence(path, root)
    ]
    instruction_verification = find_text_signal(
        instruction_files,
        [r"verification", r"test plan", r"make test", r"npm test", r"pytest", r"cargo test", r"验证", r"测试"],
        root,
    )
    boundaries = find_text_signal(
        instruction_files,
        [r"not for", r"do not", r"non-?goals?", r"scope", r"boundar", r"never", r"avoid", r"边界", r"非目标", r"不要"],
        root,
    )
    (
        commands,
        verifier_evidence,
        hollow_verifiers,
        missing_references,
        make_targets,
        package_scripts,
    ) = verification_surface(root, instruction_files, files)
    stable_make_targets = sorted(make_targets & {"check", "test", "verify"})
    stable_package_commands = {
        f"npm run {name}" for name in package_scripts & {"check", "test", "verify"}
    } & set(verifier_evidence)
    wrapper_warnings: list[str] = []
    if (
        len(commands) >= 2
        and is_repo_file(root / "Makefile", root)
        and not stable_make_targets
        and not stable_package_commands
    ):
        wrapper_warnings.append(
            "multiple verification commands discovered without a recognized make/npm default; "
            "check documented or native entrypoints before recommending a wrapper"
        )

    decision_artifacts = {
        "docs_dir": is_repo_dir(root / "docs", root),
        "specs_dir": is_repo_dir(root / "specs", root),
        "specify_dir": is_repo_dir(root / ".specify", root),
        "handoff_md": any(
            path.name.upper() == "HANDOFF.MD" and is_repo_file(path, root)
            for path in root.glob("*.md")
        ),
        "changelog": any(
            path.name.upper().startswith("CHANGELOG") and is_repo_file(path, root)
            for path in root.glob("*")
        ),
        "issue_templates": is_repo_dir(root / ".github" / "ISSUE_TEMPLATE", root),
        "pr_template": any(
            is_repo_file(path, root)
            for path in [
                root / ".github" / "pull_request_template.md",
                root / ".github" / "PULL_REQUEST_TEMPLATE.md",
            ]
        ),
    }

    todo_counts: Counter[str] = Counter()
    todo_total = 0
    fixture_marker_lines_ignored = 0
    for path in source_files:
        text = read_text(path, root, 200_000)
        # Count marker-bearing lines, not marker words. Documentation often names
        # the full marker family in one rule line; treating that as four issues
        # makes the checker flag itself instead of real open-task piles.
        relative = Path(rel(path, root))
        is_fixture = (
            any(part in {"test", "tests", "spec", "specs", "fixtures"} for part in relative.parts)
            or bool(re.search(r"(?:^|[._-])(?:test|tests|spec|specs)(?:[._-]|$)", relative.name.lower()))
        )
        count = 0
        for line in text.splitlines():
            if not MARKER_RE.search(line):
                continue
            marker_taxonomy = all(marker in line.upper() for marker in ("TODO", "FIXME", "HACK", "XXX"))
            documented_example = (
                path.suffix.lower() == ".md" and MARKER_EXAMPLE_RE.search(line)
            )
            if is_fixture or marker_taxonomy or documented_example:
                fixture_marker_lines_ignored += 1
                continue
            count += 1
        if count:
            todo_counts[rel(path, root)] += count
            todo_total += count

    todo_hotspots = [
        f"{path} markers={count}" for path, count in todo_counts.most_common(8 if mode == "deep" else 5)
    ]

    doc_ref_status = "unavailable"
    doc_ref_detail = ""
    checker = Path(__file__).with_name("check_doc_refs.py")
    if checker.is_file():
        proc = subprocess.run(
            [sys.executable, "-I", str(checker), str(root)],
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        doc_ref_status = "pass" if proc.returncode == 0 else "fail"
        if proc.stdout.strip():
            first_lines = proc.stdout.strip().splitlines()[:8]
            doc_ref_detail = " | ".join(first_lines)

    has_verifier_evidence = bool(verifier_evidence)
    verification_expected = bool(
        implementation_files or detected_manifests or workflow_count
    )
    context_expected = bool(
        implementation_files
        or workflow_count
        or any(manifest != "Makefile" for manifest in detected_manifests)
    )
    context_findings: list[str] = []
    verification_warnings: list[str] = []
    drift_warnings: list[str] = []

    if context_expected and not instruction_evidence_files:
        context_findings.append(
            "no tracked instruction evidence; non-obvious project constraint reachability is unknown"
        )
    if verification_expected and not has_verifier_evidence:
        if hollow_verifiers:
            verification_warnings.append(
                "discovered verifier entrypoints are hollow or non-substantive"
            )
        elif commands:
            verification_warnings.append(
                "commands were discovered, but none provide substantive verifier evidence"
            )
        else:
            verification_warnings.append("no substantive verifier evidence discovered")
    if missing_references:
        verification_warnings.append("instruction references missing commands")
    if generated_mirror_drift:
        drift_warnings.append("generated mirrors differ from their source files")
    if generated_mirror_coverage_gaps:
        drift_warnings.append("generated mirror comparison exceeded the bounded digest surface")
    if doc_ref_status == "fail":
        drift_warnings.append("broken documentation references")

    markdown_missing: list[str] = []
    markdown_link_status = "SKIPPED"
    if mode == "deep":
        markdown_missing = scan_markdown_links(files, root)
        markdown_link_status = "WARN" if markdown_missing else "PASS"
        if markdown_missing:
            drift_warnings.append("broken Markdown links")

    if instruction_evidence_files:
        context_status = "PASS"
    elif context_expected:
        context_status = "UNKNOWN"
    else:
        context_status = "NOT_APPLICABLE"
    verification_status = (
        "FAIL"
        if verification_expected and not has_verifier_evidence
        else ("WARN" if verification_warnings else "PASS")
    )
    decision_status = "PASS"
    wrapper_status = "WARN" if wrapper_warnings else "PASS"
    drift_status = "WARN" if drift_warnings else "PASS"

    if context_status == "FAIL" or verification_status == "FAIL" or doc_ref_status == "fail":
        overall = "FAIL"
    elif context_status == "UNKNOWN" or "WARN" in {
        context_status, verification_status, decision_status, wrapper_status,
        drift_status, markdown_link_status,
    }:
        overall = "WARN"
    else:
        overall = "PASS"

    top_ext = [f"{ext} files={count}" for ext, count in extensions.most_common(10)]
    largest_sources = [
        f"{rel(path, root)} lines={lines} bytes={size}"
        for lines, size, path in source_stats[: (10 if mode == "deep" else 5)]
    ]
    largest_dirs = [f"{directory} files={count}" for directory, count in dir_counts.most_common(8)]

    print("=== PROJECT SHAPE ===")
    print(f"maintainability_status: {overall}")
    print(f"mode: {mode}")
    print(f"tracked_files: {tracked_count}")
    print(f"generated_mirror_files_collapsed: {generated_mirror_files_collapsed}")
    print(f"generated_mirror_files_drifted: {len(generated_mirror_drift)}")
    print(f"generated_mirror_comparison_gaps: {len(generated_mirror_coverage_gaps)}")
    print("generated_mirror_drift:")
    print_list(generated_mirror_drift, limit=10)
    print("generated_mirror_coverage_gaps:")
    print_list(generated_mirror_coverage_gaps, limit=10)
    print("top_extensions:")
    print_list(top_ext)
    print("largest_source_files:")
    print_list(largest_sources)
    print("largest_directories:")
    print_list(largest_dirs)

    print("=== AI CONTEXT SURFACE ===")
    print(f"context_status: {context_status}")
    print(f"AGENTS.md: {'yes' if is_repo_file(root / 'AGENTS.md', root) else 'no'}")
    print(f"CLAUDE.md: {'yes' if is_repo_file(root / 'CLAUDE.md', root) else 'no'}")
    print(f".github/copilot-instructions.md: {'yes' if is_repo_file(root / '.github' / 'copilot-instructions.md', root) else 'no'}")
    github_instruction_count = (
        sum(
            1
            for path in (root / ".github" / "instructions").glob("*.md")
            if is_repo_file(path, root)
        )
        if is_repo_dir(root / ".github" / "instructions", root) else 0
    )
    print(f".github/instructions/*.md: {github_instruction_count}")
    print(f"GEMINI.md: {'yes' if is_repo_file(root / 'GEMINI.md', root) else 'no'}")
    print(f"verification_guidance: {'yes' if instruction_verification else 'no'}")
    print(f"boundary_guidance: {'yes' if boundaries else 'no'}")
    print("context_findings:")
    print_list(context_findings)
    print("instruction_files:")
    print_list([rel(path, root) for path in instruction_files])
    print("instruction_evidence_files:")
    print_list([rel(path, root) for path in instruction_evidence_files])

    print("=== VERIFICATION SURFACE ===")
    print(f"verification_status: {verification_status}")
    print("detected_manifests:")
    print_list(detected_manifests)
    print("commands:")
    print_list(commands, limit=12 if mode == "summary" else None)
    print("verifier_evidence:")
    print_list(verifier_evidence, limit=12 if mode == "summary" else None)
    print("hollow_verifiers:")
    print_list(hollow_verifiers, limit=12 if mode == "summary" else None)
    print("missing_referenced_commands:")
    print_list(missing_references, limit=10 if mode == "summary" else None)
    print("verification_findings:")
    print_list(verification_warnings)

    print("=== VERIFICATION WRAPPER SURFACE ===")
    print(f"wrapper_status: {wrapper_status}")
    print(f"makefile_present: {'yes' if is_repo_file(root / 'Makefile', root) else 'no'}")
    print("stable_make_targets:")
    print_list([f"make {target}" for target in stable_make_targets])
    print("wrapper_findings:")
    print_list(wrapper_warnings)

    print("=== DECISION ARTIFACTS ===")
    print(f"decision_artifacts_status: {decision_status}")
    for key, value in decision_artifacts.items():
        print(f"{key}: {'yes' if value else 'no'}")

    print("=== DRIFT MARKERS ===")
    print(f"drift_status: {drift_status}")
    print(f"todo_markers: {todo_total}")
    print(f"fixture_or_instruction_marker_lines_ignored: {fixture_marker_lines_ignored}")
    print("todo_hotspots:")
    print_list(todo_hotspots)
    print(f"broken_doc_references: {doc_ref_status}")
    if doc_ref_detail and (mode == "deep" or doc_ref_status == "fail"):
        print(f"broken_doc_reference_detail: {safe_label(doc_ref_detail)}")
    print("drift_findings:")
    print_list(drift_warnings)

    print("=== MARKDOWN LINK SURFACE ===")
    print(f"markdown_link_status: {markdown_link_status}")
    print("missing_markdown_links:")
    if mode == "deep":
        print_list(markdown_missing, limit=20)
    else:
        print("  (skipped: deep mode only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
