#!/usr/bin/env python3
"""Check punctuation and CJK/Latin mixing in prose, by locale.

Flags half-width punctuation inside CJK sentences (including across a markdown
emphasis marker, so `**标签**:` is caught), a comma or semicolon glued to the
next Latin letter, half-width parens hugging a Han char, missing or wrong
spacing between CJK and Latin, and em/en dashes. Skips fenced code blocks,
inline code, URLs, and markdown links so punctuation that belongs to code is
never flagged.

Run as: python3 check_punctuation.py [--lang LANG] [--fix] [FILE]
  --lang  zh | en | ja | auto   (default: auto)
  --fix   print corrected text to stdout (zero-ambiguity fixes only)
  FILE    file to read; reads stdin when omitted

Default mode prints findings and exits 1 when any exist, otherwise prints
"punctuation: ok" and exits 0.
"""

from __future__ import annotations

import argparse
import re
import sys

# Character-class endpoints (verify against a Unicode table when editing):
# CJK U+4E00-U+9FFF + ext-A U+3400-U+4DBF; KANA U+3040-U+30FF; HANGUL U+AC00-U+D7A3.
CJK = "一-鿿㐀-䶿"
KANA = "぀-ヿ"
HANGUL = "가-힣"

URL_RE = re.compile(r"https?://(?:\([^()]*\)|[A-Za-z0-9\-._~:/?#\[\]@!$&'*+,;=%])+")
# group(1) captures only the (url) target so the [label] stays visible to checks.
MD_LINK_RE = re.compile(r"\[[^\]]*\](\((?:[^()]|\([^()]*\))*\))")

# Single-class matchers reused across detect_lang / fix_zh_line (compiled once).
_HANGUL_RE = re.compile(f"[{HANGUL}]")
_KANA_RE = re.compile(f"[{KANA}]")
_CJK_RE = re.compile(f"[{CJK}]")
_LATIN_RE = re.compile(r"[A-Za-z0-9]")
_LINE_END_RE = re.compile(r"(\r\n|\r|\n)\Z")
_CJK_KANA_HANGUL_RE = re.compile(f"[{CJK}{KANA}{HANGUL}]")
_LINE_SPLIT_RE = re.compile(r"\r\n|\r|\n")

FULLWIDTH = {",": "，", ".": "。", ";": "；", ":": "：", "!": "！", "?": "？"}
# Half-width keys of FULLWIDTH, reused as the [,.;:!?] character class so the
# map and the regexes built from it stay a single source of truth.
_HALFWIDTH = "".join(FULLWIDTH)
# Full-width CJK point marks: the six values above plus 顿号. A half-width space
# touching any of these is a typesetting error, so --fix strips it; check_en
# reuses the same set as its "full-width punctuation in English" class.
_CJK_PUNCT = "".join(FULLWIDTH.values()) + "、"
# Half-width paren -> full-width, for the CJK-adjacent paren check (report only).
FULLPAREN = {"(": "（", ")": "）"}


def _inline_code_spans(line: str):
    """Yield (start, end) for each inline-code span, CommonMark-style: a run of
    n backticks opens and the next run of exactly n backticks closes. A pure
    linear scan with no regex backtracking, so a pathological long backtick run
    cannot blow up -- and a real short span on the same line as a long run keeps
    its exemption (the old regex guard dropped inline-code for the whole line)."""
    i, n = 0, len(line)
    while i < n:
        if line[i] != "`":
            i += 1
            continue
        j = i
        while j < n and line[j] == "`":
            j += 1
        run = j - i
        k = j
        while k < n:
            if line[k] == "`":
                end = k
                while end < n and line[end] == "`":
                    end += 1
                if end - k == run:
                    yield (i, end)
                    i = end
                    break
                k = end
            else:
                k += 1
        else:
            i = j  # no matching closer; the backticks are literal text


def exempt_mask(line: str) -> list[bool]:
    """Per-character mask; True marks positions inside inline code, a URL, or the
    (url) target of a markdown link -- never inspected or rewritten. The [label]
    of a markdown link stays visible (it is rendered prose). A trailing ASCII
    mark on a bare URL immediately followed by a CJK/kana/Hangul char is released
    from the mask: it is a sentence separator, not part of the URL."""
    mask = [False] * len(line)
    spans: list[tuple[int, int]] = []
    for m in MD_LINK_RE.finditer(line):
        spans.append((m.start(1), m.end(1)))
    for m in URL_RE.finditer(line):
        s, e = m.start(), m.end()
        while e > s and line[e - 1] in _HALFWIDTH and e < len(line) and _CJK_KANA_HANGUL_RE.match(line[e]):
            e -= 1
        spans.append((s, e))
    spans.extend(_inline_code_spans(line))
    for s, e in spans:
        for i in range(s, e):
            mask[i] = True
    return mask


