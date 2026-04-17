---
name: veritas
description: Activates before the assistant asserts factual claims about code, executes risky or destructive operations, ends or resumes a work session, or when the user reports that prior information was incorrect. Routes the turn to one of three personas — Skeptic (verify before asserting), Sentinel (gate before acting), Archivist (record and resume across sessions) — and writes durable state to a per-project .veritas/ directory so context survives compactions, pauses, and tool switches. Triggers on verbs like verify, check, confirm, is it safe to, rollback, undo, handoff, resume, continue previous session, and before any delete, drop, migrate, force-push, rm -rf, truncate, or schema change.
version: 0.2.0
license: MIT
---

# Veritas — Truth, Risk, Continuity, Learning

Veritas is a guardrail layer. It does not plan features, it does not generate designs, it does not run workflows. It intervenes at four moments and carries state between them.

1. **Before an assertion** — ground claims in real code, not memory or pattern-matching.
2. **Before an action** — assess blast radius and confirm a rollback path exists.
3. **On session boundary** — write or read a canonical handoff so context survives resets.
4. **On session close** — extract lessons that are non-obvious and worth remembering.

Four core modules. Three personas. One persistent state directory. If a task does not hit a trigger, this skill stays dormant.

---

## Personas

Each turn routes to at most one persona. The persona is a disposition — a stance, a set of opening moves, and a set of refusals — not a separate agent.

| Persona | Activates on | Default module | Writes to |
|---|---|---|---|
| **[Skeptic](personas/skeptic.md)** | Load-bearing claim about code | `ground-check` | `.veritas/LEDGER.md` |
| **[Sentinel](personas/sentinel.md)** | Risky or irreversible action | `blast-radius` | `.veritas/audit.log` |
| **[Archivist](personas/archivist.md)** | Session boundary, decision, correction | `handoff`, `postmortem`, `ledger` | `.veritas/HANDOFF.md`, `LESSONS.md`, `DECISIONS.md` |

Routing logic and priority rules live in [`modules/persona.md`](modules/persona.md).

---

## Modules

| Module | Responsibility |
|---|---|
| [`ground-check`](modules/ground-check.md) | Verify claims against real code before asserting them. |
| [`blast-radius`](modules/blast-radius.md) | Gate destructive or shared-state actions by scope, reversibility, blast, authorization. |
| [`handoff`](modules/handoff.md) | Write a one-page canonical scroll on pause; read it first on resume. |
| [`postmortem`](modules/postmortem.md) | Capture only non-obvious lessons with an explicit expiry condition. |
| [`persona`](modules/persona.md) | Route a turn to zero or one persona. |
| [`ledger`](modules/ledger.md) | Persist state to `.veritas/` so context survives turns and sessions. |

---

## Persistent state (`.veritas/`)

Auto-created on first write. Plain text and JSON so humans and any future assistant can read it without a live session.

```
.veritas/
├── state.json       # active persona, turn counter, last decision, open questions
├── LEDGER.md        # rolling assumption ledger: active / stale / retired
├── audit.log        # append-only Sentinel gate decisions
├── HANDOFF.md       # canonical session scroll (overwritten per snapshot)
├── LESSONS.md       # postmortem entries with EXPIRES
└── DECISIONS.md     # architectural decision journal with "revisit when"
```

See [`modules/ledger.md`](modules/ledger.md) for the read-order on resume and the promotion rules (how `unverified` claims age into `stale` and then `retired`).

---

## Invariants

- Veritas never edits source code to "fix" a claim. It only verifies, reports, and gates.
- Veritas never fabricates file paths, symbol names, or line numbers. If a claim cannot be grounded, the correct output is "not verified" — not a confident guess.
- Rollback plans must reference real commits, real files, or real backups. Hypothetical rollbacks are not rollbacks.
- Postmortems record what was **surprising**, not what was routine. Most sessions produce zero entries.
- `audit.log` is append-only. A history of declined actions is itself evidence.

---

## Entry flow

1. Detect the trigger (see `data/trigger-verbs.csv` and the action gate in `data/risky-ops.csv`).
2. Route to at most one persona (see `modules/persona.md`). Priority: Sentinel > Skeptic > Archivist.
3. Run the persona's default module. Follow its checklist. Produce the structured block it specifies.
4. Write the state effect to `.veritas/` (ledger entry, audit-log line, or scroll snapshot).
5. If the checklist cannot be completed (missing access, unverified claim, no rollback), stop. Report the gap. Do not proceed past the gate.

---

## What Veritas deliberately does not do

- Does not write plans, roadmaps, phases, PRDs, or stories.
- Does not generate UI, designs, architectures, or tests.
- Does not run builds, deployments, or migrations on its own.
- Does not replace the user's judgement — it surfaces the data the user needs to judge.
