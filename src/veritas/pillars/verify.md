# Pillar: verify

**Purpose** — write tests before code, debug by bisect not by guessing, and keep tests linked to the claims they cover.

## When this pillar activates

- User says: "test", "debug", "why is this failing", "add coverage for".
- Explicit slash: `/verify <target>`.
- A bug is reproduced or a feature needs test coverage.

## Two modes

### Mode A — TDD (new feature)

1. **Failing test first.** The test describes the behavior. If you cannot write the test, you cannot write the feature.
2. **Run it.** Confirm it fails for the expected reason, not an import error or a typo. The test must fail *because* the feature is missing.
3. **Minimum code to pass.** Write the smallest change that turns the test green. Do not refactor yet.
4. **Run it again.** Confirm green, and confirm no previously-passing test broke.
5. **Refactor.** Only with green tests as a safety net. Commit the refactor separately.
6. **Claim linkage.** Append a claim to `.veritas/claims.jsonl` for the behavior ("`foo()` returns `None` on empty input"), with `evidence` pointing to the test file and line.

### Mode B — Systematic debug (bug)

1. **Reproduce.** A deterministic script or test that triggers the bug. If it's flaky, make it deterministic before going further — intermittent bugs are two bugs.
2. **Bisect.** `git bisect` or manual binary search on the first bad commit. For data-triggered bugs, bisect the input.
3. **Hypothesize.** One sentence, falsifiable. "Fetches run in the wrong order when the cache is cold" is a hypothesis; "something is wrong with caching" is not.
4. **Test the hypothesis.** Change one thing. Re-run the reproduction. If wrong, a new hypothesis — not a new "thing to try".
5. **Fix with a regression test** that would have caught this bug if it had existed before the fix.

## Claim linkage and invalidation

Every passing test → one entry in `.veritas/claims.jsonl`:

```json
{"id":"c_...","text":"foo returns None on empty input","status":"verified","evidence":[{"file":"tests/test_foo.py","line":12}],"touched_files":["src/foo.py","tests/test_foo.py"],"depends_on":[]}
```

When `src/foo.py` changes, `track-claims.py invalidate-changed` marks the claim `stale`. That is the **signal to re-run the test**, not a signal that the code is broken. Re-run → if green, re-verify the claim; if red, the bug is new.

## Output

- The failing test (or reproduction).
- The minimal fix.
- The passing test.
- The claim id added to the DAG.

Do not output a wall of prose explaining the bug. The test is the explanation.

## Anti-patterns

- "I'll add tests later." No. The test comes with the feature or it does not come at all.
- Debugging by adding print statements without a hypothesis. Print adds data; it does not narrow the space.
- Marking a test skip to make CI green. A skip is a TODO with teeth that bite you silently.
- Tests with no assertion — these are latency checks, not tests.
