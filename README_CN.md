<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/2h/waza.svg" width="120" />
  <h1>Waza</h1>
  <p><b>把熟练的工程习惯，变成 AI 能跑的技能</b></p>
  <p><a href="README.md">English</a> · 中文 · <a href="README_TW.md">繁體</a> · <a href="README_JA.md">日本語</a> · <a href="README_KR.md">한국어</a> · <a href="README_DE.md">Deutsch</a> · <a href="README_FR.md">Français</a></p>
  <a href="https://github.com/tw93/Waza/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/tw93/Waza/test.yml?branch=main&style=flat-square&label=tests" alt="Tests"></a>
  <a href="https://github.com/tw93/Waza/stargazers"><img src="https://img.shields.io/github/stars/tw93/Waza?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/tw93/Waza/releases"><img src="https://img.shields.io/github/v/tag/tw93/Waza?label=version&style=flat-square" alt="Version"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License"></a>
  <a href="https://twitter.com/HiTw93"><img src="https://img.shields.io/badge/follow-Tw93-red?style=flat-square&logo=Twitter" alt="Twitter"></a>
</div>

<br/>

<div align="center">
  <img src="assets/waza_skills.svg" width="1000" />
</div>

## 技能

每个工程习惯对应一个独立技能，Claude Code 输入斜杠命令即可触发，Codex 则直接按技能名调用

| 技能 | 触发时机 | 它做什么 |
| :--- | :--- | :--- |
| [`/think`](skills/think/SKILL.md) | 动手写新代码前 | 深入推敲方案并压测设计，产出决策完备且能直接落地的执行计划 |
| [`/ui`](skills/ui/SKILL.md) | 构建前端界面 | 告别平庸的默认模板，带着明确设计风格对照真实截图反复打磨 |
| [`/check`](skills/check/SKILL.md) | 任务完成或准备发布 | 结合项目规范逐行审查改动，验证实际结果并稳妥处理发布流程 |
| [`/hunt`](skills/hunt/SKILL.md) | 遇到 Bug 或异常行为 | 动手修之前彻底查清根本原因，尤其是面对以前正常运行的功能 |
| [`/write`](skills/write/SKILL.md) | 撰写或修改文案 | 改写中英文本使其自然流畅，剔除生硬公式化的套话与机器感 |
| [`/learn`](skills/learn/SKILL.md) | 探索完全陌生的领域 | 按六阶段完整调研流程，把陌生领域系统消化并沉淀成文 |
| [`/read`](skills/read/SKILL.md) | 阅读网页链接或 PDF | 快速提取精炼摘要，或转成方便引用归档的干净 Markdown |
| [`/health`](skills/health/SKILL.md) | 检查智能体运行状态 | 排查 Agent 配置与指令漂移，先轻量概览再深入诊断 |

每个技能都是一个独立目录，内置参考文档、辅助脚本以及真实踩坑沉淀的避坑指南

## 安装

**Claude Code、Codex、Cursor 与其他 Agent**

```bash
npx skills add tw93/Waza -a claude-code codex cursor -g -y
```

也可以直接告诉你的 Agent 帮你安装：
> 阅读 https://github.com/tw93/Waza/blob/main/llms.txt 帮我安装 Waza

技能统一存放在 `~/.agents/skills` 共享目录，Claude Code 通过软链接接入，Codex、Cursor、Gemini CLI、Copilot、Amp、Kimi Code CLI 以及其他能读取该目录的 Agent 都会自动加载这 8 个技能。拥有独立技能目录的 Agent 可在 `-a` 后指定其 ID，比如 `antigravity-cli` 或 `qwen-code`，后续通过 `npx skills update -g -y` 保持更新

**宿主插件方式**，如果你更习惯使用宿主自有的更新命令（技能带有命名空间前缀，如 `/waza:check`）：

```bash
# Claude Code（更新命令：claude plugin update waza）
/plugin marketplace add tw93/Waza
/plugin install waza@waza

# Codex（更新命令：codex plugin marketplace upgrade waza，然后 codex plugin add waza@waza）
codex plugin marketplace add tw93/Waza
codex plugin add waza@waza
```

**Claude Desktop**：下载 [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip)，打开 Customize > Skills > "+" > Create skill 并上传压缩包，更新时点击卡片上的 "..." 选择 Replace 再上传最新的 ZIP 即可

**Pi**：`pi install npm:@tw93/waza`，通过 `pi update npm:@tw93/waza` 更新

## 技能串联

技能串联由你做主，每个技能跑完既定目标就停下，拿到明确授权后会自动接力完成整套流程，不需要在每个环节反复确认

**常见工作流：**

- **做新功能**：`/think` 想透方案 → 确认后动手实现 → `/check` 把关合并
- **排查修复**：`/hunt` 查清根因 → 动手修复 → `/check` 验证并发布
- **调研成文**：`/read` 读取素材 → `/learn` 消化梳理 → `/write` 润色文字
- **排查验证**：`/hunt` 定位根因 → 动手改完 → `/check` 审查改动

## 项目上下文

Waza 只沉淀通用的工程习惯，`/check` 运行时只从目标仓库公开的项目文件与你的任务要求提炼约束，比如 README、包清单、Makefile 和 CI 配置，绝不读取私有路径、凭证或 Token，具体上下文模板可参考 [`skills/check/references/project-context.md`](skills/check/references/project-context.md)

