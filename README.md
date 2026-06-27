<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/2h/waza.svg" width="120" />
  <h1>Waza</h1>
  <p><b>Engineering habits you already know, turned into skills AI agents can run.</b></p>
  <a href="https://github.com/tw93/Waza/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/tw93/Waza/test.yml?branch=main&style=flat-square&label=tests" alt="Tests"></a>
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
| [`/think`](skills/think/SKILL.md) | Before building anything new | Challenges the problem, pressure-tests the design, and produces a decision-complete plan another agent can implement. |
| [`/design`](skills/design/SKILL.md) | Building frontend interfaces | Produces distinctive UI, including screenshot-driven aesthetic iteration, with a committed direction rather than generic defaults. |
| [`/check`](skills/check/SKILL.md) | After a task, before merging or release | Reviews the diff, extracts project-specific constraints, handles approved release/publish/push/reaction follow-through, and verifies with evidence. |
| [`/hunt`](skills/hunt/SKILL.md) | Any bug, regression, or unexpected behavior | Systematic debugging. Root cause confirmed before any fix is applied, especially when something used to work. |
| [`/write`](skills/write/SKILL.md) | Writing or editing prose | Rewrites prose to sound natural in Chinese and English. Cuts stiff, formulaic phrasing. |
| [`/learn`](skills/learn/SKILL.md) | Diving into an unfamiliar domain | Six-phase research workflow: collect, digest, outline, fill in, refine, then self-review and publish. |
| [`/read`](skills/read/SKILL.md) | Any URL or PDF | Reads URLs and PDFs with platform-specific routing. Plain reads return a concise summary; Markdown output is used when asked to convert, quote, cite, save, or feed downstream work. |
| [`/health`](skills/health/SKILL.md) | Auditing Agent Health | Checks Codex, Claude Code, project instructions, verifier output, and AI maintainability with a budget-aware summary pass before deep inspection. |

Each skill is a folder with reference docs, helper scripts, and gotchas from real failures.

## Install

One command installs all eight skills, with no prompts and no errors. Copy and run:

```bash
npx skills add tw93/Waza -a claude-code codex cursor -g -y
```

This installs to Claude Code, Codex, and Cursor, plus any other agent that reads the shared `~/.agents/skills` directory. Update later with `npx skills update -g -y`, or pass one agent (e.g. `-a claude-code`) to scope it.

**Native plugin** (for host-native update commands)

```bash
# Claude Code: install, then `claude plugin update waza`
/plugin marketplace add tw93/Waza
/plugin install waza@waza

# Codex: install, then `codex plugin marketplace upgrade waza`
codex plugin marketplace add tw93/Waza
codex plugin add waza@waza
```

**Claude Desktop**: download [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip), then Customize > Skills > "+" > Create skill, and upload the ZIP. Re-upload the latest ZIP to update.

**Pi**: `pi install npm:@tw93/waza` (update with `pi update npm:@tw93/waza`). `/health` audits Pi settings alongside Claude Code and Codex.

To hear about new versions, watch [GitHub Releases](https://github.com/tw93/Waza/releases).

## Project Context

Waza keeps the generic programmer habits inside the public skill. `/check` becomes project-aware by reading the target repository's public context and the user's task constraints.

- Project commands come from README files, package manifests, Makefiles, CI workflows, and explicit user instructions.
- Project hard stops include generated artifacts, protected files, version synchronization, release assets, and domain-specific safety risks.
- Public docs and examples must not include credentials, certificate paths, private key filenames, tokens, or personal machine details.

See [`skills/check/references/project-context.md`](skills/check/references/project-context.md) for the review context template.

## Chaining Skills

Skills are designed to be chained together, but transitions are manual. Each skill stops after completing its task and waits for you to decide the next step.

**Common workflows:**

- **Design a feature**: `/think` → approve → say "implement X" → `/check` → merge
- **Ship a fix**: `/hunt` → fix → `/check` → release/publish/push/issue follow-through
- **Research and write**: `/read` (fetch sources) → `/learn` (synthesize) → `/write` (polish)
- **Debug and verify**: `/hunt` (find root cause) → fix → `/check` (review changes)

Each arrow represents a manual user action. Skills don't automatically trigger each other.

## Extras

### Statusline

A minimal statusline for Claude Code: context window, 5-hour quota, and 7-day quota. Color-coded by usage, no progress bars, no noise.

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/y9/RUgevg.png" width="1000" />
</div>

```bash
curl -sL https://github.com/tw93/Waza/releases/latest/download/setup-statusline.sh | bash
```

**Codex** has native statusline items. Add to `~/.codex/config.toml`:

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "context-used", "five-hour-limit", "weekly-limit"]
status_line_use_colors = true
```

Codex shows remaining quota; the Claude Code statusline above shows used percentage (upstream does not yet expose `five-hour-used` / `weekly-used`).

### Optional Rules

Three independent toggles. Copy the ones you want (swap `claude-code` for `codex` on Codex):

```bash
# English coaching: appends a short 😇 correction when your prompt has an English mistake
curl -sL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh | bash -s -- english claude-code

# Anti-patterns: always-on cross-skill guardrails (read before acting, no scope creep, no unsolicited summaries)
curl -sL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh | bash -s -- anti-patterns claude-code

# Routing hint: tells non-Claude hosts to prefer Waza skills when a request matches their triggers
curl -sL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh | bash -s -- waza-routing claude-code
```

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/24/vfkGOi.png" width="1000" />
</div>

Curl URLs use the latest GitHub release asset. Set `WAZA_REF=main` before the command if you want bleeding-edge scripts.

## Uninstall

```bash
npx skills remove tw93/Waza -g
rm -f ~/.claude/statusline.sh
rm -f ~/.claude/rules/english.md
rm -f ~/.claude/rules/anti-patterns.md
rm -f ~/.claude/rules/waza-routing.md
```

For Claude Desktop, delete Waza from Customize > Skills. For Codex rule installs, remove the marked Waza blocks from `~/.codex/AGENTS.md`.

## Background

Tools like Superpowers and gstack are impressive but heavy: too many skills, too much configuration, too steep a learning curve.

Every rule the author writes is also a ceiling. The model can only do what the instructions say. Waza goes the other way: each skill sets a clear goal and the constraints that matter, then steps back. As models improve, that restraint pays compound interest.

Eight skills for the habits that actually matter. Each does one thing, has a clear trigger, and stays out of the way. Built from real projects, refined through 300+ sessions across 7 projects. Every gotcha traces to a real failure.

The `/health` skill grew from the six-layer Claude Code framework described in [this post](https://tw93.fun/en/2026-03-12/claude.html), and now covers Codex, Claude Code, Pi, verifier surfaces, and AI maintainability.

## Support

- The most direct way to support me is getting [Mole for Mac](https://mole.fit), my paid Mac cleanup app.
- If Waza helped you, [share it](https://twitter.com/intent/tweet?url=https://github.com/tw93/Waza&text=Waza%20-%20AI%20coding%20skills%20for%20the%20complete%20engineer.) with friends or give it a star.
- Got ideas or bugs? Open an issue or PR, feel free to contribute your best AI model.
- I have two cats, TangYuan and Coke. If you think Waza delights your life, you can feed them <a href="https://cats.tw93.fun?name=Waza" target="_blank">canned food 🥩</a>.

<details>
<summary>These lovely people already did 🐱</summary>
<br/>
<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>
</details>

## License

MIT License. Feel free to use Waza and contribute.
