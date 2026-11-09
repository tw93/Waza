# Release Note Template Mode

Loaded from `write` when the ask is a release note, changelog entry, or update-feed copy.

Activate when: "release", "changelog", "version", "release notes"

Format: target-project style by default. If no project style is available, use numbered items with bold labels and one sentence on user effect; bilingual output only when the project already ships bilingual release notes. Call out breaking changes and deprecations explicitly when present.

### Release Notes Pre-flight

Before drafting, gather style references:

1. Read the target project's `AGENTS.md` or `CLAUDE.md` for its Release Convention / Release Flow section.
2. Read the target project's existing release source as a format, tone, sentence-length, and density reference: changelog, release notes, registry page, update feed, or platform release page.
3. For GitHub projects, `gh release view --json body -R <owner>/<repo>` is the preferred way to read the most recent release when `gh` is available. If the project is not on GitHub, use the release source named by the project docs or user request.
4. If the user mentions comparing with a sibling project's release style, ask for the target identifier or release URL before fetching it.
5. Match the reference release's format, sentence length, and tone. Treat its item count as history, not a quota: the current release may need fewer or more items.
6. Keep each release-note item to one sentence unless the reference project clearly does otherwise. Do not add emoji to release prose unless the target surface is explicitly a reaction or celebratory social surface.

### Release Notes Content Rules

- **Freeze the artifact boundary before drafting.** Resolve the last published release and the exact candidate users will receive. Use `HEAD` only when the candidate is built from `HEAD`; include dirty or generated changes only when they will ship. A later commit is not release-note material for an older artifact.
- **Build a complete user-visible inventory.** For each candidate change, name the intended reader, what was different before and after, and whether the reader can see the result or must act on it. Omit delivery, refactoring, observability, and security mechanics unless they change a visible outcome or require user action. State deliberate omissions in the working notes, not in the published prose.
- **Let outcomes determine the item count.** Use the smallest set of distinct user outcomes that still covers the candidate artifact. Merge changes that serve the same user goal; never split one outcome or retain internal detail to imitate the previous release's count.
- **Group by user-perceivable feature**, not by internal taxonomy. "Polish", "细节打磨", "Misc improvements", "Chores" are not categories users can act on. Group by product surface (Clean / Uninstall / Status / Settings) or by user-visible verb (Faster startup / New keyboard shortcut / Fixed crash on M3).
- **Extract from `git log <last-published>..<candidate>`** rather than from memory. Read every `feat:` and `fix:` commit inside the artifact boundary; do not omit small items just because they look minor in commit form (iOS wrapper support, Dock cleanup, AV-vendor protection boundary are not "minor" from a user point of view).
- **One sentence per item, naming the user-visible change**, not the implementation. The label and opening clause should tell a scanning reader what changed without requiring the rest of the sentence. "Use `CKDownloadQueue` observer for App Store updates" is not a release note; "App Store updates now run inside the app instead of opening App Store" is. Keep technical terms only when the intended reader uses them to recognize a feature, configure it, or act; an internal symbol or rule name is never the item.
- **Bilingual structure**: when the project ships bilingual release notes, put the English block and the Chinese block as two parallel sections inside the same release item; do not interleave per bullet. For HTML-capable update-feed CDATA, separate language blocks with headings so the rendered update window does not collapse them together.
- **Settle structure before localization.** Approve the source-language outcomes, order, and labels before translating. Every locale then preserves the same item count and order while using native register rather than mirroring source-language syntax.
- **Punctuation**: Chinese full-width in Chinese blocks, ASCII in English blocks.