def overlaps_exempt(mask: list[bool], start: int, end: int) -> bool:
    return any(mask[start:end])


def split_line_ending(raw: str) -> tuple[str, str]:
    r"""Split a raw line into (body, trailing newline) where the newline is one
    of \r\n, \r, \n, or empty. Lets --fix preserve original line endings
    instead of normalizing CRLF to LF."""
    m = _LINE_END_RE.search(raw)
    return (raw[: m.start()], m.group()) if m else (raw, "")


def _split_keepends(text: str) -> list[str]:
    r"""Split into lines on \r\n / \r / \n only -- NOT the extra Unicode
    separators (U+2028/2029/000B/000C/0085) that str.splitlines() also breaks
    on -- so a reported line number matches what an editor or grep counts. Each
    piece keeps its trailing newline, like splitlines(keepends=True)."""
    if not text:
        return []
    lines: list[str] = []
    start = 0
    for m in _LINE_SPLIT_RE.finditer(text):
        lines.append(text[start : m.end()])
        start = m.end()
    if start < len(text):
        lines.append(text[start:])
    return lines


def fence_state(line: str, fence: tuple[str, int] | None) -> tuple[str, int] | None:
    """Track fenced-code state across lines, CommonMark-style. `fence` is None
    outside a fence, or (char, length) inside one. An opener is indented <= 3
    spaces and is >= 3 identical fence chars (``` or ~~~). A closer is the same
    char, a run at least as long as the opener, and nothing else on the line.
    Tracking char + length keeps mixed ``` / ~~~ blocks, and a ```` block that
    contains a ``` line, from closing early; the indent rule stops a 4-space
    indented ``` from being read as a fence and swallowing the text after it."""
    indent = len(line) - len(line.lstrip(" "))
    if indent > 3:
        return fence
    stripped = line[indent:]
    if fence is None:
        for ch in ("`", "~"):
            if stripped.startswith(ch * 3):
                run = len(stripped) - len(stripped.lstrip(ch))
                return (ch, run)
        return None
    ch, length = fence
    if stripped.startswith(ch * length):
        run = len(stripped) - len(stripped.lstrip(ch))
        if run >= length and not stripped[run:].strip():
            return None
    return fence


def detect_lang(text: str) -> str:
    # Sample the language from real prose: fenced code, inline code, URLs, and
    # link targets are stripped per line, so one kana inside a ```js block does
    # not route an otherwise-Chinese document to ja. kana wins globally (any kana
    # anywhere => ja, hence the early return); else Han => zh; Hangul is checked
    # LAST so a mostly-Chinese text that merely quotes a Korean glyph stays zh.
    saw_cjk = saw_hangul = False
    fence: tuple[str, int] | None = None
    for raw in _split_keepends(text):
        body, _ = split_line_ending(raw)
        was_in_fence = fence is not None
        fence = fence_state(body, fence)
        if fence is not None or was_in_fence:
            continue
        prose = "".join(c for c, m in zip(body, exempt_mask(body)) if not m)
        if _KANA_RE.search(prose):
            return "ja"
        saw_cjk = saw_cjk or bool(_CJK_RE.search(prose))
        saw_hangul = saw_hangul or bool(_HANGUL_RE.search(prose))
    return "zh" if saw_cjk else "ko" if saw_hangul else "en"


class Finding:
    def __init__(self, line: int, col: int, kind: str, snippet: str, suggestion: str):
        self.line = line
        self.col = col
        self.kind = kind
        self.snippet = snippet
        self.suggestion = suggestion

    def format(self, source: str) -> str:
        return f"{source}:{self.line}:{self.col} [{self.kind}] {self.snippet!r} -> {self.suggestion}"


