# Waza Website Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a bilingual (EN/ZH) Astro static site for Waza — a marketing landing page plus eight skill documentation pages — using the "纸本白" visual theme.

**Architecture:** Single Astro project at `waza-site/` inside the repo root. All skill content lives in `src/data/skills.ts` (both languages in one file). Bilingual toggle is client-side only: a `data-lang` attribute on `<html>` toggled by JS, with `[data-lang="zh"] .en { display:none }` CSS rules hiding the inactive language.

**Tech Stack:** Astro 4, TypeScript, vanilla CSS (no framework), static output, deployable to GitHub Pages or Vercel.

---

## File Map

```
waza-site/
├── src/
│   ├── data/
│   │   └── skills.ts              ← all skill content, EN + ZH
│   ├── components/
│   │   ├── Nav.astro              ← sticky nav with language toggle
│   │   ├── Hero.astro             ← centered hero + install command
│   │   ├── SkillsList.astro       ← three-column list rows on landing page
│   │   ├── SkillSidebar.astro     ← left sidebar on detail pages
│   │   └── Footer.astro           ← minimal footer
│   ├── layouts/
│   │   ├── BaseLayout.astro       ← <html>, <head>, Nav, Footer, lang script
│   │   └── SkillLayout.astro      ← sidebar + content area wrapper
│   ├── pages/
│   │   ├── index.astro            ← landing page
│   │   └── skills/
│   │       └── [skill].astro      ← dynamic detail page
│   └── styles/
│       └── global.css             ← CSS variables + reset + bilingual rules
├── public/
│   └── favicon.svg
└── astro.config.mjs
```

---

## Task 1: Initialize the Astro project

**Files:**
- Create: `waza-site/` (project root)
- Create: `waza-site/astro.config.mjs`
- Create: `waza-site/package.json` (generated)
- Create: `waza-site/tsconfig.json` (generated)

- [ ] **Step 1: Scaffold a minimal Astro project**

```bash
cd /path/to/Waza
npm create astro@latest waza-site -- --template minimal --typescript strict --no-git --no-install
cd waza-site
npm install
```

Expected output: project created, dependencies installed.

- [ ] **Step 2: Verify dev server starts**

```bash
npm run dev
```

Expected: `http://localhost:4321` opens, shows default page. Stop with Ctrl+C.

- [ ] **Step 3: Verify build succeeds**

```bash
npm run build
```

Expected: `dist/` created, no errors.

- [ ] **Step 4: Create directory structure**

```bash
mkdir -p src/data src/components src/layouts src/styles public
```

- [ ] **Step 5: Commit**

```bash
git add waza-site/
git commit -m "feat(site): initialize Astro project"
```

---

## Task 2: Design tokens in global.css

**Files:**
- Create: `waza-site/src/styles/global.css`

- [ ] **Step 1: Write global.css**

Create `waza-site/src/styles/global.css`:

```css
/* Design tokens */
:root {
  --bg: #fafaf8;
  --surface: #f5f0e8;
  --border: #ede9e0;
  --border-light: #e8e4dc;
  --accent: #c8a96e;
  --accent-muted: #a08060;
  --text-primary: #1a1a1a;
  --text-secondary: #888;
  --text-muted: #aaa;
  --text-faint: #bbb;
  --code-bg: #1a1a1a;
  --code-text: #c8a96e;
  --font-serif: Georgia, 'Times New Roman', serif;
  --font-mono: 'Fira Code', 'Cascadia Code', Consolas, monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Reset */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html { font-size: 16px; scroll-behavior: smooth; }

body {
  background: var(--bg);
  color: var(--text-primary);
  font-family: var(--font-sans);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

a { color: inherit; text-decoration: none; }
img { max-width: 100%; display: block; }

/* Bilingual: default shows EN, hides ZH */
.zh { display: none; }

/* When html[data-lang="zh"]: hide EN, show ZH */
html[data-lang="zh"] .zh { display: revert; }
html[data-lang="zh"] .en { display: none; }

/* Utilities */
.label {
  font-size: 10px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: var(--accent);
}

.mono {
  font-family: var(--font-mono);
  font-size: 0.875rem;
}

code {
  font-family: var(--font-mono);
  background: var(--code-bg);
  color: var(--code-text);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.8125rem;
}
```

- [ ] **Step 2: Commit**

