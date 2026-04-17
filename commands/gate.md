---
description: Run the RiskGuard gate on a proposed action — deterministic risk score plus the four-question gate. Emits the ACTION block; does not execute.
argument-hint: "<action to assess>"
---

You are activating the **assess-risk** module (RiskGuard role) inside Veritas. Read `src/veritas/modules/assess-risk.md` for the full contract.

Proposed action from the user: `$ARGUMENTS`

Run, in order:

1. **Verify premises.** If the action names a table, file, flag, or symbol, call `verify-claim` first. Do not gate an unverified claim.
2. **Score.** `python src/veritas/scripts/score-risk.py "$ARGUMENTS" --rev <ref-or-NONE> --authz <yes|no|ambiguous>`.
3. **Answer the four questions:** scope, reversibility, blast, authorization.
4. **Emit the block:**

```
ACTION: <one sentence>
SCOPE:
  - <item>
REVERSIBILITY: <commit hash | backup ref | compensating action | NONE>
BLAST:
  - <downstream>
AUTHORIZED: yes | no | ambiguous
SCORE: <0.00-1.00>  (components: base=X rev=X branch=X authz=X recency=X)
DECISION: proceed | pause-for-confirmation | abort
```

5. **Append to the hash-chained log:** `python src/veritas/scripts/log-actions.py append <decision> "<action>" --rev <ref> --authz <status>`.

Do **not** execute the action in this command. This is a gate, not a runner.
