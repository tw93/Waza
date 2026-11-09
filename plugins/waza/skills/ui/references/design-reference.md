# Design Reference

## Tech Stack Conflicts

These combinations produce silent failures or incoherent output. Never combine them:

| Never combine | Why |
|---|---|
| Tailwind + CSS Modules on the same element | Specificity conflicts, unpredictable cascade |
| Framer Motion + CSS transitions on the same element | Double-animating the same property causes jank |
| styled-components or emotion + Tailwind | Two competing class systems fighting for the same DOM node |
| Heroicons + Lucide + Font Awesome in one project | Visual inconsistency, size mismatches, bundle bloat |
| Multiple Google Font families as display fonts | Competing personalities cancel each other out |
| Glassmorphism backdrop-filter + solid `border: 1px solid` | Solid borders shatter the layered depth illusion |
| Dark background + `#ffffff` text at full opacity | Too harsh; use `rgba(255,255,255,0.85)` or `#f0f0f0` |
| Tailwind v4 `@theme` + dynamically constructed class names | `@theme` tokens generate utility classes JIT; if class names are built from variables or not present in scanned source, the class is purged and styles silently disappear. Fix: use static class names in source files, add to `safelist`, or define custom colors in `:root` + `extend.colors` in `tailwind.config.js` instead of `@theme` |

Before writing the first component, name the single CSS strategy for the project: Tailwind only, CSS Modules only, or CSS-in-JS only. Do not drift from it.

## Common Traps

Before submitting, check whether any of the following slipped in without intention:

- A three-part hero: large headline, one-line subtext, two CTA buttons side by side
- A grid of cards with identical rounded corners, identical drop shadows, identical padding
- A top navigation bar with logo left, links center, primary action far right
- Sections that alternate between white and `#f9f9f9`
- A centered icon or illustration sitting above a heading above a paragraph
- A four-column footer with equal-weight columns

Any of these can appear if they serve the design intentionally. They cannot appear by default.

Final test: if you swapped in completely different content and the layout still made sense without changes, you built a template, not a design. Redo it.

## Content Authenticity

Placeholder copy that looks real but is not real breaks the illusion the moment a user reads it. Apply these rules before handoff.

**Sample data:**
- No generic names: not John Doe, Jane Smith, Alex Johnson, or any first-name-last-name combination that reads as filler. Use culturally varied names with real specificity (e.g., Priya Mehta, Lars Eriksson, Nia Okafor).
- No generic company names: not Acme Corp, Nexus, SmartFlow, TechCorp, Initech. Pick names with a domain (e.g., Meridian Logistics, Hokkaido Ceramics, Vantage Bioworks).
- No Lorem Ipsum. Write short real copy that matches the layout's reading level.
- No round numbers in data samples. `99.99%` uptime, `50%` conversion, `$100.00` MRR look synthetic. Use organic values instead: `99.94%`, `47.2%`, `$99.00`.
- Multiple avatar instances must not share the same image. Multiple blog post or event cards must not share the same date.

**UI copy:**
- **Meaning lost in a copy cut:** Judge what the remaining text implies, not just whether words repeat a heading. Keep guarantees, scope and limits when removing them changes that implication; clearer wording can be the right edit without shortening. Before rendering a candidate, run existing copy checks across affected locales and reconcile corresponding surfaces on other platforms with their accepted wording. Compare the whole surface before and after: a settings list with uneven descriptions or a card left holding only an icon needs a layout decision, not another isolated text deletion.
- Sentence case on all headings. Title Case On Every Heading is the most common AI tell in body copy.
- Remove exclamation marks from success states ("Saved!" becomes "Saved", "Done!" becomes "Done"). Reserve `!` for genuine urgency.
- Never open an error message with "Oops!". It reads as condescending.
- No passive voice in error messages ("Something went wrong" becomes "We couldn't load your data. Try refreshing.").
- Banned AI marketing words in hero copy, CTAs, and feature descriptions: Elevate, Seamless, Unleash, Delve, Tapestry, Game-changer, Next-Gen, "In the world of...". These words communicate nothing about the product. Name the specific value instead.

