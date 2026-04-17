# Pillar: execute

**Purpose** — run a plan in atomic, reversible steps. Every step passes the risk gate; every commit maps to one logical change.

## When this pillar activates

- User says: "implement", "build the phase", "ship this", "run the plan".
- Explicit slash: `/execute <phase-or-plan>`.
- A plan exists (either in the chat or in `.planning/` / `docs/plan.md`) and the next action is to produce code.

## Preconditions

- A plan is readable and has a clear "next step".
- Working tree is clean, or the dirty files are intentional context for the step.
- `.veritas/state.json` exists; `phase` and `step` fields are current or about to be set.

If any precondition is missing, stop and surface the gap. Do not execute against an unwritten plan.

## The per-step loop

Each step is a single logical change. For each step:

### 1. Ground premises

Every claim the step depends on ("function X returns Y", "table Z exists", "config flag F defaults to D") must be verified now. Do not trust the plan's claims without re-grounding them against the current tree.

- `python src/veritas/scripts/verify-claim.py path|symbol|version <args>`
- Log to `.veritas/claims.jsonl` with `depends_on` linking to any parent claim from the plan.

### 2. Score the risk

```
python src/veritas/scripts/score-risk.py "<command>" --rev <ref> --authz <yes|no|ambiguous>
```

If `recommendation != proceed`, stop. Emit the `ACTION / SCOPE / REVERSIBILITY / BLAST / AUTHORIZED / SCORE / DECISION` block. The user speaks next.

### 3. Apply

One file at a time when possible. Prefer `Edit` over `Write` on existing files. Do not combine unrelated changes.

### 4. Run the test

TDD order: the failing test now passes, and no previously-passing test fails. If the test suite is slow, run the narrowest relevant subset first, then the full suite before the commit.

### 5. Commit atomically

```
<phase>/<step>: <one-sentence what>

<optional body: why, not what>
```

One commit = one logical change. If the message needs "and", split.

### 6. Log the action

```
python src/veritas/scripts/log-actions.py append proceed "<commit subject>" --rev <short-hash> --authz yes
```

The hash chain captures the decision; history.jsonl captures the pattern for future risk scoring.

### 7. Advance state

```
python src/veritas/scripts/track-state.py set-role risk-guard
```

Increment `step`. When the phase's last step is done, set `phase` to the next and `step` to 1.

## Resume behavior

On a new session: read `.veritas/HANDOFF.md`, verify the checksum, run `invalidate-changed`, re-ground the next-step claims. Do not blindly pick up at the stored `step` — verify the tree still reflects it.

## Anti-patterns

- Multi-step commits ("set up auth and add logout"). Split.
- Gating an unverified claim. Verify first, gate second.
- Running the full test suite once at the end — late feedback is expensive feedback.
- Skipping `log-actions.py append` because "it's just a small commit". The chain has no "small" entries; it has entries.
