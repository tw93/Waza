<p align="center">
  <a href="https://www.atlascloud.ai/?utm_source=github&utm_medium=link&utm_campaign=waza">
    <img src="docs/atlas-cloud-logo.png" alt="Atlas Cloud" width="200">
  </a>
</p>

> 🎁 **[Atlas Cloud](https://www.atlascloud.ai/?utm_source=github&utm_medium=link&utm_campaign=waza)** powers Waza with Claude Opus 4, Claude Sonnet 4, and 57 other frontier LLMs via a unified OpenAI-compatible API — access all Anthropic Claude models and more through a single endpoint. [View all models](https://www.atlascloud.ai/models) · [Coding Plan](https://www.atlascloud.ai/console/coding-plan)

<details>
<summary>📋 59 models available on Atlas Cloud</summary>

| Model | Type |
|-------|------|
| deepseek-ai/deepseek-v4-pro | LLM |
| deepseek-ai/deepseek-v4-0520 | LLM |
| deepseek-ai/deepseek-v4-flash | LLM |
| deepseek-ai/deepseek-r2 | LLM |
| deepseek-ai/deepseek-r2-0528 | LLM |
| deepseek-ai/deepseek-r1-0528 | LLM |
| deepseek-ai/deepseek-r1 | LLM |
| deepseek-ai/deepseek-prover-v2 | LLM |
| moonshot-ai/kimi-k2 | LLM |
| moonshot-ai/kimi-k2-0711 | LLM |
| moonshot-ai/kimi-k1.5-long | LLM |
| qwen/qwen3-235b-a22b | LLM |
| qwen/qwen3-30b-a3b | LLM |
| qwen/qwen3-32b | LLM |
| qwen/qwq-32b | LLM |
| openai/gpt-5 | LLM |
| openai/gpt-5-mini | LLM |
| openai/gpt-4.1 | LLM |
| openai/gpt-4o | LLM |
| openai/o3 | LLM |
| openai/o4-mini | LLM |
| openai/o3-mini | LLM |
| anthropic/claude-sonnet-4-5 | LLM |
| anthropic/claude-opus-4 | LLM |
| anthropic/claude-sonnet-4 | LLM |
| anthropic/claude-haiku-4-5 | LLM |
| google/gemini-2.5-pro | LLM |
| google/gemini-2.5-flash | LLM |
| google/gemini-2.5-flash-lite | LLM |
| google/gemini-2.0-flash | LLM |
| xai/grok-4 | LLM |
| xai/grok-3 | LLM |
| xai/grok-3-mini | LLM |
| meta-llama/llama-4-scout | LLM |
| meta-llama/llama-4-maverick | LLM |
| meta-llama/llama-3.3-70b | LLM |
| cohere/command-a | LLM |
| mistral/mistral-large | LLM |
| minimax/minimax-m1 | LLM |
| 01ai/yi-lightning | LLM |
| seedance/seedance-v1-pro | Video |
| seedance/seedance-v1-pro-fast | Video |
| seedance/seedance-v1-lite | Video |
| kling/kling-v2.1-pro | Video |
| kling/kling-v2.1-standard | Video |
| kling/kling-v1.6-pro | Video |
| kling/kling-v1.6-standard | Video |
| wan2/wan2.1-t2v-turbo | Video |
| wan2/wan2.1-i2v-turbo | Video |
| veo/veo3.1-fast | Video |
| veo/veo3-fast | Video |
| veo/veo3 | Video |
| runway/gen4-turbo | Video |
| stable-diffusion/sd3.5-large | Image |
| flux/flux1.1-pro-ultra | Image |
| flux/flux1.1-pro | Image |
| ideogram/ideogram-v3 | Image |
| recraft/recraft-v3 | Image |
| minimax/hailuo-i2v-01-live | Video |
</details>

---

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

## Install and Update

Most users should install Waza globally, so the same skills are available in every project.

**Claude Code**

```bash
npx skills add tw93/Waza -a claude-code -g -y
```

This installs `/think`, `/design`, `/check`, `/hunt`, `/write`, `/learn`, `/read`, and `/health`. Install just one with `npx skills add tw93/Waza --skill think -a claude-code -g -y`.

**Codex**

```bash
npx skills add tw93/Waza -a codex -g -y
```

Install just one with `npx skills add tw93/Waza --skill think -a codex -g -y`. Codex sessions can invoke installed skills by name or link to the installed `SKILL.md` path shown by `npx skills path tw93/Waza`.

**Antigravity**

```bash
npx skills add tw93/Waza -a antigravity -g -y
npx skills add tw93/Waza -a antigravity-cli -g -y
```

Use `antigravity` for the desktop app and `antigravity-cli` for the terminal agent. Both use Waza's standard `skills/<name>/SKILL.md` layout through the skills installer.

**OpenCode**

```bash
npx skills add tw93/Waza -a opencode -g -y
```

OpenCode loads Waza through its native skill tool after installation. Invoke the skills by name when the task matches `think`, `design`, `check`, `hunt`, `write`, `learn`, `read`, or `health`.

**Claude Code plugin marketplace** (single-skill entries require Claude Code v2.1.143+)

```bash
/plugin marketplace add tw93/Waza
/plugin install waza@waza
```

This installs all eight skills. Install just one with `/plugin install waza-<name>@waza` (for example, `waza-think@waza`) on Claude Code v2.1.143 or newer.

**Claude Desktop**

Download [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip), open Customize > Skills > "+" > Create skill, and upload the ZIP.

**Pi coding agent**

```bash
pi install npm:@tw93/waza
```

Pi can load Waza's standard `skills/<name>/SKILL.md` layout from the repo or from the published `@tw93/waza` npm package, which exposes `pi.skills` metadata pointing at `./skills`. `/health` audits Pi settings, configured packages, and local skill roots alongside Claude Code and Codex.

**Update**

```bash
npx skills update -g -y
```

Marketplace installs use `claude plugin update <skill>`. Claude Desktop users can replace the old skill with the latest [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip).
Pi users can run `pi update npm:@tw93/waza`, or `pi update --extensions` to update all installed Pi packages.
To hear about new versions, watch [GitHub Releases](https://github.com/tw93/Waza/releases) for Waza.

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

### English Coaching

Optional rule for English practice. When your prompt contains an English mistake, the agent appends a short 😇 correction; Chinese-only prompts stay untouched.

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/24/vfkGOi.png" width="1000" />
</div>

```bash
# Claude Code
curl -sL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh | bash -s -- english claude-code

# Codex
curl -sL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh | bash -s -- english codex
```

### Anti-Patterns

Optional always-on guardrails for cross-skill behaviors: stop acting before reading, no hallucinated paths, no scope creep, no unsolicited summaries. Skill-agnostic, applies in every session.

```bash
curl -sL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh | bash -s -- anti-patterns claude-code
```

Use `codex` instead of `claude-code` for Codex. Curl URLs use the latest GitHub release asset. Set `WAZA_REF=main` before the command if you want bleeding-edge scripts.

### Routing Hint

Optional pointer that tells the host to prefer Waza skills when a request matches their triggers. Useful for Codex, Pi, and other agents that do not auto-route from skill `description`. Claude Code already routes through descriptions, so this is opt-in even there.

```bash
curl -sL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh | bash -s -- waza-routing claude-code
```

Use `codex` instead of `claude-code` for Codex.

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

- If Waza helped you, [share it](https://twitter.com/intent/tweet?url=https://github.com/tw93/Waza&text=Waza%20-%20AI%20coding%20skills%20for%20the%20complete%20engineer.) with friends or give it a star.
- Got ideas or bugs? Open an issue or PR, feel free to contribute your best AI model.
- I have two cats, TangYuan and Coke. If you think Waza delights your life, you can feed them <a href="https://cats.tw93.fun?name=Waza" target="_blank">canned food 🥩</a>.

<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>

## License

MIT License. Feel free to use Waza and contribute.