## Placeholders Over Imitations

When an icon, image, or component is unavailable: use a placeholder. In hi-fi design a labeled placeholder is always better than a low-quality attempt at the real thing. Examples: a grey rectangle for a hero image, a monogram wordmark for a missing logo, a dashed border for a component not yet designed.

Never draw illustrative imagery using inline SVG. SVG is for icons and geometric shapes. For photography, illustrations, or product shots, use a placeholder and ask the user to supply real assets.

## Production Quality Baseline

Check before handoff. Accessibility and the CSS-pattern bans are non-negotiable; everything else below is craft detail in service of the locked direction.

> Treat the sections below as craft details, not defaults. Only apply them when they serve the locked visual direction. If removing a detail changes nothing about how the interface feels, leave it out.

### Accessibility
- Icon-only buttons need `aria-label`
- Actions use `<button>`, navigation uses `<a>` (not `<div onClick>`)
- Images need `alt` (or `alt=""` if decorative)
- Visible focus states: `focus-visible:ring-*` or equivalent; never `outline: none` without replacement

### Animation

Settle whether it animates before settling how, and let frequency decide. Something the user triggers hundreds of times a day (keyboard shortcut, command palette, hotkey tab switch) gets no animation, because at that repetition motion is indistinguishable from lag; tens of times a day (hover, list navigation, disclosure) gets the shortest form that still reads; occasional surfaces (modal, drawer, toast, sheet) get the standard treatment; rare or once-only moments (onboarding, first result, completion) can carry delight. Never animate a keyboard-initiated state change. If the only answer to "why does this move?" is that it looks nice, and the user will see it daily, delete it.

Once motion is earned, duration follows the element: press feedback 100-160ms, tooltip and small popover 125-200ms, dropdown and select 150-250ms, modal and drawer 200-500ms. An interactive element over 300ms needs a stated reason. Perceived speed is set by the first frame, not the total, so a 200ms ease-out feels faster than a 200ms ease-in covering the same distance; when something feels slow, fix the curve before the number.

- Honor `prefers-reduced-motion`: disable or reduce animations when set
- Animate `transform`/`opacity` only (compositor-friendly, no layout thrash)
- Default to no bounce or elastic easing: real objects decelerate smoothly; use exponential ease-out (`ease-out-quart`, `ease-out-quint`, or `cubic-bezier(0.16,1,0.3,1)`). The exception is motion a finger or pointer is still driving (drag-to-dismiss, press-and-hold, momentum handoff), where a small bounce (`bounce` 0.1-0.3, or spring `dampingFraction` 0.6-0.8) reads as physical rather than decorative. Motion the system starts on its own stays strictly ease-out
- Never enter from `scale(0)` or exit to it: nothing physical appears out of nothing. Enter from `scale(0.95)` paired with `opacity: 0`; even a barely visible starting size makes the entrance read as an object arriving rather than materializing
- Anchor the origin to the trigger: popovers, dropdowns, menus, and tooltips scale from the control that opened them, not from their own center (`transform-origin: var(--transform-origin)` in Base UI, `.scaleEffect(_:anchor:)` in SwiftUI). Modals are the exception and stay centered, because nothing anchors them
- Interruptible animations: prefer CSS transitions for interactive state changes (hover, toggle, open/close) because they retarget mid-animation; reserve keyframe animations for staged sequences that run once (e.g., staggered page enters)
- Staggered enter: split content into semantic chunks with ~100ms delay; titles into words at ~80ms; typical enter uses `opacity: 0 → 1`, `translateY(12px) → 0`, and `blur(4px) → 0`
- Subtle exit: use a small fixed `translateY(-12px)` instead of full height; keep duration ~150ms `ease-in`, shorter and softer than enter. That short exit is the only place `ease-in` belongs; on an enter, hover, press, or anything the user is watching for a response, it delays the first frame and reads as lag
- Contextual icon swaps: animate with `scale: 0.25 → 1`, `opacity: 0 → 1`, and `blur: 4px → 0px`. With a spring library: `{ type: "spring", duration: 0.3, bounce: 0 }`. Without: keep both icons in DOM (one absolute) and cross-fade with CSS using `cubic-bezier(0.2, 0, 0, 1)`. No rotation unless rotation is semantically meaningful (e.g. a chevron indicating direction change)
- Press feedback: an immediate selected, open, or loading state already acknowledges activation. When that signal is delayed, a restrained active-state change can bridge the gap; if scale fits the product, `scale(0.96)` is one interruptible option. Frequent and reduced-motion interactions keep still feedback
- Page-load guard: use `initial={false}` on animated presence wrappers for toggles, tabs, and icon swaps to prevent enter animations on first render; do not use it for intentional page-load entrance sequences
- Overlapping states: if a crossfade reads as two objects, inspect identity, stacking, and container geometry before retuning duration. Distinct objects may need an asymmetric exit/entry or an immediate swap; blur belongs only to an intentional morph, not to hiding duplicated content or a layout jump

