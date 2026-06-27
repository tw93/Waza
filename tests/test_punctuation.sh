#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test_helpers.sh"

CHECKER="$ROOT/skills/write/scripts/check-punctuation.sh"
tmpdir=$(make_tmpdir)

# 1. Clean Chinese prose passes.
printf '%s\n' '这是一句中文。下一句也正常。' > "$tmpdir/clean.md"
bash "$CHECKER" --lang zh "$tmpdir/clean.md" >"$tmpdir/clean.out"
grep -q 'punctuation: ok' "$tmpdir/clean.out"

# 2. Half-width punctuation between Han characters is flagged (non-zero exit).
printf '%s\n' '这是一句中文,后面接英文.' > "$tmpdir/bad.md"
if bash "$CHECKER" --lang zh "$tmpdir/bad.md" >"$tmpdir/bad.out"; then
  echo "should reject half-width punctuation in zh"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/bad.out"

# 3. Punctuation inside inline code is exempt.
printf '%s\n' '见 `中文,标点` 的写法。' > "$tmpdir/code.md"
bash "$CHECKER" --lang zh "$tmpdir/code.md" >"$tmpdir/code.out"
grep -q 'punctuation: ok' "$tmpdir/code.out"

# 4. auto-detect routes Chinese to the zh checker (no --lang).
printf '%s\n' '这是,中文。' > "$tmpdir/auto.md"
if bash "$CHECKER" "$tmpdir/auto.md" >"$tmpdir/auto.out"; then
  echo "auto should flag zh half-width"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/auto.out"

# 5. Double-backtick inline code is exempt.
printf '%s\n' '见 ``中文,标点`` 的写法。' > "$tmpdir/code2.md"
bash "$CHECKER" --lang zh "$tmpdir/code2.md" >"$tmpdir/code2.out"
grep -q 'punctuation: ok' "$tmpdir/code2.out"

# 6. Missing space between CJK and Latin is flagged.
printf '%s\n' '用了一个月的Claude感觉不错。' > "$tmpdir/space.md"
if bash "$CHECKER" --lang zh "$tmpdir/space.md" >"$tmpdir/space.out"; then
  echo "should flag missing CJK/Latin space"; exit 1
fi
grep -q 'zh-missing-space' "$tmpdir/space.out"

# 7. Em-dash is flagged.
printf '%s\n' '这是一个判断——其实没必要。' > "$tmpdir/dash.md"
if bash "$CHECKER" --lang zh "$tmpdir/dash.md" >"$tmpdir/dash.out"; then
  echo "should flag em-dash"; exit 1
fi
grep -q 'dash' "$tmpdir/dash.out"

# 8. Full-width punctuation inside English text is flagged.
printf '%s\n' 'This is fine。Really?' > "$tmpdir/en.md"
if bash "$CHECKER" --lang en "$tmpdir/en.md" >"$tmpdir/en.out"; then
  echo "should flag full-width punct in en"; exit 1
fi
grep -q 'en-fullwidth-punct' "$tmpdir/en.out"

# 9. Clean English passes.
printf '%s\n' 'This sentence is perfectly normal.' > "$tmpdir/en-ok.md"
bash "$CHECKER" --lang en "$tmpdir/en-ok.md" >"$tmpdir/en-ok.out"
grep -q 'punctuation: ok' "$tmpdir/en-ok.out"

# 10. ASCII comma/period adjacent to Japanese is flagged.
printf '%s\n' 'これはテストです.次の文,続き' > "$tmpdir/ja.md"
if bash "$CHECKER" --lang ja "$tmpdir/ja.md" >"$tmpdir/ja.out"; then
  echo "should flag ascii punct in ja"; exit 1
fi
grep -q 'ja-ascii-punct' "$tmpdir/ja.out"

# 11. Korean is reserved: auto-detect skips with exit 0.
printf '%s\n' '한국어 문장입니다.' > "$tmpdir/ko.md"
bash "$CHECKER" "$tmpdir/ko.md" >"$tmpdir/ko.out" 2>"$tmpdir/ko.err"
grep -q 'reserved' "$tmpdir/ko.err"

# 12. Auto-detect routes a Japanese sample to the ja checker.
if bash "$CHECKER" "$tmpdir/ja.md" >"$tmpdir/ja-auto.out"; then
  echo "auto should flag ja sample"; exit 1
