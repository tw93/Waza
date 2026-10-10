<div align="center">
  <img src="https://raw.githubusercontent.com/tw93/Waza/main/assets/logo.svg" width="120" />
  <h1>Waza</h1>
  <p><b>Tw93의 엔지니어링 습관을 당신의 스킬로</b></p>
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

각각의 엔지니어링 습관이 독립된 스킬로 구성되어 있으며, 각 스킬은 참조 문서, 헬퍼 스크립트, 실제 실패 사례에서 얻은 노하우가 담긴 독립된 디렉터리입니다. Claude Code에서는 슬래시 명령어로 실행하며, Codex에서는 스킬 이름으로 직접 호출합니다.

| 스킬 | 실행 타이밍 | 역할 |
| :--- | :--- | :--- |
| [`/think`](skills/think/SKILL.md) | 새로운 코드를 작성하기 전 | 문제의 본질을 검증하고, 즉시 구현 가능한 완성도 높은 계획 수립 |
| [`/ui`](skills/ui/SKILL.md) | 프론트엔드 UI 구축 시 | 기본 템플릿에 기대지 않고 분명한 디자인 방향으로 UI를 만들며, 스크린샷을 활용한 시각적 반복도 지원 |
| [`/check`](skills/check/SKILL.md) | 작업 완료 후·머지 및 배포 전 | 프로젝트 규칙에 맞춰 변경 사항을 검토하고 결과를 검증하며, 승인된 배포와 유지보수 작업을 처리 |
| [`/hunt`](skills/hunt/SKILL.md) | 버그 및 리그레션 발생 시 | 수정 전에 근본 원인을 확정하고, 이전에 잘 되던 기능이 깨졌을 때는 특히 철저히 추적 |
| [`/write`](skills/write/SKILL.md) | 문서 작성 및 퇴고 시 | 중국어·영어 문장의 부자연스러운 AI 느낌을 없애고 매끄럽고 읽기 쉽게 다듬기 |
| [`/learn`](skills/learn/SKILL.md) | 낯선 분야를 깊이 조사할 때 | 수집·요약·개요·작성·퇴고·검토의 6단계 워크플로우로 체계적 리서치 |
| [`/read`](skills/read/SKILL.md) | 웹 링크나 PDF 문서를 읽을 때 | 핵심을 명확히 요약하거나 인용 및 저장에 적합한 깔끔한 Markdown 추출 |
| [`/health`](skills/health/SKILL.md) | 에이전트 설정 점검 시 | 에이전트 설정과 지침 드리프트를 진단하고, 먼저 가볍게 훑은 뒤 깊이 점검 |

## 설치 방법

**Claude Code, Codex, Cursor 및 기타 에이전트**

```bash
npx skills add tw93/Waza -a claude-code codex cursor -g -y
```

스킬은 공유 디렉터리인 `~/.agents/skills`에 저장됩니다. Claude Code는 심볼릭 링크로 연결되며, Codex, Cursor, Gemini CLI, Copilot, Amp, Kimi Code CLI 등 해당 디렉터리를 읽는 에이전트에서 자동으로 활성화됩니다. 독립 디렉터리를 사용하는 에이전트는 `-a` 뒤에 ID(예: `antigravity-cli`, `qwen-code`)를 지정하세요. 업데이트는 `npx skills update -g -y`로 실행합니다. AI 에이전트에게 직접 설치를 요청할 수도 있습니다:
> 다음 문서를 읽고 Waza를 설치해 줘: https://github.com/tw93/Waza/blob/main/llms.txt

**호스트 플러그인 방식** (네임스페이스 포함: `/waza:check`):

```bash
# Claude Code (업데이트: claude plugin update waza)
/plugin marketplace add tw93/Waza
/plugin install waza@waza

# Codex (업데이트: codex plugin marketplace upgrade waza 후 codex plugin add waza@waza)
codex plugin marketplace add tw93/Waza
codex plugin add waza@waza
```

