---
name: write
description: "Rewrites and polishes prose in Chinese or English, removes AI-like wording, and reviews product localization copy while preserving intent for drafts, docs, release notes, launch copy, and social posts. Use when users ask in any language to draft, rewrite, proofread, localize, polish release notes, remove AI-like wording, or prepare launch and social copy. Not for code comments, commit messages, or inline docs."
when_to_use: "帮我写, 改稿, 润色, 去AI味, 写一段, 审稿, 文档review, 本地化文案, 多语言文案, i18n copy, localization copy, check this document, 推特, twitter, X推文, tweet, social post, 连贯性, 段落连贯, draft, edit text, proofread, sound natural, polish, rewrite"
dispatch_intent: "Writing, editing prose, polish, release notes, launch/social copy, remove AI tone"
---

# Write: Cut the AI Taste

Prefix your first line with 🥷 inline, not as its own paragraph.

**Update check (non-blocking).** Before starting, run `bash scripts/check-update.sh` once; if it prints a line, relay it to the user, then continue. It runs at most once a day, only reads a public version file, sends no data, and fails silently.

Strip AI patterns from prose and rewrite it to sound human. Do not improve vocabulary; remove the performance of improvement.

## Outcome Contract

- Outcome: the prose preserves the author's intent while sounding natural for its audience and surface.
- Done when: meaning, factual claims, and structure are preserved unless the user asked to change them, and AI-like wording is removed; punctuation and CJK/Latin mixing pass the Punctuation Gate for the output language.
- Evidence: supplied text, target audience, project style references, release or product state, and requested language.
- Output: the edited prose only, unless the user asked for notes, variants, or review comments.

## Core Stance

This skill is a catalog of smells, not a checklist to run top to bottom. Use it to recognize AI taste, then make judgment calls. The reference files (especially `write-zh.md`) are long because they accumulated examples over many sessions; do not try to apply every rule to every text. Applying more rules is not doing a better job.

- **Over-editing is failure, equal to under-editing.** If a sentence is already natural, clear, and stable, leave it. Most polish is subtraction (cut repetition, summary-tone, restated conclusions), not phrase-by-phrase replacement.
- **The author's voice wins.** Keep the author's existing colloquial words, cadence, and stance. When a rule conflicts with a deliberate authorial or genre choice (a question title in a narrative piece, a list the author wants kept), the author wins. Rules are defaults, not laws.
- **Banned-phrase lists and replacement tables are examples, not find-and-replace.** A flagged word that reads naturally in context stays. Match the smell, not the string.
- **Prefer fewer, stronger edits.** Three changes that matter beat thirty mechanical swaps that flatten the voice.

When distilling a new lesson into this skill, fold it into an existing principle instead of appending another banned phrase. This skill must not grow monotonically; collapsing specifics back into principles is part of maintaining it.

## Pre-flight

1. **Text present?** If the user gave only an instruction with no actual prose to edit, ask for the text in one sentence. Do not proceed.
2. **Audience locked?** If the intended audience is unclear and cannot be inferred from the text (blog reader vs RFC vs email), ask before editing. Junior engineer and senior architect prose should read completely different.
3. **Language detected from the text being edited**, not the user's command:
   - Contains Chinese characters + release notes or social post mode → load `references/write-zh-release-notes.md`
   - Contains Chinese characters + bilingual or translation review → load `references/write-zh-bilingual.md`
   - Product/site/app localization review across multiple locales → load `references/write-product-localization.md`; also load `references/write-zh-bilingual.md` when Chinese copy is present
   - Contains Chinese characters (default prose) → load `references/write-zh-prose.md` (quick rules); load `references/write-zh.md` for the full AI-taste pattern catalog
   - Otherwise → load `references/write-en.md`

Read the loaded reference file. Then edit. No summary, no commentary, no explanation of changes unless explicitly asked.

## Durable Context Preflight

See [rules/durable-context.md](../../rules/durable-context.md) for when to read durable context, the read-order budget, and the memory-type mapping.

For `/write`, voice and format constraints are `decision`, `preference`, and `principle` entries; editing checks are `pattern` and `learning`. The supplied text, audience, project docs, current release state, and source material override memory. Durable preferences can set brevity, tone, and social-post shape. They do not override the hard rule to edit in place, keep meaning intact, and avoid change lists unless the user explicitly asks.

## Hard Rules