fi
grep -q 'ja-ascii-punct' "$tmpdir/ja-auto.out"

# 13. --fix converts half-width punctuation to full-width and adds CJK/Latin spaces.
printf '%s\n' '用了Claude感觉不错,挺好.' > "$tmpdir/fixin.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/fixin.md" >"$tmpdir/fixed.out"
grep -q '用了 Claude 感觉不错，挺好。' "$tmpdir/fixed.out"

# 14. --fix leaves inline code untouched.
printf '%s\n' '见 `中文,标点` 这里。' > "$tmpdir/fixcode.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/fixcode.md" >"$tmpdir/fixcode.out"
grep -q '`中文,标点`' "$tmpdir/fixcode.out"

# 15. --fix on a non-zh language is a visible no-op (stderr note, text unchanged).
printf '%s\n' 'Plain english text.' > "$tmpdir/enfix.md"
bash "$CHECKER" --lang en --fix "$tmpdir/enfix.md" >"$tmpdir/enfix.out" 2>"$tmpdir/enfix.err"
grep -q 'no rules for en' "$tmpdir/enfix.err"
grep -q 'Plain english text.' "$tmpdir/enfix.out"

# 16. --fix preserves CRLF line endings (does not normalize to LF).
printf '用了Claude感觉不错,挺好.\r\n' > "$tmpdir/crlf.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/crlf.md" >"$tmpdir/crlf.out"
grep -q $'\r' "$tmpdir/crlf.out"
grep -q '用了 Claude 感觉不错，挺好。' "$tmpdir/crlf.out"

# 17. Fenced code block content is exempt.
printf '%s\n' '正文一句。' '```' '块里,故意半角,不该报.' '```' '结尾一句。' > "$tmpdir/fence.md"
bash "$CHECKER" --lang zh "$tmpdir/fence.md" >"$tmpdir/fence.out"
grep -q 'punctuation: ok' "$tmpdir/fence.out"

# 18. URLs and markdown links with parentheses are exempt (inner commas not flagged).
printf '%s\n' '见 [文档](https://x.com/(a),三章) 和 https://y.com/(b) 说明。' > "$tmpdir/paren.md"
bash "$CHECKER" --lang zh "$tmpdir/paren.md" >"$tmpdir/paren.out"
grep -q 'punctuation: ok' "$tmpdir/paren.out"

# 19. Mixed fence markers (a ~~~ block containing a ``` line) do not falsely toggle.
printf '%s\n' '~~~' '围栏内,不报.' '```' '围栏内,也不报.' '~~~' '围栏外,要报.' > "$tmpdir/mixfence.md"
if bash "$CHECKER" --lang zh "$tmpdir/mixfence.md" >"$tmpdir/mixfence.out"; then
  echo "mixed fence: should flag the line outside the fence"; exit 1
fi
grep -qE ':6:[0-9]+ \[zh-halfwidth-punct\]' "$tmpdir/mixfence.out"
if grep -qE ':[24]:[0-9]+ \[' "$tmpdir/mixfence.out"; then echo "mixed fence: must not flag inside the fence"; exit 1; fi

# 20. ja flags half-width ! and 2+ spaces around Latin.
printf '%s\n' 'テスト!と  Code' > "$tmpdir/ja2.md"
if bash "$CHECKER" --lang ja "$tmpdir/ja2.md" >"$tmpdir/ja2.out"; then
  echo "ja should flag ! and multi-space"; exit 1
fi
grep -q 'ja-ascii-punct' "$tmpdir/ja2.out"
grep -q 'ja-extra-space' "$tmpdir/ja2.out"

# 21. --fix on ja is a visible no-op (stderr note, text unchanged).
printf '%s\n' 'これはテストです.' > "$tmpdir/jafix.md"
bash "$CHECKER" --lang ja --fix "$tmpdir/jafix.md" >"$tmpdir/jafix.out" 2>"$tmpdir/jafix.err"
grep -q 'no rules for ja' "$tmpdir/jafix.err"
grep -q 'これはテストです.' "$tmpdir/jafix.out"