```bash
git add waza-site/src/styles/global.css
git commit -m "feat(site): add design tokens and global CSS"
```

---

## Task 3: BaseLayout component

**Files:**
- Create: `waza-site/src/layouts/BaseLayout.astro`

- [ ] **Step 1: Write BaseLayout.astro**

Create `waza-site/src/layouts/BaseLayout.astro`:

```astro
---
export interface Props {
  title?: string;
  description?: string;
}
const {
  title = 'Waza — Engineering habits for Claude Code',
  description = 'Eight skills for the habits that actually matter. /think, /design, /check, /hunt, /write, /learn, /read, /health.',
} = Astro.props;
---
<!doctype html>
<html lang="en" data-lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="description" content={description} />
    <title>{title}</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="stylesheet" href="/src/styles/global.css" />
  </head>
  <body>
    <slot />
    <script>
      // Restore language preference on every page load
      const saved = localStorage.getItem('waza-lang');
      if (saved === 'zh') {
        document.documentElement.setAttribute('data-lang', 'zh');
      }
    </script>
  </body>
</html>
```

- [ ] **Step 2: Verify build still passes**

```bash
cd waza-site && npm run build
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add waza-site/src/layouts/BaseLayout.astro
git commit -m "feat(site): add BaseLayout with lang persistence"
```

---

## Task 4: Skill data file

**Files:**
- Create: `waza-site/src/data/skills.ts`

This is the single source of truth for all skill content. No MDX files needed — the data is short enough to live in one TypeScript file.

- [ ] **Step 1: Write skills.ts**

Create `waza-site/src/data/skills.ts`:

```typescript
export interface Skill {
  slug: string;
  command: string;
  when: { en: string; zh: string };
  what: { en: string; zh: string };
  trigger: string;
  chainWith: { en: string; zh: string };
}

export const skills: Skill[] = [
  {
    slug: 'think',
    command: '/think',
    when: {
      en: 'Before building anything new',
      zh: '动手构建任何新东西之前',
    },
    what: {
      en: 'Challenges the problem, pressure-tests the design, validates architecture before any code is written.',
      zh: '挑战问题本身，对设计进行压力测试，在写任何代码之前先验证架构是否成立。',
    },
    trigger: '/think I want to add a caching layer to the API',
    chainWith: {
      en: '/think → implement → /check',
      zh: '/think → 实现 → /check',
    },
  },
  {
    slug: 'design',
    command: '/design',
    when: {
      en: 'Building frontend interfaces',
      zh: '构建前端界面时',
    },
    what: {
      en: 'Produces distinctive UI with a committed aesthetic direction, not generic defaults.',
      zh: '生成有主见的 UI 设计，确定明确的审美方向，而不是泛泛的通用默认风格。',
    },
    trigger: '/design a dashboard for showing API usage metrics',
    chainWith: {
      en: '/think → implement with /design → /check',
      zh: '/think → 使用 /design 实现 → /check',
    },
  },
  {
    slug: 'check',
    command: '/check',
    when: {
      en: 'After a task, before merging',
      zh: '任务完成后、合并代码之前',
    },
    what: {
      en: 'Reviews the diff, auto-fixes safe issues, flags destructive commands, verifies with evidence.',
      zh: '审查 diff，自动修复安全问题，标记危险命令，并附上证据进行验证。',
    },
    trigger: '/check',
    chainWith: {
      en: 'Any skill → fix → /check',
      zh: '任意技能 → 修复 → /check',
    },
  },
  {
    slug: 'hunt',
    command: '/hunt',
    when: {
      en: 'Any bug or unexpected behavior',
      zh: '遇到任何 bug 或意外行为时',
    },
    what: {
      en: 'Systematic debugging. Root cause confirmed before any fix is applied.',
      zh: '系统性调试。在应用任何修复之前先确认根本原因。',
    },
    trigger: '/hunt the login flow returns 401 intermittently',
    chainWith: {
      en: '/hunt → fix → /check',
      zh: '/hunt → 修复 → /check',
    },
  },
  {
    slug: 'write',
    command: '/write',
    when: {
      en: 'Writing or editing prose',
      zh: '写作或编辑文章时',
    },
    what: {
      en: 'Rewrites prose to sound natural in Chinese and English. Cuts stiff, formulaic phrasing.',
      zh: '将文章重写为自然流畅的中文或英文，去除生硬、程式化的表达。',
    },
    trigger: '/write [paste your draft]',
    chainWith: {
      en: '/read → /learn → /write',
      zh: '/read → /learn → /write',
    },
  },
  {
    slug: 'learn',
    command: '/learn',
    when: {
      en: 'Diving into an unfamiliar domain',
      zh: '深入陌生领域时',
    },
    what: {
      en: 'Six-phase research workflow: collect, digest, outline, fill in, refine, then self-review and publish.',
      zh: '六阶段研究流程：收集、消化、大纲、填充、精炼，最后自我审查并发布。',
    },
    trigger: '/learn Rust ownership and borrowing',
    chainWith: {
      en: '/read (fetch sources) → /learn → /write (polish)',
      zh: '/read（抓取资料）→ /learn → /write（润色）',
    },
  },
  {
    slug: 'read',
    command: '/read',
    when: {
      en: 'Any URL or PDF',
      zh: '需要读取任意 URL 或 PDF 时',
    },
    what: {
      en: 'Fetches content as clean Markdown with platform-specific routing. Special handling for GitHub, PDFs, WeChat, and Feishu.',
      zh: '将内容抓取为干净的 Markdown，针对不同平台智能路由。特别支持 GitHub、PDF、微信和飞书。',
    },
    trigger: '/read https://example.com/some-paper.pdf',
    chainWith: {
      en: '/read → /learn → /write',
      zh: '/read → /learn → /write',
    },
  },
  {
    slug: 'health',
    command: '/health',
    when: {
      en: 'Auditing Claude Code setup',
      zh: '审计 Claude Code 配置时',
    },
    what: {
      en: 'Checks CLAUDE.md, rules, skills, hooks, MCP, and behavior. Flags issues by severity.',
      zh: '检查 CLAUDE.md、rules、skills、hooks、MCP 及行为配置。按严重程度标记问题。',
    },
    trigger: '/health',
    chainWith: {
      en: 'Run periodically after config changes',
      zh: '每次修改配置后定期运行',
    },
  },
];

export function getSkill(slug: string): Skill | undefined {
  return skills.find((s) => s.slug === slug);
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd waza-site && npm run build
```

