# Activation reference

Veritas auto-activates when the next action matches a trigger. Each turn routes to at most one **persona**, which runs exactly one **module** and writes to `.veritas/`. This document is the specification the skill uses to decide.

## The decision tree

```
Next action is in data/risky-ops.csv, or touches shared state / prod / other humans?
  ├─ yes → Sentinel → blast-radius
  └─ no  → continue

Next action is a load-bearing factual claim about code / config / version / symbol?
  ├─ yes → Skeptic → ground-check
  └─ no  → continue

Session boundary (pause, end, switch tool, resume)?
  ├─ yes → Archivist → handoff
  └─ no  → continue

A mistake was just corrected, or an unusual path was just validated?
  ├─ yes → Archivist → postmortem
  └─ no  → continue

A decision was just made with a real reason (not an implementation choice)?
  ├─ yes → Archivist → ledger (write DECISIONS.md entry)
  └─ no  → stay dormant
```

Only one persona per turn. Only one module per persona activation.

## Priority order

If two triggers fire in the same turn, use this order. A higher rule wins and the lower is deferred to the next turn.

1. **Sentinel (`blast-radius`)** — never proceed past a risky action, even to verify a claim.
2. **Skeptic (`ground-check`)** — verify the claim before writing a lesson or decision about it.
3. **Archivist (`handoff`)** — state capture comes before session close.
4. **Archivist (`postmortem`)** — lesson capture comes after the decision is made.
5. **Archivist (`ledger`)** — decision-journal entries are the last step.

## State effects

Each activation writes at least one artifact in `.veritas/`:

| Persona | Module | Writes to |
|---|---|---|
| Skeptic | `ground-check` | `.veritas/LEDGER.md`, `state.json.last_claim_status` |
| Sentinel | `blast-radius` | `.veritas/audit.log`, `state.json.last_gate_decision` |
| Archivist | `handoff` | `.veritas/HANDOFF.md`, `state.json` snapshot |
| Archivist | `postmortem` | `.veritas/LESSONS.md` (only if filter passes) |
| Archivist | `ledger` | `.veritas/DECISIONS.md`, age-promotes `LEDGER.md` entries |

## Dormancy

Veritas is dormant by default. These situations **do not** trigger Veritas:

- The assistant is exploring, reading, or explaining code (no assertion, no action).
- The user is asking a question that does not require a factual answer about their code.
- A routine edit with an obvious, reversible diff on a local branch.
- A conversational turn that produces no file change and no side effect.
- Re-stating a claim already grounded in the same session (checked via `state.json.last_claim_status`).

## Trigger data

- [`src/veritas/data/trigger-verbs.csv`](../src/veritas/data/trigger-verbs.csv) — user-visible verbs that hint at a trigger, with the persona and module each maps to.
- [`src/veritas/data/risky-ops.csv`](../src/veritas/data/risky-ops.csv) — action gate with default decisions.

Both files are append-only across minor versions. Removing a row is a breaking change.
