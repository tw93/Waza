# Waza Skill Resolver

## Shared Output Marker

所有技能都沿用同一个输出约定：首行内联带上 `🥷`，不要单独起段。这个约定写在各自的 `SKILL.md` 里，`scripts/verify_skills.py` 也会校验它。

触发词到技能的路由表。Claude Code 通过每个 SKILL.md 的 `description` 自动匹配，这份文档是给人看的集中索引，也是 `scripts/verify_skills.py` 的校验依据。改 SKILL.md 的适用范围时，同步改这里。

> **Read the skill file before acting.** 两个技能都可能匹配时，两个都读。它们设计成可串联（例：`/think` → 实现 → `/check`）。

## 按工作流阶段分路

### Pre-build（动手前）

| 触发 | 技能 |
|------|------|
| 新功能 / 架构决策 / "怎么设计" / "应该用什么方案" / "判断一下" / "有没有必要" / "值不值得" / 商业化/产品 pivot / 需要可执行计划或 handoff / 어떻게설계 / 어떤방식 / 필요한가 | `skills/think/SKILL.md` |
| UI / 组件 / 页面 / 视觉界面 / 前端 / 截图里说"丑"、"不清晰"、"很怪" / 真实截图视觉 polish / 못생겼다 / 안맞다 | `skills/ui/SKILL.md` |

### Post-build（交付前）

| 触发 | 技能 |
|------|------|
| 实现完成 / 合并前 / "review 一下" / "看看这段代码" / release gate / 生成产物检查 / safety sink 审查 / `code-review` / 코드봐줘 / 리뷰해줘 | `skills/check/SKILL.md` |
| release / publish / push / release reaction / 发布 / 提交 / 关闭 issue / 发布前检查 / 发布表情 / registry/appcast/asset 检查 / 릴리즈 / 발행 | `skills/check/SKILL.md` (Ship / Release Follow-through) |
| review issue / review PR / triage / 批量处理 / "看看有没有 issue" / close issue | `skills/check/SKILL.md` (Triage Mode) |
| 项目体检 / project audit / 项目评分 / 给项目打分 / 深入分析项目代码 / 评估项目质量 / 代码质量评分 / scorecard / linus 风格 review / rate this codebase / score this project / 프로젝트 평가 | `skills/check/SKILL.md` (Project Audit Mode) |

### Diagnostic（出问题了）

| 触发 | 技能 |
|------|------|
| 报错 / 崩溃 / 测试失败 / 行为异常 / "为什么不工作" / 以前是好的 / 回归 / 截图回归 / 反复修不好 / stale cache / 队列或生成物边界 / 왜안되지 / 계속안되네 | `skills/hunt/SKILL.md` |
| Claude/Codex/Pi 忽略指令 / hook 失灵 / MCP 异常 / Codex 配置 / Pi 配置 / AGENTS.md / config.toml / agent instructions / 配置审计 / health 消耗 token / AI coding 腐化 / 代码变烂 / 维护性 / hotspot ownership / 上下文混乱 / 验证缺失 / 验证命令失真 / Claude안듣는다 / 설정점검 | `skills/health/SKILL.md` |

### Content（内容进出）

| 触发 | 技能 |
|------|------|
| 消息含 http(s) URL / 任何网页链接 / PDF 路径 / "看一下这个", "读一下这个" / 이링크봐줘 / 읽어봐 | `skills/read/SKILL.md` |
| 写作 / 改稿 / 润色 / 去 AI 味（中英文、韩文） / 本地化文案 / 多语言产品文案 / 推特推文 / 社交媒体文案 / launch copy / release notes 文案 / 글써줘 / 고쳐줘 | `skills/write/SKILL.md` |
| 文档审阅 / 白皮书 / release notes prose 审核 / "审稿" / "check this document" | `skills/write/SKILL.md` (Document Review Mode) |
| 深度研究一个陌生领域 / 六阶段研究到成稿 / 一批材料沉淀成文章 / 깊이공부 | `skills/learn/SKILL.md` |

## Disambiguation（歧义消解）

多个技能都可能匹配时按以下规则：