Expected: no type errors.

- [ ] **Step 3: Commit**

```bash
git add waza-site/src/data/skills.ts
git commit -m "feat(site): add bilingual skill data"
```

---

## Task 5: Nav component

**Files:**
- Create: `waza-site/src/components/Nav.astro`

- [ ] **Step 1: Write Nav.astro**

Create `waza-site/src/components/Nav.astro`:

```astro
---
export interface Props {
  currentPath?: string;
}
const { currentPath = '/' } = Astro.props;
---
<nav class="nav">
  <a href="/" class="nav-logo">
    <span class="en">WAZA · 技</span>
    <span class="zh">WAZA · 技</span>
  </a>
  <div class="nav-links">
    <a href="/#skills" class="nav-link">
      <span class="en">Skills</span>
      <span class="zh">技能</span>
    </a>
    <a
      href="https://github.com/tw93/Waza"
      target="_blank"
      rel="noopener"
      class="nav-link"
    >GitHub ↗</a>
    <button class="lang-toggle" id="lang-toggle" aria-label="Toggle language">
      <span class="en-label">EN</span>
      <span class="sep"> | </span>
      <span class="zh-label">中</span>
    </button>
  </div>
</nav>

<script>
  const btn = document.getElementById('lang-toggle')!;
  function updateToggle() {
    const lang = document.documentElement.getAttribute('data-lang') ?? 'en';
    const enLabel = btn.querySelector('.en-label') as HTMLElement;
    const zhLabel = btn.querySelector('.zh-label') as HTMLElement;
    enLabel.style.fontWeight = lang === 'en' ? '700' : '400';
    zhLabel.style.fontWeight = lang === 'zh' ? '700' : '400';
    enLabel.style.color = lang === 'en' ? 'var(--text-primary)' : 'var(--text-faint)';
    zhLabel.style.color = lang === 'zh' ? 'var(--text-primary)' : 'var(--text-faint)';
  }
  btn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-lang') ?? 'en';
    const next = current === 'en' ? 'zh' : 'en';
    document.documentElement.setAttribute('data-lang', next);
    localStorage.setItem('waza-lang', next);
    updateToggle();
  });
  updateToggle();
</script>

<style>
  .nav {
    position: sticky;
    top: 0;
    z-index: 100;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 40px;
    background: var(--bg);
    border-bottom: 1px solid var(--border);
  }
  .nav-logo {
    font-size: 12px;
    letter-spacing: 2px;
    font-weight: 600;
    color: var(--accent);
  }
  .nav-links {
    display: flex;
    gap: 24px;
    align-items: center;
  }
  .nav-link {
    font-size: 13px;
    color: var(--text-secondary);
    transition: color 0.15s;
  }
  .nav-link:hover { color: var(--text-primary); }
  .lang-toggle {
    background: none;
    border: 1px solid var(--border-light);
    border-radius: 12px;
    padding: 3px 12px;
    font-size: 11px;
    cursor: pointer;
    display: flex;
    gap: 2px;
    color: var(--text-secondary);
    font-family: var(--font-sans);
  }
  .lang-toggle:hover { border-color: var(--accent); }
  .sep { color: var(--border-light); }

  @media (max-width: 640px) {
    .nav { padding: 12px 20px; }
    .nav-link:not(:last-child) { display: none; }
  }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add waza-site/src/components/Nav.astro
git commit -m "feat(site): add Nav with language toggle"
```