### Performance
- GPU compositing: only use `will-change` for `transform`, `opacity`, or `filter`. Never `will-change: all`. Add only when you notice first-frame stutter; do not apply preemptively to every element
- Images: explicit `width` and `height` (prevents layout shift)
- Below-fold images: `loading="lazy"`
- Critical fonts: `font-display: swap`

### Touch and Mobile
- `touch-action: manipulation` (prevents double-tap zoom delay)
- Full-bleed layouts: `env(safe-area-inset-*)` for notch devices
- Modals and drawers: `overscroll-behavior: contain`
- Hover guard: wrap interactive hover states with `@media(hover:hover)` so they only apply on pointer devices, not touch screens. Tailwind: `[@media(hover:hover)]:hover:bg-...`. Without this, a tapped element on mobile gets a permanent hover state until the next tap elsewhere.

### Typography Details
- Text wrapping: keep natural wrapping by default. Use balancing for a deliberately composed headline only after inspecting the actual container and locales; do not force explanatory prose into a headline shape or add manual breaks merely to equalize lines. Keep code and pre-formatted text unchanged.
- Font smoothing: apply `-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale` once on the root layout (macOS only)
- Tabular numbers: use `font-variant-numeric: tabular-nums` for counters, timers, prices, number columns, or any dynamically updating numbers
- Letter-spacing scales with font size: display type needs negative tracking to look engineered rather than stretched. Two tiers: roughly -0.022em for display sizes (32px and above), -0.012em for mid-range (20–28px), normal at 16px and below. Apply to any display-weight typeface, not just geometric sans. Positive letter-spacing on large headlines is always wrong.

