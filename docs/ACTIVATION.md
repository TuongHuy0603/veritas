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

## Trigger data

- [`src/veritas/data/trigger-verbs.csv`](../src/veritas/data/trigger-verbs.csv) — verbs + phrase patterns → pillar / role / module.
- [`src/veritas/data/risky-ops.csv`](../src/veritas/data/risky-ops.csv) — action gate with `base_score` column.
- [`src/veritas/data/pillar-intents.csv`](../src/veritas/data/pillar-intents.csv) — intent phrase → pillar routing.
- [`src/veritas/data/design-rules.csv`](../src/veritas/data/design-rules.csv) — design-system rules consumed by the design pillar.

All four files are append-only across minor versions. Removing or relocating a row is a breaking change.
