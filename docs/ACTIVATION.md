# Activation reference

Veritas auto-activates when the next action matches a trigger. This document is the specification the skill uses to decide.

## The decision tree

```
Next action is an assertion about code?
  ├─ yes → ground-check
  └─ no  → continue

Next action is in data/risky-ops.csv or touches shared state?
  ├─ yes → blast-radius
  └─ no  → continue

Session is ending, pausing, resuming, or user is switching tools?
  ├─ yes → handoff
  └─ no  → continue

A mistake was just corrected, or an unusual path was just validated?
  ├─ yes → postmortem
  └─ no  → stay dormant
```

Only one module runs per invocation. Veritas does not chain modules inside a single turn.

## Priority order

If two triggers fire in the same turn, use this order:

1. `blast-radius` — never proceed past a risky action without the gate.
2. `ground-check` — a claim about code comes before acting on it.
3. `handoff` — state capture comes before session close.
4. `postmortem` — the last step, when everything else is done.

## Dormancy

The skill is dormant by default. These situations **do not** trigger Veritas:

- The assistant is exploring, reading, or explaining code (no assertion, no action).
- The user is asking a question that does not require a factual answer about their code.
- A routine edit with an obvious, reversible diff on a local branch.
- A conversational turn that produces no output file change and no side effect.

## Trigger data

- [`src/veritas/data/trigger-verbs.csv`](../src/veritas/data/trigger-verbs.csv) — user-visible verbs that hint at a trigger.
- [`src/veritas/data/risky-ops.csv`](../src/veritas/data/risky-ops.csv) — the action gate.

Both files are append-only across minor versions. Removing a row is a breaking change.