# 22. Pathological backtick run does not hang (ReDoS guard).
python3 -c 'import sys; sys.stdout.write("x" + chr(96) * 2000 + "中,文\n")' > "$tmpdir/redos.md"
TIMEOUT="$(command -v timeout || command -v gtimeout || true)"
if [ -n "$TIMEOUT" ]; then
  "$TIMEOUT" 5 bash "$CHECKER" --lang zh "$tmpdir/redos.md" >/dev/null 2>&1 && rc=0 || rc=$?
  [ "$rc" != 124 ] || { echo "ReDoS guard: checker hung on a pathological backtick run"; exit 1; }
fi

# 23. A bare URL does not swallow the Chinese text that follows it.
printf '%s\n' '详见 https://a.com/path,后面的逗号,该报。' > "$tmpdir/urltail.md"
if bash "$CHECKER" --lang zh "$tmpdir/urltail.md" >"$tmpdir/urltail.out"; then
  echo "URL tail: Chinese punctuation after a bare URL should still be flagged"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/urltail.out"

# 24. --lang ko is rejected (ko is auto-detected only, not a user-facing option).
if bash "$CHECKER" --lang ko "$tmpdir/clean.md" >/dev/null 2>&1; then
  echo "--lang ko should be rejected by argparse choices"; exit 1
fi

# 25. A 4-space-indented ```-like line is not a fence opener (text after it is checked).
printf '%s\n' '    ```' '正文,应该报。' > "$tmpdir/indentfence.md"
if bash "$CHECKER" --lang zh "$tmpdir/indentfence.md" >"$tmpdir/indentfence.out"; then
  echo "indented fence: text after a 4-space-indented \`\`\` must still be checked"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/indentfence.out"

# 26. A 4-backtick fence containing a 3-backtick line does not close early.
printf '%s\n' '````' '块里,不报.' '```' '块里,也不报.' '````' '外面,要报。' > "$tmpdir/nestfence.md"
if bash "$CHECKER" --lang zh "$tmpdir/nestfence.md" >"$tmpdir/nestfence.out"; then
  echo "nested fence: should flag only the line outside the block"; exit 1
fi
grep -qE ':6:[0-9]+ \[zh-halfwidth-punct\]' "$tmpdir/nestfence.out"
if grep -qE ':[24]:[0-9]+ \[' "$tmpdir/nestfence.out"; then echo "nested fence: must not flag inside the block"; exit 1; fi

# 27. Many short inline-code spans on one line are not skipped by the ReDoS guard.
printf '%s\n' '`a` `b` `c` `d` `e` 后面 `中文,不报` 还有 `x` 这些。' > "$tmpdir/spans.md"
bash "$CHECKER" --lang zh "$tmpdir/spans.md" >"$tmpdir/spans.out"
grep -q 'punctuation: ok' "$tmpdir/spans.out"

# 28. --fix deletes the half-width space after a full-widthed comma (Q2a).
printf '%s\n' '话, 后面。' > "$tmpdir/sp-after.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/sp-after.md" >"$tmpdir/sp-after.out"
grep -q '^话，后面。$' "$tmpdir/sp-after.out"

# 29. --fix deletes the half-width space before a full-widthed comma.
printf '%s\n' '话 ,后面。' > "$tmpdir/sp-before.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/sp-before.md" >"$tmpdir/sp-before.out"
grep -q '^话，后面。$' "$tmpdir/sp-before.out"

# 30. --fix deletes multiple half-width spaces hugging the mark.
printf '%s\n' '话,  后面。' > "$tmpdir/sp-multi.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/sp-multi.md" >"$tmpdir/sp-multi.out"
grep -q '^话，后面。$' "$tmpdir/sp-multi.out"

# 31. --fix drops the space between a full-width mark and following Latin.
printf '%s\n' '中文. English' > "$tmpdir/sp-latin.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/sp-latin.md" >"$tmpdir/sp-latin.out"
grep -q '^中文。English$' "$tmpdir/sp-latin.out"

# 32. Scope B: a space hugging an already-full-width mark is also cleaned.
printf '%s\n' '结束。 然后' > "$tmpdir/sp-existing.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/sp-existing.md" >"$tmpdir/sp-existing.out"
grep -q '^结束。然后$' "$tmpdir/sp-existing.out"

# 33. Counter-case: half-width commas in a numeric list stay untouched.
printf '%s\n' '第 1, 2, 3 项。' > "$tmpdir/sp-nums.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/sp-nums.md" >"$tmpdir/sp-nums.out"
grep -q '^第 1, 2, 3 项。$' "$tmpdir/sp-nums.out"

