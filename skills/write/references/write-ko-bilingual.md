# 한영 혼용 및 대역어 규칙 (Bilingual & Terminology Rules)

## 1. 한영 혼용 기준
- IT 기술 용어, 고유 명사, 프레임워크 이름은 영어 그대로 표기하거나 인라인 코드(` `)를 사용합니다.
- 불필요하게 억지 한글화(예: interface -> 접점)를 하지 않습니다.
- 한글 뒤에 괄호로 영어를 병기하는 방식(예: 라우팅(routing))은 꼭 필요한 최초 1회로 제한합니다.

## 2. 고정 대역어 (Fixed terminology)
- Fine-tuning -> 미세 조정
- Refactoring -> 리팩토링 (리팩터링보다 통용됨)
- Deploy -> 배포
- Deprecated -> 지원 종료 / 폐기 예정
- Backward compatibility -> 하위 호환성
- Boilerplate -> 보일러플레이트
- Endpoint -> 엔드포인트

## 3. 한영 병렬 릴리즈 노트 포맷 (Bilingual Release Notes)
- 글로벌 사용자를 위한 릴리즈 노트 작성 시, 영어 블록을 먼저 배치하고 이어서 한국어 블록을 배치합니다.
- 영어와 한국어 내용은 1:1로 대응되어야 하지만, 직역하지 않고 각 언어에 맞는 가장 자연스러운 문투를 사용해야 합니다.

예시:
```markdown
### Changelog

1. **Feature**: Added concise rule support.
2. ...

### 업데이트 내용

1. **기능**: 간결한 규칙 지원 추가.
2. ...
```
