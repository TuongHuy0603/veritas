# Activation reference

Veritas activates via one of two paths: the assistant auto-routes a turn to a pillar, or the user types an explicit slash command. This document specifies the decision tree.

## Decision tree

```
Did the user type a slash command (/plan, /design, /execute, /verify, /gate, /ground, /handoff, /resume)?
  ├─ yes → run the named pillar / module, skip auto-routing
  └─ no  → continue to auto-routing

Is the next action in data/risky-ops.csv, or does it touch shared state / prod / other humans?
  ├─ yes → guardrail / RiskGuard / assess-risk
  └─ no  → continue

Is the next action a load-bearing factual claim about code / config / version / symbol?
  ├─ yes → guardrail / Verifier / verify-claim
  └─ no  → continue

Is this a session boundary (pause, end, switch tool, resume)?
  ├─ yes → guardrail / SessionRecorder / save-session
  └─ no  → continue

Is the user requesting a plan, PRD, architecture, or story breakdown?
  ├─ yes → plan pillar
  └─ no  → continue

Is the user requesting UI/UX, design system, palette, or frontend contract?
  ├─ yes → design pillar
  └─ no  → continue

Is a plan ready and the next action is to produce code?
  ├─ yes → execute pillar
  └─ no  → continue

Is the target a test to write or a bug to reproduce?
  ├─ yes → verify pillar
  └─ no  → continue

Was a mistake just corrected, or an unusual path just validated?
  ├─ yes → guardrail / SessionRecorder / record-lesson
  └─ no  → stay dormant
```

Only one pillar per turn. Guardrail triggers **interrupt** the other pillars.

## Priority when multiple guardrail triggers fire

1. **Verifier (`verify-claim`)** first if a risky action contains an unverified premise. Gating an unverified claim is theatre.
2. **RiskGuard (`assess-risk`)** next — the gate cannot be bypassed even to record.
3. **SessionRecorder (`save-session` / `record-lesson` / `track-state`)** last — record follows decision.

## State effects per activation

| Pillar / Module | Writes to |
|---|---|
| `plan` | `.veritas/claims.jsonl` (unverified claims), `.veritas/DECISIONS.md` |
| `design` | `.veritas/DECISIONS.md` |
| `execute` | `.veritas/actions.jsonl`, `.veritas/history.jsonl`, `.veritas/state.json` (phase, step) |
| `verify` | `.veritas/claims.jsonl` (verified claims linked to tests) |
| `verify-claim` | `.veritas/claims.jsonl`, `state.json.last_claim_status` |
| `assess-risk` | `.veritas/actions.jsonl`, `.veritas/history.jsonl`, `state.json.last_gate_decision` |
| `save-session` | `.veritas/HANDOFF.md`, `.veritas/state.json` snapshot |
| `record-lesson` | `.veritas/LESSONS.md` (only if filter passes) |
| `track-state` | `.veritas/state.json`, cascade `claims.jsonl` statuses |

## Dormancy

Veritas stays dormant when:

- The assistant is exploring, reading, or explaining code (no assertion, no action).
- The user is asking a conversational question that does not require a factual answer about code.
- A routine edit on a local branch with an obvious, reversible diff.
- A re-statement of a claim already grounded in the same session (checked via `state.json.last_claim_status`).

## Trigger data — two tables, two jobs

The trigger data is deliberately split so each table has a single responsibility. They are not redundant; they route different things.

- [`src/veritas/data/trigger-verbs.csv`](../src/veritas/data/trigger-verbs.csv) — **guardrail-only routing.** Verbs that fire a role (verifier / risk-guard / session-recorder) and a module. Used by the guardrail interrupt path.
- [`src/veritas/data/pillar-intents.csv`](../src/veritas/data/pillar-intents.csv) — **pillar routing.** Intent phrases that select a pillar (plan / design / execute / verify / guardrail) and the slash command that maps to it.
- [`src/veritas/data/risky-ops.csv`](../src/veritas/data/risky-ops.csv) — action gate with `base_score` column. Consumed by `score-risk.py` and by `assess-risk` escalation rules.
- [`src/veritas/data/design-rules.csv`](../src/veritas/data/design-rules.csv) — design-system rules consumed by the design pillar.

All four files are append-only across minor versions. Removing or relocating a row is a breaking change.