# 34. Inline code is preserved; only the comma outside it is full-widthed and de-spaced.
printf '%s\n' '`a, b` 这种, 对。' > "$tmpdir/sp-code.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/sp-code.md" >"$tmpdir/sp-code.out"
grep -q '^`a, b` 这种，对。$' "$tmpdir/sp-code.out"

# 35. A markdown link LABEL is rendered prose; half-width punctuation in it is checked.
printf '%s\n' '见 [中文,标点](https://x.com) 一下。' > "$tmpdir/label.md"
if bash "$CHECKER" --lang zh "$tmpdir/label.md" >"$tmpdir/label.out"; then
  echo "md-link label punctuation should be checked"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/label.out"

# 36. Punctuation inside a URL (md-link target or bare URL query) stays exempt.
printf '%s\n' '见 [文档](https://x.com/a,b) 和 https://y.com/?x=1,2 说明。' > "$tmpdir/urlin.md"
bash "$CHECKER" --lang zh "$tmpdir/urlin.md" >"$tmpdir/urlin.out"
grep -q 'punctuation: ok' "$tmpdir/urlin.out"

# 37. A half-width comma right after a bare URL, followed by CJK, is a sentence separator -> flagged.
printf '%s\n' '访问 https://example.com,然后继续。' > "$tmpdir/urltail2.md"
if bash "$CHECKER" --lang zh "$tmpdir/urltail2.md" >"$tmpdir/urltail2.out"; then
  echo "comma after bare URL followed by CJK should be flagged"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/urltail2.out"

# 38. A short inline-code span stays exempt even on a line that also has a long backtick run.
python3 -c 'import sys; sys.stdout.write("正常 " + chr(96)+"中文,标点"+chr(96) + " 文字 " + chr(96)*60 + " 结尾。\n")' > "$tmpdir/longrun.md"
bash "$CHECKER" --lang zh "$tmpdir/longrun.md" >"$tmpdir/longrun.out"
grep -q 'punctuation: ok' "$tmpdir/longrun.out"

# 39. auto-detect: a mostly-Chinese line with one Korean glyph still routes to zh, not skipped ko.
printf '%s\n' '这是中文,标点。한字。' > "$tmpdir/zh-ko.md"
if bash "$CHECKER" "$tmpdir/zh-ko.md" >"$tmpdir/zh-ko.out" 2>&1; then
  echo "Chinese text with one Korean glyph must not be skipped as ko"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/zh-ko.out"

# 40. ja flags a half-width colon/semicolon adjacent to kana (parity with zh).
printf '%s\n' 'テスト:次' > "$tmpdir/ja-colon.md"
if bash "$CHECKER" --lang ja "$tmpdir/ja-colon.md" >"$tmpdir/ja-colon.out"; then
  echo "ja should flag a half-width colon adjacent to kana"; exit 1
fi
grep -q 'ja-ascii-punct' "$tmpdir/ja-colon.out"

# 41. A full-width space (U+3000) in Chinese prose is flagged.
printf '%s\n' '中文　English' > "$tmpdir/fwspace.md"
if bash "$CHECKER" --lang zh "$tmpdir/fwspace.md" >"$tmpdir/fwspace.out"; then
  echo "full-width space U+3000 should be flagged"; exit 1
fi
grep -q 'zh-fullwidth-space' "$tmpdir/fwspace.out"

# 42. A half-width sentence-ender after Latin/digit closing a Chinese clause is flagged.
printf '%s\n' '性能提升了 50%!' > "$tmpdir/tailpunct.md"
if bash "$CHECKER" --lang zh "$tmpdir/tailpunct.md" >"$tmpdir/tailpunct.out"; then
  echo "half-width sentence-ender after a digit should be flagged"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/tailpunct.out"

# 43. Counter-case: a Latin enumeration comma "API, SDK" inside Chinese is NOT flagged.
printf '%s\n' '用 API, SDK 和工具' > "$tmpdir/latinlist.md"
bash "$CHECKER" --lang zh "$tmpdir/latinlist.md" >"$tmpdir/latinlist.out"
grep -q 'punctuation: ok' "$tmpdir/latinlist.out"

