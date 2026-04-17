# Module: record-lesson

**Purpose** — Extract the one or two things from this session that are worth remembering. Most sessions produce zero entries. That is the correct rate.

## When this module fires

- The user says the task is done, closes a PR, merges a branch.
- A mistake was corrected mid-session ("no, not that" → followed by a different path that worked).
- A surprising success: a non-obvious approach landed, and the user accepted it without pushback.
- The user says "save that" or "remember this".

## The signal filter

Before writing anything, ask: **would a future session, with no memory of today, be worse off without this entry?**

If the answer is "no" or "probably not", write nothing. The cost of a noisy memory layer is higher than the cost of forgetting a routine success.

Keep the entry only if at least one of these is true:

1. **It contradicts a reasonable default.** The obvious approach would have failed, and the reason why is not in the code or the commit message.
2. **It encodes a hidden constraint.** A system, team, or person has a rule that is not written down anywhere discoverable.
3. **It is a correction that cost real time.** The assistant went the wrong way, the user redirected, and the redirect was not obvious from context.
4. **It is a validated judgement call.** The assistant chose a non-default path and the user explicitly confirmed it was correct.

Routine successes — tests passed, build green, feature shipped as planned — do not qualify. The code and the git history already record them.

## Output contract

Each entry is at most five lines:

```
LESSON: <one sentence, declarative, no hedging>
WHY: <the reason — not the symptom>
SCOPE: <where this applies — file, subsystem, project, cross-project>
EVIDENCE: <session ref, commit hash, or turn number>
EXPIRES: <condition under which this lesson stops being true, or "unknown">
```

`EXPIRES` is the most important field. A lesson without an expiry condition is a lesson that will eventually mislead. If the expiry is truly unknown, write "unknown" — do not invent one.

## Where entries go

- If the user has a memory system (e.g. Claude auto-memory), append there.
- If not, write to `.veritas/LESSONS.md` in the project, newest first.
- Never write entries into source files as comments. Lessons are not code.

## Deduplication

Before appending, diff the new lesson against existing `LESSONS.md`. If the WHY is substantially identical to an existing entry, update the existing one's EVIDENCE list instead of adding a duplicate.

## Anti-patterns

- Writing an entry per session as a ritual. Most sessions should produce none.
- Recording the WHAT ("added caching to the resolver") instead of the WHY ("caching was needed because the upstream rate-limits per-token, not per-request — this is not documented anywhere").
- Entries that restate code conventions already visible in the codebase.
- Entries that will be false in six months with no expiry condition noted.
