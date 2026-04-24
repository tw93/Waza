# Waza Website Design

**Date:** 2026-04-24  
**Status:** Approved

## Overview

A marketing landing page combined with inline skill documentation, built as a single Astro project. The primary goal is to help visitors understand what each of the eight skills does before they decide to install.

## Goals

- **Primary audience:** Individual developers and engineering teams
- **Core action:** Understand the eight skills first, then install
- **Secondary action:** Team members sharing Waza with colleagues

## Visual Style

**Theme:** 纸本白 (Warm Paper White)

| Token | Value |
|-------|-------|
| Background | `#fafaf8` |
| Surface | `#f5f0e8` |
| Border | `#ede9e0` / `#e8e4dc` |
| Accent | `#c8a96e` (gold-brown) |
| Text primary | `#1a1a1a` |
| Text secondary | `#888` |
| Text muted | `#aaa` / `#bbb` |
| Code block bg | `#1a1a1a` |
| Code block text | `#c8a96e` |

**Typography:**
- Headings: Georgia (serif)
- Body: System sans-serif
- Code / skill commands: Monospace

**Tone:** Engineer-facing, warm, precise. No marketing superlatives.

## Language

- Default: English
- `EN | 中` toggle in the navigation bar
- Documentation pages support Chinese content

## Tech Stack

- **Framework:** Astro (static site generation)
- **Content:** MDX for skill documentation pages
- **Deployment:** Static hosting (GitHub Pages or Vercel)

## Site Structure

```
/                        ← Landing page
/skills/think            ← Skill detail page
/skills/design
/skills/check
/skills/hunt
/skills/write
/skills/learn
/skills/read
/skills/health
```

## Landing Page — Section by Section

### 1. Navigation

```
WAZA · 技          Skills    GitHub ↗         EN | 中
```

- Logo left, links center-right, language toggle far right
- Sticky on scroll

### 2. Hero

Centered, symmetric layout.

```
                わざ — TECHNIQUE AS INSTINCT

    Engineering habits you already know,
       turned into skills Claude can run.

         8 skills · Claude Code · Codex · One install

       ┌─────────────────────────────────────┐
       │  npx skills add tw93/Waza    copy   │
       └─────────────────────────────────────┘

              — or — Browse skills ↓
```

- Title in Georgia serif, 28–32px
- Install command in dark code block with one-click copy
- Subtle "Browse skills" link scrolls to the skills section

### 3. Skills List

Three-column aligned list rows. Each row: `command | when | description`.

```
/think    Before building    Challenges the problem, pressure-tests the design,
                             validates architecture before any code is written.

/design   Frontend UI        Produces distinctive UI with a committed aesthetic
                             direction, not generic defaults.

/check    Before merging     Reviews the diff, auto-fixes safe issues, flags
                             destructive commands, verifies with evidence.
...
```

- Section heading: `SKILLS` (small caps, gold) + `Eight habits. One install.` (Georgia)
- Each row is clickable, links to `/skills/[name]`
- Hover state: subtle background highlight

### 4. Footer

```
WAZA · 技                          ⭐ Star on GitHub

npx skills add tw93/Waza           MIT License · tw93
```

## Skill Detail Page

### Layout

Left sidebar navigation + right content area.

```
┌─────────────────┬──────────────────────────────────────┐
│ WAZA · 技   EN│中│                                      │
├────────┬────────┴──────────────────────────────────────┤
│ SKILLS │  /think                                        │
│        │  Before building anything new                  │
│ /think │                                                │
│ /design│  WHAT IT DOES                                  │
│ /check │  Challenges the problem, pressure-tests the    │
│ /hunt  │  design, validates architecture before any     │
│ /write │  code is written.                              │
│ /learn │                                                │
│ /read  │  TRIGGER                                       │
│ /health│  /think I want to add a caching layer          │
│        │                                                │
│        │  CHAIN WITH                                    │
│        │  /think → implement → /check                   │
└────────┴────────────────────────────────────────────────┘
```

### Skill Page Content Sections

Each skill detail page contains:

1. **Command** — `/think` in monospace, large
2. **When** — One-line trigger description in italic
3. **What it does** — 2–3 sentences from the existing README description
4. **Trigger example** — Inline code block showing a real usage
5. **Chain with** — Which skills naturally precede or follow this one

### Sidebar

- Lists all eight skills by command name
- Active skill highlighted in `#1a1a1a` bold, others in muted grey
- Fixed position, scrolls independently on long pages

## Content Source

All skill descriptions are sourced directly from `skills/*/SKILL.md` and the README table. No new copy is invented — the website surfaces existing content in a readable format.

## Out of Scope

- Search functionality
- User accounts or authentication
- Interactive skill demos
- Blog or changelog section
- Analytics (can be added later via Astro integration)

## File Structure (Astro Project)

```
waza-site/
├── src/
│   ├── pages/
│   │   ├── index.astro          ← Landing page
│   │   └── skills/
│   │       └── [skill].astro    ← Dynamic skill detail page
│   ├── components/
│   │   ├── Nav.astro
│   │   ├── Hero.astro
│   │   ├── SkillsList.astro
│   │   ├── Footer.astro
│   │   └── SkillSidebar.astro
│   ├── layouts/
│   │   ├── BaseLayout.astro
│   │   └── SkillLayout.astro
│   ├── content/
│   │   └── skills/              ← MDX files for each skill
│   └── styles/
│       └── global.css           ← CSS variables (color tokens above)
├── public/
└── astro.config.mjs
```

## Success Criteria

- A visitor with no prior knowledge of Waza can read the homepage and understand what all eight skills do in under 2 minutes
- The install command is visible above the fold on desktop
- All eight skill detail pages are reachable from the sidebar without going back to the homepage
- The site renders correctly on mobile (sidebar collapses to a top dropdown or hamburger)
- Bilingual toggle switches all UI text; skill content pages load the correct language variant
