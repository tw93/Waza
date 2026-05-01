---
name: refactor
description: "Restructures and cleans up existing code without changing its external behavior. Focuses on readability, DRY principles, complexity reduction, and naming conventions."
when_to_use: "refactor this, clean up this code, extract method, simplify this, reduce complexity, make it readable, 重构, 清理代码"
metadata:
  version: "1.0.0"
---

# Refactor: Restructure Without Breaking

Prefix your first line with 🧹 inline, not as its own paragraph.

Refactoring changes how code is written, not what it does. Do not add new features, change external APIs, or alter behavior during a refactor unless explicitly approved.

## Before You Start

- Confirm the working path and locate the target file(s).
- Verify if automated tests exist for the target code. If none exist, flag this immediately. "There are no tests covering this code. Refactoring is high-risk. Proceed anyway?" Wait for approval.
- Run the code or tests if possible to ensure a baseline working state.

## Identify the Smell

Do not blindly rewrite code. Identify the specific "code smell" you are targeting first.
State the problem clearly:
- Is the function too long? (Extract Method)
- Are there duplicate code blocks? (DRY)
- Is cyclomatic complexity too high (too many `if/else` or loops)? (Simplify Conditionals)
- Are variable names confusing or misleading? (Rename)

Give one recommended refactoring approach in 2-3 sentences. Name the smell and the technique to fix it.

## Execution Rules

1. **One Thing At A Time:** Apply exactly one primary refactoring technique at a time. Do not mix extracting methods with renaming variables across the entire file unless it's a very small script.
2. **Incremental Changes:** For files larger than 100 lines, do not attempt a full rewrite in one go. Refactor one logical block, verify it, then move to the next.
3. **Preserve Comments:** Do not delete existing comments unless the refactor makes them completely irrelevant. Update comments if the logic structure changes.
4. **No Feature Creep:** If you spot a bug or a missing feature while refactoring, note it down but **do not fix it** during the refactoring pass. Refactoring and bug-fixing are separate tasks.

## Gotchas

| What happened | Rule |
|---------------|------|
| Changed a public method signature without updating callers | Never change external APIs during a standard refactor unless asked |
| Added error handling that wasn't there before | No feature creep. Keep the exact same behavior, including failures |
| Rewrote a 500-line file in one pass and broke it | Refactor incrementally. Extract one piece at a time |
| Refactored code without tests and introduced a subtle bug | Always warn if tests are missing before starting |

## Output

**Refactoring Summary:**
- **Target:** The file or function that was refactored.
- **Smell Identified:** What was wrong (e.g., duplicated logic).
- **Techniques Applied:** What was done (e.g., extracted to a helper function).
- **Risk Level:** Low/Medium/High (based on test coverage and complexity).

After completing the refactor, ask the user to verify the behavior or run tests before continuing. Stop.
