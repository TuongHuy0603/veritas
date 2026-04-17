# Module: verify-claim

**Purpose** — Prevent the assistant from stating things about code that turn out to be invented, renamed, or removed.

## When this module fires

Any time the assistant is about to output a factual claim of the form:

- "The function `X` in `path/to/file` does Y."
- "This project uses library `L` version `V`."
- "The config flag `F` defaults to `D`."
- "Line `N` of `file` calls `Z`."

If the claim is load-bearing — i.e. the user or the assistant's next step depends on it — it **must** be grounded before it is stated. A claim is load-bearing when the next likely action (edit, run, commit, ship, gate decision) rests on the claim being true.

### Priority rule

`verify-claim` runs **before** `assess-risk` when a proposed risky action contains an unverified premise. Example: "`DROP TABLE sessions`" — `verify-claim` first confirms the table exists and is named exactly that, then `assess-risk` gates the drop. Gating an unverified premise is theatre.

## The grounding checklist

Run each applicable step. Stop at the first step that disproves the claim.

1. **Path claim** — does the file exist? Use a directory listing or file-read, not memory.
2. **Symbol claim** — does the function, class, variable, or flag exist in the claimed file? Use a code search, not recall. Regex alone is not enough: matches inside comments or strings are false positives.
3. **Behavior claim** — does the code actually do what is claimed, or is the claim inferred from the name? Read the body, do not trust the signature.
4. **Version claim** — is the version string present in a manifest file (package.json, pyproject.toml, Cargo.toml, go.mod, etc.) right now? Prior sessions do not count.
5. **Cross-file claim** — if the claim spans files ("X calls Y which imports Z"), each hop must be verified, not just the endpoints.

Helper: `scripts/verify-claim.py` runs the path, symbol, and version checks with exit `0` on verified and `1` on not-verified.

## Output contract

Produce a short block, not a paragraph:

```
CLAIM: <one sentence>
GROUNDED: yes | no | partial
EVIDENCE:
  - <file>:<line> — <what was observed>
  - <file>:<line> — <what was observed>
GAPS:
  - <any hop that could not be verified>
```

If `GROUNDED: no`, the assistant must not state the claim as fact. It may state it as a hypothesis: "I think X, but I could not verify it because …".

## State effect

Every grounded or ungrounded claim is appended to the provenance DAG at `.veritas/claims.jsonl` (one JSON object per line) with `depends_on` links to prior claims. When a cited file changes, `scripts/track-claims.py invalidate-changed` cascades the `stale` status to every dependent claim.

## Anti-patterns

- Quoting a function signature from memory to justify a claim about its body.
- Citing a line number without reading the file in the current session.
- Using "typically" or "usually" to paper over an unverified specific.
- Re-asserting a claim that was grounded in a prior session. Cache is not truth.
- Treating a regex match inside a comment as evidence of a live symbol.
