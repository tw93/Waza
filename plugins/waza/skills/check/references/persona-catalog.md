# Specialist Reviewer Activation Catalog

The orchestrator reads the full diff and uses judgment (not keyword matching) to decide which specialists to activate. This catalog defines the signals to reason about.

## Review Coordination

Use the activation signals below. When the environment has an agent or sub-agent facility, launch all activated specialists in parallel, each with the full diff and its own persona brief. If no parallel reviewer facility exists, run the specialist passes sequentially in the same session.

Merge findings: when two specialists flag the same code location, keep the higher severity and note cross-reviewer agreement. Findings on different code locations are never duplicates even if they share a theme.

Every specialist finding is a claim to verify, not a fact to act on. For HIGH and CRITICAL claims, when the agent facility allows it, spawn one independent skeptic per finding whose only brief is to refute it against the actual code; a finding the skeptic refutes on direct read is dropped or downgraded regardless of which persona raised it. Without the facility, run the skeptic pass yourself: re-read the cited code this turn and confirm the claim is real and live, not already handled elsewhere, not consistent-by-design, not a latent-only risk labeled as a live bug. Parallel reviewers over-report from name-based inference and partial context; drop what dissolves on direct read, and cite the verification path before routing anything to Autofix or sign-off.

## Conditional Specialists

### Security Reviewer

**Agent file:** `agents/reviewer-security.md`
**Activate at:** Standard or Deep depth

Activate when the diff changes code an attacker could reach or influence: trust-boundary input, auth or crypto, credentials, or query/shell/path construction.

**Do not activate** for: pure UI changes, config file updates, test-only changes, documentation.

### Architecture Reviewer

**Agent file:** `agents/reviewer-architecture.md`
**Activate at:** Standard or Deep depth

Activate when the diff changes how modules relate: boundaries, public APIs or signatures, cross-module dependencies, or a major dependency, rather than logic inside one module.

**Do not activate** for: single-file bug fixes, test additions, style changes, documentation updates.

## Adversarial Pass (Deep only)

No dedicated agent file. When the environment has an agent facility, the orchestrator runs the four angles as parallel agents, each blind to the others' findings; otherwise it runs them as an extra reasoning pass after all findings are collected.

**Activate at:** Deep depth only; the Deep criteria live in SKILL.md's Scope table.

Adversarial pass asks: "If I wanted to break this system through this specific diff, what would I do?"

Four attack angles:
1. **Assumption violation** -- What does this code assume is always true? (format, ordering, range) What happens when it is not?
2. **Composition failures** -- What breaks when this new code interacts with the existing system under concurrent load or partial failure?
3. **Cascade construction** -- What sequence of valid operations leads to an invalid state?
4. **Abuse cases** -- What happens on the 1000th request, during a deployment, with two users editing the same resource simultaneously?

Report adversarial findings with the evidence that supports them; SKILL.md's Finding Quality Gate decides what survives.
