---
description: Execute a plan phase with atomic commits. Each step passes a risk-scored gate; each commit corresponds to one test turning green.
argument-hint: "<phase name or plan file>"
---

You are activating the **execute** pillar of Veritas. Read `src/veritas/pillars/execute.md` for the full contract.

Target from the user: `$ARGUMENTS`

Workflow per step:

1. **Ground premises.** For every claim the step rests on ("function X returns Y", "table Z exists"), call `scripts/verify-claim.py` or read the file directly. Update `.veritas/claims.jsonl`.
2. **Score the action.** Run `scripts/score-risk.py "<command>" --rev <ref> --authz <status>`. If `recommendation != proceed`, stop and emit the gate block.
3. **Apply the change.** One file at a time when possible.
4. **Run the test.** TDD order: the test that was failing should now pass; nothing else should regress.
5. **Commit atomically.** Message format: `<phase>/<step>: <one-sentence what>` — one logical change per commit.
6. **Append to the action log.** `scripts/log-actions.py append proceed "<commit subject>" --rev <hash> --authz yes`.

Rules:

- No multi-step commits. If you find yourself writing a commit message with "and", split it.
- No gate skips. A `pause-for-confirmation` decision stops the flow; the user speaks next.
- `.veritas/state.json` tracks `phase` and `step` so a resume picks up at the right point.
