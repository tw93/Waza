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
