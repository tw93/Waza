<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/2h/waza.svg" width="120" />
  <h1>Waza</h1>
  <p><b>熟練のエンジニアリング習慣を、AIが実行できるスキルに</b></p>
  <p><a href="README.md">English</a> · <a href="README_CN.md">中文</a> · <a href="README_TW.md">繁體</a> · 日本語 · <a href="README_KR.md">한국어</a> · <a href="README_DE.md">Deutsch</a> · <a href="README_FR.md">Français</a></p>
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

## スキル一覧

それぞれのエンジニアリング習慣が独立したスキルとして用意されています。Claude Code ではスラッシュコマンドを入力、Codex ではスキル名を指定して呼び出します

| スキル | トリガーのタイミング | 役割 |
| :--- | :--- | :--- |
| [`/think`](skills/think/SKILL.md) | 新しいコードを書く前 | 要件と設計を検証し、そのまま実装可能な意思決定済みの計画を作成 |
| [`/ui`](skills/ui/SKILL.md) | フロントエンドUI構築時 | デフォルトのテンプレートを避け、実画面のスクリーンショットを元に洗練されたUIを構築 |
| [`/check`](skills/check/SKILL.md) | 実装完了後・マージやリリース前 | プロジェクト規約に基づいて差分を検証し、承認されたリリース作業を実行 |
| [`/hunt`](skills/hunt/SKILL.md) | バグやデグレの発生時 | 原因を推測せず、以前正常に動いていたコードの根本原因を徹底的に特定 |
| [`/write`](skills/write/SKILL.md) | 文章の執筆や推敲時 | 機械的なAI感を排除し、自然で読みやすい文章（日英）にリライト |
| [`/learn`](skills/learn/SKILL.md) | 未知の分野の調査時 | 収集・要約・構成・執筆・推敲・レビューの6段階で体系的にリサーチ |
| [`/read`](skills/read/SKILL.md) | WebリンクやPDFの閲覧時 | 要点を簡潔にまとめるか、引用や保存に適したクリーンなMarkdownを出力 |
| [`/health`](skills/health/SKILL.md) | エージェントの状態監査時 | エージェント設定や指示の乖離を診断し、トークン消費を抑えながら検査 |

各スキルは独立したディレクトリになっており、リファレンスドキュメント、補助スクリプト、実運用で得た回避策が同梱されています

## インストール

**Claude Code、Codex、Cursor、その他のエージェント**

```bash
npx skills add tw93/Waza -a claude-code codex cursor -g -y
```

AIエージェントに直接インストールを依頼することも可能です：
> 阅读 https://github.com/tw93/Waza/blob/main/llms.txt 帮我安装 Waza

スキルは共通の `~/.agents/skills` ディレクトリに保存されます。Claude Code はシンボリックリンク経由で連携し、Codex、Cursor、Gemini CLI、Copilot、Amp、Kimi Code CLI など、このディレクトリを読み込む各エージェントで自動的に利用可能になります。専用ディレクトリを持つエージェントは `-a` の後にID（例：`antigravity-cli`、`qwen-code`）を指定してください。更新は `npx skills update -g -y` で行います

**ホストのプラグイン機能を利用する場合**（スキル名に名前空間が付きます：`/waza:check`）：

```bash
# Claude Code（更新：claude plugin update waza）
/plugin marketplace add tw93/Waza
/plugin install waza@waza

# Codex（更新：codex plugin marketplace upgrade waza、その後 codex plugin add waza@waza）
codex plugin marketplace add tw93/Waza
codex plugin add waza@waza
```

**Claude Desktop**：[waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip) をダウンロードし、Customize > Skills > "+" > Create skill からZIPをアップロードします。更新時はカードの "..." から Replace を選択し、最新のZIPを再度アップロードしてください

**Pi**：`pi install npm:@tw93/waza`、更新は `pi update npm:@tw93/waza`

## スキルの連携

スキルの組み合わせは自由です。各スキルは要求された成果物を生成すると停止しますが、明確に承認されたワークフローであれば確認を挟まずにスムーズに次のステップへ引き継がれます

**一般的なワークフロー：**