## 附加工具与规则

### 状态栏

Claude Code 极简状态栏：显示上下文窗口、5 小时配额与 7 天配额，按用量着色，没有进度条，没有视觉噪音

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/y9/RUgevg.png" width="1000" />
</div>

```bash
(
  set -e
  WAZA_STATUSLINE_SCRIPT="$(mktemp -t waza-statusline.XXXXXX)"
  trap 'rm -f "$WAZA_STATUSLINE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-statusline.sh -o "$WAZA_STATUSLINE_SCRIPT"
  # 可以先检查脚本内容：less "$WAZA_STATUSLINE_SCRIPT"
  bash "$WAZA_STATUSLINE_SCRIPT"
)
```

**Codex** 原生支持状态栏字段，直接添加到 `~/.codex/config.toml`：

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "context-used", "five-hour-limit", "weekly-limit"]
status_line_use_colors = true
```

Codex 显示剩余额度，上方 Claude Code 状态栏显示已用百分比

### 可选规则

可选规则用于补充技能之外的持久化习惯，写入 Agent 的系统提示词中生效，只安装技能默认不会开启，按需复制执行即可（在对应 Agent 上将 `claude-code` 替换为 `codex` 或 `antigravity-cli`）：

```bash
(
  set -e
  WAZA_RULE_SCRIPT="$(mktemp -t waza-rule.XXXXXX)"
  trap 'rm -f "$WAZA_RULE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh -o "$WAZA_RULE_SCRIPT"
  # 可以先检查脚本内容：less "$WAZA_RULE_SCRIPT"

  # 英文写作教练：Prompt 中有英文表达错误时，在结尾追加一条简短的 😇 纠错建议
  bash "$WAZA_RULE_SCRIPT" english claude-code

  # 行为防错守则：全局常驻约束（先看再改、不随意扩大范围、不主动输出冗余总结）
  bash "$WAZA_RULE_SCRIPT" anti-patterns claude-code

  # 技能路由提示：提示非 Claude 宿主在命中对应场景时优先调用 Waza 技能
  bash "$WAZA_RULE_SCRIPT" waza-routing claude-code

  # 日常清晰表达：术语统一、条件明确、保留不确定性
  # Clarity 规则目前在 main 分支可用，尚未进入正式发版
  WAZA_REF=main bash "$WAZA_RULE_SCRIPT" clarity claude-code
)
```

[Clarity](rules/clarity.md) 借鉴了 ASD-STE100 的清晰写作原则，不会强加受控英文语法，也不会改变你的个人表达风格。重新运行命令可更新已装规则，生效需重启新会话。Codex 会在 `~/.codex/AGENTS.md` 写入标记块，Claude Code 与 Antigravity 则安装为规则文件，其他工具直接复制进对应的系统提示词即可

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/24/vfkGOi.png" width="1000" />
</div>

下载脚本默认使用最新的 GitHub Release 资源，如需体验 bleeding-edge 脚本可在命令前指定 `WAZA_REF=main`

## 为什么做 Waza

Waza 在日文中意为技艺，是千锤百炼后化为本能的招式。好工程师从不只是写代码，更懂动手前推敲边界、排查时深挖根因、交付前逐行把关。AI 算力充沛，但缺少工程约束容易输出平庸，每个 Waza 技能只明确结果、红线与验证方式，把具体路径留给模型自主发挥

像 Superpowers 或 gstack 这类工具虽然强大但体量较重，Waza 保持克制，只收录 8 个真正核心的工程习惯，每个技能专心做好一件事。来自 7 个项目、300 多次真实会话的实战沉淀，每一条避坑指南都来自踩过的真实深坑，并与另外两款工具组成三部曲：[Kaku](https://github.com/tw93/Kaku) 负责写代码，[Waza](https://github.com/tw93/Waza) 负责磨习惯，[Kami](https://github.com/tw93/Kami) 负责出文档

## 卸载

```bash
npx skills remove tw93/Waza -g
rm -f ~/.claude/statusline.sh
rm -f ~/.claude/rules/english.md
rm -f ~/.claude/rules/anti-patterns.md
rm -f ~/.claude/rules/waza-routing.md
rm -f ~/.claude/rules/clarity.md
```

Claude Desktop 直接在 Customize > Skills 中删除 Waza，Codex 规则安装从 `~/.codex/AGENTS.md` 中移除对应的 Waza 标记块，Antigravity 从 `~/.gemini/antigravity-cli/rules/` 删除对应规则文件，其他工具从系统提示词中移除即可，移除后开启新会话生效

## 支持

- 最直接的支持方式是购买 [Mole for Mac](https://mole.fit)，这是我开发的 Mac 清理应用
- 如果 Waza 对你有帮助，欢迎点个 Star，[分享给朋友](https://twitter.com/intent/tweet?url=https://github.com/tw93/Waza&text=Waza%20-%20AI%20coding%20skills%20for%20the%20complete%20engineer.)，或者提交 Issue 与 PR
- 我养了两只猫，汤圆和可乐，如果 Waza 帮到了你，可以给它们加个 <a href="https://cats.tw93.fun?name=Waza" target="_blank">罐头 🥩</a>

<details>
<summary>已经赞助过的可爱朋友们 🐱</summary>
<br/>
<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>
</details>

## 许可证

MIT License