### Surfaces
- Concentric border radius: calculate `outerRadius = innerRadius + padding` so nested rounded corners feel intentional, not mechanical; if padding exceeds `24px`, treat layers as separate surfaces and choose each radius independently
- Optical alignment: nudge icons by eye, not just by math, so buttons feel centered; buttons with text and an icon use slightly less padding on the icon side (e.g., `pl-4 pr-3.5`); play triangles and asymmetric icons should shift `1px`-`2px` toward the heavier side, or fix the SVG directly
- Shadows over borders: use layered `box-shadow` for depth on cards, buttons, and elevated elements so the surface feels lifted, not fenced in; reserve actual `border` for dividers, table cells, and layout separation (applies primarily to light mode; on dark surfaces see the dark-mode surface hierarchy rule below)
- Image outlines: add a subtle inset outline so images hold their own depth without altering layout dimensions: `outline: 1px solid rgba(0,0,0,0.1); outline-offset: -1px` (light) or `outline: 1px solid rgba(255,255,255,0.1); outline-offset: -1px` (dark)
- Minimum hit area: keep every interactive target at least 40×40px so even small controls feel generous and precise; extend with a centered pseudo-element when the visible element is smaller, and never let hit areas of two interactive elements overlap
- Multi-card alignment: cards in one row share one height, and a shorter card gets another line of fact, not extra padding. Bottom-align all CTA buttons so height variations between cards don't create a ragged action row. In pricing or comparison cards, align feature list items to a shared Y origin across all columns. In side-by-side panels (testimonials, plans, feature breakdowns), title, description, price, and action button must share baselines across the row. Section top and bottom padding need not be symmetric: optical balance often requires bottom padding 20-25% larger than top. Constrain body paragraph width to approximately 65 characters (ch) to maintain comfortable reading line length.
- Light-mode app surface hierarchy: adjacent nested surfaces must be visually distinguishable. Minimum: background-color step of at least 4% lightness between sidebar and main area, and between main area and cards; or a shadow of at least `0 1px 3px rgba(0,0,0,0.10)` on elevated cards. A white card on a near-white background with `box-shadow: 0 1px 2px rgba(0,0,0,0.05)` is invisible -- that is not depth, it is noise.
- Dark-mode surface hierarchy: the page canvas is a near-black solid (e.g. `#08090a`). Elevation is communicated by adding semi-transparent white overlays on top of that canvas: cards at `rgba(255,255,255,0.02)`, elevated surfaces at `0.04`, prominent panels at `0.05`. Borders follow the same logic: `rgba(255,255,255,0.05)` for subtle, `0.08` for standard. Traditional drop shadows (dark on dark) are nearly invisible; luminance stepping through background opacity is the primary depth cue on dark surfaces.
- Border radius system: define a named radius scale during direction lock instead of picking values ad-hoc. A minimal scale is 3–4 tiers (e.g. `{4px, 8px, 12px, pill}`); a richer system might run 6–8 tiers. The point is committing to a named set before the first component so that all surfaces speak the same spatial language -- not covering every possible radius value.

### Adding to Existing UI

When extending an existing interface, first spend time understanding its visual vocabulary. Match all of the following before writing the first line of new code:
- Copywriting tone and reading level (technical? casual? punchy?)
- Color palette and semantic color roles (which tokens mean "danger", "success", "muted")
- Hover and click states: scale, color shift, underline, background fill
- Animation style: duration, easing, whether interactions bounce or are strictly ease-out
- Shadow and card treatment: which surfaces are elevated, which are flush
- Layout density and whitespace rhythm
- Border radius choices and whether buttons are pill, square, or a specific fixed value

If swapping in different content would make the new component look out of place, the vocabulary was not matched closely enough.

### Responsive & Screen Verification
- Verify the rendered surface, not a type check or CSS-balance read. Several regressions (early wraps, orphaned separator dots, table overflow) are invisible in source and only show in the render. Screenshot at phone (375px, plus 320px for buttons) and desktop (1280px), in every shipped locale, with long words and localized strings inside buttons, tabs, nav, and compact cards.
- Line widows: inspect short last lines in the rendered block, including nested inline code. Check container width and imposed breaks before changing copy; tighten repetition only when meaning and qualifications survive. A short last line alone does not justify deleting useful content, shrinking type, or adding a narrower width cap. Apply line budgets to the named component, not every paragraph.
- Mobile CTA resting state: natural width, left-aligned to the surrounding text edge, height unchanged. Centering reads as floating; full-width `flex: 1` reads heavy; dropping button height to relieve a "too full" feel treats a width problem as a height one.
- Spacing is a system, not a per-gap value. Run section spacing as one responsive ladder; when a page reads too airy or too tight, scale the whole set by a single factor across all breakpoints rather than tuning one gap. Asymmetry that survives tuning is structural.
- Long-form and documentation surfaces stay light: a borderless prev/next text pager (not bordered cards), a sidebar active state as a thin rail rather than a filled block, and build-time zero-runtime-JS code highlighting (bake static spans, plain code stays the source) over a shipped highlighter.

## Data Visualization Surfaces

For dashboards, analytics views, chart-heavy interfaces, or number-dense displays, load `references/design-data-viz.md`. It owns dashboard defaults, chart selection, number alignment, and product-benchmark extraction.