- **新機能の開発**：`/think` で設計を固める → 承認後に実装 → `/check` でレビューしてマージ
- **不具合の修正**：`/hunt` で原因特定 → 修正 → `/check` で検証してリリース
- **調査と執筆**：`/read` で資料収集 → `/learn` で体系化 → `/write` で文章を磨く
- **デバッグと検証**：`/hunt` で根本原因を特定 → 修正 → `/check` で変更差分をレビュー

## プロジェクトコンテキスト

Waza は汎用的なエンジニアリングの型のみを提供します。`/check` は実行時に対象リポジトリの公開情報（README、パッケージ定義、Makefile、CI設定）とタスク要件を読み取るため、秘密鍵やトークンなどの非公開情報にアクセスすることはありません

## 追加ツールとルール

### ステータスライン

Claude Code 向けのミニマルなステータスライン：コンテキストウィンドウ、5時間制限、7日間制限の使用率を色分け表示し、余計なノイズを排除します

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/y9/RUgevg.png" width="1000" />
</div>

```bash
(
  set -e
  WAZA_STATUSLINE_SCRIPT="$(mktemp -t waza-statusline.XXXXXX)"
  trap 'rm -f "$WAZA_STATUSLINE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-statusline.sh -o "$WAZA_STATUSLINE_SCRIPT"
  bash "$WAZA_STATUSLINE_SCRIPT"
)
```

**Codex** は標準でステータスライン表示に対応しています。`~/.codex/config.toml` に追加してください：

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "context-used", "five-hour-limit", "weekly-limit"]
status_line_use_colors = true
```

### オプションルール

日常のやりとりに適用できるルールです。必要なものをコピーして実行してください：

```bash
(
  set -e
  WAZA_RULE_SCRIPT="$(mktemp -t waza-rule.XXXXXX)"
  trap 'rm -f "$WAZA_RULE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh -o "$WAZA_RULE_SCRIPT"

  # 英語コーチング：プロンプトに英語の誤りがある場合、末尾に短いアドバイスを追加
  bash "$WAZA_RULE_SCRIPT" english claude-code

  # アンチパターン防御：勝手なコード変更や不要な要約の出力を防止
  bash "$WAZA_RULE_SCRIPT" anti-patterns claude-code

  # スキルルーティング：該当する場面で Waza スキルを優先的に呼び出すよう指示
  bash "$WAZA_RULE_SCRIPT" waza-routing claude-code

  # 明確な回答ルール：ASD-STE100 の原則に基づくわかりやすい日常対話
  WAZA_REF=main bash "$WAZA_RULE_SCRIPT" clarity claude-code
)
```

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/24/vfkGOi.png" width="1000" />
</div>

## 開発の背景

Waza（技、わざ）は武道における技術や鍛錬を意味します。

優れたエンジニアはコードを書くだけでなく、事前の設計検証、根本原因の追求、差分の自己レビューを欠かしません。AI は高い出力を持ちますが、適切な制約がなければ凡庸な成果物になりがちです。Waza はゴールと境界条件を定め、具体的なアプローチはモデルの推論に委ねます。

無駄な機能を削ぎ落とし、本当に価値のある 8 つの習慣に絞り込みました。300 以上のセッションと実戦から得た知見が凝縮されています。[Kaku](https://github.com/tw93/Kaku)（コードを書く）、[Waza](https://github.com/tw93/Waza)（習慣を磨く）、[Kami](https://github.com/tw93/Kami)（ドキュメントを作る）の三部作として構成されています

## アンインストール

```bash
npx skills remove tw93/Waza -g
rm -f ~/.claude/statusline.sh
rm -f ~/.claude/rules/english.md
rm -f ~/.claude/rules/anti-patterns.md
rm -f ~/.claude/rules/waza-routing.md
rm -f ~/.claude/rules/clarity.md
```

## サポート

- 最も直接的な支援方法は、Mac クリーナーアプリ [Mole for Mac](https://mole.fit) の購入です
- Waza が役に立った場合は、Star や共有をお願いします
- 飼い猫の「湯円（TangYuan）」と「コーラ（Coke）」に <a href="https://cats.tw93.fun?name=Waza" target="_blank">おやつ 🥩</a> をご馳走することもできます

<details>
<summary>スポンサー一覧 🐱</summary>
<br/>
<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>
</details>

## ライセンス

MIT License
