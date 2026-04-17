---
name: veritas
description: A five-pillar builder and guardrail for AI-assisted software work. Auto-activates when the user or the assistant is about to plan a feature, design a UI, execute a phase, write or debug tests, assert facts about code, run destructive operations, pause, or resume. Routes each turn to exactly one pillar — plan, design, execute, verify, or guardrail — with a shared persistent state directory (.veritas/) containing a provenance DAG of claims, a hash-chained action log, a canonical session scroll, and a decision journal. Explicit slash commands are also available: /plan, /design, /execute, /verify, /gate, /ground, /handoff, /resume. Triggers on verbs like plan, PRD, break this down, design, palette, build, ship, TDD, debug, verify, check, is it safe to, delete, drop, force push, rm -rf, migrate, rollback, handoff, and resume.
version: 1.0.0
license: MIT
---

# Veritas — an umbrella builder and guardrail

Veritas routes the current turn to one of five pillars, shares state across all of them, and refuses to fabricate. It replaces five disconnected concerns — planning, design, execution, verification, safety — with one surface that carries provenance between them.

## The five pillars

| Pillar | Activates when | Slash | Produces |
|---|---|---|---|
| [**plan**](pillars/plan.md) | Feature goal with no written plan | `/plan` | Brainstorm + PRD + architecture + stories; assumptions logged as unverified claims |
| [**design**](pillars/design.md) | UI/UX brief, design system, or frontend phase starting | `/design` | Grounded design system (colors with contrast, type, spacing, components, a11y notes) |
| [**execute**](pillars/execute.md) | Plan ready, next action is code | `/execute` | Atomic commits, per-step risk gate, hash-chained action log |
| [**verify**](pillars/verify.md) | New feature needs coverage, or a bug needs diagnosis | `/verify` | Failing test → minimal fix → passing test, linked to a claim id |
| [**guardrail**](pillars/guardrail.md) | Interrupts other pillars when asserting / acting / saving | `/gate`, `/ground`, `/handoff`, `/resume` | The existing six modules and three roles |

Exactly one pillar per turn. Guardrail triggers **interrupt** the other pillars (gate cannot be bypassed even to record a lesson).

## The three guardrail roles

| Role | Responsibility | Default module |
|---|---|---|
| [**Verifier**](personas/verifier.md) | Ground claims in real code before asserting | [`verify-claim`](modules/verify-claim.md) |
| [**RiskGuard**](personas/risk-guard.md) | Gate destructive or shared-state actions | [`assess-risk`](modules/assess-risk.md) |
| [**SessionRecorder**](personas/session-recorder.md) | Snapshot / resume session; record non-obvious lessons | [`save-session`](modules/save-session.md), [`record-lesson`](modules/record-lesson.md), [`track-state`](modules/track-state.md) |

Priority when multiple triggers fire in one turn: **Verifier → RiskGuard → SessionRecorder**. Verifier runs first because gating an unverified premise is theatre.

## Persistent state (`.veritas/`)

Auto-created on first write. Shared by all pillars. Plain text and JSON.

| File | Purpose | Pillar(s) |
|---|---|---|
| `state.json` | Active role, turn counters, last decision | all |
| `claims.jsonl` | Provenance DAG of claims with `depends_on`, `evidence[].fingerprint` | plan, verify, guardrail |
| `actions.jsonl` | Hash-chained log of gate decisions (tamper-evident) | execute, guardrail |
| `history.jsonl` | Approved actions; feeds recency component of risk score | execute, guardrail |
| `HANDOFF.md` | Canonical session scroll (committed to git) | all |
| `LESSONS.md` | Non-obvious lessons with `EXPIRES` | guardrail |
| `DECISIONS.md` | Architectural decisions with `Revisit when` | plan, design |
| `private/` | Gitignored; user-scoped secrets only | any |

Read order on resume: `state.json` → `HANDOFF.md` → `claims.jsonl` (check stale) → `actions.jsonl` (tail + verify chain) → `DECISIONS.md` (only if next step touches a recorded decision).

## Scripts

- `scripts/verify-claim.py` — path / symbol / version grounding checks.
- `scripts/track-claims.py` — add, verify, retire, invalidate-changed (cascade).
- `scripts/log-actions.py` — append, verify, tail the hash-chained action log.
- `scripts/score-risk.py` — deterministic risk score for a proposed action.
- `scripts/track-state.py` — init, set-role, migrate the state directory.

All zero-dependency Python. Runnable directly; no install step for the scripts themselves.

## Invariants

- Veritas **never fabricates** file paths, symbol names, line numbers, versions, or commit hashes. Unverifiable claims are marked unverified, not smoothed into prose.
- Veritas **never bypasses** a gate to "save time". Time saved by skipping a gate is interest borrowed against a future failure.
- Veritas **rollbacks must reference** a real commit, backup, snapshot, or compensating action. Hypothetical rollbacks are not rollbacks.
- Veritas **records are append-where-it-matters.** `actions.jsonl` is hash-chained; editing past entries breaks the chain and is detectable.
- Veritas **stays dormant** when no trigger fires. Exploring, reading, explaining — these are not triggers.

## What Veritas does not do

- Does not run builds, deployments, migrations, or shell commands on its own. It gates and advises; the assistant executes.
- Does not replace the user's judgement. Every pillar surfaces the data the user needs to judge.
- Does not track telemetry, call home, or require network access. Every artifact is local and plaintext.
