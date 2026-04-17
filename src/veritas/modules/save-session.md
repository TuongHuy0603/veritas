# Module: save-session

**Purpose** — Make a session's context survive a reset, a compaction, or a jump to a different AI tool. Context that lives only in the current chat is fragile.

## When this module fires

- The user says "pause", "continue later", "handoff", "switch tool", "save state".
- The conversation is long and the assistant notices drift (contradicting earlier claims, forgetting recent decisions, re-asking resolved questions).
- The user is about to switch from this assistant to another (other AI CLI, another person, another terminal).
- On explicit session close.

## The session scroll

A single markdown file, canonical format, portable across tools. Write it to the project root as `.veritas/HANDOFF.md` (overwrite the prior scroll — it is a snapshot, not an append log).

```markdown
# Session Scroll — <UTC timestamp>

## Goal
<one paragraph: what the user is trying to accomplish in this thread>

## State
- Branch: <name> @ <commit hash>
- Working tree: <clean | dirty — list changed files>
- Last successful action: <what>
- Last failed action: <what and why>
- Last persona: <verifier | risk-guard | session-recorder | none>
- Last gate decision: <proceed | pause-for-confirmation | abort | none>

## Decisions made (with why)
- <decision> — <one-line reason>

## Open questions
- <question> — <who needs to answer>

## Next step
<exactly one sentence — what the next assistant should do first>

## Do not
- <traps, dead ends, or destructive paths already ruled out>

## Checksum
<sha256 of the state.json file at the moment of writing>
```

## Rules

- **One page max.** A scroll that does not fit on a screen has failed. Cut ruthlessly.
- **No pronouns without antecedents.** "Fix it" means nothing to the next reader.
- **Absolute, not relative.** "Thursday" becomes the date. "That function" becomes `path/to/file.py:funcname`.
- **Decisions carry their reason.** A decision without a reason will be reopened on resume.
- **Do-not list is mandatory.** The most expensive part of resuming is rediscovering dead ends.
- **Checksum is mandatory.** The receiving assistant recomputes sha256 of `.veritas/state.json` and must match before acting.

## On resume

Read `.veritas/HANDOFF.md` first, before doing anything else. Then:

1. Verify the branch and commit hash match the current state.
2. Recompute the sha256 of `.veritas/state.json` and compare against the checksum in the scroll. On mismatch, the scroll is stale — trust `git log` and `state.json` instead.
3. Re-run `verify-claim` on any scroll claim that is load-bearing for the next step.
4. Acknowledge the handoff to the user in one line: "Resumed from scroll dated X, next step is Y."
5. If the scroll is older than 24 hours, assume the tree has moved. Check `git log` before trusting the "last successful action".

## Anti-patterns

- Writing the scroll at the start of a session "just in case" — it will be stale by the time it matters.
- Copying the whole chat transcript into the scroll. The scroll is a decision record, not a log.
- Resuming without reading the do-not list, and walking straight into a ruled-out path.
- Omitting the checksum to "save space". Without it the scroll has no integrity guarantee.
