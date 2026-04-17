---
name: veritas
description: Activates before the assistant asserts factual claims about code, executes risky or destructive operations, ends or resumes a work session, or when the user reports that prior information was incorrect. Grounds claims in real code before stating them, gates actions by blast radius and reversibility, produces a canonical handoff when context grows stale, and captures non-obvious lessons on session close. Triggers on verbs like verify, check, confirm, is it safe to, rollback, undo, handoff, resume, continue previous session, and before any delete, drop, migrate, force-push, rm -rf, truncate, or schema change.
version: 0.1.0
license: MIT
---

# Veritas — Truth, Risk, Continuity, Learning

Veritas is a guardrail layer. It does not plan features, it does not generate designs, it does not run workflows. It intervenes at four moments:

1. **Before an assertion** — ground claims in real code, not memory or pattern-matching.
2. **Before an action** — assess blast radius and confirm a rollback path exists.
3. **On session boundary** — write or read a canonical handoff so context survives resets.
4. **On session close** — extract lessons that are non-obvious and worth remembering.

Veritas is intentionally small. Four modules, one decision tree. If a task does not hit one of the four moments, this skill stays dormant.

---

## When to invoke which module

Route by the user's intent and the risk of the next action, not by keyword alone.

| User intent or situation | Module |
|---|---|
| About to say "X function does Y" or "file Z contains W" | `modules/ground-check.md` |
| About to run a destructive, irreversible, or shared-state action | `modules/blast-radius.md` |
| Pausing work, context feels stale, or resuming a prior session | `modules/handoff.md` |
| Task completed or a mistake was corrected | `modules/postmortem.md` |

See `data/trigger-verbs.csv` for the verb catalog and `data/risky-ops.csv` for the action gate.

---

## Invariants

- Veritas never edits source code to "fix" a claim. It only verifies, reports, and gates.
- Veritas never fabricates file paths, symbol names, or line numbers. If a claim cannot be grounded, the correct output is "not verified" — not a confident guess.
- Veritas rollback plans must reference real commits, real files, or real backups. Hypothetical rollbacks are not rollbacks.
- Veritas postmortems record what was **surprising**, not what was routine. A successful task that went as expected usually produces zero entries.

---

## Entry flow

1. Detect the trigger (see `data/trigger-verbs.csv` + the action gate in `data/risky-ops.csv`).
2. Pick the module from the table above. Only one module runs per invocation.
3. Follow the module's checklist. Each module produces a short structured output, not prose.
4. If the checklist cannot be completed (missing access, unverified claim, no rollback), stop. Report the gap to the user. Do not proceed past the gate.

---

## What Veritas deliberately does not do

- Does not write plans, roadmaps, phases, PRDs, or stories.
- Does not generate UI, designs, architectures, or tests.
- Does not run builds, deployments, or migrations on its own.
- Does not replace the user's judgement — it surfaces the data the user needs to judge.