# 44. A U+2028 line separator is in-line, not a line break: line numbers match grep/editors.
python3 -c 'import sys; sys.stdout.write("第一行,错 第二行,错\n")' > "$tmpdir/u2028.md"
bash "$CHECKER" --lang zh "$tmpdir/u2028.md" >"$tmpdir/u2028.out" || true
if grep -qE ':2:' "$tmpdir/u2028.out"; then echo "U+2028 must not create a line 2"; exit 1; fi
grep -qE ':1:[0-9]+ \[zh-halfwidth-punct\]' "$tmpdir/u2028.out"

# 45. (1) Half-width punctuation after a bold marker is flagged (** sits between Han and the mark).
printf '%s\n' '**决策**: 保持现状。' > "$tmpdir/bold.md"
if bash "$CHECKER" --lang zh "$tmpdir/bold.md" >"$tmpdir/bold.out"; then
  echo "should flag half-width colon after a bold marker"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/bold.out"

# 46. (1) --fix full-widths the punctuation after a bold marker and keeps the ** intact.
printf '%s\n' '**决策**: 保持。' > "$tmpdir/boldfix.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/boldfix.md" >"$tmpdir/boldfix.out"
grep -qF '**决策**：保持。' "$tmpdir/boldfix.out"

# 47. (1) A real asterisk between non-CJK is left alone, AND the bridge fires across an
# asterisk from a Han char -- drop the [*_]* bridge and the positive case below turns red.
printf '%s\n' '公式 2*3=6 成立。' > "$tmpdir/star.md"
bash "$CHECKER" --lang zh "$tmpdir/star.md" >"$tmpdir/star.out"
grep -q 'punctuation: ok' "$tmpdir/star.out"
printf '%s\n' '中文*,后面' > "$tmpdir/star2.md"
if bash "$CHECKER" --lang zh "$tmpdir/star2.md" >"$tmpdir/star2.out"; then
  echo "bridge should flag a half-width mark reached across an asterisk from a Han char"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/star2.out"

# 48. (2) A comma glued to the next Latin letter (no space) is flagged in zh prose.
printf '%s\n' '模型 sonnet,haiku 都跑。' > "$tmpdir/latincomma.md"
if bash "$CHECKER" --lang zh "$tmpdir/latincomma.md" >"$tmpdir/latincomma.out"; then
  echo "should flag a Latin comma with no following space"; exit 1
fi
grep -q 'missing-space-after-punct' "$tmpdir/latincomma.out"

# 49. (2) The same check fires in en mode.
printf '%s\n' 'run sonnet,haiku now' > "$tmpdir/encomma.md"
if bash "$CHECKER" --lang en "$tmpdir/encomma.md" >"$tmpdir/encomma.out"; then
  echo "en should flag a comma with no following space"; exit 1
fi
grep -q 'missing-space-after-punct' "$tmpdir/encomma.out"

# 50. (2) Counter-case: a thousands separator (1,000) and a spaced list (API, SDK) are both spared.
printf '%s\n' '共 1,000 项，用 API, SDK。' > "$tmpdir/nums2.md"
bash "$CHECKER" --lang zh "$tmpdir/nums2.md" >"$tmpdir/nums2.out"
grep -q 'punctuation: ok' "$tmpdir/nums2.out"

# 51. (3) A half-width paren touching a Han char is flagged (conservative: only when CJK-adjacent).
printf '%s\n' '这个判断(见上)成立。' > "$tmpdir/paren-zh.md"
if bash "$CHECKER" --lang zh "$tmpdir/paren-zh.md" >"$tmpdir/paren-zh.out"; then
  echo "should flag a half-width paren touching a Han char"; exit 1
fi
grep -q 'zh-halfwidth-paren' "$tmpdir/paren-zh.out"

# 52. (3) Counter-case: a paren around pure Latin/code, not touching a Han char, is left alone.
printf '%s\n' '调用 foo(x) 完成。' > "$tmpdir/paren-en.md"
bash "$CHECKER" --lang zh "$tmpdir/paren-en.md" >"$tmpdir/paren-en.out"
grep -q 'punctuation: ok' "$tmpdir/paren-en.out"

# 53. (3) --fix does NOT rewrite parens (report-only; full-widthing (English) is a house-style call).
printf '%s\n' '这个判断(见上)。' > "$tmpdir/paren-nofix.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/paren-nofix.md" >"$tmpdir/paren-nofix.out"
grep -qF '判断(见上)' "$tmpdir/paren-nofix.out"

