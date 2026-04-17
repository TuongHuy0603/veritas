# Module: blast-radius

**Purpose** — Gate actions by how bad it is if they are wrong. The assistant defaults to action; Veritas defaults to a pause at the gate.

## When this module fires

Before executing any operation listed in `data/risky-ops.csv`, or any operation whose effect extends beyond the current working tree:

- Deletions of files, branches, tables, indexes, collections, or cloud resources.
- Force operations: `push --force`, `reset --hard`, `rebase` on shared branches, `checkout --`.
- Schema or data changes: migrations, `DROP`, `TRUNCATE`, bulk `UPDATE` without `WHERE`.
- Shared-surface actions: posting PRs, comments, messages, emails, webhooks.
- Package changes: removing dependencies, downgrading, editing lockfiles by hand.
- Anything that touches production, staging, or another person's environment.

## The four-question gate

The assistant must be able to answer all four before proceeding. If any answer is "don't know", **stop**.

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
DECISION: proceed | pause-for-confirmation | abort
```

The assistant emits this block and then either acts (`proceed`), waits (`pause-for-confirmation`), or declines (`abort`). It does not negotiate the decision silently.

## Escalation rules

- If `REVERSIBILITY: NONE`, default to `pause-for-confirmation` even if `AUTHORIZED: yes`. Irreversible authorized actions still deserve a last look.
- If the action touches a shared branch (`main`, `master`, `release/*`, `prod`), default to `pause-for-confirmation` unless the user has named the branch explicitly in the current turn.
- If `BLAST` includes another human's work-in-progress (their branch, their draft, their data), default to `abort` until they are in the loop.

## Anti-patterns

- Running the action and then writing the block. The block is a gate, not a log.
- Treating "the user said yes ten minutes ago" as standing authorization for new destructive steps.
- Listing a rollback that has never been tested in this codebase.
