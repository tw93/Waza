<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/2h/waza.svg" width="120" />
  <h1>Waza</h1>
  <p><b>익숙한 엔지니어링 습관을 AI 에이전트가 실행하는 스킬로</b></p>
  <p><a href="README.md">English</a> · <a href="README_CN.md">中文</a> · <a href="README_TW.md">繁體</a> · <a href="README_JA.md">日本語</a> · 한국어 · <a href="README_DE.md">Deutsch</a> · <a href="README_FR.md">Français</a></p>
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

## 스킬 목록

각각의 엔지니어링 습관이 독립된 스킬로 구성되어 있습니다. Claude Code 에서는 슬래시 명령어로 실행하며, Codex 에서는 스킬 이름으로 직접 호출합니다

| 스킬 | 실행 타이밍 | 역할 |
| :--- | :--- | :--- |
| [`/think`](skills/think/SKILL.md) | 새로운 코드를 작성하기 전 | 문제의 본질을 검증하고, 즉시 구현 가능한 완성도 높은 계획 수립 |
| [`/ui`](skills/ui/SKILL.md) | 프론트엔드 UI 구축 시 | 기본 템플릿을 지양하고, 실제 스크린샷을 기반으로 개성 있고 완성도 높은 UI 구축 |
| [`/check`](skills/check/SKILL.md) | 작업 완료 후·머지 및 배포 전 | 프로젝트 규칙에 맞춰 변경 사항을 꼼꼼히 검토하고 배포 절차 검증 |
| [`/hunt`](skills/hunt/SKILL.md) | 버그 및 리그레션 발생 시 | 짐작으로 수정하지 않고, 이전 작동 코드의 근본 원인을 철저히 추적 |
| [`/write`](skills/write/SKILL.md) | 문서 작성 및 퇴고 시 | 부자연스러운 AI 느낌을 없애고 매끄럽고 읽기 쉬운 문장으로 다듬기 |
| [`/learn`](skills/learn/SKILL.md) | 낯선 분야를 깊이 조사할 때 | 수집·요약·개요·작성·퇴고·검토의 6단계 워크플로우로 체계적 리서치 |
| [`/read`](skills/read/SKILL.md) | 웹 링크나 PDF 문서를 읽을 때 | 핵심을 명확히 요약하거나 인용 및 저장에 적합한 깔끔한 Markdown 추출 |
| [`/health`](skills/health/SKILL.md) | 에이전트 상태 점검 시 | 에이전트 설정과 프롬프트 드리프트를 진단하고 가볍게 상태 점검 |

각 스킬은 참조 문서, 헬퍼 스크립트, 실제 실패 사례에서 얻은 노하우가 담긴 독립된 디렉터리입니다

## 설치 방법

**Claude Code, Codex, Cursor 및 기타 에이전트**

```bash
npx skills add tw93/Waza -a claude-code codex cursor -g -y
```

AI 에이전트에게 직접 설치를 요청할 수도 있습니다:
> Install Waza for me by reading https://github.com/tw93/Waza/blob/main/llms.txt

스킬은 공유 디렉터리인 `~/.agents/skills` 에 저장됩니다. Claude Code 는 심볼릭 링크로 연결되며, Codex, Cursor, Gemini CLI, Copilot, Amp, Kimi Code CLI 등 해당 디렉터리를 읽는 에이전트에서 자동으로 활성화됩니다. 독립 디렉터리를 사용하는 에이전트는 `-a` 뒤에 ID(예: `antigravity-cli`, `qwen-code`)를 지정하세요. 업데이트는 `npx skills update -g -y` 로 실행합니다

**호스트 플러그인 방식**（네임스페이스 포함: `/waza:check`）：

```bash
# Claude Code（업데이트: claude plugin update waza）
/plugin marketplace add tw93/Waza
/plugin install waza@waza

# Codex（업데이트: codex plugin marketplace upgrade waza 후 codex plugin add waza@waza）
codex plugin marketplace add tw93/Waza
codex plugin add waza@waza
```

**Claude Desktop**：[waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip) 다운로드 후 Customize > Skills > "+" > Create skill 에서 업로드합니다. 업데이트 시 카드에서 "..." > Replace 를 선택해 최신 ZIP을 다시 업로드하세요

**Pi**：`pi install npm:@tw93/waza`, 업데이트는 `pi update npm:@tw93/waza`

## 스킬 연계 워크플로우