---

## Task 6: Hero component

**Files:**
- Create: `waza-site/src/components/Hero.astro`

- [ ] **Step 1: Write Hero.astro**

Create `waza-site/src/components/Hero.astro`:

```astro
<section class="hero">
  <p class="label eyebrow">
    <span class="en">わざ — TECHNIQUE AS INSTINCT</span>
    <span class="zh">わざ — 技法即本能</span>
  </p>
  <h1 class="hero-title">
    <span class="en">Engineering habits you already know,<br />turned into skills Claude can run.</span>
    <span class="zh">你早已熟悉的工程习惯，<br />变成了 Claude 可以执行的技能。</span>
  </h1>
  <p class="hero-sub">
    <span class="en">8 skills · Claude Code · Codex · One install</span>
    <span class="zh">8 个技能 · Claude Code · Codex · 一键安装</span>
  </p>
  <div class="install-block">
    <code id="install-cmd">npx skills add tw93/Waza</code>
    <button class="copy-btn" id="copy-btn" aria-label="Copy install command">
      <span class="en">copy</span>
      <span class="zh">复制</span>
    </button>
  </div>
  <p class="browse-hint">
    <span class="en">— or — <a href="#skills">Browse skills ↓</a></span>
    <span class="zh">— 或者 — <a href="#skills">浏览技能 ↓</a></span>
  </p>
</section>

<script>
  const btn = document.getElementById('copy-btn')!;
  btn.addEventListener('click', async () => {
    await navigator.clipboard.writeText('npx skills add tw93/Waza');
    const spans = btn.querySelectorAll('span');
    spans.forEach(s => { s.textContent = s.classList.contains('zh') ? '已复制！' : 'copied!'; });
    setTimeout(() => {
      spans.forEach(s => { s.textContent = s.classList.contains('zh') ? '复制' : 'copy'; });
    }, 2000);
  });
</script>

<style>
  .hero {
    padding: 72px 40px 56px;
    text-align: center;
    max-width: 720px;
    margin: 0 auto;
  }
  .eyebrow {
    margin-bottom: 20px;
    font-size: 11px;
    letter-spacing: 3px;
  }
  .hero-title {
    font-family: var(--font-serif);
    font-size: clamp(22px, 4vw, 32px);
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.35;
    margin-bottom: 16px;
  }
  .hero-sub {
    font-size: 13px;
    color: var(--text-secondary);
    font-style: italic;
    margin-bottom: 36px;
  }
  .install-block {
    display: inline-flex;
    align-items: center;
    background: var(--code-bg);
    border-radius: 6px;
    padding: 10px 18px;
    gap: 16px;
    margin-bottom: 16px;
  }
  #install-cmd {
    background: none;
    color: var(--code-text);
    padding: 0;
    font-size: 13px;
  }
  .copy-btn {
    background: none;
    border: none;
    border-left: 1px solid #2a2a2a;
    padding-left: 16px;
    font-size: 11px;
    color: #555;
    cursor: pointer;
    font-family: var(--font-sans);
  }
  .copy-btn:hover { color: var(--accent); }
  .browse-hint {
    font-size: 12px;
    color: var(--text-faint);
  }
  .browse-hint a {
    color: var(--accent);
  }
  .browse-hint a:hover { text-decoration: underline; }

  @media (max-width: 640px) {
    .hero { padding: 48px 20px 40px; }
    .install-block { flex-direction: column; gap: 8px; }
    .copy-btn { border-left: none; border-top: 1px solid #2a2a2a; padding-left: 0; padding-top: 8px; }
  }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add waza-site/src/components/Hero.astro
git commit -m "feat(site): add Hero with install command + copy"
```

