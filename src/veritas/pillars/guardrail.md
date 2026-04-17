# Pillar: guardrail

**Purpose** — intervene at four specific moments in any other pillar's work: before an assertion, before a risky action, at a session boundary, at session close.

This pillar is the umbrella over the six core modules and three roles that predate the pillar layer. It is the original Veritas.

## When this pillar activates

Automatically, from within other pillars:

- `plan` / `design` / `execute` / `verify` about to assert a fact about code → Verifier takes over.
- Any pillar about to run a risky or irreversible operation → RiskGuard takes over.
- User pauses, switches tools, or resumes → SessionRecorder takes over.
- A decision was just made with a real reason, or a mistake was corrected → SessionRecorder records it.

## Roles

- **[Verifier](../personas/verifier.md)** → `verify-claim` module.
- **[RiskGuard](../personas/risk-guard.md)** → `assess-risk` module.
- **[SessionRecorder](../personas/session-recorder.md)** → `save-session`, `record-lesson`, `track-state` modules.

## Modules

- [`verify-claim`](../modules/verify-claim.md) — ground claims in real code.
- [`assess-risk`](../modules/assess-risk.md) — gate risky actions by score + four questions.
- [`save-session`](../modules/save-session.md) — canonical scroll + checksum on pause/resume.
- [`record-lesson`](../modules/record-lesson.md) — capture only non-obvious lessons, with `EXPIRES`.
- [`route-role`](../modules/route-role.md) — which role runs this turn.
- [`track-state`](../modules/track-state.md) — the `.veritas/` directory contract.

## Priority across pillars

Guardrail triggers **interrupt** other pillars. If the `execute` pillar is applying a change and the change triggers `assess-risk`, the execute loop pauses at step 2 (score the risk) until the gate clears. The gate's decision is appended to `.veritas/actions.jsonl` whether or not the pillar resumes.

## State

All four artifacts in `.veritas/` (state.json, claims.jsonl, actions.jsonl, history.jsonl, HANDOFF.md, LESSONS.md, DECISIONS.md) are shared by every pillar. Guardrail does not own a private namespace.

## Anti-patterns

- Treating guardrail as optional in "simple" pillar work. Risky actions do not announce themselves as risky — the gate catches what looks routine.
- Disabling guardrail to move faster. Speed from skipped verification is interest borrowed from a future failure.