## Reflex Fonts to Reject

LLMs default to these because they dominate training data. Using them signals "no decision was made." Pick from foundries with a clear voice instead. The ban is on reflex use as a display face; informed product-UI use (e.g. Inter for a dense data table) is allowed when justified.

Reject: Inter, DM Sans, DM Serif Display, DM Serif Text, Outfit, Plus Jakarta Sans, Instrument Sans, Instrument Serif, Space Grotesk, Space Mono, IBM Plex Sans, IBM Plex Serif, IBM Plex Mono, Syne, Fraunces, Newsreader, Lora, Crimson Pro, Crimson Text, Playfair Display, Cormorant, Cormorant Garamond.

## Font Selection Procedure

1. Write three words that describe the brand (e.g. "precise, minimal, fast").
2. Name the three fonts you would reach for reflexively.
3. Reject all three.
4. Pick a typeface from a named foundry (Klim, Commercial Type, Colophon, Grilli Type, OH no Type, Village, etc.) or an open-source option with a clear personality that matches the brand words. Be able to explain why that specific typeface in one sentence.

## CJK & Multilingual Type

When the interface mixes Chinese, Japanese, or Korean with Latin, Latin-only type rules silently break the CJK text. Apply these before handoff:

- **Latin face first, system CJK face after** in the stack, so each script renders with correct glyphs: `font-family: -apple-system, "SF Pro Text", "PingFang SC", "Noto Sans SC", sans-serif;`. Latin runs use the Latin face; Han characters fall through to the CJK face.
- **Give CJK body text more line-height than Latin**: roughly 1.7–1.8 for reading. Dense Hanzi needs more vertical room than the 1.4–1.5 that suits Latin body copy.
- **Tag runs with `lang="zh"` / `lang="ja"` / `lang="en"`** so the browser picks the right font and line-breaking. Mixed-language paragraphs break badly without it.
- **Serif reading modes need an explicit CJK serif fallback.** Most Latin "reading serif" webfonts carry no CJK glyphs, so a serif toggle silently drops Chinese back to a sans and looks broken. Pair them: `"<reading serif>", "Songti SC", "Noto Serif SC", serif`.
- **Do not apply negative letter-spacing to CJK runs.** The display-type tracking rule above is Latin-only; tightening tracking on Hanzi cramps the glyphs and reads as a rendering bug. Scope tracking to `lang="en"` runs.

## Color System: OKLCH Rules

- Use OKLCH instead of HSL. OKLCH is perceptually uniform: equal numeric changes produce equal perceived changes across the spectrum.
- Reduce chroma as lightness approaches the extremes. At 85% lightness a chroma around 0.08 is enough; pushing to 0.15 looks garish. At 15% lightness, tighten chroma similarly.
- Tint neutrals toward the brand hue with a chroma of 0.005 to 0.01. Even this faint amount is perceptible and creates subconscious cohesion.
- 60-30-10 is about visual weight, not pixel count. 60% neutral/surface, 30% secondary text and borders, 10% accent.
- Never use gray text on a colored background. Use a shade of the background hue at reduced lightness instead.

## Theme Matrix

Choose light or dark deliberately based on audience and context. Neither is a default.

| Context | Direction | Reason |
|---|---|---|
| Trading or analytics dashboard, night-shift use | Dark | High data density; reduced glare during long sessions |
| Children's reading or learning app | Light | Welcoming, low fatigue for eyes still developing contrast sensitivity |
| Enterprise SRE or observability tool | Dark | Operator context; dark surfaces read at a glance in low-light NOC rooms |
| Weekend planning, recipes, journaling | Light | Ambient daytime use; light feels casual and approachable |
| Music player or media browser | Dark | Content-forward; dark surfaces recede and let media pop |
| Hospital or clinical patient portal | Light | Trust and legibility are paramount; clinical associations favor light |
| Vintage or artisanal brand site | Cream/warm light | Dark would clash with the analog material references |