---

## Task 7: SkillsList component

**Files:**
- Create: `waza-site/src/components/SkillsList.astro`

- [ ] **Step 1: Write SkillsList.astro**

Create `waza-site/src/components/SkillsList.astro`:

```astro
---
import { skills } from '../data/skills';
---
<section class="skills-section" id="skills">
  <header class="skills-header">
    <p class="label">SKILLS</p>
    <h2 class="skills-heading">
      <span class="en">Eight habits. One install.</span>
      <span class="zh">八个习惯。一键安装。</span>
    </h2>
  </header>
  <ul class="skills-list">
    {skills.map((skill) => (
      <li class="skill-row">
        <a href={`/skills/${skill.slug}`} class="skill-link">
          <span class="skill-command mono">{skill.command}</span>
          <span class="skill-when">
            <span class="en">{skill.when.en}</span>
            <span class="zh">{skill.when.zh}</span>
          </span>
          <span class="skill-what">
            <span class="en">{skill.what.en}</span>
            <span class="zh">{skill.what.zh}</span>
          </span>
        </a>
      </li>
    ))}
  </ul>
</section>

<style>
  .skills-section {
    max-width: 880px;
    margin: 0 auto;
    padding: 64px 40px;
  }
  .skills-header {
    text-align: center;
    margin-bottom: 40px;
  }
  .skills-heading {
    font-family: var(--font-serif);
    font-size: 22px;
    font-weight: 700;
    color: var(--text-primary);
    margin-top: 8px;
  }
  .skills-list {
    list-style: none;
    border-top: 1px solid var(--border);
  }
  .skill-row {
    border-bottom: 1px solid var(--border);
  }
  .skill-link {
    display: grid;
    grid-template-columns: 88px 160px 1fr;
    gap: 0 24px;
    align-items: baseline;
    padding: 16px 12px;
    transition: background 0.15s;
  }
  .skill-link:hover {
    background: var(--surface);
    border-radius: 4px;
  }
  .skill-command {
    color: var(--accent);
    font-weight: 600;
    font-size: 13px;
  }
  .skill-when {
    font-size: 12px;
    color: var(--text-secondary);
    font-style: italic;
  }
  .skill-what {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.6;
  }

  @media (max-width: 640px) {
    .skills-section { padding: 40px 20px; }
    .skill-link {
      grid-template-columns: 1fr;
      gap: 4px;
      padding: 14px 8px;
    }
    .skill-when { font-style: normal; }
  }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add waza-site/src/components/SkillsList.astro
git commit -m "feat(site): add SkillsList three-column layout"
```

---

## Task 8: Footer component

**Files:**
- Create: `waza-site/src/components/Footer.astro`

- [ ] **Step 1: Write Footer.astro**

Create `waza-site/src/components/Footer.astro`:

```astro
<footer class="footer">
  <div class="footer-inner">
    <span class="footer-logo">WAZA · 技</span>
    <div class="footer-right">
      <a
        href="https://github.com/tw93/Waza"
        target="_blank"
        rel="noopener"
        class="footer-link"
      >
        <span class="en">⭐ Star on GitHub</span>
        <span class="zh">⭐ GitHub 点 Star</span>
      </a>
      <span class="footer-sep">·</span>
      <span class="footer-license">
        <span class="en">MIT License · tw93</span>
        <span class="zh">MIT 协议 · tw93</span>
      </span>
    </div>
  </div>
  <div class="footer-install">
    <code>npx skills add tw93/Waza</code>
  </div>
</footer>

<style>
  .footer {
    border-top: 1px solid var(--border);
    padding: 32px 40px;
    background: var(--surface);
  }
  .footer-inner {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
    gap: 12px;
  }
  .footer-logo {
    font-size: 12px;
    letter-spacing: 2px;
    color: var(--accent);
    font-weight: 600;
  }
  .footer-right {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: var(--text-secondary);
  }
  .footer-link { color: var(--text-secondary); }
  .footer-link:hover { color: var(--accent); }
  .footer-sep { color: var(--border); }
  .footer-install code {
    font-size: 12px;
  }

  @media (max-width: 640px) {
    .footer { padding: 24px 20px; }
  }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add waza-site/src/components/Footer.astro
git commit -m "feat(site): add Footer component"
```

