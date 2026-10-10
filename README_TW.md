<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/2h/waza.svg" width="120" />
  <h1>Waza</h1>
  <p><b>把 Tw93 的工程習慣，變成你的技能</b></p>
  <p><a href="README.md">English</a> · <a href="README_CN.md">中文</a> · 繁體 · <a href="README_JA.md">日本語</a> · <a href="README_KR.md">한국어</a> · <a href="README_DE.md">Deutsch</a> · <a href="README_FR.md">Français</a></p>
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

每個工程習慣對應一個獨立技能，Claude Code 輸入斜線指令即可觸發，Codex 則直接依技能名稱呼叫

| 技能 | 觸發時機 | 它做什麼 |
| :--- | :--- | :--- |
| [`/think`](skills/think/SKILL.md) | 動手寫新程式碼前 | 深入推敲方案並壓測設計，產出決策完備且能直接落地的執行計畫 |
| [`/ui`](skills/ui/SKILL.md) | 建構前端介面 | 產出有明確設計方向的介面，不套預設模板，也能拿截圖反覆迭代視覺 |
| [`/check`](skills/check/SKILL.md) | 任務完成後，合併或發布前 | 結合專案規範審查改動、驗證結果，並在你授權後處理發布和維護動作 |
| [`/hunt`](skills/hunt/SKILL.md) | 遇到 Bug 或異常行為 | 動手修之前徹底查清根本原因，特別是面對以前正常運作的功能 |
| [`/write`](skills/write/SKILL.md) | 撰寫或修改文案 | 改寫中英文本使其自然流暢，剔除生硬公式化的套話與機器感 |
| [`/learn`](skills/learn/SKILL.md) | 探索完全陌生的領域 | 按六階段完整研究流程，把陌生領域系統消化並沉澱成文 |
| [`/read`](skills/read/SKILL.md) | 閱讀網頁連結或 PDF | 快速提取精練摘要，或轉成方便引用歸檔的乾淨 Markdown |
| [`/health`](skills/health/SKILL.md) | 稽核 Agent 設定 | 排查 Agent 設定與指令漂移，先輕量概覽再深入診斷 |

每個技能都是一個獨立目錄，內建參考文件、輔助腳本以及真實踩坑沉澱的避坑指南

## 安裝

**Claude Code、Codex、Cursor 與其他 Agent**

```bash
npx skills add tw93/Waza -a claude-code codex cursor -g -y
```

也可以直接告訴你的 Agent 幫你安裝：
> 閱讀 https://github.com/tw93/Waza/blob/main/llms.txt 幫我安裝 Waza

技能統一存放在 `~/.agents/skills` 共享目錄，Claude Code 透過符號連結接入，Codex、Cursor、Gemini CLI、Copilot、Amp、Kimi Code CLI 以及其他能讀取該目錄的 Agent 都會自動載入這 8 個技能。擁有獨立技能目錄的 Agent 可在 `-a` 後指定其 ID，比如 `antigravity-cli` 或 `qwen-code`，後續透過 `npx skills update -g -y` 保持更新

**宿主外掛方式**，如果你更習慣使用宿主自有的更新指令（技能帶有命名空間前綴，如 `/waza:check`）：

```bash
# Claude Code（更新指令：claude plugin update waza）
/plugin marketplace add tw93/Waza
/plugin install waza@waza

# Codex（更新指令：codex plugin marketplace upgrade waza，然後 codex plugin add waza@waza）
codex plugin marketplace add tw93/Waza
codex plugin add waza@waza
```

**Claude Desktop**：下載 [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip)，開啟 Customize > Skills > "+" > Create skill 並上傳壓縮檔，更新時點選卡片上的 "..." 選擇 Replace 再上傳最新的 ZIP 即可

**Pi**：`pi install npm:@tw93/waza`，透過 `pi update npm:@tw93/waza` 更新

## 技能串聯

技能串聯由你作主，每個技能跑完既定目標就停下，拿到明確授權後會自動接力完成整套流程，不需要在每個環節反覆確認

**常見工作流程：**

- **做新功能**：`/think` 想透方案，確認後動手實作，再用 `/check` 把關合併
- **排查修復**：`/hunt` 查清根因，動手修復，再用 `/check` 驗證並發布
- **研究成文**：`/read` 讀取素材，`/learn` 消化梳理，`/write` 潤色文字
- **排查驗證**：`/hunt` 定位根因，動手改完，再用 `/check` 審查改動

## 專案上下文

Waza 只沉澱通用的工程習慣，`/check` 執行時只從目標儲存庫公開的專案檔案與你的任務要求提煉約束，比如 README、套件清單、Makefile 和 CI 設定，絕不讀取私有路徑、憑證或 Token，具體上下文模板可參考 [`skills/check/references/project-context.md`](skills/check/references/project-context.md)

## 附加工具與規則

### 狀態列

Claude Code 極簡狀態列：顯示上下文視窗、5 小時配額與 7 天配額，按用量著色，沒有進度條，沒有視覺噪音

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/y9/RUgevg.png" width="1000" />
</div>

```bash
(
  set -e
  WAZA_STATUSLINE_SCRIPT="$(mktemp -t waza-statusline.XXXXXX)"
  trap 'rm -f "$WAZA_STATUSLINE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-statusline.sh -o "$WAZA_STATUSLINE_SCRIPT"
  # 可以先檢查腳本內容：less "$WAZA_STATUSLINE_SCRIPT"
  bash "$WAZA_STATUSLINE_SCRIPT"
)
```