- **Meaning first, style second.** If removing an AI pattern would change the author's intended meaning, keep the original.
- **No silent restructuring.** Do not reorganize headings, reorder paragraphs, or merge sections unless structural changes are explicitly requested. Edit in place. (Exception: Long-form Article Mode treats structural cuts and merges as in-scope, since structure is the main problem there; it still proposes them as change-points first instead of doing them silently.)
- **Artifact-grounded claims.** For launch copy, release notes, social posts, product pages, and public replies, ground factual claims in real source material: current app behavior, runnable artifact, screenshot, product page, release page, changelog, issue/PR, or user-provided draft. Do not present handoffs, plans, old memory, or stale screenshots as current product truth, and do not turn concrete product evidence into generic marketing language.
- **No em-dash.** Never produce em-dash (U+2014 `—`) or en-dash (U+2013 `–`) in Chinese or English output. Em-dash is the strongest AI-tone fingerprint in this style of writing. Use commas, periods, colons, semicolons, or parentheses to break clauses. Hyphen-minus (`-`) inside compound words is allowed; replace it with a space or a period when possible. When editing a draft that contains em-dashes, replace every one before returning the text.
- **Stop after output.** Deliver the rewritten text. Do not append a list of changes, a justification, or a closer. (Exception: Long-form Article Mode returns change-points for review instead of a rewritten blob; see that mode.)

## Punctuation Gate

Before returning any produced text (a rewrite, or generated release / reply / social copy), resolve the checker across install layouts and run it:

```bash
GATE="${CLAUDE_SKILL_DIR:+$CLAUDE_SKILL_DIR/scripts/check-punctuation.sh}"
[ -f "${GATE:-}" ] || GATE="${CLAUDE_SKILL_DIR:+$CLAUDE_SKILL_DIR/skills/write/scripts/check-punctuation.sh}"
[ -f "${GATE:-}" ] || GATE="./skills/write/scripts/check-punctuation.sh"
[ -f "${GATE:-}" ] || GATE="$(npx skills path tw93/Waza 2>/dev/null)/skills/write/scripts/check-punctuation.sh"
[ -f "${GATE:-}" ] || { echo "punctuation gate not found; reinstall Waza or set CLAUDE_SKILL_DIR" >&2; exit 1; }
bash "$GATE" --lang <zh|en|ja|auto> <file>   # or pipe text via stdin
```

`${CLAUDE_SKILL_DIR}` is host-injected. The first path is this skill's own `scripts/` (standalone skill, full bundle, or repo); the fallbacks cover the inlined-root release ZIP, where the script ships under `skills/write/scripts/`.

It enforces character-level punctuation by locale (half/full-width marks, CJK/Latin spacing, em/en dashes) and skips code, inline code, URLs, and markdown link targets, so it never fires on code; the script header documents the exact rule set. Fix every finding while preserving meaning; `--fix` rewrites only the zero-ambiguity zh cases to stdout. `--lang auto` classifies the whole input by fixed priority: any kana routes to ja, else any CJK to zh, else any Hangul to ko (reserved, skipped), else en, so a mostly-Chinese text that merely quotes a Korean glyph still routes to zh; pass an explicit `--lang` for mixed-locale or predominantly-English text. The checker owns character-level punctuation only; quote direction and other judgment calls stay with you and the reference files.

## Long-form Article Mode

Activate when: editing a Markdown article or file over ~300 lines, or one with multiple `##` sections plus tables and images (technical long-reads, blog posts, deep dives).

In long-form, the dominant problem is usually structural: the same checklist repeated across sections, prose that re-reads a table sitting right above it, list bloat, whole redundant sections. Sentence-level AI taste is the smaller half. A single in-place polish pass cannot see or fix the structural half, which is why a plain `/write` on a long article feels like it changed wording but left the bloat. This mode therefore overrides two Hard Rules: structural cuts and merges are in-scope, and the output is change-points for review, not a rewritten blob.

Workflow:

1. **Map first, read-only.** Before editing anything, read the whole article and list every `##` section, table, list, and image. Flag three structural problems: cross-section repetition (same checklist / judgment list / core claim in 2+ sections), table re-reading (a section whose prose walks the rows of the table above it), and whole redundant sections or paragraphs.
2. **Propose cuts as change-points.** Show before to after for each structural cut or merge and let the user pick the subset. Never delete a whole section or paragraph silently; confirm first, since it may hold a fact found nowhere else (see `references/write-zh.md` 删段之前先确认信息量).
3. **Then line-level de-AI**, section by section, per `references/write-zh.md`.
4. **Output is change-points, not a blob.** Show what changed so the user can review and keep their own hand-edits. Only return fully rewritten text when the user says 直接改 / just rewrite; when you do return a full rewrite, run the Punctuation Gate on it first.

Do not single-pass rewrite a 40k-character article: it silently overwrites the author's hand-tuned phrasing and cannot be reviewed as a diff. See `references/write-zh.md` 结构级重复与表格复读（长文专项）for the matching content rules.

## Bilingual Review Mode

Activate when: mixed Chinese/English, "Chinese copywriting", "bilingual consistency", "release notes"