1. **最具体优先**：`/ui` 比 `/think` 更具体（仅限 UI 决策）。用户说"帮我设计登录页"时优先 `/ui`。
2. **URL 按内容类型二次分流**：消息含 URL → 先走 `/read` 取回 Markdown → 如果用户要总结或分析，继续完成总结或分析；如果是长文研究性素材再接 `/learn`。
3. **改错 vs review**：代码已经交付或走到 PR → `/check`；代码跑不通或行为错了 → `/hunt`。两者都可能匹配"帮我看看"，按"有没有具体错误现象"判断。
4. **配置/维护性异常 vs 代码错误**：Claude/Codex 本身不听话、hook 不触发、MCP 掉链子、AGENTS/CLAUDE/config.toml 漂移、`/health` 消耗 token、AI coding 腐化、上下文混乱、验证缺失或验证命令失真 → `/health`；用户写的代码抛异常 → `/hunt`。
5. **发布动作 vs 发布文案**：要写 release notes / changelog → `/write`；要提交、打 tag、publish、push、上传 release asset、补 GitHub release reactions、回复/关闭 issue → `/check`。
6. **截图审美 vs 截图回归**：截图里说"丑/不好看/不清晰"且是审美校准 → `/ui`；截图证明以前好的现在坏了、渲染错、状态错、生成物错 → `/hunt`。
7. **长文产出 vs 润色**：从零到成稿 → `/learn`；已有稿子要改 → `/write`。
8. **判断 vs 调试**："判断一下" + 报错/异常/不工作 → `/hunt`（诊断问题）；"判断一下" + 有没有必要/该不该保留/值不值得 → `/think` Evaluation Mode（价值判断）。
9. **继续优化 vs 调试**："继续优化" / "优化代码" 不含报错或异常现象 → `/check`（代码质量改善）；有具体报错或回归 → `/hunt`。
10. **需求包 vs issue 队列**：两个技能都有 Triage Mode。对象是还没实施的一批诉求/截图（判断接受与否）→ `/think` Triage Mode；对象是仓库里已存在的 issue/PR（处置、回复、关闭）→ `/check` Triage Mode。
11. **兜底**：两个都模糊时读两个 SKILL.md 的 "Not for" 段，用排除法；还是模糊就问用户。

## Chaining（常见串联）

技能之间默认不自动串联。每个技能完成后会停下来，等用户决定下一步，除非当前请求或项目公开上下文已经明确授权后续动作（例如 "implement this plan", "review then ship if green", "triage and close"）。

- `/think` 出方案 → **用户说"实现"** → 实施 → **用户说"/check"** → `/check` 把关
- `/think` 出可执行计划 → **用户说"Implement the plan / 可以干 / 直接改"** → 按计划实施，不重新争论方向
- `/hunt` 修复 issue → **用户说"发布 / push / 关闭 issue"** → `/check` 做发布前检查和收尾
- `/read` 取回多篇 URL → **用户说"/learn"** → `/learn` 综合成文；如果同一回合已经明确要求总结或分析，`/read` fetch 后直接满足该请求
- `/learn` 出初稿 → **用户说"/write"** → `/write` 去 AI 味
- `/hunt` 定位根因 → **用户说"修"** → 修完 → **用户说"/check"** → `/check` 确认没副作用
- `/health` 发现 skill 配置问题 → **用户说"修"** → 修完 → **用户说"/health"** → 再跑一次 `/health`

## Latent vs Deterministic

Waza 的技能都是 fat skill（Markdown 判断），底层的确定性约束走 `scripts/verify_skills.py` 和 `rules/*.md`。新加能力时先问：

- 需要判断 / 适应场景 / 追问用户？→ skill
- 同入同出 / 只是校验和列举？→ script 或 rule

不要把 lint 检查写成 skill，也不要把"怎么研究一个陌生领域"塞进脚本。详见根目录 `AGENTS.md` 的决策表。

## Project Context

通用程序员能力沉淀在 Waza。遇到具体项目时，先从公开项目上下文提炼约束，再执行对应技能：

- `code-review` / `/check` -> 从 diff、README、manifest、CI、release notes 中提炼验证命令、生成物、风险、safety sinks 和发布规则。
- GitHub issue/PR/release intents -> 由 `skills/check/SKILL.md` 处理。目标是 GitHub 时优先使用 `gh` 或可用的 GitHub 工具；非 GitHub 平台按项目公开上下文选择对应 CLI/API。
- Release/publish intents -> 由 `skills/check/SKILL.md` 从项目公开发布文档、脚本和 CI 中确认前置条件、产物和验证命令。

本地 durable memory / preview 可以作为可选私有上下文来理解用户偏好、旧决策和可迁移模式；它不属于公开项目约束，且必须用当前代码、日志、测试、文档或远端状态重新验证。

不要把证书路径、私钥文件名、token、个人机器路径或未公开的机器配置写进 Waza。
