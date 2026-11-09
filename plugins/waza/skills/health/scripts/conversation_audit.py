#!/usr/bin/env python3
"""Stream Claude and Codex project JSONL into bounded, redacted health evidence.

Deep mode scans every previous session for signals. Summary mode scans up to
three recent previous sessions from a bounded candidate window. Every file
modified inside the live window is excluded so parallel active sessions cannot
become evidence. Codex sessions are included when their session metadata resolves
inside the target project root. This is a project-scoped audit unless the caller
explicitly enables all-project mode.

Owns project-scoped, redacted conversation signals and coverage receipts. Structured runtime events define interruptions; cloned history must not multiply corrections.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from collections import Counter, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional


MAX_SIGNALS = 20
MAX_FILE_LIST = 10
EXTRACT_HEAD = 30
EXTRACT_TAIL = 120
MAX_SIGNAL_CHARS = 320
MAX_EXTRACT_CHARS = 800
MAX_MESSAGE_CHARS = 4096
MAX_RECORD_CHARS = 1_048_576
MAX_CONTENT_ITEMS = 256
MAX_TOOL_NAME_CHARS = 120
LIVE_WINDOW_SECONDS = 300
SUMMARY_CANDIDATE_LIMIT = 200
MIN_CLONE_CONTEXT_MESSAGES = 4

CONTEXT_RE = re.compile(
    r"conversation was compressed|context limit|context window|truncat|/compact|"
    r"context management|token limit|window is full|compaction|"
    r"会话已压缩|上下文窗口|上下文限制",
    re.IGNORECASE,
)
CORRECTION_RE = re.compile(
    r"^(?:please[ :]*)?(?:you misunderstood|that(?:'s| is) not what i meant|"
    r"do not do that again|please don't|don't|do not|stop|next time|"
    r"use\b.{0,100}\binstead\b|not\b.{0,100}\bbut\b)|"
    r"^.{0,20}(?:你理解错|理解有误|我说的是|肯定不是|不是.{0,32}而是|"
    r"还是不对|怎么还有问题|还是有问题|请不要|不要再|不要|"
    r"别再|别用|下次|改成|改为|少一点|短一点|简单一点|去掉|统一成)",
    re.IGNORECASE,
)
DELIVERY_RE = re.compile(
    r"为啥不提交|都提交了吗|全部提交了吗|全部\s*push(?:了吗)?|"
    r"push了吗|提交了吗|why (?:didn't|did not) you (?:commit|push)",
    re.IGNORECASE,
)
PERSISTENCE_RE = re.compile(r"^(?:继续|continue|keep going)[.!。！\s]*$", re.IGNORECASE)
PLATFORM_INTERRUPTION_RE = re.compile(
    r"API Error|No response requested|Request interrupted|response failed|"
    r"connection (?:closed|reset)|internal server error",
    re.IGNORECASE,
)
JAPANESE_RE = re.compile(r"[ぁ-んァ-ヶ]")
CJK_RE = re.compile(r"[\u3400-\u9fffぁ-んァ-ヶ]")
JAPANESE_REQUEST_RE = re.compile(
    r"(?:请\s*)?(?:用|改用|切换到)\s*(?:日语|日文).{0,12}(?:回复|回答|输出)|"
    r"(?:回复|回答|输出).{0,12}(?:日语|日文)|"
    r"(?:reply|respond|answer|output).{0,20}(?:in\s+)?japanese|"
    r"(?:use|switch\s+to)\s+japanese(?:\s+for\s+(?:the\s+)?(?:reply|response|answer|output))?|"
    r"日本語で.{0,12}(?:返信|回答|出力)",
    re.IGNORECASE,
)
THEME_PATTERNS = {
    "authorization_delivery": re.compile(
        r"提交|commit|push|发布|publish|回复|关闭|close|不要提交|先不要提交",
        re.IGNORECASE,
    ),
    "completion_persistence": re.compile(
        r"全部|所有|彻底|查漏补缺|不要留下次|继续|做完|完成|仔细看看|"
        r"all of|everything|finish|keep going|continue",
        re.IGNORECASE,
    ),
    "simplicity_scope": re.compile(
        r"不要增加复杂度|如无必要勿增实体|过度设计|不要过度|臃肿|"
        r"keep it simple|over.?design|unnecessary",
        re.IGNORECASE,
    ),
    "brevity_style": re.compile(
        r"啰嗦|短一点|简短|简单一点|字太多|少一点|concise|shorter|too long",
        re.IGNORECASE,
    ),
    "visual_product_judgment": re.compile(
        r"图片|按钮|focus|边框|布局|界面|样式|高度|宽度|菜单|UI|视觉|"
        r"image|button|border|layout|menu",
        re.IGNORECASE,
    ),
    "localization_wording": re.compile(
        r"中文|英文|日语|日文|文案|翻译|单词|措辞|叫法|wording|translation",
        re.IGNORECASE,
    ),
    "release_version_truth": re.compile(
        r"版本|发布|release|nightly|preview|stable|appcast|已经上线|已经发布",
        re.IGNORECASE,
    ),
    "verification_evidence": re.compile(
        r"仔细|分析|判断|验证|测试|复核|看看所有|证据|verify|test|audit|evidence",
        re.IGNORECASE,
    ),
}
INJECTED_PREFIXES = (
    "<task-notification",
    "<permissions",
    "<environment_context",
    "<multi_agent",
    "<system-reminder",
    "<recommended_plugins",
    "# AGENTS.md instructions",
)

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SECRET_RE = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{12,}|"
    r"github_pat_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{10,}|"
    r"AKIA[A-Z0-9]{16}|"
    r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b"
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
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?P<label>(?:(?:OPENSSH|RSA|EC|DSA|ENCRYPTED) )?PRIVATE KEY)-----"
    r".*?(?:-----END (?P=label)-----|$)",
    re.DOTALL,
)
HASH_RE = re.compile(r"\b[0-9a-f]{32,}\b", re.IGNORECASE)
ABS_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])/(?:Users|home|private|tmp|var|etc|opt|Volumes)/[^\s`\"'<>]+"
)
TILDE_PATH_RE = re.compile(r"(?<![A-Za-z0-9_])~/(?:[^\s`\"'<>]+)")
WINDOWS_ABS_PATH_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Za-z]:\\|\\\\)[^\s`\"'<>]+"
)


@dataclass
class ConversationFile:
    path: Path
    mtime: float
    mtime_ns: int
    size: int
    device: int
    inode: int
    runtime: str = "claude_project_logs"


@dataclass
class Message:
    role: str
    text: str
    ordinal: int


@dataclass
class Signal:
    label: str
    text: str
    file: str
    mtime: float
    ordinal: int
    runtime: str
    lineage: str
    message_index: int


@dataclass
class ScanStats:
    files_read: int = 0
    bytes_read: int = 0
    records: int = 0
    messages: int = 0
    parse_errors: int = 0
    read_errors: int = 0
    changed_files: int = 0
    oversized_records: int = 0
    tool_calls: Counter[str] = field(default_factory=Counter)
    tool_results: int = 0
    tool_errors: int = 0


def flatten_text(content: object, limit: int = MAX_MESSAGE_CHARS) -> str:
    if isinstance(content, str):
        return content[:limit]
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    remaining = limit
    for item in content[:MAX_CONTENT_ITEMS]:
        value = ""
        if isinstance(item, str):
            value = item
        elif isinstance(item, dict) and item.get("type") in {
            "text",
            "input_text",
            "output_text",
        }:
            candidate = item.get("text")
            if isinstance(candidate, str):
                value = candidate
        if not value or remaining <= 0:
            continue
        bounded = value[:remaining]
        parts.append(bounded)
        remaining -= len(bounded)
        if remaining <= 0:
            break
    return " ".join(parts)


def sanitize(text: str, limit: int) -> str:
    text = PRIVATE_KEY_RE.sub("<private-key>", text)
    text = SECRET_ASSIGNMENT_RE.sub(
        lambda match: f"{match.group('name')}{match.group('separator')}<secret>",
        text,
    )
    text = SECRET_RE.sub("<secret>", text)
    text = EMAIL_RE.sub("<email>", text)
    text = URL_RE.sub("<url>", text)
    text = ABS_PATH_RE.sub("<path>", text)
    text = TILDE_PATH_RE.sub("<path>", text)
    text = WINDOWS_ABS_PATH_RE.sub("<path>", text)
    text = HASH_RE.sub("<hash>", text)
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def message_from_record(record: dict[str, object], ordinal: int) -> Optional[Message]:
    if record.get("type") == "event_msg":
        payload = record.get("payload")
        if not isinstance(payload, dict):
            return None
        payload_type = payload.get("type")
        if payload_type == "turn_aborted":
            reason = payload.get("reason")
            detail = reason[:MAX_MESSAGE_CHARS] if isinstance(reason, str) else "unknown"
            return Message("platform", f"Codex turn_aborted: {detail}", ordinal)
        if payload_type == "error":
            detail = flatten_text(payload.get("message", "")) or "structured error"
            return Message("platform", f"Codex error: {detail}", ordinal)

    if record.get("type") == "response_item":
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("type") != "message":
            return None
        role = str(payload.get("role") or "")
        if role not in {"user", "assistant", "system"}:
            return None
        text = flatten_text(payload.get("content", ""))
        if not text.strip():
            return None
        if role == "user" and text.lstrip().startswith(INJECTED_PREFIXES):
            return None
        return Message(role=role, text=text, ordinal=ordinal)

    if record.get("isMeta") or record.get("toolUseResult") is not None:
        return None
    message = record.get("message")
    message_dict = message if isinstance(message, dict) else {}
    role_value = message_dict.get("role") or record.get("role") or record.get("type")
    role = str(role_value or "")
    if role not in {"user", "assistant", "system"}:
        return None
    content = message_dict.get("content", record.get("content", record.get("text", "")))
    text = flatten_text(content)
    if not text.strip():
        return None
    if role == "user" and text.lstrip().startswith(INJECTED_PREFIXES):
        return None
    return Message(role=role, text=text, ordinal=ordinal)


def update_tool_receipts(record: dict[str, object], stats: ScanStats) -> None:
    if record.get("type") == "response_item":
        payload = record.get("payload")
        if isinstance(payload, dict):
            payload_type = payload.get("type")
            if payload_type in {"custom_tool_call", "function_call", "local_shell_call"}:
                name = payload.get("name") or payload_type
                stats.tool_calls[str(name)[:MAX_TOOL_NAME_CHARS]] += 1
            elif payload_type in {
                "custom_tool_call_output",
                "function_call_output",
                "local_shell_call_output",
            }:
                stats.tool_results += 1
                if (
                    payload.get("status") in {"failed", "error"}
                    or payload.get("isError") is True
                    or payload.get("is_error") is True
                ):
                    stats.tool_errors += 1
        return

    message = record.get("message")
    message_dict = message if isinstance(message, dict) else {}
    content = message_dict.get("content", record.get("content"))
    if isinstance(content, list):
        for item in content[:MAX_CONTENT_ITEMS]:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use":
                name = item.get("name")
                stats.tool_calls[str(name or "unknown")[:MAX_TOOL_NAME_CHARS]] += 1
            elif item.get("type") == "tool_result":
                stats.tool_results += 1
                if item.get("is_error") is True:
                    stats.tool_errors += 1
    if record.get("toolUseResult") is not None:
        stats.tool_results += 1
        result = record.get("toolUseResult")
        if isinstance(result, dict) and (
            result.get("isError") is True or result.get("is_error") is True
        ):
            stats.tool_errors += 1


def japanese_dominant(text: str) -> bool:
    kana = len(JAPANESE_RE.findall(text))
    cjk = len(CJK_RE.findall(text))
    return kana >= 4 and kana / max(cjk, 1) >= 0.25


def classify(message: Message, japanese_allowed: bool = False) -> Optional[str]:
    text = message.text.strip()
    if message.role == "platform":
        return "PLATFORM INTERRUPTION"
    if message.role == "system" and PLATFORM_INTERRUPTION_RE.search(text):
        return "PLATFORM INTERRUPTION"
    if CONTEXT_RE.search(text):
        return "CONTEXT SIGNAL"
    if (
        message.role == "assistant"
        and not japanese_allowed
        and japanese_dominant(text)
    ):
        return "LANGUAGE SIGNAL assistant=ja"
    if message.role != "user":
        return None
    if PERSISTENCE_RE.fullmatch(text):
        return "PERSISTENCE SIGNAL"
    if len(text) <= 160 and DELIVERY_RE.search(text):
        return "DELIVERY REMINDER"
    if len(text) <= 500 and CORRECTION_RE.search(text):
        return "USER CORRECTION"
    return None


def independent_signals(signals: list[Signal]) -> tuple[list[Signal], int]:
    """Collapse shared-history clones while preserving repeated real turns."""
    ordered = sorted(
        signals, key=lambda signal: (signal.mtime, signal.ordinal), reverse=True
    )
    accepted: list[Signal] = []
    seen: dict[tuple[str, str, str], set[tuple[str, str]]] = {}
    collapsed = 0
    for signal in ordered:
        normalized = re.sub(r"\s+", " ", signal.text).strip().casefold()
        key = (signal.label, normalized, signal.lineage)
        source = (signal.runtime, signal.file)
        is_clone = (
            signal.message_index >= MIN_CLONE_CONTEXT_MESSAGES
            and any(other_source != source for other_source in seen.get(key, set()))
        )
        if is_clone:
            collapsed += 1
            continue
        accepted.append(signal)
        seen.setdefault(key, set()).add(source)
    return accepted, collapsed


def scan_file(
    item: ConversationFile,
    stats: ScanStats,
    collect_messages: bool,
) -> tuple[list[Signal], list[Message], bool, int]:
    signals: list[Signal] = []
    message_head: list[Message] = []
    message_tail: deque[Message] = deque(maxlen=EXTRACT_TAIL)
    message_count = 0
    stats.files_read += 1
    stats.bytes_read += item.size
    recent_platform_interruption = False
    japanese_allowed = False
    assistant_seen = False
    lineage = hashlib.sha256()
    descriptor = -1
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(item.path, flags)
        before = os.fstat(descriptor)
        if (before.st_dev, before.st_ino) != (item.device, item.inode):
            os.close(descriptor)
            descriptor = -1
            stats.read_errors += 1
            return [], [], False, 0
        handle = os.fdopen(descriptor, encoding="utf-8", errors="replace")
        descriptor = -1
        with handle:
            ordinal = 0
            while True:
                line = handle.readline(MAX_RECORD_CHARS + 1)
                if not line:
                    break
                ordinal += 1
                stats.records += 1
                if len(line) > MAX_RECORD_CHARS and not line.endswith("\n"):
                    while line and not line.endswith("\n"):
                        line = handle.readline(MAX_RECORD_CHARS + 1)
                    stats.oversized_records += 1
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, UnicodeError):
                    stats.parse_errors += 1
                    continue
                if not isinstance(record, dict):
                    continue
                update_tool_receipts(record, stats)
                message = message_from_record(record, ordinal)
                if message is None:
                    continue
                stats.messages += 1
                message_count += 1
                lineage.update(message.role.encode("utf-8", errors="replace"))
                lineage.update(b"\0")
                lineage.update(message.text.encode("utf-8", errors="replace"))
                lineage.update(b"\0")
                if collect_messages:
                    if len(message_head) < EXTRACT_HEAD:
                        message_head.append(message)
                    else:
                        message_tail.append(message)
                label = classify(message, japanese_allowed)
                if label == "USER CORRECTION" and not assistant_seen:
                    label = None
                if label == "PLATFORM INTERRUPTION":
                    recent_platform_interruption = True
                elif label == "PERSISTENCE SIGNAL" and recent_platform_interruption:
                    label = "PLATFORM CONTINUATION"
                    recent_platform_interruption = False
                elif message.role == "user":
                    recent_platform_interruption = False
                if message.role == "user":
                    japanese_allowed = bool(JAPANESE_REQUEST_RE.search(message.text))
                elif message.role == "assistant" and label != "PLATFORM INTERRUPTION":
                    assistant_seen = True
                if label:
                    signals.append(
                        Signal(
                            label,
                            message.text,
                            sanitize(item.path.name, 240),
                            item.mtime,
                            ordinal,
                            item.runtime,
                            lineage.hexdigest(),
                            message_count,
                        )
                    )
    except OSError:
        stats.read_errors += 1
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    try:
        final_stat = item.path.stat(follow_symlinks=False)
        if (
            (final_stat.st_dev, final_stat.st_ino) != (item.device, item.inode)
            or final_stat.st_size != item.size
            or final_stat.st_mtime_ns != item.mtime_ns
        ):
            stats.changed_files += 1
    except OSError:
        stats.read_errors += 1
    messages = message_head + list(message_tail)
    return signals, messages, message_count > len(messages), message_count


def codex_project_matches(path: Path, project_root: Path) -> bool:
    try:
        if path.is_symlink():
            return False
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(
            os.open(path, flags), encoding="utf-8", errors="replace"
        ) as handle:
            for _index in range(40):
                line = handle.readline(MAX_RECORD_CHARS + 1)
                if not line:
                    break
                if len(line) > MAX_RECORD_CHARS and not line.endswith("\n"):
                    while line and not line.endswith("\n"):
                        line = handle.readline(MAX_RECORD_CHARS + 1)
                    continue
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, UnicodeError):
                    continue
                if not isinstance(record, dict) or record.get("type") != "session_meta":
                    continue
                payload = record.get("payload")
                if not isinstance(payload, dict):
                    return False
                cwd = payload.get("cwd")
                if not isinstance(cwd, str) or not cwd:
                    return False
                try:
                    candidate = Path(cwd).expanduser().resolve()
                    root = project_root.expanduser().resolve()
                    candidate.relative_to(root)
                    return True
                except (OSError, ValueError):
                    return False
    except OSError:
        return False
    return False


def newest_candidates(
    directory: Path,
    recursive: bool,
    candidate_limit: Optional[int],
) -> tuple[list[Path], bool]:
    if not recursive:
        return [path for path in directory.glob("*.jsonl") if not path.is_symlink()], False
    if candidate_limit is None:
        return [path for path in directory.rglob("*.jsonl") if not path.is_symlink()], False

    candidates: list[Path] = []
    stack = [directory]
    truncated = False
    while stack and len(candidates) <= candidate_limit:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        files = sorted(
            (
                entry
                for entry in entries
                if not entry.is_symlink()
                and entry.is_file()
                and entry.suffix == ".jsonl"
            ),
            key=lambda entry: entry.name,
            reverse=True,
        )
        remaining = candidate_limit + 1 - len(candidates)
        candidates.extend(files[:remaining])
        truncated = truncated or len(files) > remaining
        directories = sorted(
            (entry for entry in entries if not entry.is_symlink() and entry.is_dir()),
            key=lambda entry: entry.name,
        )
        stack.extend(directories)
    return (
        candidates[:candidate_limit],
        truncated or len(candidates) > candidate_limit or bool(stack),
    )


def discover(
    directory: Path,
    runtime: str = "claude_project_logs",
    recursive: bool = False,
    project_root: Optional[Path] = None,
    candidate_limit: Optional[int] = None,
) -> tuple[list[ConversationFile], int, bool]:
    files: list[ConversationFile] = []
    if directory.is_symlink() or not directory.is_dir():
        return files, 0, False
    try:
        scan_root = directory.resolve(strict=True)
    except OSError:
        return files, 0, False
    candidates, truncated = newest_candidates(scan_root, recursive, candidate_limit)
    for path in candidates:
        if path.is_symlink():
            continue
        try:
            path.relative_to(scan_root)
        except ValueError:
            continue
        if project_root is not None and not codex_project_matches(path, project_root):
            continue
        try:
            stat = path.stat(follow_symlinks=False)
        except OSError:
            continue
        files.append(
            ConversationFile(
                path=path,
                mtime=stat.st_mtime,
                mtime_ns=stat.st_mtime_ns,
                size=stat.st_size,
                device=stat.st_dev,
                inode=stat.st_ino,
                runtime=runtime,
            )
        )
    return (
        sorted(files, key=lambda item: (item.mtime, item.path.name), reverse=True),
        len(candidates),
        truncated,
    )


def percentage(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.0"
    return f"{100.0 * numerator / denominator:.1f}"


def print_file_manifest(
    files: list[ConversationFile],
    live_files: set[Path],
    signal_files: set[Path],
    extract_files: set[Path],
) -> None:
    print("=== CONVERSATION FILES ===")
    if not files:
        print("(no conversation files)")
        return
    for item in files[:MAX_FILE_LIST]:
        live = "yes" if item.path in live_files else "no"
        print(
            f"runtime={item.runtime} file={sanitize(item.path.name, 240)} "
            f"bytes={item.size} "
            f"live_by_recent_mtime={live} "
            f"signal_scan={'yes' if item.path in signal_files else 'no'} "
            f"extract={'yes' if item.path in extract_files else 'no'}"
        )
    if len(files) > MAX_FILE_LIST:
        print(f"conversation_file_listing_truncated: {len(files) - MAX_FILE_LIST}")


def print_receipts(stats: ScanStats) -> None:
    print("=== VERIFICATION RECEIPTS ===")
    print(f"tool_calls_seen: {sum(stats.tool_calls.values())}")
    print(f"tool_results_seen: {stats.tool_results}")
    print(f"tool_errors_seen: {stats.tool_errors}")
    if stats.tool_calls:
        rendered = ", ".join(
            f"{name}={count}" for name, count in stats.tool_calls.most_common(20)
        )
        print(f"tool_call_names: {rendered}")
    else:
        print("tool_call_names: (none)")


def signal_theme_counts(signals: list[Signal]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for signal in signals:
        if signal.label == "PLATFORM INTERRUPTION":
            counts["platform_interruption"] += 1
            continue
        if signal.label == "PLATFORM CONTINUATION":
            counts["platform_continuation"] += 1
            continue
        if signal.label == "CONTEXT SIGNAL":
            counts["context_pressure"] += 1
            continue
        if signal.label.startswith("LANGUAGE SIGNAL"):
            counts["language_drift"] += 1
            continue
        if signal.label == "PERSISTENCE SIGNAL":
            counts["unfinished_persistence"] += 1
            continue
        matched = False
        for theme, pattern in THEME_PATTERNS.items():
            if pattern.search(signal.text):
                counts[theme] += 1
                matched = True
        if not matched:
            counts["other_user_correction"] += 1
    return counts


def audit(
    directory: Path,
    mode: str,
    codex_root: Optional[Path] = None,
    project_root: Optional[Path] = None,
    all_projects: bool = False,
) -> int:
    files, discovery_candidates, discovery_limited = discover(
        directory,
        recursive=all_projects,
    )
    requested_runtimes = ["claude_project_logs"]
    runtime_roots_available = {"claude_project_logs": directory.is_dir()}
    if all_projects:
        requested_runtimes.append("codex_project_logs")
        runtime_roots_available["codex_project_logs"] = bool(
            codex_root is not None and codex_root.is_dir()
        )
    if (
        codex_root is not None
        and (project_root is not None or all_projects)
    ):
        if "codex_project_logs" not in requested_runtimes:
            requested_runtimes.append("codex_project_logs")
        runtime_roots_available["codex_project_logs"] = codex_root.is_dir()
        if codex_root.is_dir():
            codex_files, codex_candidates, codex_limited = discover(
                codex_root,
                runtime="codex_project_logs",
                recursive=True,
                project_root=None if all_projects else project_root,
                candidate_limit=(
                    SUMMARY_CANDIDATE_LIMIT
                    if mode == "summary" and not all_projects
                    else None
                ),
            )
            files.extend(codex_files)
            discovery_candidates += codex_candidates
            discovery_limited = discovery_limited or codex_limited
    files.sort(key=lambda item: (item.mtime, item.path.name), reverse=True)
    runtime_groups: dict[str, list[ConversationFile]] = {}
    for item in files:
        runtime_groups.setdefault(item.runtime, []).append(item)
    live_paths: set[Path] = set()
    now = time.time()
    for items in runtime_groups.values():
        if not items:
            continue
        recent = {
            item.path
            for item in items
            if 0 <= now - item.mtime <= LIVE_WINDOW_SECONDS
        }
        live_paths.update(recent)
    previous = [item for item in files if item.path not in live_paths]
    signal_selection = previous if mode == "deep" else previous[:3]
    extract_selection = previous[:3] if mode == "deep" else []
    signal_paths = {item.path for item in signal_selection}
    extract_paths = {item.path for item in extract_selection}
    total_previous_bytes = sum(item.size for item in previous)
    selected_signal_bytes = sum(item.size for item in signal_selection)

    stats = ScanStats()
    all_signals: list[Signal] = []
    extracts: dict[Path, tuple[list[Message], bool, int]] = {}
    for item in signal_selection:
        signals, messages, truncated, message_count = scan_file(
            item, stats, item.path in extract_paths
        )
        all_signals.extend(signals)
        if item.path in extract_paths:
            extracts[item.path] = (messages, truncated, message_count)

    print("=== CONVERSATION COVERAGE ===")
    print(f"conversation_runtime: {','.join(requested_runtimes)}")
    print(f"conversation_scope: {'all_projects' if all_projects else 'current_project'}")
    print(f"coverage_mode: {mode}")
    print(f"files_discovered: {len(files)}")
    print(f"discovery_candidates_examined: {discovery_candidates}")
    print(f"discovery_limited: {'yes' if discovery_limited else 'no'}")
    if discovery_limited:
        print(f"discovery_candidate_limit: {SUMMARY_CANDIDATE_LIMIT}")
    print(f"previous_files_available: {len(previous)}")
    print(f"live_files_skipped: {len(live_paths)}")
    print(
        f"live_skip_basis: mtime_within_{LIVE_WINDOW_SECONDS}s_per_runtime"
    )
    print(f"signal_scope: {'all_previous' if mode == 'deep' else 'recent_previous'}")
    print(f"signal_files_scanned: {stats.files_read}")
    print(f"extract_files_selected: {len(extract_selection)}")
    print(f"records_scanned: {stats.records}")
    print(f"messages_scanned: {stats.messages}")
    print(f"bytes_scanned: {stats.bytes_read}")
    print(f"previous_bytes_available: {total_previous_bytes}")
    print(
        f"previous_bytes_scanned_percent: "
        f"{percentage(selected_signal_bytes, total_previous_bytes)}"
    )
    print(f"parse_errors: {stats.parse_errors}")
    print(f"oversized_records: {stats.oversized_records}")
    print(f"read_errors: {stats.read_errors}")
    print(f"files_changed_during_scan: {stats.changed_files}")
    scan_complete = (
        mode == "deep"
        and bool(previous)
        and len(signal_selection) == len(previous)
        and stats.files_read == len(signal_selection)
        and stats.parse_errors == 0
        and stats.oversized_records == 0
        and stats.read_errors == 0
        and stats.changed_files == 0
    )
    roots_available = all(runtime_roots_available.values())
    if not roots_available:
        coverage_status = "unavailable"
    elif not previous:
        coverage_status = "no_data"
    elif mode != "deep" or len(signal_selection) != len(previous):
        coverage_status = "partial"
    elif not scan_complete:
        coverage_status = "incomplete"
    elif live_paths:
        coverage_status = "live_sessions_excluded"
    else:
        coverage_status = "complete"
    print(f"coverage_status: {coverage_status}")
    print(f"all_previous_files_scanned: {'yes' if scan_complete else 'no'}")
    cross_runtime_complete = (
        coverage_status == "complete"
        and len(requested_runtimes) > 1
        and all(runtime in runtime_groups for runtime in requested_runtimes)
    )
    print(
        f"cross_runtime_full_history: "
        f"{'yes' if cross_runtime_complete else 'no'}"
    )
    print(
        f"cross_project_full_history: "
        f"{'yes' if all_projects and cross_runtime_complete else 'no'}"
    )
    for runtime in requested_runtimes:
        runtime_files = runtime_groups.get(runtime, [])
        runtime_previous = [item for item in runtime_files if item.path not in live_paths]
        print(
            f"runtime_coverage: runtime={runtime} files={len(runtime_files)} "
            f"previous={len(runtime_previous)} bytes={sum(item.size for item in runtime_files)} "
            f"root_available={'yes' if runtime_roots_available[runtime] else 'no'}"
        )

    print_file_manifest(files, live_paths, signal_paths, extract_paths)

    ordered_signals, duplicate_signals_collapsed = independent_signals(all_signals)
    emitted = ordered_signals[:MAX_SIGNALS]
    print("=== CONVERSATION SIGNALS ===")
    print(f"raw_signals_found: {len(all_signals)}")
    print(f"independent_signals: {len(ordered_signals)}")
    print(f"duplicate_signals_collapsed: {duplicate_signals_collapsed}")
    print(f"signals_found: {len(ordered_signals)}")
    print(f"signals_emitted: {len(emitted)}")
    print(
        f"signal_output_truncated: {'yes' if len(ordered_signals) > len(emitted) else 'no'}"
    )
    if not emitted:
        print("(no conversation signals detected in declared scan scope)")
    for signal in emitted:
        snippet = sanitize(signal.text, MAX_SIGNAL_CHARS)
        print(
            f"{signal.label}: runtime={signal.runtime} file={signal.file} "
            f"record={signal.ordinal} text={snippet}"
        )

    print("=== SIGNAL THEME SUMMARY ===")
    theme_counts = signal_theme_counts(ordered_signals)
    print(f"signals_classified: {len(ordered_signals)}")
    print("theme_counts:")
    if theme_counts:
        for theme, count in theme_counts.most_common():
            print(f"  {theme}: {count}")
    else:
        print("  (none)")

    print("=== CONVERSATION EXTRACT ===")
    if mode != "deep":
        print("(skipped: summary mode; deep mode samples the first 30 and last 120 messages from three previous sessions)")
    elif not extract_selection:
        print("(no previous conversation files)")
    else:
        for item in extract_selection:
            messages, truncated, total = extracts.get(item.path, ([], False, 0))
            print(
                f"--- runtime={item.runtime} "
                f"file={sanitize(item.path.name, 240)} messages={total} "
                f"extract_truncated={'yes' if truncated else 'no'} ---"
            )
            for message in messages:
                print(f"{message.role.upper()}: {sanitize(message.text, MAX_EXTRACT_CHARS)}")

    print_receipts(stats)
    return 0


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("mode", choices=("summary", "deep"))
    parser.add_argument("--codex-root", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument(
        "--all-projects",
        action="store_true",
        help="Explicit deep-audit mode: scan every project log under both roots",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.all_projects and args.mode != "deep":
        parser.error("--all-projects requires deep mode")
    if args.all_projects and args.project_root is not None:
        parser.error("--all-projects cannot be combined with --project-root")
    if args.all_projects and args.codex_root is None:
        parser.error("--all-projects requires --codex-root")
    if not args.all_projects and (args.codex_root is None) != (args.project_root is None):
        parser.error("--codex-root and --project-root must be provided together")
    return audit(
        args.directory,
        args.mode,
        args.codex_root,
        args.project_root,
        args.all_projects,
    )


if __name__ == "__main__":
    raise SystemExit(main())
