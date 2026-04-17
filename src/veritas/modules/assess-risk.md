# Module: assess-risk

**Purpose** — Gate actions by how bad it is if they are wrong. The assistant defaults to action; Veritas defaults to a pause at the gate.

## When this module fires

Before executing any operation listed in `data/risky-ops.csv`, or any operation whose effect extends beyond the current working tree:

- Deletions of files, branches, tables, indexes, collections, or cloud resources.
- Force operations: `push --force`, `reset --hard`, `rebase` on shared branches, `checkout --`.
- Schema or data changes: migrations, `DROP`, `TRUNCATE`, bulk `UPDATE` without `WHERE`.
- Shared-surface actions: posting PRs, comments, messages, emails, webhooks.
- Package changes: removing dependencies, downgrading, editing lockfiles by hand.
- Anything that touches production, staging, or another person's environment.

## Risk scoring (v0.3.0)

Binary gates are too coarse. `assess-risk` now computes a deterministic score in `[0.0, 1.0]` from five components (weights sum to 1.0):

| Component | Weight | Signal |
|---|---|---|
| `base_score` | 0.40 | Pattern hit in `data/risky-ops.csv` (`base_score` column) |
| `reversibility` | 0.25 | `NONE` → 1.0, commit hash → 0.0, backup ref → 0.1 |
| `branch` | 0.15 | `main`/`master`/`release/*`/`prod*`/`staging` → 1.0 |
| `authorization` | 0.10 | `no` → 1.0, `ambiguous` → 0.7, `yes` → 0.0 |
| `recency` | 0.10 | Similar action approved in last 1h → −0.5 (familiarity discount) |

Thresholds:

- `score < 0.30` → **proceed**
- `0.30 ≤ score < 0.70` → **pause-for-confirmation**
- `score ≥ 0.70` → **abort**

Helper: `scripts/score-risk.py "<action>" --rev <ref> --authz <yes|no|ambiguous>` prints the score, components, and recommendation. No ML, no opaque model — every number is explainable.

## The four-question gate (still required)

Even with a proceed-level score, answer these. If any answer is "don't know", stop.

1. **Scope** — what exactly changes? Name the files, rows, resources, or recipients.
2. **Reversibility** — how do we undo this? Point to a specific commit, backup, snapshot, or compensating action. "We can write it back" is not a rollback.
3. **Blast** — what else breaks if this is wrong? List downstream consumers, running processes, open PRs, linked issues.
4. **Authorization** — did the user authorize **this specific action**, in **this specific scope**? A general "yes go ahead" earlier in the session does not authorize a newly discovered destructive step.

## Output contract

```
ACTION: <one sentence>
SCOPE:
  - <file / resource / recipient>
REVERSIBILITY: <commit hash | backup ref | compensating action | NONE>
BLAST:
  - <downstream effect>
AUTHORIZED: yes | no | ambiguous
SCORE: <0.00–1.00>  (components: base=X rev=X branch=X authz=X recency=X)
DECISION: proceed | pause-for-confirmation | abort
```

The assistant emits this block and then either acts (`proceed`), waits (`pause-for-confirmation`), or declines (`abort`). It does not negotiate the decision silently.

## Escalation rules

- If `REVERSIBILITY: NONE`, default to `pause-for-confirmation` even if `AUTHORIZED: yes`. Irreversible authorized actions still deserve a last look.
- Shared branches force `pause-for-confirmation` unless the user named the branch explicitly in the current turn.
- Actions touching another human's work-in-progress force `abort` until that human is in the loop.
- `--no-verify`, `--no-gpg-sign`, and similar hook-skips are destructive actions in their own right.

## State effect (hash-chained)

Every decision is appended to `.veritas/actions.jsonl` as a JSON line with `seq`, `prev_hash`, and `hash` (SHA-256 of the entry minus the `hash` field). Any edit to a prior line breaks the chain. `scripts/log-actions.py verify` walks the chain and reports the first break — tamper evidence, not convention.

Approvals are additionally logged to `.veritas/history.jsonl` for the recency component of future scores.

## Anti-patterns

- Running the action and then writing the block. The block is a gate, not a log.
- Treating "the user said yes ten minutes ago" as standing authorization for new destructive steps.
- Listing a rollback that has never been tested in this codebase.
- Using the score to bypass the four-question gate. Score is informative, not sufficient.
