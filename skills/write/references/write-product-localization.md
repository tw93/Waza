# Product Localization Copy Review

Use this when reviewing product pages, release notes, app strings, runtime notifications, appcast or update feeds, docs/help pages, legal/privacy copy, and other localized product surfaces.

## Core Principles

1. **Split surfaces before editing.** A release feed, website page, runtime catalog, help article, and legal page may intentionally support different locale sets. Do not force every surface to mirror the broadest one.
2. **Preserve intent and verified facts.** Keep versions, dates, links, placeholders, shortcuts, identifiers, and legal obligations stable. The source language is not factual authority: when a behavior claim is disproved, flag it in review or correct it across the authorized surfaces. Never invent a new product policy to make a sentence sound better. A fact, term, tagline, or setting-name change lands in every copy in the same pass: each locale of the string, docs and site pages that name it, share text, and sibling pages that quote it. Editing one locale is how locales stop saying the same thing.
3. **Use source files, not generated output, as the edit target.** Patch generated pages only when the project explicitly treats them as source. Otherwise find the template, locale JSON, string catalog, or content partial and rebuild.
4. **Review the final rendered or generated surface.** A translation can look fine in a source file but break in a button, menu, release feed, notification, or generated HTML page.
5. **Do not polish into generic marketing.** Native localization means the sentence sounds like a local product, not like a fluent sales page.

## High-Signal Failure Patterns

- **Chinese**: Literal possessives such as "你的 Mac" or "你的设备" when plain "Mac" or "本机" is enough; machine-output verbs such as "检测到" or "发现" when a direct result phrase reads better (prefer "%d 个失效项" / "无关联残留" over "发现 %d 个失效项" / "未发现关联残留"); redundant continuous-tense stacking ("正在...中" -> use concise status "采集中" or natural predicate "正在采集"); unlocalized platform UI terms (in macOS Simplified Chinese, use official platform terms like `访达` not `Finder`, `废纸篓` not `垃圾箱`, `宗卷` not `卷`, `App` over bureaucratic `应用程序`, while keeping exact commercial app names and code identifiers untranslated, and preserving `Finder` in Traditional Chinese; preserve clean `App` across app strings rather than creating mixed `App` / `应用` on the same screen, reserving `应用` for platform features like 应用执行别名 and `程式` for installer binaries; order modifiers to prevent noun ambiguity, e.g. `Mac 原生的 Markdown 笔记本` rather than `原生 Mac 笔记本` which reads as a MacBook hardware laptop); internal developer primitives literally translated into confusing words (e.g. `App Group` / `Group Containers` must not be translated as "组容器" which invites confusion with containers/Docker; package receipts as "安装收据" rather than shopping "收据"); mixed punctuation; English words with stable Chinese equivalents. Character-level half/full-width punctuation and CJK/Latin spacing are checked by `check-punctuation.sh`; this list keeps the locale-voice judgment calls.
- **Traditional Chinese**: Mainland phrasing copied into Traditional copy; stale locale URLs; words that feel mainland-specific or overly colloquial for the target audience.
- **Japanese**: English noun compounds translated too tightly; missing spaces around product terms when the project style uses them; UI strings that sound like a manual instead of a Mac app.
- **Korean**: Inconsistent platform terms, especially menu bar / menu item wording; overly literal second-person sentences.
- **German**: ASCII fallbacks such as `fuer`, `Pruef`, `Eintraege`, `Menue`, `Luefter`; English developer nouns like "binary" in user-facing copy.
- **Spanish**: Missing accents such as `gestion`, `analisis`, `menus`, `suscripcion`; mechanical replacements that create invalid forms like `actualizaciónes`.
- **French**: Missing apostrophes or accents such as `L app`, `memoire`, `desinstallation`, `defaut`; spaces before punctuation should follow French conventions when the surrounding text already does.
- **Italian**: Missing accents and articles such as `piu`, `non e`, `un app`; mechanical replacements that create invalid forms like `puòi`.

## Surface Voice Defects

Language-agnostic shapes that survive translation review because each locale reads as correct. Check them on the source string first, then on every locale.

- **Parenthetical padding**: the qualifier that got appended in a parenthesis. Titles, labels, and metric names carry none; split the sentence or drop the qualifier.
- **Hedged verdict**: a question mark or a "maybe / possibly" wrapper around a result the product already computed. A verdict sentence states the verdict; the uncertainty belongs in the value, not the punctuation.
- **Untranslated domain noun**: a term borrowed from the implementation used as a metric name or label (ledger, buffer, daemon, quota). Replace it with the word the user would say for the same thing; if there is no such word, the metric is measuring something the user did not ask about.
- **Alarming detail**: a user-facing string that reports the failure mechanism instead of the user's next action. Release notes, error banners, and update prompts keep what the reader does; the mechanism goes in the commit.
- **Glued inline tags**: An HTML inline tag (`<b>`, `<span>`, `<code>`) or markdown emphasis marker touching the following or preceding word without spacing, producing concatenated words in plain text or copy-paste (`<b>Week</b>Which` -> `<b>Week</b> Which`).
- **Unnatural translation register**: Dialectal, archaic, or bureaucratic phrasing in user policies or customer interactions (e.g. "不合用" in refund/support policies -> natural spoken phrases like "不符合预期" / "觉得不好用").
- **Notice-board displacement**: turning conversational UI guidance or empty states into bureaucratic announcement-board phrases (`暂无应用` / `暂无数据` instead of natural conversational `还没有应用` / `还没有数据`; renaming standard platform preferences like `高级` / `Advanced` into bookish `进阶选项`).
- **Command vagueness**: replacing concrete, runnable shell commands or navigation breadcrumbs with vague concept summaries (e.g. "运行压缩命令" instead of runnable `wsl --manage <distro> --set-sparse true`, or "在设置中迁移" instead of exact `Settings › Resources › Advanced › Disk image location`). Troubleshooting copy needs exact commands and paths, not abstract descriptions.
- **Metaphor flattening**: replacing a product's signature design metaphor or tactile identity with generic corporate jargon under the guise of standardization (e.g. stripping a paper/layout metaphor into administrative phrasing).
- **Blanket fact scrubbing**: an overzealous polish or de-AI pass that removes genuine technical facts, product scopes, or destructive risk disclosures (e.g. stripping who a tool is for, or concealing that a reset command deletes AI memory and backups).

