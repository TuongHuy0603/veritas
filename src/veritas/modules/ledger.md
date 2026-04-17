# Module: ledger

**Purpose** — Keep a rolling, file-backed record of claims, gate decisions, and state so context survives turns, compactions, and session resets.

## The four artifacts

All four live under `.veritas/` in the project root. The directory is plain text and auto-created on first write.

### 1. `.veritas/state.json`

Single-object JSON. Overwrite on every persona activation. The handshake between turns.

```json
{
  "version": "0.2.0",
  "active_persona": "skeptic | sentinel | archivist | null",
  "turn": 0,
  "last_gate_decision": "proceed | pause-for-confirmation | abort | null",
  "last_claim_status": "verified | unverified | partial | null",
  "open_questions": [],
  "updated_at": "<ISO-8601 UTC>"
}
```

### 2. `.veritas/LEDGER.md`

Assumption ledger. Append on new claims; edit in place when a claim's status changes. Never delete — retire to the bottom under `## Retired`.

```markdown
# Assumption Ledger

## Active

- [2026-04-17T09:12:00Z] `src/api/auth.py:check_token` returns `None` on missing header
  - status: verified
  - evidence: src/api/auth.py:47-53
  - scope: auth flow

- [2026-04-17T09:30:00Z] Redis TTL for session keys is 3600s
  - status: unverified
  - gap: no grep hit in current tree; may be set at runtime
  - scope: session layer

## Stale

- [2026-04-15T…] …

## Retired

- [2026-04-10T…] …
```

Promotion rules (run by Archivist on session close or daily):

- `unverified` older than 24 hours → `stale`.
- `stale` older than 7 days → `retired`.
- `verified` stays active until a code change contradicts it; then it moves straight to `retired` with a note.

### 3. `.veritas/audit.log`

Append-only, one line per Sentinel gate decision. Machine-parseable, no prose.

```
2026-04-17T09:44:12Z  blast-radius  proceed           git commit -m "…"  rev=HEAD~1  authz=explicit
2026-04-17T09:46:03Z  blast-radius  pause             DROP TABLE sessions  rev=NONE  authz=ambiguous
2026-04-17T09:47:30Z  blast-radius  abort             terraform destroy  rev=NONE  authz=no
```

Columns: timestamp, module, decision, action-summary, reversibility-ref, authorization-status.

### 4. `.veritas/DECISIONS.md`

Architectural decision journal. Append only. One entry per decision that has a real reason.

```markdown
## 2026-04-17 — Use Redis instead of Memcached for session store

**Why:** need pub/sub for logout broadcast; Memcached has no native pub/sub.
**Alternatives considered:** Memcached (rejected — no pub/sub), Postgres LISTEN/NOTIFY (rejected — session TTL noise in WAL).
**Revisit when:** logout volume drops below 1/sec (pub/sub no longer load-bearing).
```

`Revisit when` is the decision-journal equivalent of `EXPIRES` on a lesson. A decision with no revisit condition will silently become cargo.

## When this module fires

- Skeptic writes to `LEDGER.md` after every `ground-check`.
- Sentinel appends to `audit.log` after every gate decision.
- Archivist reads all four on resume, promotes ledger entries on session close, and writes `DECISIONS.md` entries when a decision has a reason worth recording.

## Read order on resume

1. `state.json` — what was the last persona and decision?
2. `HANDOFF.md` — what is the next step?
3. `LEDGER.md` — which claims are still verified, which went stale?
4. `audit.log` — tail last 10 lines to see what was paused or aborted.
5. `DECISIONS.md` — only if the next step touches an area with recorded decisions.

## Anti-patterns

- Editing `audit.log` to "clean it up". It is append-only by design; history of declined actions is itself evidence.
- Treating a `verified` ledger entry as permanent. Code moves; entries expire when the code they describe changes.
- Writing a `DECISIONS.md` entry for every choice. Most code choices are not decisions — they are implementations of an earlier decision.