def check_dash(line: str, mask: list[bool], lineno: int, findings: list[Finding]) -> None:
    """Em/en dashes are banned in both zh and en output, so the rule is shared."""
    for m in re.finditer("[—–]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        findings.append(Finding(lineno, m.start() + 1, "dash", m.group(), "replace dash with comma / period"))


def check_latin_space(line: str, mask: list[bool], lineno: int, findings: list[Finding]) -> None:
    """A comma or semicolon glued to the next Latin letter with no space is a
    spacing error in zh and en alike. Both sides are restricted to letters, so a
    thousands separator (1,000) and a spaced enumeration (API, SDK) are spared."""
    for m in re.finditer(r"[A-Za-z][,;][A-Za-z]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        p = m.group()[1]
        findings.append(Finding(lineno, m.start() + 2, "missing-space-after-punct", m.group(), f"add a space after '{p}'"))


def check_zh(line: str, mask: list[bool], lineno: int, findings: list[Finding]) -> None:
    # A half-width mark next to a Han char -- directly, or across a markdown
    # emphasis marker (** or _), so `**标签**:` is caught, not just `标签:`.
    for m in re.finditer(f"[{CJK}][*_]*[{_HALFWIDTH}]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        p = m.group()[-1]
        findings.append(Finding(lineno, m.end(), "zh-halfwidth-punct", m.group(), f"{p} -> {FULLWIDTH[p]}"))  # 1-based column of the offending punctuation
    for m in re.finditer(f"[{_HALFWIDTH}][*_]*[{CJK}]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        p = m.group()[0]
        findings.append(Finding(lineno, m.start() + 1, "zh-halfwidth-punct", m.group(), f"{p} -> {FULLWIDTH[p]}"))  # 1-based column of the offending punctuation
    for m in re.finditer(f"[{CJK}][A-Za-z0-9]|[A-Za-z0-9][{CJK}]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        findings.append(Finding(lineno, m.start() + 1, "zh-missing-space", m.group(), "add a space between CJK and Latin"))
    check_dash(line, mask, lineno, findings)
    for m in re.finditer("　", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        findings.append(Finding(lineno, m.start() + 1, "zh-fullwidth-space", "　", "use a half-width space or remove it"))
    # A half-width sentence-ender after Latin/digit/%/) that the Han-adjacent
    # rules above miss, when the line is Chinese and the mark closes a clause
    # (end-of-line, or a CJK char / CJK punctuation next). Narrow on purpose:
    # only . ! ? -- never the comma -- so Latin lists like "API, SDK" are spared.
    if _CJK_RE.search(line):
        for m in re.finditer(rf"[A-Za-z0-9%)]([.!?])(?=$|[{CJK}{_CJK_PUNCT}])", line):
            if overlaps_exempt(mask, m.start(), m.end()):
                continue
            p = m.group(1)
            findings.append(Finding(lineno, m.start(1) + 1, "zh-halfwidth-punct", m.group(), f"{p} -> {FULLWIDTH[p]}"))
    check_latin_space(line, mask, lineno, findings)
    # A half-width paren hugging a Han char: zh prose wants full-width （）. Kept
    # conservative -- only when the paren directly touches a Han char -- so a paren
    # around pure Latin or code, like foo(x), is left alone. Report only; --fix
    # never rewrites parens, since whether (English) should be full-width is a
    # house-style call left to the author.
    for m in re.finditer(r"[()]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        i = m.start()
        left = line[i - 1] if i > 0 else ""
        right = line[i + 1] if i + 1 < len(line) else ""
        if _CJK_RE.match(left) or _CJK_RE.match(right):
            paren = m.group()
            findings.append(Finding(lineno, i + 1, "zh-halfwidth-paren", paren, f"{paren} -> {FULLPAREN[paren]}"))


def check_en(line: str, mask: list[bool], lineno: int, findings: list[Finding]) -> None:
    check_dash(line, mask, lineno, findings)
    check_latin_space(line, mask, lineno, findings)
    for m in re.finditer(f"[{_CJK_PUNCT}]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        findings.append(Finding(lineno, m.start() + 1, "en-fullwidth-punct", m.group(), "use ASCII punctuation"))
    for m in re.finditer(r" +[,.;:!?]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        findings.append(Finding(lineno, m.start() + 1, "en-space-before-punct", m.group(), "remove space before punctuation"))


def check_ja(line: str, mask: list[bool], lineno: int, findings: list[Finding]) -> None:
    # Same emphasis-marker bridge as check_zh, so `**見出し**:` is caught.
    for m in re.finditer(f"[{CJK}{KANA}][*_]*[{_HALFWIDTH}]|[{_HALFWIDTH}][*_]*[{CJK}{KANA}]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        findings.append(Finding(lineno, m.start() + 1, "ja-ascii-punct", m.group(), "use full-width 、。！？：；"))
    for m in re.finditer(f"[{CJK}{KANA}] +[A-Za-z]|[A-Za-z] +[{CJK}{KANA}]", line):
        if overlaps_exempt(mask, m.start(), m.end()):
            continue
        findings.append(Finding(lineno, m.start() + 1, "ja-extra-space", m.group(), "remove space between Japanese and Latin"))


CHECKERS = {"zh": check_zh, "en": check_en, "ja": check_ja}


def fix_zh_line(line: str) -> str:
    mask = exempt_mask(line)
    chars = list(line)
    for m in re.finditer(f"[{CJK}][*_]*[{_HALFWIDTH}]", line):
        if not overlaps_exempt(mask, m.start(), m.end()):
            chars[m.end() - 1] = FULLWIDTH[line[m.end() - 1]]
    for m in re.finditer(f"[{_HALFWIDTH}][*_]*[{CJK}]", line):
        if not overlaps_exempt(mask, m.start(), m.end()):
            chars[m.start()] = FULLWIDTH[line[m.start()]]
    # check_zh flags a half-width . ! ? that closes a Chinese clause after a
    # Latin char / digit / % / ) ; replicate that detect-only rule here so --fix
    # resolves it instead of reporting a finding it cannot fix. Same regex, so the
    # fix range equals the detect range -- no new false positives.
    if _CJK_RE.search(line):
        for m in re.finditer(rf"[A-Za-z0-9%)]([.!?])(?=$|[{CJK}{_CJK_PUNCT}])", line):
            if not overlaps_exempt(mask, m.start(), m.end()):
                chars[m.start(1)] = FULLWIDTH[line[m.start(1)]]
    # A full-width point mark carries its own spacing, so any half-width space
    # hugging one (either side, however many) is wrong. Mark them, then compress
    # chars and mask together so the CJK/Latin spacing pass keeps its alignment.
    drop = [False] * len(chars)
    for p, ch in enumerate(chars):
        if ch in _CJK_PUNCT and not mask[p]:
            for step in (1, -1):
                q = p + step
                while 0 <= q < len(chars) and chars[q] == " " and not mask[q]:
                    drop[q] = True
                    q += step
    if any(drop):
        chars = [c for i, c in enumerate(chars) if not drop[i]]
        mask = [mk for i, mk in enumerate(mask) if not drop[i]]
    result: list[str] = []
    for i, ch in enumerate(chars):
        if result and not (mask[i - 1] or mask[i]):
            prev = result[-1]
            if (_CJK_RE.match(prev) and _LATIN_RE.match(ch)) or (_LATIN_RE.match(prev) and _CJK_RE.match(ch)):
                result.append(" ")
        result.append(ch)
    return "".join(result)


def fix_text(text: str, lang: str) -> str:
    if lang != "zh":
        return text
    out: list[str] = []
    fence: tuple[str, int] | None = None
    for raw in _split_keepends(text):
        body, ending = split_line_ending(raw)
        was_in_fence = fence is not None
        fence = fence_state(body, fence)
        if fence is not None or was_in_fence:
            out.append(raw)
            continue
        out.append(fix_zh_line(body) + ending)
    return "".join(out)


def iter_findings(text: str, lang: str) -> list[Finding]:
    findings: list[Finding] = []
    checker = CHECKERS.get(lang)
    if checker is None:
        return findings
    fence: tuple[str, int] | None = None
    for lineno, raw in enumerate(_split_keepends(text), start=1):
        line, _ = split_line_ending(raw)
        was_in_fence = fence is not None
        fence = fence_state(line, fence)
        if fence is not None or was_in_fence:
            continue
        mask = exempt_mask(line)
        checker(line, mask, lineno, findings)
    # The same punctuation can match both the "Han before" and "Han after"
    # rule; keep the first Finding per (line, col, kind).
    deduped: dict[tuple[int, int, str], Finding] = {}
    for f in findings:
        deduped.setdefault((f.line, f.col, f.kind), f)
    return list(deduped.values())


def main() -> int:
    parser = argparse.ArgumentParser(description="Check punctuation / CJK mixing by locale.")
    parser.add_argument("file", nargs="?", help="File to read (default: stdin)")
    parser.add_argument("--lang", default="auto", choices=["zh", "en", "ja", "auto"])
    parser.add_argument("--fix", action="store_true", help="Print corrected text to stdout")
    args = parser.parse_args()

    source = args.file or "-"
    if args.file and args.file != "-":
        # newline="" keeps original CRLF/CR so --fix does not normalize line endings.
        try:
            with open(args.file, encoding="utf-8", errors="replace", newline="") as f:
                text = f.read()
        except OSError as e:
            # Exit 2 so an unreadable path is distinct from exit 1 (= findings to fix).
            print(f"check_punctuation: cannot read {args.file}: {e.strerror or e}", file=sys.stderr)
            return 2
    else:
        text = sys.stdin.buffer.read().decode("utf-8", "replace")

    lang = detect_lang(text) if args.lang == "auto" else args.lang

    if lang == "ko":
        print("punctuation: ko locale is reserved (no rules yet); skipped", file=sys.stderr)
        if args.fix:
            sys.stdout.write(text)
        return 0

    if args.fix:
        if lang != "zh":
            print(f"punctuation: --fix has no rules for {lang}; text unchanged", file=sys.stderr)
        sys.stdout.write(fix_text(text, lang))
        return 0

    findings = iter_findings(text, lang)
    if findings:
        for f in findings:
            print(f.format(source))
        return 1
    print("punctuation: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
