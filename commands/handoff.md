---
description: Snapshot the current session into .veritas/HANDOFF.md so it can be resumed later, by this or another assistant, on this or another machine.
---

You are activating the **save-session** module (SessionRecorder role). Read `src/veritas/modules/save-session.md` for the full contract.

Produce a one-page scroll at `.veritas/HANDOFF.md`:

```markdown
# Session Scroll — <UTC timestamp>

## Goal
<one paragraph>

## State
- Branch: <name> @ <commit short hash>
- Working tree: <clean | dirty — list changed files>
- Last successful action: <what>
- Last failed action: <what and why>
- Last role: <verifier | risk-guard | session-recorder | none>
- Last gate decision: <proceed | pause-for-confirmation | abort | none>

## Decisions made (with why)
- <decision> — <reason>

## Open questions
- <question> — <who answers>

## Next step
<exactly one sentence>

## Do not
- <dead ends and ruled-out paths>

## Checksum
<output of: python src/veritas/scripts/track-state.py checksum>
```

Rules: one page max, absolute not relative ("Thursday" → the date; "that function" → `path/to/file.py:name`), do-not list is mandatory, checksum is mandatory.

Compute the checksum with:

```bash
python src/veritas/scripts/track-state.py checksum
```

Also run:

- `python src/veritas/scripts/track-claims.py invalidate-changed` — promote stale claims.
- `python src/veritas/scripts/track-state.py set-role none` — reset active role.