**Chinese rules** (from https://github.com/mzlogin/chinese-copywriting-guidelines):
- Space between Chinese and English characters (CN文字EN → CN 文字 EN)
- No mixing of punctuation (Chinese uses 、。？！；：, not commas/periods)
- Consistent terminology across all instances

**English in Chinese documents**: Flag unexplained English, suggest translation or add context.

**Bilingual pairs**: Confirm EN and CN versions convey the same meaning; mark translation loss.

## Product Localization Review Mode

Activate when: "本地化文案", "多语言文案", "localization copy", "i18n copy", product/site/app strings, release feed copy, runtime catalog, or a user asks whether localized copy feels native.

Load `references/write-product-localization.md`. If Chinese is one of the locales, also load `references/write-zh-bilingual.md`.

Default workflow:

1. Separate surfaces first: release feed, website pages, docs/help, runtime strings, legal/privacy copy, and generated pages may have different locale coverage and source files.
2. Preserve factual structure: versions, dates, links, item order, placeholders, and product behavior remain fixed unless the user asks to change them.
3. Review by locale artifacts, not by English meaning alone. Missing accents, ASCII fallbacks, literal possessives, stale locale paths, and mechanical plural or apostrophe errors are first-class issues.
4. After broad cleanup, run a second pass for replacement damage. Do not trust accent sweeps or glossary replacements until the generated output has been checked.
5. When asked to implement, patch the source localization files and rebuild generated pages. When asked only to review, return findings grouped by surface and severity.

## Release Note Template Mode

Activate when: "release", "changelog", "version", "release notes"

Generate from commit messages:
- **Breaking Changes**
- **New Features**
- **Fixes & Improvements**
- **Deprecations**

Format: target-project style by default. If no project style is available, use numbered items with bold labels, one sentence on user effect, and bilingual output only when the project already uses bilingual release notes.

### Release Notes Pre-flight

Before drafting, gather style references:

1. Read the target project's `CLAUDE.md` for its Release Convention / Release Flow section.
2. Read the target project's existing release source as a style, length, and density reference: changelog, release notes, registry page, update feed, or platform release page.
3. For GitHub projects, `gh release view --json body -R <owner>/<repo>` is the preferred way to read the most recent release when `gh` is available. If the project is not on GitHub, use the release source named by the project docs or user request.
4. If the user mentions comparing with a sibling project's release style, ask for the target identifier or release URL before fetching it.
5. Match the reference release's item count, sentence length, and tone. Do not invent a new format.
6. Keep each release-note item to one sentence unless the reference project clearly does otherwise. Do not add emoji to release prose unless the target surface is explicitly a reaction or celebratory social surface.

### Release Notes Content Rules

- **Group by user-perceivable feature**, not by internal taxonomy. "Polish", "细节打磨", "Misc improvements", "Chores" are not categories users can act on. Group by product surface (Clean / Uninstall / Status / Settings) or by user-visible verb (Faster startup / New keyboard shortcut / Fixed crash on M3).
- **Extract from `git log <last-tag>..HEAD`** rather than from memory. Read every `feat:` and `fix:` commit; do not omit small items just because they look minor in commit form (iOS wrapper support, Dock cleanup, AV-vendor protection boundary are not "minor" from a user point of view).
- **One sentence per item, naming the user-visible change**, not the implementation. "Use `CKDownloadQueue` observer for App Store updates" is not a release note; "App Store updates now run inside the app instead of opening App Store" is.
- **Bilingual structure**: when the project ships bilingual release notes, put the English block and the Chinese block as two parallel sections inside the same release item; do not interleave per bullet. For HTML-capable update-feed CDATA, separate language blocks with headings so the rendered update window does not collapse them together.
- **No em-dash** in release prose (covered by the Hard Rule). Use Chinese full-width punctuation in Chinese blocks, ASCII in English blocks.

## Public Reply Mode (GitHub issue / PR)

Activate when: "回复 issue", "reply to PR", "comment on #N", "回 issue", or the user asks for the text of a GitHub issue / PR comment.

Five hard rules for the reply body:

1. **Open with `@<reporter>` + one thanks line.** Match the reporter's language (Chinese → "感谢反馈" / English → "thanks for the detailed report"). No exclamation mark. No emoji. No "🙏".
2. **Then state the cause in one sentence, the impact in one sentence.** No multi-paragraph background, no internal symbol names, no walk-through of the fix.
3. **Then state the ship state**, exactly one of: already shipped in v<X.Y.Z>, fixed on `main` and going out in the next release, planned for v<X.Y.Z>, not planned (with one-line reason and an alternative path). Do not write "already shipped" without release evidence in the current turn.
4. **Two paragraphs maximum**, separated by one blank line. No bullet lists, no section headers, no code blocks except a one-line command when actually needed.
5. **No em-dash.** Use commas, periods, colons. (Covered by the Hard Rule, surfaced again because issue replies attract this pattern.)

The reply is the final user-facing text, not an agent log. Do not write "刚才我判断错了", "前面回复有误", "I re-read it and changed the comment", or any meta narration about your own process. If editing an existing maintainer comment, replace it with the clean final wording as if it were the only comment the user will read.

Before posting, re-read the live issue / PR with `gh issue view <num>` or `gh pr view <num>`. Do not reply from memory; titles, states, and author languages change between sessions.

For paid / subscribed users, acknowledge the purchase relationship and the inconvenience in one phrase, then state the boundary. Do not over-explain. When the current product cannot support their setup, suggest the safest practical path (upgrade macOS, wait for the next release, provide logs, refund route) without arguing.

Closing rule: when closing as `completed`, the comment must independently explain what was fixed and the expected release. When closing as `not planned`, the comment must independently explain the current boundary and an alternative path. Do not rely on prior thread context as the explanation.

## Document Review Mode

Activate when: PDF, document, white paper, "review this document", "check this document", "审稿"

Review checklist:
- **Privacy scan**: Detect PII (names, companies, employment dates, salary hints, location details). Hard stop if any text implies job seeking, competitor info, or personal data leakage.
- **Tone consistency**: Flag voice shifts, register mismatches, formulaic phrasing. Check for AI patterns using the loaded `write-zh.md` or `write-en.md` rules.
- **Bilingual validation**: For CN/EN pairs, confirm translation accuracy and terminology consistency. Apply Bilingual Review Mode rules.
- **Rendering check**: Placeholder text remaining (`Lorem ipsum`, `TODO`, `[TBD]`), broken image links.
- **Durable-doc scan**: If the document is a review report, scorecard, or diagnostic snapshot, flag dated claims, stale line references, private paths, repo-specific commands, and current-score framing. Recommend extracting stable rules instead of preserving the snapshot as evergreen guidance.

Output format: same as prose rewrite, but append `privacy: clear / N issues found` after the reviewed text.

## Paragraph Coherence Mode

Activate when: "连贯性", "段落连贯", "可读性", "coherence", "flow check", "段落顺不顺"

Do not rewrite. Instead, work through each paragraph in sequence:
1. Flag transitions that abruptly shift topic without a signal.
2. Flag paragraphs where the opening sentence does not follow from the previous paragraph's close.
3. Flag rhythm issues: monotone sentence length (all short or all long across a whole paragraph).
4. Suggest the minimal fix for each: one word, one reordered clause, one bridging sentence.

Output: a numbered list of issues, each with the paragraph location and a one-line fix suggestion. Then ask if the user wants any applied.

## Tweet / Social Post Mode

Activate when: "推特", "twitter", "X推文", "tweet", "social post", "折叠长度", "长文推特", "发文"

Apply the five announcement rules for product-engineer projects when the project context or prior artifact shows this style:
1. **Lead with community**: open with the social anchor (star count, user thanks, whose feedback drove the fix). Changes follow, not lead.
2. **Highlights over completeness**: pick 2 to 4 of the most interesting changes. Dropping whole items is fine.
3. **UX framing**: phrase each point as "你用它的时候..." or "有一种...的感觉", not "这个工具做了...".
4. **One stance**: include at least one opinionated sentence revealing why decisions were made.
5. **Native Chinese rhythm**: use idiomatic phrasing. Avoid translation-sounding terms.

Close casually with an invitation, not a CTA. End with one short sentence inviting readers to try, not "立即升级".

For other engineering projects or English posts, apply the same structure (community lead, highlights, UX framing, one stance, casual close) adapted to the project's voice.

## Gotchas

| What happened | Rule |
|---------------|------|
| Reorganized headings without being asked | Do not restructure; edit in place unless structure changes are explicitly requested |
| Appended a "changes made" list after the rewrite | Output is the edited text only. No changelog, no commentary. |
| Used formal register for a blog draft | Match the target audience's register. Blog is conversational, not academic. |
| Applied Chinese/English spacing rules to a pure-English text | Bilingual spacing rules (半角/全角) only apply when the text mixes Chinese and English |
| Polished the user's voice into generic launch copy | Preserve the author's cadence and stance. Use real product artifacts to sharpen facts, not to replace the voice. |
| Drafted release or social copy from memory or a handoff | Read the current release page, changelog, issue/PR, runnable artifact, product page, screenshot, or supplied source before making factual claims. |
| Wrote launch copy in one pass without checking the live screenshots | Iterate: draft, compare against the real product screenshot or page, tighten wording to match what ships, repeat until copy and artifact agree |
| Polished a review report until it sounded timeless | Keep snapshots labeled as snapshots, or distill them into stable rules. Do not make dated claims sound evergreen |

## Output

Return only the edited prose. If the text was truncated or if multiple versions were possible, note that in one sentence after the body. Otherwise, no wrapper, no preamble, no postscript.