If the answer is not obvious from the context, default to light. If the user's context implies both modes, ship light first and layer dark-mode tokens on top.

## Absolute Bans (CSS-Pattern Level)

These patterns appear in the majority of AI-generated interfaces. Each one has a specific rewrite.

| Pattern | Why | Rewrite |
|---|---|---|
| `border-left` or `border-right` wider than 1px as a section accent | The single most overused "design touch" in admin and dashboard UIs; it looks like a mistake at anything beyond a hairline divider | Change element structure: use a colored dot, a short horizontal rule, a background swatch, or a typographic weight shift instead |
| `background-clip: text` gradient text | Decorative rather than meaningful; one of the top AI design tells; illegible when printed or in high-contrast mode | Use a solid brand color, a tinted neutral, or typographic weight for emphasis |
| `backdrop-filter: blur` glassmorphism as the default card surface | Expensive on low-power devices; overused; the layered-depth illusion breaks with a solid border | Use elevated surfaces via background color steps and `box-shadow` instead |
| Purple-to-blue gradients or cyan-on-dark accent systems | The canonical "AI design" color palette; communicates nothing about the brand | Pick a palette from the brand words via the OKLCH rules above |
| Generic rounded-rect card with `box-shadow` as the default container | Template thinking; applies the same container to every content type regardless of hierarchy | Default to cardless sections; only add card treatment when the content type requires it |
| Modals as a lazy escape for overflow UI | Interrupts flow and breaks browser back navigation; used when an inline expansion, drawer, or separate page would be better | Inline expand, detail panel, or dedicated route; modals only when the action truly requires focus-lock |
| `transition: all` or animating width/height/padding/margin | Forces the browser into layout recalculation on every frame | List exact properties (`transition-property: transform, opacity`; Tailwind's `transition-transform` covers `transform, translate, scale, rotate`, use `transition-[scale,opacity,filter]` for mixed properties); use `grid-template-rows: 0fr to 1fr` for height reveals |

## Reference-site Brand Presets (awesome-design-md)

`VoltAgent/awesome-design-md` maintains DESIGN.md files extracted from real-world brand sites. Running `npx getdesign@latest add <brand>` drops the file into the project root, giving the agent concrete token values to decompose rather than reasoning from memory.

**Usage rule:** never auto-run the command. Offer it as an option during direction lock, run it only with explicit user approval, and treat the result as seed decomposition material, not a finished direction. After an approved run, read the generated `DESIGN.md` at project root and do the three-property decomposition from direction question 2 in `SKILL.md` against that file rather than from memory; the user still names the aesthetic precisely.

**Conflict resolution:** this skill's rules always win. If the preset recommends a font on the Reflex Fonts blocklist (e.g. Inter as a display face), discard it and apply the Font Selection Procedure. If it proposes a pattern in the Absolute Bans table (e.g. purple-to-blue gradient), discard it. State the override in the handoff summary.

## Reference Material Priority

When source code and a screenshot are both available for a reference UI: read the code. Source files contain exact token values; screenshots require guessing. Reconstruct from what is written, not what is visible.

When only a URL is provided: fetching it returns extracted text only, with no layout information. For visual references ("make it look like X"), ask for a screenshot rather than inferring visual design from stripped HTML.

## DESIGN.md Scaffold (Optional, Production UIs)

For a multi-page or production UI, emit a short `DESIGN.md`-style summary before writing the first component. This forces enumeration of decisions that would otherwise be left implicit and lets the user correct direction early. The nine sections:

1. **Visual Theme and Atmosphere** - mood, density, design philosophy in 2-3 sentences
2. **Color Palette and Roles** - semantic name + value + functional role for each color token
3. **Typography Rules** - font family, size scale, weight scale, line-height, letter-spacing; a table if more than 4 levels
4. **Component Stylings** - buttons (all states), cards (if used), inputs, navigation; describe each with states (default, hover, active, disabled)
5. **Layout Principles** - spacing scale, grid columns, whitespace philosophy
6. **Depth and Elevation** - shadow system or background-color-step system; describe each level
7. **Do's and Don'ts** - 5 to 10 guardrails specific to this project, not generic rules
8. **Responsive Behavior** - breakpoints, how navigation collapses, touch target minimums
9. **Agent Prompt Guide** - a quick color reference (name: value pairs) + 3 to 5 example component prompts ready to paste into a follow-up request. Prompts must be specific enough to execute without further lookup: every value, every radius, every letter-spacing, every weight inlined. Example standard (values are illustrative, use the project's own tokens): "Create a hero on `{bg-canvas}`, headline at 48px weight 600, line-height 1.00, letter-spacing -0.022em, color `{text-primary}`, CTA at `{accent}` with `{btn-radius}` radius"; that level of specificity, not "hero with primary color and CTA button"

For a single component or quick prototype, skip this. The three-line thesis in SKILL.md is sufficient.

## Aesthetic Review Checks

Run before the handoff summary of a new page or visual system; fix any that fail first.

- Is the brand or product unmistakable in the first screen?
- Is there one strong visual anchor (real imagery, not a decorative gradient)?
- Can the page be understood by scanning headlines only?
- Does each section have one job?
- Are cards actually necessary, or just default styling?
- Does motion improve hierarchy or atmosphere, or is it ornamental?
- Would the design still feel premium if all decorative shadows were removed?

## Pre-Handoff Checklist: Strategic Omissions

These are audit prompts, not automatic implementation scope. Run through them before handoff and report material omissions. Add one only when the current task or target project's public requirements include that surface; never create a route, footer link, consent flow, or policy page as incidental visual polish.

- [ ] **Custom 404 page**: if the task includes routing or production hardening, a branded page needs a clear path back (home link, search, or most-used nav items).
- [ ] **Back navigation**: every page reachable by user action must have a clear, functional path back. Dead-end pages (detail views, confirmation screens, modal-only flows) are UX failures.
- [ ] **Form client-side validation**: email fields validate format before submit; required fields show inline errors; error messages appear adjacent to the field, not only at form top.
- [ ] **Skip-to-content link**: a visually hidden `<a href="#main-content">Skip to main content</a>` as the first focusable element in the document. Required for keyboard accessibility.
- [ ] **Cookie consent**: if the product's actual tracking and jurisdiction require consent, flag the missing flow and scope it to that requirement.
- [ ] **Footer Privacy and Terms links**: if the product's legal and distribution requirements call for them, verify they are discoverable without inventing a new footer in an unrelated task.

These are product-readiness questions. A visual-polish request may surface them, but does not authorize building them.

## App Shell Rules

When building a sidebar + main workspace layout (Slack, Linear, Notion class):
- Decorative backgrounds default to off
- Surface hierarchy uses background-color steps and shadow only
- Activation feedback follows Animation: immediate state changes count; app-shell controls do not all need press scale
- Button radius is consistent within each component type (pick one: pill, square, or one fixed value, do not mix)
- Commit to a named radius scale before the first component (see Border radius system above)

## Options Guide

When asked for design options, give at least 3 variations spread across genuinely different dimensions:

- **Dimensions to vary**: visual density, typographic personality, color temperature, layout structure, motion character, amount of decoration, level of abstraction
- **Mix approaches**: one option that follows existing conventions closely, one that remixes the brand DNA in a new way, one that is deliberately unexpected
- **Progress from basic to bold**: the first option is safe and understandable; later options push further
- Three options that differ only by accent color are not three variations. Vary the layout, the typeface, the motion, the surface treatment.

---

*Rules in Reflex Fonts, Font Selection, OKLCH, Theme Matrix, Absolute Bans, the motion rules, and the AI Slop Test adapted from [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache 2.0). DESIGN.md Scaffold adapted from [getdesign.md](https://getdesign.md) (MIT); concept credited to Google Stitch. Content Authenticity, Multi-Card Alignment, and Strategic Omissions inspired by [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill).*
