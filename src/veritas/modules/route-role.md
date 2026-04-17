# Module: route-role

**Purpose** — Route the current turn to at most one role. A role (formerly "persona") is a disposition — a stance, a set of opening moves, and a set of refusals — with its own state.

## When this module fires

On every turn where at least one core module trigger is detected. Role selection runs **before** the module executes. Zero or one role per turn.

## Routing table

| Trigger signal | Role | Module |
|---|---|---|
| Load-bearing claim about code, config, version, or symbol | **Verifier** | `verify-claim` |
| User confident assertion paired with a code/file/function/config reference | **Verifier** | `verify-claim` |
| Command or edit matching `data/risky-ops.csv` | **RiskGuard** | `assess-risk` |
| Action extends beyond working tree (shared branch, prod, other humans) | **RiskGuard** | `assess-risk` |
| Session boundary: pause, end, switch tool, resume | **SessionRecorder** | `save-session` |
| Task completed with surprise, or mistake just corrected | **SessionRecorder** | `record-lesson` |
| Claim created, verified, promoted, retired | **SessionRecorder** | `track-state` |

## Priority when multiple triggers fire

1. **Verifier first** if the risky action contains an unverified premise. `DROP TABLE sessions` — verify the table exists before gating the drop.
2. **RiskGuard** next — the gate cannot be bypassed even to record a lesson.
3. **SessionRecorder** last — record after the decision, not before.

This order inverts the v0.2 rule and is the correct one: gating unverified premises is theatre.

## Dormancy

If no trigger fires, no role is selected. The assistant continues with its normal behavior. Veritas is a guardrail, not a narrator.

## State effects

When a role activates, routing writes the active role to `.veritas/state.json`:

```json
{
  "active_role": "verifier | risk-guard | session-recorder | null",
  "turn": 42,
  "role_turns": { "verifier": 12, "risk-guard": 5, "session-recorder": 3 },
  "last_gate_decision": "pause-for-confirmation",
  "last_claim_status": "verified",
  "updated_at": "<ISO-8601>"
}
```

`role_turns` is how each role exerts its own state: Verifier reads `last_claim_status` to skip re-verifying a claim already grounded this session; RiskGuard reads `role_turns.risk-guard` to detect gate fatigue (too many gates in one session may indicate a plan-level problem, not a per-action one).

## Anti-patterns

- Running two roles in one turn to "be thorough". One turn, one role, one module.
- Treating a role as a costume. A role is a ruleset — it either applies or it does not.
- Activating SessionRecorder on every turn "to keep the scroll fresh". Scrolls written too early are stale by the time they matter.
