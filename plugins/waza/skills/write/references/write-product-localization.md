# Product Localization Copy Review

Use this when reviewing product pages, release notes, app strings, runtime notifications, appcast or update feeds, docs/help pages, legal/privacy copy, and other localized product surfaces.

## Core Principles

1. **Split surfaces before editing.** A release feed, website page, runtime catalog, help article, and legal page may intentionally support different locale sets. Do not force every surface to mirror the broadest one.
2. **Keep product facts fixed.** Preserve versions, dates, item order, links, placeholders, keyboard shortcuts, product names, bundle IDs, and behavior claims unless the user asked to change them.
3. **Use source files, not generated output, as the edit target.** Patch generated pages only when the project explicitly treats them as source. Otherwise find the template, locale JSON, string catalog, or content partial and rebuild.
4. **Review the final rendered or generated surface.** A translation can look fine in a source file but break in a button, menu, release feed, notification, or generated HTML page.
5. **Do not polish into generic marketing.** Native localization means the sentence sounds like a local product, not like a fluent sales page.

## High-Signal Failure Patterns

- **Chinese**: Literal possessives such as "你的 Mac" or "你的设备" when plain "Mac" or "本机" is enough; machine-output verbs such as "检测到" when a result sentence would read better; mixed punctuation; English words with stable Chinese equivalents. Character-level half/full-width punctuation and CJK/Latin spacing are checked by `check_punctuation.py`; this list keeps the locale-voice judgment calls.
- **Traditional Chinese**: Mainland phrasing copied into Traditional copy; stale locale URLs; words that feel mainland-specific or overly colloquial for the target audience.
- **Japanese**: English noun compounds translated too tightly; missing spaces around product terms when the project style uses them; UI strings that sound like a manual instead of a Mac app.
- **Korean**: Inconsistent platform terms, especially menu bar / menu item wording; overly literal second-person sentences.
- **German**: ASCII fallbacks such as `fuer`, `Pruef`, `Eintraege`, `Menue`, `Luefter`; English developer nouns like "binary" in user-facing copy.
- **Spanish**: Missing accents such as `gestion`, `analisis`, `menus`, `suscripcion`; mechanical replacements that create invalid forms like `actualizaciónes`.
- **French**: Missing apostrophes or accents such as `L app`, `memoire`, `desinstallation`, `defaut`; spaces before punctuation should follow French conventions when the surrounding text already does.
- **Italian**: Missing accents and articles such as `piu`, `non e`, `un app`; mechanical replacements that create invalid forms like `puòi`.

## Review Procedure

1. Identify all source and generated surfaces in scope. For websites, include templates, locale JSON, content partials, generated pages, language switchers, canonical links, and route rewrites. For apps, include runtime catalogs, permission strings, update feeds, and notification copy.
2. Pick the factual source of truth. Release notes usually follow the English release page or changelog; runtime copy follows the current app behavior and placeholders.
3. Run a first pass for local voice: remove translationese, restore local punctuation, and keep product names stable.
4. Run a second pass for mechanical artifacts: missing accents, stale paths, invalid plural forms, malformed placeholders, and accidental path translations.
5. Rebuild generated files and rerun the relevant project checks. If the user only asked for review, list the required checks instead of claiming they ran.

## Rewrite Rules

- Keep placeholders exactly, including order and type: `%@`, `%d`, `%1$@`, `{name}`, and similar tokens.
- Do not glue translated fragments with punctuation in code or copy. A full sentence or format string per locale is safer.
- Avoid broad find-and-replace unless it is followed by residual scans. Broad accent fixes can produce broken words.
- Leave product names and established UI names in English when the product itself uses them that way.
- Legal and privacy copy should be plain and accurate. Do not make it friendlier by weakening obligations, data collection boundaries, refund terms, or third-party roles.
- Release feed localization can be narrower than website localization. Respect the surface-specific product decision.

## Output Guidance

For rewrite requests, return the edited localized copy. For review requests, group findings by surface first, then locale. Call out blockers where copy misstates product behavior, privacy, legal terms, version history, or update availability.