**Codex** 原生支援狀態列欄位，直接新增至 `~/.codex/config.toml`：

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "context-used", "five-hour-limit", "weekly-limit"]
status_line_use_colors = true
```

Codex 顯示剩餘額度，上方 Claude Code 狀態列顯示已用百分比（上游暫未提供 `five-hour-used` / `weekly-used`）

### 選用規則

選用規則用於補充技能之外的長期習慣，寫入 Agent 的持久化指令後生效，只安裝技能預設不會開啟，按需複製執行即可（在對應 Agent 上將 `claude-code` 替換為 `codex` 或 `antigravity-cli`）：

```bash
(
  set -e
  WAZA_RULE_SCRIPT="$(mktemp -t waza-rule.XXXXXX)"
  trap 'rm -f "$WAZA_RULE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh -o "$WAZA_RULE_SCRIPT"
  # 可以先檢查腳本內容：less "$WAZA_RULE_SCRIPT"

  # 英文寫作教練：Prompt 中有英文表達錯誤時，在結尾追加一條簡短的 😇 糾錯建議
  bash "$WAZA_RULE_SCRIPT" english claude-code

  # 行為防錯守則：全域常駐約束（先看再改、不隨意擴大範圍、不主動輸出冗餘總結）
  bash "$WAZA_RULE_SCRIPT" anti-patterns claude-code

  # 技能路由提示：提示非 Claude 宿主在命中對應場景時優先呼叫 Waza 技能
  bash "$WAZA_RULE_SCRIPT" waza-routing claude-code

  # 日常清晰表達：術語統一、條件明確、保留不確定性
  # Clarity 規則目前在 main 分支可用，尚未進入正式版
  WAZA_REF=main bash "$WAZA_RULE_SCRIPT" clarity claude-code
)
```

[Clarity](rules/clarity.md) 借鑑了 ASD-STE100 的清晰寫作原則，不會強加受控英文語法，也不會改變你的個人表達風格。重新執行指令即可更新，開一個新會話後生效。Codex 會在 `~/.codex/AGENTS.md` 寫入標記塊，Claude Code 與 Antigravity 則安裝為規則檔案，其他工具把規則複製進各自的自訂指令即可

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/24/vfkGOi.png" width="1000" />
</div>

下載腳本預設使用最新的 GitHub Release 資源，想用 main 上最新的腳本，可以在指令前加 `WAZA_REF=main`

## 為什麼做 Waza

Waza（技，わざ）在日本武術裡指招式，是一個動作反覆練到變成本能的那種功夫。好工程師不只是寫程式碼，動手前會反覆推敲需求，排查時會追到根因，提交前會自己過一遍 diff，查資料也會回到第一手來源。這些事 AI 都能做，但沒有結構約束，輸出就會滑向泛泛而談、不夠精確。每個 Waza 技能只寫清要什麼結果、哪些紅線不能碰、結果怎麼驗證，具體路徑交給模型自己選，模型越強，這份克制就越值錢

Superpowers、gstack 這類工具很強，但也很重，技能太多，設定也太多。Waza 只留 8 個技能，每個只管一件事、觸發條件清楚，都是在 7 個專案、300 多次真實會話裡磨出來的，每條避坑指南都對應一次真實翻車。`/health` 技能就是從[這篇文章](https://tw93.fun/2026-03-12/claude.html)裡講的 Claude Code 六層框架長出來的

Waza 和另外兩款工具組成三部曲，[Kaku](https://github.com/tw93/Kaku)（書く）負責寫程式碼，[Waza](https://github.com/tw93/Waza)（技）負責磨習慣，[Kami](https://github.com/tw93/Kami)（紙）負責出文件，可以把它們看成一家人，Kaku 是爸爸，Waza 是姊姊，Kami 是妹妹

## 移除

```bash
npx skills remove tw93/Waza -g
rm -f ~/.claude/statusline.sh
rm -f ~/.claude/rules/english.md
rm -f ~/.claude/rules/anti-patterns.md
rm -f ~/.claude/rules/waza-routing.md
rm -f ~/.claude/rules/clarity.md
```

Claude Desktop 直接在 Customize > Skills 中刪除 Waza，Codex 規則安裝從 `~/.codex/AGENTS.md` 中移除對應的 Waza 標記塊，Antigravity 從 `~/.gemini/antigravity-cli/rules/` 刪除對應規則檔案，其他工具從自訂指令中移除即可，移除後開啟新會話生效

## 支持

- 最直接的支持方式是購買 [Mole for Mac](https://mole.fit)，這是我開發的 Mac 清理應用
- 如果 Waza 對你有幫助，歡迎點個 Star，[分享給朋友](https://twitter.com/intent/tweet?url=https://github.com/tw93/Waza&text=Waza%20-%20AI%20coding%20skills%20for%20the%20complete%20engineer.)，或者提交 Issue 與 PR
- 我養了兩隻貓，湯圓和可樂，如果 Waza 幫到了你，可以給牠們加個 <a href="https://cats.tw93.fun?name=Waza" target="_blank">罐頭 🥩</a>

<details>
<summary>已經贊助過的可愛朋友們 🐱</summary>
<br/>
<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>
</details>

## 授權條款

MIT License，歡迎自由使用和參與貢獻