---

## Task 9: Landing page (index.astro)

**Files:**
- Modify: `waza-site/src/pages/index.astro`

- [ ] **Step 1: Write index.astro**

Replace the contents of `waza-site/src/pages/index.astro`:

```astro
---
import BaseLayout from '../layouts/BaseLayout.astro';
import Nav from '../components/Nav.astro';
import Hero from '../components/Hero.astro';
import SkillsList from '../components/SkillsList.astro';
import Footer from '../components/Footer.astro';
---
<BaseLayout>
  <Nav currentPath="/" />
  <main>
    <Hero />
    <SkillsList />
  </main>
  <Footer />
</BaseLayout>
```

- [ ] **Step 2: Run dev server and verify landing page**

```bash
cd waza-site && npm run dev
```

Open `http://localhost:4321`. Verify:
- Nav renders with logo, links, language toggle
- Hero shows title, install command, copy button
- Skills section shows all 8 skills in three-column rows
- Footer renders

- [ ] **Step 3: Test language toggle**

Click `EN | 中` toggle. Verify:
- Chinese text appears where `.zh` spans exist
- English text hides
- Clicking again restores English

- [ ] **Step 4: Commit**

```bash
git add waza-site/src/pages/index.astro
git commit -m "feat(site): complete landing page"
```

---

## Task 10: SkillSidebar component

**Files:**
- Create: `waza-site/src/components/SkillSidebar.astro`

- [ ] **Step 1: Write SkillSidebar.astro**

Create `waza-site/src/components/SkillSidebar.astro`:

```astro
---
import { skills } from '../data/skills';
export interface Props {
  activeSlug: string;
}
const { activeSlug } = Astro.props;
---
<aside class="sidebar">
  <p class="label sidebar-label">
    <span class="en">SKILLS</span>
    <span class="zh">技能</span>
  </p>
  <nav>
    <ul class="sidebar-list">
      {skills.map((skill) => (
        <li>
          <a
            href={`/skills/${skill.slug}`}
            class={`sidebar-link mono ${skill.slug === activeSlug ? 'active' : ''}`}
          >
            {skill.command}
          </a>
        </li>
      ))}
    </ul>
  </nav>
</aside>

<style>
  .sidebar {
    width: 160px;
    flex-shrink: 0;
    background: var(--surface);
    border-right: 1px solid var(--border);
    padding: 28px 16px;
    position: sticky;
    top: 57px; /* nav height */
    height: calc(100vh - 57px);
    overflow-y: auto;
  }
  .sidebar-label {
    margin-bottom: 16px;
    font-size: 9px;
    letter-spacing: 2px;
  }
  .sidebar-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .sidebar-link {
    display: block;
    padding: 6px 8px;
    font-size: 13px;
    color: var(--text-faint);
    border-radius: 4px;
    transition: color 0.15s, background 0.15s;
  }
  .sidebar-link:hover {
    color: var(--text-primary);
    background: var(--border-light);
  }
  .sidebar-link.active {
    color: var(--text-primary);
    font-weight: 700;
    background: var(--border-light);
  }

  @media (max-width: 768px) {
    .sidebar {
      width: 100%;
      height: auto;
      position: static;
      border-right: none;
      border-bottom: 1px solid var(--border);
      padding: 16px 20px;
    }
    .sidebar-list {
      flex-direction: row;
      flex-wrap: wrap;
      gap: 4px;
    }
    .sidebar-link {
      font-size: 12px;
      padding: 4px 10px;
      border: 1px solid var(--border-light);
      border-radius: 12px;
    }
  }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add waza-site/src/components/SkillSidebar.astro
git commit -m "feat(site): add SkillSidebar with active state"
```

---

## Task 11: SkillLayout component

**Files:**
- Create: `waza-site/src/layouts/SkillLayout.astro`

- [ ] **Step 1: Write SkillLayout.astro**

Create `waza-site/src/layouts/SkillLayout.astro`:

```astro
---
import BaseLayout from './BaseLayout.astro';
import Nav from '../components/Nav.astro';
import SkillSidebar from '../components/SkillSidebar.astro';
import Footer from '../components/Footer.astro';
export interface Props {
  title?: string;
  activeSlug: string;
}
const { title, activeSlug } = Astro.props;
---
<BaseLayout title={title}>
  <Nav />
  <div class="skill-page">
    <SkillSidebar activeSlug={activeSlug} />
    <main class="skill-content">
      <slot />
    </main>
  </div>
  <Footer />
</BaseLayout>

<style>
  .skill-page {
    display: flex;
    min-height: calc(100vh - 57px - 96px); /* full height minus nav and footer */
  }
  .skill-content {
    flex: 1;
    padding: 40px 48px;
    max-width: 720px;
  }

  @media (max-width: 768px) {
    .skill-page { flex-direction: column; }
    .skill-content { padding: 28px 20px; }
  }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add waza-site/src/layouts/SkillLayout.astro
git commit -m "feat(site): add SkillLayout with sidebar"
```

---

## Task 12: Dynamic skill detail page

**Files:**
- Create: `waza-site/src/pages/skills/[skill].astro`

- [ ] **Step 1: Create the skills directory**

```bash
mkdir -p waza-site/src/pages/skills
```

- [ ] **Step 2: Write [skill].astro**

Create `waza-site/src/pages/skills/[skill].astro`:

```astro
---
import SkillLayout from '../../layouts/SkillLayout.astro';
import { skills, getSkill } from '../../data/skills';

export function getStaticPaths() {
  return skills.map((skill) => ({
    params: { skill: skill.slug },
  }));
}

const { skill: slug } = Astro.params;
const skill = getSkill(slug)!;
---
<SkillLayout
  title={`${skill.command} — Waza`}
  activeSlug={skill.slug}
>
  <article class="skill-article">
    <header class="skill-header">
      <h1 class="skill-command mono">{skill.command}</h1>
      <p class="skill-when">
        <span class="en">{skill.when.en}</span>
        <span class="zh">{skill.when.zh}</span>
      </p>
    </header>

    <section class="skill-section">
      <p class="label section-label">
        <span class="en">WHAT IT DOES</span>
        <span class="zh">它做什么</span>
      </p>
      <p class="skill-what">
        <span class="en">{skill.what.en}</span>
        <span class="zh">{skill.what.zh}</span>
      </p>
    </section>

    <section class="skill-section">
      <p class="label section-label">
        <span class="en">TRIGGER</span>
        <span class="zh">触发示例</span>
      </p>
      <pre class="trigger-block"><code>{skill.trigger}</code></pre>
    </section>

    <section class="skill-section">
      <p class="label section-label">
        <span class="en">CHAIN WITH</span>
        <span class="zh">组合使用</span>
      </p>
      <p class="chain-text mono">
        <span class="en">{skill.chainWith.en}</span>
        <span class="zh">{skill.chainWith.zh}</span>
      </p>
    </section>
  </article>
</SkillLayout>

<style>
  .skill-article {
    display: flex;
    flex-direction: column;
    gap: 36px;
  }
  .skill-header {
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }
  .skill-command {
    font-size: 28px;
    font-weight: 700;
    color: var(--accent);
    margin-bottom: 8px;
  }
  .skill-when {
    font-size: 14px;
    color: var(--text-secondary);
    font-style: italic;
    font-family: var(--font-serif);
  }
  .skill-section {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .section-label {
    font-size: 9px;
    letter-spacing: 2px;
  }
  .skill-what {
    font-size: 15px;
    color: var(--text-primary);
    line-height: 1.75;
  }
  .trigger-block {
    background: var(--code-bg);
    border-radius: 6px;
    padding: 14px 18px;
    overflow-x: auto;
  }
  .trigger-block code {
    background: none;
    padding: 0;
    font-size: 13px;
  }
  .chain-text {
    font-size: 14px;
    color: var(--text-secondary);
  }
</style>
```

- [ ] **Step 3: Run dev server and verify all skill pages**

```bash
cd waza-site && npm run dev
```

Visit each of these URLs and verify the page renders:
- `http://localhost:4321/skills/think`
- `http://localhost:4321/skills/health`

Verify:
- Sidebar shows all 8 skills, active one bold
- Command, when, what, trigger, chain sections all render
- Language toggle switches text to Chinese