스킬 간의 조합은 자유롭습니다. 각 스킬은 지정된 결과를 달성하면 정지하지만, 명시적으로 승인된 워크플로우라면 매 단계마다 묻지 않고 자연스럽게 다음 작업으로 이어집니다

**자주 쓰이는 워크플로우:**

- **새 기능 구현**: `/think` 로 설계 검증 → 승인 후 구현 → `/check` 로 최종 검토 후 머지
- **버그 해결**: `/hunt` 로 원인 규명 → 수정 → `/check` 로 검증 후 배포
- **리서치 및 작성**: `/read` 로 자료 수집 → `/learn` 으로 체계화 → `/write` 로 문장 다듬기
- **디버깅 및 검증**: `/hunt` 로 근본 원인 파악 → 수정 → `/check` 로 변경 사항 검토

## 프로젝트 컨텍스트

Waza 는 범용적인 엔지니어링 습관만을 제공합니다. `/check` 는 런타임에 대상 저장소의 공개 정보(README, 패키지 파일, Makefile, CI 설정)와 작업 조건만을 읽으며, 비공개 경로나 토큰에는 접근하지 않습니다

## 추가 도구 및 규칙

### 상태 표시줄

Claude Code 용 미니멀 상태 표시줄: 컨텍스트 윈도우, 5시간 한도, 7일 한도 사용률을 색상으로 직관적으로 표시합니다

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

**Codex** 설정 (`~/.codex/config.toml`):

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "context-used", "five-hour-limit", "weekly-limit"]
status_line_use_colors = true
```

### 선택적 규칙

에이전트의 일상 대화 습관을 교정하는 선택 규칙입니다:

```bash
(
  set -e
  WAZA_RULE_SCRIPT="$(mktemp -t waza-rule.XXXXXX)"
  trap 'rm -f "$WAZA_RULE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh -o "$WAZA_RULE_SCRIPT"

  # 영어 코칭: 프롬프트에 영어 실수가 있을 때 짧은 교정 팁 제공
  bash "$WAZA_RULE_SCRIPT" english claude-code

  # 안티패턴 방지: 임의 수정이나 불필요한 장황한 요약 방지
  bash "$WAZA_RULE_SCRIPT" anti-patterns claude-code

  # 스킬 라우팅: 관련 상황에서 Waza 스킬 우선 호출
  bash "$WAZA_RULE_SCRIPT" waza-routing claude-code

  # 명확한 일상 답변: ASD-STE100 기반의 간결하고 정확한 소통
  WAZA_REF=main bash "$WAZA_RULE_SCRIPT" clarity claude-code
)
```

<div align="center">
  <img src="https://gw.alipayobjects.com/zos/k/24/vfkGOi.png" width="1000" />
</div>

## Waza를 만든 이유

Waza(技, わざ)는 무술에서 끊임없이 연마하여 본능이 된 기술을 뜻합니다.

좋은 엔지니어는 코딩만 잘하는 것이 아니라, 설계 검증, 근본 원인 분석, 변경 사항 자체 검토에 능숙합니다. AI 는 강력하지만 적절한 제약이 없으면 평범하고 두루뭉술한 결과물을 냅니다. Waza 는 목표와 원칙만을 명시하고, 구체적인 해결 경로는 모델의 판단에 맡깁니다.

비대한 도구 대신 실제로 중요한 8가지 핵심 습관에 집중했습니다. 300회 이상의 실전 세션을 거치며 다듬어졌습니다. [Kaku](https://github.com/tw93/Kaku)(코드 작성), [Waza](https://github.com/tw93/Waza)(습관 연마), [Kami](https://github.com/tw93/Kami)(문서 완성) 3부작의 일원입니다

## 삭제 방법

```bash
npx skills remove tw93/Waza -g
rm -f ~/.claude/statusline.sh
rm -f ~/.claude/rules/english.md
rm -f ~/.claude/rules/anti-patterns.md
rm -f ~/.claude/rules/waza-routing.md
rm -f ~/.claude/rules/clarity.md
```

## 후원 안내

- 가장 직접적인 응원은 유료 Mac 클리너 앱 [Mole for Mac](https://mole.fit) 을 이용해 주시는 것입니다
- Waza 가 도움이 되었다면 Star 나 공유를 부탁드립니다
- 고양이 탕위안(TangYuan)과 콜라(Coke)에게 <a href="https://cats.tw93.fun?name=Waza" target="_blank">간식 🥩</a> 을 선물할 수도 있습니다

<details>
<summary>후원해 주신 분들 🐱</summary>
<br/>
<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>
</details>

## 라이선스

MIT License
