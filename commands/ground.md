---
description: Ground a factual claim about code against the actual codebase before asserting it. Emits the CLAIM block; logs the result to the provenance DAG.
argument-hint: "<claim to verify>"
---

You are activating the **verify-claim** module (Verifier role). Read `src/veritas/modules/verify-claim.md` for the full contract.

Claim from the user: `$ARGUMENTS`

Run, in order:

1. **Restate the claim in one sentence.** No hedges, no paraphrase.
2. **Choose the check:**
   - Path claim → does the file exist?
   - Symbol claim → does the function/class/flag exist in the named file?
   - Behavior claim → read the body; the name lies.
   - Version claim → read the manifest file right now.
   - Cross-file claim → verify each hop.
3. **Run the check.** Prefer `python src/veritas/scripts/verify-claim.py path|symbol|version <args>`. Fall back to file-read and grep.
4. **Emit the block:**

```
CLAIM: <one sentence>
GROUNDED: yes | no | partial
EVIDENCE:
  - <file>:<line> — <what was observed>
GAPS:
  - <any hop that could not be verified>
```

5. **Log to the DAG:** `python src/veritas/scripts/track-claims.py add --text "<claim>" --file <file> [--line N]`, then `verify <id>` if grounded.

If `GROUNDED: no`, **do not** state the claim as fact downstream. State it as a hypothesis and name the gap.