- [ ] **Step 4: Verify static build generates all pages**

```bash
npm run build && ls dist/skills/
```

Expected: 8 directories (`think/`, `design/`, `check/`, `hunt/`, `write/`, `learn/`, `read/`, `health/`)

- [ ] **Step 5: Commit**

```bash
git add waza-site/src/pages/skills/
git commit -m "feat(site): add dynamic skill detail pages"
```

---

## Task 13: Favicon

**Files:**
- Create: `waza-site/public/favicon.svg`

- [ ] **Step 1: Create a minimal SVG favicon**

Create `waza-site/public/favicon.svg`:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
  <rect width="32" height="32" rx="6" fill="#1a1a1a"/>
  <text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle"
        font-family="Georgia, serif" font-size="18" fill="#c8a96e">技</text>
</svg>
```

- [ ] **Step 2: Commit**

```bash
git add waza-site/public/favicon.svg
git commit -m "feat(site): add favicon"
```

---

## Task 14: Deployment configuration

**Files:**
- Modify: `waza-site/astro.config.mjs`

- [ ] **Step 1: Update astro.config.mjs for static output**

Replace the contents of `waza-site/astro.config.mjs`:

```javascript
// @ts-check
import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  // If deploying to GitHub Pages at tw93.github.io/Waza, set:
  // site: 'https://tw93.github.io',
  // base: '/Waza',
  //
  // If deploying to a custom domain (e.g. waza.tw93.fun), set:
  // site: 'https://waza.tw93.fun',
  build: {
    assets: '_assets',
  },
});
```

- [ ] **Step 2: Run final build and check for errors**

```bash
cd waza-site && npm run build
```

Expected: `dist/` contains `index.html`, `skills/think/index.html`, etc. No errors.

- [ ] **Step 3: Preview the built site locally**

```bash
npm run preview
```

Open `http://localhost:4321`. Verify the built site matches dev behavior.

- [ ] **Step 4: Commit**

```bash
git add waza-site/astro.config.mjs
git commit -m "feat(site): configure Astro static output"
```

---

## Task 15: CSS import fix + global stylesheet wiring

**Files:**
- Modify: `waza-site/src/layouts/BaseLayout.astro`

Astro doesn't serve raw `/src/` files in production. The stylesheet import in BaseLayout must use an Astro import, not a raw URL.

- [ ] **Step 1: Fix the stylesheet import in BaseLayout.astro**

In `waza-site/src/layouts/BaseLayout.astro`, replace:

```astro
<link rel="stylesheet" href="/src/styles/global.css" />
```

With:

```astro
---
import '../styles/global.css';
---
```

Move the import to the frontmatter block (inside `---`).

- [ ] **Step 2: Run build to confirm no CSS errors**

```bash
cd waza-site && npm run build
```

Expected: no warnings about missing stylesheets.

- [ ] **Step 3: Commit**

```bash
git add waza-site/src/layouts/BaseLayout.astro
git commit -m "fix(site): wire global CSS via Astro import"
```

---

## Self-Review

### Spec coverage check

| Spec requirement | Covered by |
|-----------------|------------|
| Landing page + docs, single Astro project | Task 1, 9, 12 |
| 纸本白 visual theme, color tokens | Task 2 |
| EN/ZH toggle in nav | Task 5 |
| Hero: centered, install command, copy | Task 6 |
| Skills: three-column list rows, clickable | Task 7 |
| Footer: GitHub star + install command | Task 8 |
| Skill detail: left sidebar | Task 10, 11 |
| Skill page: command, when, what, trigger, chain | Task 12 |
| Static output (GitHub Pages / Vercel) | Task 14 |
| Mobile: sidebar collapses | Task 10 (media query) |
| Bilingual toggle persists across pages | Task 3 (localStorage) |
| CSS import production fix | Task 15 |
| Favicon | Task 13 |

All spec requirements covered. No gaps.

### Placeholder scan

No TBD, TODO, or "similar to above" patterns found. All code steps include complete implementations.

### Type consistency

- `Skill` interface defined in Task 4, consumed identically in Tasks 7, 10, 12
- `getSkill(slug)` defined in Task 4, used in Task 12
- `activeSlug: string` prop defined in SkillSidebar (Task 10) and SkillLayout (Task 11), passed correctly in Task 12
- CSS class `.en` / `.zh` defined in Task 2, used consistently in Tasks 5–12