# 54. (P2) --fix full-widths a half-width sentence-ender that closes a Chinese line after Latin (codex finding).
printf '%s\n' '这次用的是 API?' > "$tmpdir/tail-fix-api.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/tail-fix-api.md" >"$tmpdir/tail-fix-api.out"
grep -qxF '这次用的是 API？' "$tmpdir/tail-fix-api.out"

# 55. (P2) Same gap after a digit/percent at end of line.
printf '%s\n' '性能提升了 50%!' > "$tmpdir/tail-fix-percent.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/tail-fix-percent.md" >"$tmpdir/tail-fix-percent.out"
grep -qxF '性能提升了 50%！' "$tmpdir/tail-fix-percent.out"

# 56. (P2) Latin-tail ender followed by a CJK punctuation mark is also full-widthed.
printf '%s\n' '这次用的是 API?。' > "$tmpdir/tail-fix-cjkpunct.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/tail-fix-cjkpunct.md" >"$tmpdir/tail-fix-cjkpunct.out"
grep -qxF '这次用的是 API？。' "$tmpdir/tail-fix-cjkpunct.out"

# 57. (review) en-space-before-punct gets a positive assertion (was the only detect rule with none).
printf '%s\n' 'Hello , world.' > "$tmpdir/en-space.md"
if bash "$CHECKER" --lang en "$tmpdir/en-space.md" >"$tmpdir/en-space.out"; then
  echo "en should flag a space before punctuation"; exit 1
fi
grep -q 'en-space-before-punct' "$tmpdir/en-space.out"

# 58. (review) --fix does NOT rewrite an em-dash (detect-only, same contract test 53 pins for parens).
printf '%s\n' '判断——其实不必。' > "$tmpdir/dash-nofix.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/dash-nofix.md" >"$tmpdir/dash-nofix.out"
grep -qF '——' "$tmpdir/dash-nofix.out"

# 59. (review) --fix does NOT rewrite a full-width space U+3000 (ambiguous: delete vs half-width).
printf '%s\n' '中文　English' > "$tmpdir/fwspace-nofix.md"
bash "$CHECKER" --lang zh --fix "$tmpdir/fwspace-nofix.md" >"$tmpdir/fwspace-nofix.out"
grep -qF '　' "$tmpdir/fwspace-nofix.out"

# 60. (review) The en-dash (U+2013) branch of the dash rule is exercised, not just em-dash.
printf '%s\n' '范围 1–2 之间。' > "$tmpdir/endash.md"
if bash "$CHECKER" --lang zh "$tmpdir/endash.md" >"$tmpdir/endash.out"; then
  echo "en-dash should be flagged by the dash rule"; exit 1
fi
grep -q '\[dash\]' "$tmpdir/endash.out"

# 61. (review) ja also catches a half-width mark across a bold marker (parity with zh test 45).
printf '%s\n' '**見出し**: 値' > "$tmpdir/ja-bold.md"
if bash "$CHECKER" --lang ja "$tmpdir/ja-bold.md" >"$tmpdir/ja-bold.out"; then
  echo "ja should flag a half-width colon after a bold marker"; exit 1
fi
grep -q 'ja-ascii-punct' "$tmpdir/ja-bold.out"

# 62. (review F4) A missing/unreadable file exits 2 (distinct from findings code 1) with a stderr note.
bash "$CHECKER" --lang zh "$tmpdir/does-not-exist.md" >"$tmpdir/missing.out" 2>"$tmpdir/missing.err" && rc=0 || rc=$?
[ "$rc" = 2 ] || { echo "missing file should exit 2 (not the findings code), got $rc"; exit 1; }
grep -q 'cannot read' "$tmpdir/missing.err"

# 63. (review F3) Kana inside a code fence does not misroute an otherwise-Chinese doc to ja.
printf '%s\n' '这是中文,有标点。' '```js' '// テスト用' '```' '继续中文,这里。' > "$tmpdir/codekana.md"
if bash "$CHECKER" "$tmpdir/codekana.md" >"$tmpdir/codekana.out" 2>&1; then
  echo "kana in a code fence must not stop zh detection"; exit 1
fi
grep -q 'zh-halfwidth-punct' "$tmpdir/codekana.out"

echo "punctuation smoke: ok"