## Review Procedure

1. Identify all source and generated surfaces in scope. For websites, include templates, locale JSON, content partials, generated pages, language switchers, canonical links, and route rewrites. For apps, include runtime catalogs, permission strings, update feeds, and notification copy.
2. Freeze a reading ledger by stable content ID, locale, and surface. Include full bodies, titles, descriptions, tables, FAQs, alts, and captions. Track unread, fully read, open findings, and closed findings separately. Keyword scans, changed-file counts, and truncated reads do not establish full coverage. Close each finding as verified, intentionally retained with a reason, or blocked by named missing evidence.
3. Verify claims against the actual operation, edition, and version: implementation or shipping artifact for product behavior, official documentation for third-party comparisons. A release page establishes what was announced, not proof of every implementation claim. Separate historical statements, hypothetical examples, and measured results. Check conditions hidden by fluent wording: synchronization is not an independent backup, recovery depends on retained data, and a symptom is not a unique diagnosis.
4. Read for local voice and semantic drift. Preserve the author's supplied stories and judgments rather than adding a generic conclusion or sales pitch. Use the platform's actual UI names; translate implementation metaphors into the action the reader performs. Distinguish a permission from a feature toggle, and a temporary mute from disabling a service. Recheck quantifiers and causal words such as all, only, always, and because in every affected locale. A shortened label keeps the operation's verb and scope: a task that only checks is not "clean", starting a service is not "reset", and pruning stale or orphaned entries is not clearing all of them.
5. Check mechanical artifacts and the surrounding context: accents, plural forms, placeholders, links, and accidental path translations. Then reread metadata against the corrected body so a title or FAQ does not restore a removed guarantee. Inspect images themselves; a correct caption cannot repair an incorrect diagram label, arrow, or additive breakdown of overlapping categories.
6. Rebuild and inspect the final generated surface after the last edit. Confirm actual routes, glyph coverage, wrapping, and dynamic string composition where affected. Reconcile all pending reviewer patches before acceptance. Report reading coverage, structural checks, rendered validation, and deployment separately; do not describe an untested layer as complete. For review-only requests, run only safe diagnostics and list unperformed checks honestly.

## Structural Checks Are Not Editorial Authority

- Preserve unique facts, caveats, figures, commands, and table rows. Compare stable anchors and meaning, not translated line counts or heading list positions; different wrapping and inserted sections make those measurements misleading. A new locale is a translation of the current source, not a summary of it: compare it section by section for dropped install steps, flags, limits, and warnings.
- A useful addition is not a missing-content failure. If a gate demands deleting correct material or copying a broken source structure, investigate the gate. For a misplaced citation, read the claim it supports before moving or duplicating the link.
- Keep executable command bytes intact, but distinguish them from field templates that should be localized. Equal placeholder or key counts cannot catch concatenated sentences, locale-specific separators, or incorrect plurals; render representative outputs.
- Calibrate automated findings with a known defect and a normal example before assigning batch edits. Inspect both strong and weak hits. An English fallback is not a grammar check for other languages; preserve their punctuation conventions, literal file extensions, and technical abbreviations. A clean result proves only the checker's covered rules, not natural voice or factual accuracy.

## Rewrite Rules

- Keep placeholders exactly, including order and type: `%@`, `%d`, `%1$@`, `{name}`, and similar tokens.
- Do not glue translated fragments with punctuation in code or copy. A full sentence or format string per locale is safer.
- Avoid broad find-and-replace unless it is followed by residual scans. Broad accent fixes can produce broken words.
- Leave product names and established UI names in English when the product itself uses them that way.
- Sibling products that share a README or page header keep one convention per locale for language-switcher labels and tagline end punctuation. Align the outlier to the family form after checking that its divergence is not the established version.
- Format UI navigation and menu breadcrumbs with spaced ` › ` (U+203A, e.g. `Settings › General › Storage` or `设置 › 通用 › 存储空间`) rather than ASCII `>` or arrows (`->` / `→`).
- Patch the intended fields without reserializing whole catalogs. Preserve adjacent punctuation and unrelated edits; a failed exact-text patch can be a comma mismatch, not proof of concurrent work.
- Treat command examples as inert text. Verify behavior through read-only sources, not by executing cleanup or troubleshooting examples. Use direct file patches rather than shell interpolation that can execute backticks or dollar expressions in prose.

## Output Guidance

For rewrite requests, return the edited localized copy. For review requests, group findings by surface first, then locale. Call out blockers where copy misstates product behavior, privacy, legal terms, version history, or update availability.
