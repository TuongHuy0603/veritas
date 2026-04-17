---
description: Resume a prior session from the .veritas/HANDOFF.md scroll. Verifies checksum and re-grounds load-bearing claims before acting.
---

You are activating the **save-session** module (SessionRecorder role) in resume mode. Read `src/veritas/modules/save-session.md` for the full contract.

Do these, **in order**, before anything else:

1. **Read `.veritas/HANDOFF.md`.** Do nothing else until it has been read.
2. **Verify branch and commit.** `git rev-parse HEAD` vs the scroll. On mismatch, trust `git log` over the scroll.
3. **Verify the checksum.** Recompute `sha256` of `.veritas/state.json` and compare against the scroll's `Checksum` field. On mismatch, the scroll is stale — treat state.json as the source of truth.
4. **Invalidate drifted claims.** `python src/veritas/scripts/track-claims.py invalidate-changed`. Any claim whose file has changed since verification is now `stale`.
5. **Re-ground load-bearing claims.** For each scroll claim that the next step depends on, run `verify-claim` now. Old groundings in a stale tree do not count.
6. **Verify the action log.** `python src/veritas/scripts/log-actions.py verify`. If the chain is broken, report it to the user before proceeding.
7. **Acknowledge in one line:** "Resumed from scroll dated X, next step is Y."

Only then begin work. Respect the scroll's **Do not** list — the most expensive thing on resume is retracing a ruled-out path.
