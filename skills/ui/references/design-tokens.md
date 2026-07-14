# Design Tokens: Color and Typography

Motion rules live in [design-reference.md](./design-reference.md) under Animation and Motion Specifics. This file owns color and typography only.

## Color System: OKLCH Rules

- Use OKLCH instead of HSL. OKLCH is perceptually uniform: equal numeric changes produce equal perceived changes across the spectrum.
- Reduce chroma as lightness approaches the extremes. At 85% lightness, chroma around 0.08 is enough; pushing to 0.15 looks garish.
- Tint neutrals toward the brand hue with a chroma of 0.005 to 0.01.
- 60-30-10 is about visual weight, not pixel count: 60% neutral/surface, 30% secondary text and borders, 10% accent.
- Never use gray text on a colored background. Use a shade of the background hue at reduced lightness instead.

## Theme Matrix

| Context | Direction | Reason |
|---|---|---|
| Trading or analytics dashboard, night-shift use | Dark | High data density; reduced glare during long sessions |
| Children's reading or learning app | Light | Welcoming, low fatigue |
| Enterprise SRE or observability tool | Dark | Operator context; dark surfaces read at a glance in low-light rooms |
| Weekend planning, recipes, journaling | Light | Ambient daytime use; light feels casual |
| Music player or media browser | Dark | Content-forward; dark surfaces recede and let media pop |
| Hospital or clinical patient portal | Light | Trust and legibility are paramount |
| Vintage or artisanal brand site | Cream/warm light | Dark would clash with the analog material references |

If the answer is not obvious from context, default to light.

## Reflex Fonts to Reject

These fonts dominate training data. Using them signals no decision was made. The ban is on reflex use as a display face; informed product-UI use (e.g. Inter for a dense data table) is allowed when justified.

Reject: Inter, DM Sans, DM Serif Display, DM Serif Text, Outfit, Plus Jakarta Sans, Instrument Sans, Instrument Serif, Space Grotesk, Space Mono, IBM Plex Sans, IBM Plex Serif, IBM Plex Mono, Syne, Fraunces, Newsreader, Lora, Crimson Pro, Crimson Text, Playfair Display, Cormorant, Cormorant Garamond.

## Font Selection Procedure

1. Write three words that describe the brand (e.g. "precise, minimal, fast").
2. Name the three fonts you would reach for reflexively.
3. Reject all three.
4. Pick a typeface from a named foundry (Klim, Commercial Type, Colophon, Grilli Type, OH no Type, Village) or an open-source option with a clear personality. Be able to explain why in one sentence.

## Typography Details

- `text-wrap: balance` on headings and short text blocks; `text-wrap: pretty` on body paragraphs
- `-webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale` once on root layout (macOS only)
- `font-variant-numeric: tabular-nums` for counters, timers, prices, number columns
- Letter-spacing: roughly -0.022em for display sizes (32px+), -0.012em for mid-range (20-28px), normal at 16px and below
- **Korean UI**: Always use [Pretendard](https://github.com/orioncactus/pretendard) as the default sans-serif font for Korean interfaces to ensure optimal legibility and native-like rendering.
