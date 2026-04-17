---
description: Systematic test and debug. TDD for new code, bisect-driven for bugs, coverage linked to claims in the DAG.
argument-hint: "<test name or bug description>"
---

You are activating the **verify** pillar of Veritas. Read `src/veritas/pillars/verify.md` for the full contract.

Target from the user: `$ARGUMENTS`

### If the target is a new feature → TDD

1. Write the smallest failing test that describes the behavior.
2. Run it. Confirm it fails for the expected reason, not a setup error.
3. Write the minimum code to pass.
4. Run it. Confirm green.
5. Refactor only after green. Commit the refactor separately.

### If the target is a bug → systematic debug

1. **Reproduce** — a deterministic script or test that triggers the bug.
2. **Bisect** — `git bisect` or manual binary search for the first bad commit / input.
3. **Hypothesize** — one sentence, falsifiable.
4. **Test the hypothesis** — change one thing, re-run.
5. **Fix, with a regression test that would have caught this.**

### Claim linkage

Every passing test becomes a claim in `.veritas/claims.jsonl` with `depends_on` pointing to the file(s) it covers. When a file changes, `track-claims.py invalidate-changed` cascades `stale` to the associated test claims — a signal to re-run, not re-verify blindly.

### Output

- The failing test (or reproduction).
- The minimal fix.
- The passing test.
- The claim id added to the DAG.
