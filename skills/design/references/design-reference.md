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

Before writing the first component, name the single CSS strategy for the project: Tailwind only, CSS Modules only, or CSS-in-JS only. Do not drift from it.

## Common Traps

Before submitting, check whether any of the following slipped in without intention:

- A purple or blue gradient over white as the hero background
- A three-part hero: large headline, one-line subtext, two CTA buttons side by side
- A grid of cards with identical rounded corners, identical drop shadows, identical padding
- A top navigation bar with logo left, links center, primary action far right
- Sections that alternate between white and `#f9f9f9`
- A centered icon or illustration sitting above a heading above a paragraph
- A four-column footer with equal-weight columns

Any of these can appear if they serve the design intentionally. They cannot appear by default.

Final test: if you swapped in completely different content and the layout still made sense without changes, you built a template, not a design. Redo it.

## Production Quality Baseline

Check before handoff. These are not aesthetic choices, they are non-negotiable.

### Accessibility
- Icon-only buttons need `aria-label`
- Actions use `<button>`, navigation uses `<a>` (not `<div onClick>`)
- Images need `alt` (or `alt=""` if decorative)
- Visible focus states: `focus-visible:ring-*` or equivalent; never `outline: none` without replacement

### Animation
- Honor `prefers-reduced-motion`: disable or reduce animations when set
- Animate `transform`/`opacity` only (compositor-friendly, no layout thrash)
- Never `transition: all`; list properties explicitly
- Interruptible animations: prefer CSS transitions for interactive state changes (hover, toggle, open/close) because they retarget mid-animation; reserve keyframe animations for staged sequences that run once (e.g., staggered page enters)
- Staggered enter: split content into semantic chunks with ~100ms delay; titles into words at ~80ms; typical enter uses `opacity: 0 → 1`, `translateY(12px) → 0`, and `blur(4px) → 0`
- Subtle exit: use a small fixed `translateY(-12px)` instead of full height; keep duration ~150ms `ease-in`, shorter and softer than enter
- Contextual icon swaps: animate with `scale: 0.25 → 1`, `opacity: 0 → 1`, and `blur: 4px → 0px`. With Motion: `transition: { type: "spring", duration: 0.3, bounce: 0 }`. Without Motion: keep both icons in DOM (one absolute) and cross-fade with CSS using `cubic-bezier(0.2, 0, 0, 1)`
- Scale on press: buttons use `scale(0.96)` on active/press via CSS transitions so the press can be interrupted; add a `static` prop to disable when motion would be distracting
- Page-load guard: use `initial={false}` on `AnimatePresence` for toggles, tabs, and icon swaps to prevent enter animations on first render; do not use it for intentional page-load entrance sequences

### Performance
- Transition specificity: never `transition: all`; list exact properties (e.g., `transition-property: scale, opacity`). Tailwind's `transition-transform` covers `transform, translate, scale, rotate`; use `transition-[scale,opacity,filter]` for mixed properties
- GPU compositing: only use `will-change` for `transform`, `opacity`, or `filter`. Never `will-change: all`. Add only when you notice first-frame stutter; do not apply preemptively to every element
- Images: explicit `width` and `height` (prevents layout shift)
- Below-fold images: `loading="lazy"`
- Critical fonts: `font-display: swap`

### Touch and Mobile
- `touch-action: manipulation` (prevents double-tap zoom delay)
- Full-bleed layouts: `env(safe-area-inset-*)` for notch devices
- Modals and drawers: `overscroll-behavior: contain`

### Typography Details
- Text wrapping: `text-wrap: balance` on headings and short text blocks (≤6 lines in Chromium, ≤10 in Firefox); `text-wrap: pretty` on body paragraphs and longer text; leave default on code blocks and pre-formatted text
- Font smoothing: apply `-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale` once on the root layout (macOS only)
- Tabular numbers: use `font-variant-numeric: tabular-nums` for counters, timers, prices, number columns, or any dynamically updating numbers

### Surfaces
- Concentric border radius: `outerRadius = innerRadius + padding`; if padding is larger than `24px`, treat layers as separate surfaces and choose each radius independently
- Optical alignment: buttons with text and icon use slightly less padding on the icon side (e.g., `pl-4 pr-3.5`); play triangles and asymmetric icons shift `1px`–`2px` to the heavier side or fix the SVG directly
- Shadows over borders: use layered `box-shadow` for depth on cards, buttons, and elevated elements; use actual `border` only for dividers, table cells, and layout separation
- Image outlines: add a subtle inset outline for consistent depth using `outline: 1px solid rgba(0,0,0,0.1); outline-offset: -1px` (light) or `outline: 1px solid rgba(255,255,255,0.1); outline-offset: -1px` (dark)
- Minimum hit area: interactive elements need at least 40×40px; extend with a centered pseudo-element when the visible element is smaller; never let hit areas of two interactive elements overlap