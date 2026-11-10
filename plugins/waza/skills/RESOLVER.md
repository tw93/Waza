# Waza Skill Resolver

## Shared Output Marker

所有技能都沿用同一个输出约定：首行内联带上 `🥷`，不要单独起段。这个约定写在各自的 `SKILL.md` 里，`scripts/verify_skills.py` 也会校验它。

触发词到技能的路由表。Claude Code 通过每个 SKILL.md 的 `description` 自动匹配，这份文档是给人看的集中索引，也是 `scripts/verify_skills.py` 的校验依据。改 SKILL.md 的适用范围时，同步改这里。

> **Read the skill file before acting.** 两个技能都可能匹配时，两个都读。它们设计成可串联（例：`/think` → 实现 → `/check`）。

## 按工作流阶段分路

### Pre-build（动手前）

| 触发 | 技能 |
|------|------|
| 新功能 / 架构决策 / "怎么设计" / "应该用什么方案" / "有没有必要" / "值不值得" / 商业化/产品 pivot / 需要可执行计划或 handoff | `skills/think/SKILL.md` |
| UI / 组件 / 页面 / 视觉界面 / 前端 / 截图里说"丑"、"不清晰"、"很怪" / 真实截图视觉 polish | `skills/ui/SKILL.md` |

### Post-build（交付前）

| 触发 | 技能 |
|------|------|
| 实现完成 / 合并前 / "review 一下" / "看看这段代码" / release gate / 生成产物检查 / safety sink 审查 / `code-review` | `skills/check/SKILL.md` |
| release / publish / push / release reaction / 发布 / 提交 / 关闭 issue / 发布前检查 / "值得发布了吗" / 发布表情 / registry/appcast/asset 检查 | `skills/check/references/mode-ship.md` |
| review issue / review PR / triage / 批量处理 / "看看有没有 issue" / close issue | `skills/check/references/mode-triage.md` |
| audit / 项目体检 / 项目评分 / 给项目打分 / 深入分析项目代码 / scorecard / linus 风格 review | `skills/check/references/mode-audit.md` |

### Diagnostic（出问题了）

| 触发 | 技能 |
|------|------|
| 报错 / 崩溃 / 测试失败 / 行为异常 / "为什么不工作" / 以前是好的 / 回归 / 截图回归 / 反复修不好 / stale cache / 队列或生成物边界 | `skills/hunt/SKILL.md` |
| Claude/Codex/Pi 忽略指令 / hook 失灵 / MCP 异常 / Codex 或 Pi 配置 / agent instructions / 配置审计 / AI coding 腐化 / 精简规则 / 精简 skills / 规则瘦身 | `skills/health/SKILL.md` |

### Content（内容进出）

| 触发 | 技能 |
|------|------|
| 请求读取、抓取、引用、转换或保存网页链接或 PDF / "看一下这个", "读一下这个" / 内置搜索结果单薄时换 DeepSeek 搜索 | `skills/read/SKILL.md` |
| 写作 / 改稿 / 润色 / 去 AI 味（中英文） / 本地化文案 / 多语言产品文案 / 推特推文 / 社交媒体文案 / launch copy / release notes 文案 | `skills/write/SKILL.md` |
| 文档审阅 / 白皮书 / release notes prose 审核 / "审稿" / "check this document" | `skills/write/SKILL.md` (Document Review Mode) |
| 技术说明改写 / 指令消歧 / 安装步骤、错误提示、工具描述的措辞 / "clarify instructions" / "technical writing" | `skills/write/SKILL.md` 加载 `references/write-technical.md`，只处理文字，提示词设计与代码行为不在此模式内 |
| 深度研究一个陌生领域 / 六阶段研究到成稿 / 一批材料沉淀成文章 | `skills/learn/SKILL.md` |

## Disambiguation（歧义消解）

多个技能都可能匹配时按以下规则：

1. **最具体优先**：`/ui` 比 `/think` 更具体（仅限 UI 决策）。用户说"帮我设计登录页"时优先 `/ui`。
2. **URL 按内容类型二次分流**：用户请求读取 URL 内容时，先走 `/read` 取回 Markdown，再完成用户要求的总结或分析，长文研究性素材可继续交给 `/learn`。
3. **改错 vs review**：代码已经交付或走到 PR → `/check`；代码跑不通或行为错了 → `/hunt`。两者都可能匹配"帮我看看"，按"有没有具体错误现象"判断。
4. **配置/维护性异常 vs 代码错误**：Claude/Codex 本身不听话、hook 不触发、MCP 掉链子、AGENTS/CLAUDE/config.toml 漂移、`/health` 消耗 token、AI coding 腐化、上下文混乱、验证缺失或验证命令失真 → `/health`；用户写的代码抛异常 → `/hunt`。
5. **发布动作 vs 发布文案**：要写 release notes / changelog → `/write`；要提交、打 tag、publish、push、上传 release asset、补 GitHub release reactions、回复/关闭 issue → `/check`。
6. **截图审美 vs 截图回归**：截图里说"丑/不好看/不清晰"且是审美校准 → `/ui`；截图证明以前好的现在坏了、渲染错、状态错、生成物错 → `/hunt`。
7. **长文产出 vs 润色**：从零到成稿 → `/learn`；已有稿子要改 → `/write`。
8. **判断 vs 调试**：报错/异常/不工作 → `/hunt`；有没有必要/该不该保留/值不值得 → `/think` Evaluation Mode。
9. **质量改善 vs 调试**：已有可审 diff、要改善代码质量且没有报错 → `/check`；有具体报错或回归 → `/hunt`。
10. **需求包 vs issue 队列**：两个技能都有 Triage Mode。对象是还没实施的一批诉求/截图（判断接受与否）→ `/think` Triage Mode；对象是仓库里已存在的 issue/PR（处置、回复、关闭）→ `/check` Triage Mode。
11. **兜底**：两个都模糊时读两个 SKILL.md 的 "Not for" 段，用排除法；还是模糊就问用户。

## Chaining（常见串联）

技能边界用于分工，不缩小用户已授权的任务。单项请求不自动扩大；同一请求明确包含多个技能的工作时，按对应技能或现有能力继续完成，共用完成清单，不在内部交接点再次索要授权。提交、发布等动作仍需其对应授权。

- `/think` 出方案 → **用户说"实现"** → 实施 → **用户说"/check"** → `/check` 把关
- `/think` 出可执行计划 → **用户说"Implement the plan / 可以干 / 直接改"** → 按计划实施，不重新争论方向
- `/hunt` 修复 issue → **用户说"发布 / push / 关闭 issue"** → `/check` 做发布前检查和收尾
- `/read` 取回多篇 URL → **用户说"/learn"** → `/learn` 综合成文；如果同一回合已经明确要求总结或分析，`/read` fetch 后直接满足该请求
- `/learn` 出初稿 → **用户说"/write"** → `/write` 去 AI 味
- `/hunt` 定位根因 → **用户说"修"** → 修完 → **用户说"/check"** → `/check` 确认没副作用
- `/health` 发现 skill 配置问题 → **用户说"修"** → 修完 → **用户说"/health"** → 再跑一次 `/health`
