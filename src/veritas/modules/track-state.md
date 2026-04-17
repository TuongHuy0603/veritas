# Module: track-state

**Purpose** — Keep a file-backed record of claims (as a provenance DAG), gate decisions (as a hash-chained log), and session state so context survives turns, compactions, and resets.

## The artifacts

All live under `.veritas/` in the project root. Plain text and JSON so any future reader — human or assistant — can use them without a live session.

### 1. `.veritas/state.json`

Single-object JSON. Overwrite on every role activation. The handshake between turns.

```json
{
  "version": "0.3.0",
  "active_role": "verifier | risk-guard | session-recorder | null",
  "turn": 0,
  "role_turns": { "verifier": 0, "risk-guard": 0, "session-recorder": 0 },
  "last_gate_decision": "proceed | pause-for-confirmation | abort | null",
  "last_claim_status": "verified | unverified | partial | null",
  "open_questions": [],
  "updated_at": "<ISO-8601 UTC>"
}
```

Schema: `state/schema.json`.

### 2. `.veritas/claims.jsonl` — provenance DAG

Line-delimited JSON, one claim per line:

```json
{"id":"c_ab12","text":"check_token returns None on missing header","status":"verified","depends_on":["c_98ef"],"evidence":[{"file":"src/api/auth.py","line":47,"fingerprint":"a1b2c3d4"}],"commit_sha":"abcdef0","touched_files":["src/api/auth.py"],"created_at":"2026-04-17T09:12:00Z","updated_at":"2026-04-17T09:12:00Z"}
```

Each claim records:

- `depends_on` — list of claim ids this claim rests on. Invalidation cascades.
- `evidence[].fingerprint` — sha1 of the cited file at verification time.
- `touched_files` — used by `invalidate-changed` to detect drift.

When a cited file changes on disk, `scripts/track-claims.py invalidate-changed` marks the claim `stale` and cascades `stale` to every claim whose `depends_on` includes it.

**Promotion rules** (run by SessionRecorder on session close or daily):

- `unverified` older than 24 hours → `stale`.
- `stale` older than 7 days → `retired`.
- `verified` stays active until a file in `touched_files` changes, then → `stale`.

### 3. `.veritas/actions.jsonl` — hash-chained gate log

One JSON object per line. Each has `seq`, `prev_hash`, and `hash` (SHA-256 of the entry minus the `hash` field). Genesis `prev_hash` is 64 zeros.

```json
{"seq":1,"timestamp":"2026-04-17T09:44:12Z","module":"assess-risk","decision":"proceed","action":"git commit","reversibility":"HEAD~1","authorization":"yes","prev_hash":"000…000","hash":"f3a…b21"}
{"seq":2,"timestamp":"2026-04-17T09:46:03Z","module":"assess-risk","decision":"pause-for-confirmation","action":"DROP TABLE sessions","reversibility":"NONE","authorization":"ambiguous","prev_hash":"f3a…b21","hash":"9c0…e44"}
```

`scripts/log-actions.py verify` walks the chain; any edit or truncation of a prior line breaks it and reports the first break. Tamper evidence, not convention.

### 4. `.veritas/history.jsonl` — approval history for risk scoring

One entry per `proceed` decision: timestamp, action, authorization. Consumed by `scripts/score-risk.py` to compute the `recency` component (familiar approved patterns get a small discount).

### 5. `.veritas/HANDOFF.md`

Canonical session scroll, overwritten per snapshot. Committed to git (portable across machines and tools). See `modules/save-session.md`.

### 6. `.veritas/LESSONS.md`

Record-lesson entries with EXPIRES. Newest first. Committed to git.

### 7. `.veritas/DECISIONS.md`

Architectural decision journal. Append only. Each entry includes **Why** and **Revisit when**.

### 8. `.veritas/private/` — gitignored

User-scoped secrets that must not leave the local machine (tokens, WIP credentials, personal notes). Everything else in `.veritas/` is safe to commit.

## Read order on resume

1. `state.json` — what was the last role and decision?
2. `HANDOFF.md` — what is the next step, what is the do-not list?
3. `claims.jsonl` — filter by `status=verified` to recover known truths; `status=stale` to see what needs re-verifying.
4. `actions.jsonl` — tail last 10 entries to see what was paused or aborted.
5. `DECISIONS.md` — only if the next step touches an area with recorded decisions.

## Anti-patterns

- Editing `actions.jsonl` to "clean it up". The chain breaks, `log-actions.py verify` will fail, and the audit value is gone.
- Treating a `verified` claim as permanent. Files move; entries expire when their cited files change. Run `invalidate-changed` on resume.
- Writing a `DECISIONS.md` entry for every choice. Most code choices are implementations of an earlier decision, not decisions themselves.
- Putting secrets anywhere other than `.veritas/private/`. The rest of the directory is committed.
