<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/2h/waza.svg" width="120" />
  <h1>Waza</h1>
  <p><b>Engineering habits you already know, turned into skills Claude can run.</b></p>
  <a href="https://github.com/tw93/Waza/stargazers"><img src="https://img.shields.io/github/stars/tw93/Waza?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/tw93/Waza/releases"><img src="https://img.shields.io/github/v/tag/tw93/Waza?label=version&style=flat-square" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://twitter.com/HiTw93"><img src="https://img.shields.io/badge/follow-Tw93-red?style=flat-square&logo=Twitter" alt="Twitter"></a>
</div>

<br/>

## Why

Waza (技, わざ) is a Japanese martial arts term for technique: a move practiced until it becomes instinct.

A good engineer does not just write code. They think through requirements, review their own work, debug systematically, design interfaces that feel intentional, and read primary sources. They write clearly, and learn new domains by producing output, not consuming content.

AI is more capable than most engineers at raw output. But without structure, that capability drifts into generic, imprecise work. Waza channels it into precision: eight skills that set clear goals and constraints, then let the model do what it does best.

Part of a trilogy: [Kaku](https://github.com/tw93/Kaku) (書く) writes code, [Waza](https://github.com/tw93/Waza) (技) drills habits, [Kami](https://github.com/tw93/Kami) (紙) ships documents. Think of them as a family: Kaku is the dad, Waza the big sister, Kami the little sister.

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/qa/waza_repaired_v4.svg" width="1000" />
</div>

## Skills

Each engineering habit gets an installed skill. In Claude Code, type the slash command. In Codex, invoke the installed skill by name and follow the same playbook.

| Skill | When | What it does |
| :--- | :--- | :--- |
| [`/think`](skills/think/SKILL.md) | Before building anything new | Challenges the problem, pressure-tests the design, validates architecture before any code is written. |
| [`/design`](skills/design/SKILL.md) | Building frontend interfaces | Produces distinctive UI with a committed aesthetic direction, not generic defaults. |
| [`/check`](skills/check/SKILL.md) | After a task, before merging | Reviews the diff, auto-fixes safe issues, flags destructive commands, verifies with evidence. |
| [`/refactor`](skills/refactor/SKILL.md) | Cleaning up code | Restructures existing code to improve readability, reduce complexity, and apply DRY without changing external behavior. |
| [`/hunt`](skills/hunt/SKILL.md) | Any bug or unexpected behavior | Systematic debugging. Root cause confirmed before any fix is applied. |
| [`/write`](skills/write/SKILL.md) | Writing or editing prose | Rewrites prose to sound natural in Chinese and English. Cuts stiff, formulaic phrasing. |
| [`/learn`](skills/learn/SKILL.md) | Diving into an unfamiliar domain | Six-phase research workflow: collect, digest, outline, fill in, refine, then self-review and publish. |
| [`/read`](skills/read/SKILL.md) | Any URL or PDF | Fetches content as clean Markdown with platform-specific routing. Special handling for GitHub, PDFs, WeChat, and Feishu. |
| [`/health`](skills/health/SKILL.md) | Auditing Claude Code setup | Checks CLAUDE.md, rules, skills, hooks, MCP, and behavior. Flags issues by severity. |

Each skill is a folder with reference docs, helper scripts, and gotchas from real failures.

## Chaining Skills

Skills are designed to be chained together, but transitions are manual. Each skill stops after completing its task and waits for you to decide the next step.

**Common workflows:**

- **Design a feature**: `/think` → approve → say "implement X" → `/check` → merge
- **Research and write**: `/read` (fetch sources) → `/learn` (synthesize) → `/write` (polish)
- **Debug and verify**: `/hunt` (find root cause) → fix → `/check` (review changes)

Each arrow represents a manual user action. Skills don't automatically trigger each other.

## Extras

### Statusline

A minimal statusline for Claude Code: context window, 5-hour quota, and 7-day quota.

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/y9/RUgevg.png" width="1000" />
</div>

Color coding: green below 70%, yellow at 70-85%, red above 85% for context; blue, magenta, red for quota thresholds. No progress bars, no noise.

```bash
curl -sL https://raw.githubusercontent.com/tw93/Waza/main/scripts/setup-statusline.sh | bash
```

### English Coaching

Most AI models were trained on far more English than any other language, so every prompt in your native tongue goes through an invisible translation layer. Switch to English and the reasoning sharpens, answers get more precise, and every session doubles as language practice.

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/24/vfkGOi.png" width="1000" />
</div>

Claude corrects your mistakes in place, tagging each one with its pattern name so you learn the rule, not just the fix.

```bash
# Claude Code
mkdir -p ~/.claude/rules && curl -fsSL https://raw.githubusercontent.com/tw93/Waza/main/rules/english.md -o ~/.claude/rules/english.md

# Codex
mkdir -p ~/.codex && curl -fsSL https://raw.githubusercontent.com/tw93/Waza/main/rules/english.md >> ~/.codex/AGENTS.md
```

## Install

**Claude Code**

```bash
npx skills add tw93/Waza -a claude-code -g -y
```

**Codex**

```bash
npx skills add tw93/Waza -a codex -g -y
```

**Claude Desktop**

Download [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip), open Customize > Skills > "+" > Create skill, and upload the ZIP.

**Compatibility**

`/health` is Claude Code only. The other skills are written to use the host environment's native question, search, fetch, and agent mechanisms. `/check` runs parallel specialist reviewers when the host supports them; otherwise it performs the same passes inline.

## Uninstall

```bash
# Remove all skills
npx skills remove tw93/Waza -g

# Remove Claude Desktop skill
# Open Customize > Skills, find Waza, click "..." > Delete

# Remove statusline
rm -f ~/.claude/statusline.sh
# Then remove the statusLine key from ~/.claude/settings.json

# Remove English Coaching (Claude Code)
rm -f ~/.claude/rules/english.md

# Remove English Coaching (Codex): remove the English Coaching block from ~/.codex/AGENTS.md
```

## Background

Tools like Superpowers and gstack are impressive, but they are heavy. Too many skills, too much configuration, too steep a learning curve for engineers who just want to get things done.

There's also a subtler problem. Every rule the author writes becomes a ceiling. The model can only do what the instructions say and can't go further. Waza goes the other direction. Each skill sets a clear goal and the constraints that matter, then steps back. As models improve, that restraint pays compound interest.

Eight skills for the habits that actually matter. Each does one thing, has a clear trigger, and stays out of the way. Not complete by design, just the right amount done well.

Built from patterns across real projects, refined through actual use. Every gotcha traces to a real failure: a wrong code path that took four rounds to find, a release posted before artifacts were uploaded, a server restarted eight times without reading the error. 30 days, 300+ sessions, 7 projects, 500 hours.

The `/health` skill is based on the six-layer framework described in [this post](https://tw93.fun/en/2026-03-12/claude.html).

## Support

- If Waza helped you, [share it](https://twitter.com/intent/tweet?url=https://github.com/tw93/Waza&text=Waza%20-%20Claude%20Code%20skills%20for%20the%20complete%20engineer.) with friends or give it a star.
- Got ideas or bugs? Open an issue or PR, feel free to contribute your best AI model.
- I have two cats, TangYuan and Coke. If you think Waza delights your life, you can feed them <a href="https://miaoyan.app/cats.html?name=Waza" target="_blank">canned food 🥩</a>.

<div align="center">
  <a href="https://miaoyan.app/cats.html?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/MiaoYan@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>

## License

MIT License. Feel free to use Waza and contribute.
