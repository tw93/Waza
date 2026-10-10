# Long-form Article Mode

Loaded from `write` when the input is a long draft that needs structural work before line edits.

Activate when: a long article needs structural review. Multiple headings or images alone do not authorize restructuring.

Read the whole article to distinguish useful explanation from repeated conclusions, table re-reads and generic endings. Preserve the strongest version of a supported point. Do not assume a long article is padded or set a target fraction to delete.

Workflow:

1. **Map first, read-only.** Before editing anything, read the whole article and list every `##` section, table, list, and image. Flag three structural problems: cross-section repetition (same checklist / judgment list / core claim in 2+ sections), table re-reading (a section whose prose walks the rows of the table above it), and whole redundant sections or paragraphs.
2. **Test the paragraph's contribution.** Experience, emotion, personal conviction, qualifications and explanations can all carry a paragraph. Lack of a new fact or source is not grounds for cutting it. Check whether an edit loses the author's stance or emotional intensity, as well as factual meaning. A shorter, more neutral draft can be a worse one. Keep the maker's hands-on perspective: personal verified pitfalls, concrete costs, and real tradeoffs are far more valuable than AI-generated exhaustive taxonomies or recapping already-established concepts. Deliberate series titles or column names are authorial choices, not AI pattern flags.
3. **Respect the editing scope.** Read-only requests get proposed change-points. Explicit rewrite requests authorize edits within that scope; do not ask again for routine sentence cuts. Name whole-paragraph cuts in the diff summary, and ask before deleting a section or reorganizing headings unless that structural work was requested.
4. **Then line-level de-AI**, section by section, using the relevant language references. For mirrors, check both meaning and native rhythm.
5. **Return the requested artifact.** For repository edits, preserve frontmatter, code, media, links and substantive explanations, run the site's build, and report the scoped diff. A pasted-text rewrite returns the prose. Run the Punctuation Gate on edited prose without changing technical examples to satisfy a style rule.

Do not single-pass rewrite a long article: it silently overwrites the author's hand-tuned phrasing and cannot be reviewed as a diff. See `write-zh.md` 结构级重复与表格复读（长文专项）for the matching content rules.