**Claude Desktop**: [waza.zip](https://github.com/tw93/Waza/releases/latest/download/waza.zip)을 다운로드한 뒤 Customize > Skills > "+" > Create skill에서 업로드합니다. 업데이트할 때는 카드에서 "..." > Replace를 선택해 최신 ZIP을 다시 업로드하세요.

**Pi**: `pi install npm:@tw93/waza`, 업데이트는 `pi update npm:@tw93/waza`로 실행합니다.

## 스킬 연계 워크플로우

스킬 간의 조합은 자유롭습니다. 각 스킬은 지정된 결과를 달성하면 정지하지만, 명시적으로 승인된 워크플로우라면 매 단계마다 묻지 않고 자연스럽게 다음 작업으로 이어집니다.

**자주 쓰이는 워크플로우:**

- **새 기능 구현**: `/think`로 설계를 검증하고, 승인 후 구현한 뒤 `/check`로 최종 검토하고 머지
- **버그 해결**: `/hunt`로 원인을 규명하고, 수정한 뒤 `/check`로 변경 사항을 검토하고 필요하면 배포
- **리서치 및 작성**: `/read`로 자료를 모으고, `/learn`으로 체계화한 뒤 `/write`로 문장 다듬기

## 프로젝트 컨텍스트

Waza는 범용적인 엔지니어링 습관만을 제공합니다. `/check`는 런타임에 대상 저장소의 공개 정보(README, 패키지 파일, Makefile, CI 설정)와 작업 조건만을 읽으며, 비공개 경로나 자격 증명, 토큰에는 접근하지 않습니다. 리뷰 컨텍스트 템플릿은 [`skills/check/references/project-context.md`](skills/check/references/project-context.md)를 참고하세요.

## 추가 도구 및 규칙

curl URL은 최신 GitHub 릴리스 자산을 사용합니다. main의 최신 스크립트를 쓰려면 명령 앞에 `WAZA_REF=main`을 지정하세요.

### 상태 표시줄

Claude Code용 미니멀 상태 표시줄: 컨텍스트 윈도우, 5시간 한도, 7일 한도를 사용량에 따라 색으로 표시하며, 진행 막대나 군더더기는 없습니다.

<div align="center">
  <img src="https://raw.githubusercontent.com/tw93/Waza/main/assets/statusline.png" width="1000" />
</div>

```bash
(
  set -e
  WAZA_STATUSLINE_SCRIPT="$(mktemp -t waza-statusline.XXXXXX)"
  trap 'rm -f "$WAZA_STATUSLINE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-statusline.sh -o "$WAZA_STATUSLINE_SCRIPT"
  # 실행 전에 내용을 먼저 확인하세요: less "$WAZA_STATUSLINE_SCRIPT"
  bash "$WAZA_STATUSLINE_SCRIPT"
)
```

**Codex** 설정 (`~/.codex/config.toml`):

```toml
[tui]
status_line = ["model-with-reasoning", "current-dir", "context-used", "five-hour-limit", "weekly-limit"]
status_line_use_colors = true
```

Codex는 남은 한도를, 위의 Claude Code 상태 표시줄은 사용한 비율을 표시합니다(업스트림에서 아직 `five-hour-used` / `weekly-used`를 제공하지 않음).

### 선택적 규칙

선택적 규칙은 에이전트의 영구 지침에 설치하면 스킬을 호출하지 않을 때도 적용됩니다. Waza 스킬만 설치해서는 활성화되지 않습니다. 필요한 규칙을 복사해 실행하세요(Codex나 Antigravity에서는 `claude-code`를 `codex` 또는 `antigravity-cli`로 바꾸세요):

```bash
(
  set -e
  WAZA_RULE_SCRIPT="$(mktemp -t waza-rule.XXXXXX)"
  trap 'rm -f "$WAZA_RULE_SCRIPT"' EXIT
  curl -fL https://github.com/tw93/Waza/releases/latest/download/setup-rule.sh -o "$WAZA_RULE_SCRIPT"
  # 실행 전에 내용을 먼저 확인하세요: less "$WAZA_RULE_SCRIPT"

  # 영어 코칭: 프롬프트에 영어 실수가 있을 때 짧은 교정 팁 제공
  bash "$WAZA_RULE_SCRIPT" english claude-code

  # 안티패턴 방지: 임의 수정이나 불필요한 장황한 요약 방지
  bash "$WAZA_RULE_SCRIPT" anti-patterns claude-code

  # 스킬 라우팅: 관련 상황에서 Waza 스킬 우선 호출
  bash "$WAZA_RULE_SCRIPT" waza-routing claude-code

  # 명확한 일상 답변: ASD-STE100 기반의 간결하고 정확한 소통
  # Clarity는 main 브랜치에서 사용할 수 있으며 아직 정식 릴리스에는 포함되지 않았습니다
  WAZA_REF=main bash "$WAZA_RULE_SCRIPT" clarity claude-code
)
```

[Clarity](rules/clarity.md)는 ASD-STE100의 명확한 글쓰기 원칙을 가져오지만, 통제 영어 문법을 강요하거나 문체를 바꾸지는 않습니다. 명령을 다시 실행하면 설치된 규칙이 업데이트되며, 그 뒤 새 세션을 시작하세요. Codex는 `~/.codex/AGENTS.md`에 표시된 블록을 추가하고, Claude Code와 Antigravity는 규칙 파일을 설치합니다. 다른 도구에서는 규칙을 해당 도구의 영구 사용자 지정 지침에 복사하세요.

<div align="center">
  <img src="https://raw.githubusercontent.com/tw93/Waza/main/assets/clarity.png" width="1000" />
</div>

## Waza를 만든 이유

Waza(技, わざ)는 무술에서 끊임없이 연마하여 본능이 된 기술을 뜻합니다. 좋은 엔지니어는 코드만 쓰지 않습니다. 요구 사항을 따져 묻고, 근본 원인까지 디버깅하고, 자신의 변경 사항을 검토하고, 1차 자료를 읽습니다. AI는 이 모든 일을 해낼 수 있지만, 구조가 없으면 결과물이 평범하고 부정확한 쪽으로 흘러갑니다. Waza의 각 스킬은 목표 결과, 넘지 말아야 할 선, 결과 검증 방법만 정하고, 구체적인 경로는 모델이 고르게 둡니다. 모델이 좋아질수록 이 절제의 가치는 커집니다.

Superpowers나 gstack 같은 도구는 강력하지만 무겁고, 스킬도 설정도 너무 많습니다. Waza는 규모를 작게 유지합니다. 정말 중요한 습관만 담은 8개 스킬이 각자 한 가지 일과 분명한 실행 조건을 가집니다. 7개 프로젝트에서 300회 이상의 세션을 거치며 다듬었고, 모든 노하우는 실제 실패에서 나왔습니다. `/health` 스킬은 [이 글](https://tw93.fun/en/2026-03-12/claude.html)에서 소개한 Claude Code 6계층 프레임워크에서 출발했습니다.

[Kaku](https://github.com/tw93/Kaku)(書く)가 코드를 쓰고, [Waza](https://github.com/tw93/Waza)(技)가 습관을 다지고, [Kami](https://github.com/tw93/Kami)(紙)가 문서를 완성하는 3부작입니다. 가족으로 치면 Kaku는 아빠, Waza는 큰딸, Kami는 막내딸입니다.

## 삭제 방법

```bash
npx skills remove tw93/Waza -g
rm -f ~/.claude/statusline.sh
rm -f ~/.claude/rules/english.md
rm -f ~/.claude/rules/anti-patterns.md
rm -f ~/.claude/rules/waza-routing.md
rm -f ~/.claude/rules/clarity.md
```

상태 표시줄을 설치했다면 `~/.claude/settings.json`에서 `statusLine` 항목도 삭제하세요. Claude Desktop에서는 Customize > Skills에서 Waza를 삭제하세요. Codex에 규칙을 설치했다면 `~/.codex/AGENTS.md`에서 Waza 표시 블록을 제거하세요. Antigravity에서는 `~/.gemini/antigravity-cli/rules/`에서 선택한 규칙 파일을 삭제하세요. 다른 도구에 복사한 규칙은 해당 도구의 사용자 지정 지침에서 제거하세요. 규칙을 제거한 뒤에는 새 세션을 시작하세요.

## 후원 안내

- 가장 직접적인 응원은 유료 Mac 클리너 앱 [Mole for Mac](https://mole.fit)을 이용해 주시는 것입니다
- Waza가 도움이 되었다면 Star를 눌러 주시거나, [공유](https://twitter.com/intent/tweet?url=https://github.com/tw93/Waza&text=Waza%20-%20AI%20coding%20skills%20for%20the%20complete%20engineer.)해 주시거나, Issue나 PR을 남겨 주세요
- 고양이 탕위안(TangYuan)과 콜라(Coke)에게 <a href="https://cats.tw93.fun?name=Waza" target="_blank">간식 🥩</a>을 선물할 수도 있습니다

<details>
<summary>후원해 주신 분들 🐱</summary>
<br/>
<div align="center">
  <a href="https://cats.tw93.fun?name=Waza"><img src="https://cdn.jsdelivr.net/gh/tw93/sponsors@main/assets/sponsors.svg" width="1000" loading="lazy" /></a>
</div>
</details>

## 라이선스

MIT License. Please feel free to use and contribute to the development.
