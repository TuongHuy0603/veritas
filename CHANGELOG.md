# Changelog

All notable changes to this project. Dates are UTC.

## [1.0.0] — 2026-04-17

The guardrail-only beta becomes an umbrella builder. Five pillars, eight slash commands, a provenance DAG, a hash-chained action log, deterministic risk scoring.

### Added

- **Five pillars** (`src/veritas/pillars/`):
  - `plan` — brainstorm → PRD → architecture → stories, each assumption logged as a claim.
  - `design` — grounded design system: detects existing stack, applies `data/design-rules.csv`, ships contrast ratios with every color pair.
  - `execute` — atomic-commit loop with per-step gate and hash-chained action log.
  - `verify` — TDD for features, bisect-driven systematic debug for bugs, tests linked to claims in the DAG.
  - `guardrail` — umbrella over the existing six modules / three roles.
- **Eight slash commands** (`commands/`): `/plan`, `/design`, `/execute`, `/verify`, `/gate`, `/ground`, `/handoff`, `/resume`.
- **Provenance DAG** for claims (`src/veritas/scripts/track-claims.py`). Each claim records `depends_on`, `evidence[].fingerprint`, `touched_files`. File drift cascades `stale` to every dependent claim.
- **Hash-chained action log** (`src/veritas/scripts/log-actions.py`). Tamper-evident `actions.jsonl` with `prev_hash` + `hash`. `log-actions.py verify` walks the chain and reports the first break.
- **Deterministic risk scoring** (`src/veritas/scripts/score-risk.py`). Five components (base / reversibility / branch / authorization / recency), explainable, no ML.
- **History file** (`.veritas/history.jsonl`) — feeds the recency component of future risk scores.
- **State migration** (`track-state.py migrate`) — upgrades pre-0.3 state.json files.
- `data/pillar-intents.csv` — intent → pillar routing table.
- `data/design-rules.csv` — accessibility and design-system rules referenced by the design pillar.
- `data/risky-ops.csv` gains a `base_score` column.
- `tests/` — subprocess tests for the three new scripts.

### Changed

- **All module and persona files renamed to semantic verb-object names.**
  - `ground-check` → `verify-claim`
  - `blast-radius` → `assess-risk`
  - `handoff` → `save-session`
  - `postmortem` → `record-lesson`
  - `persona` → `route-role`
  - `ledger` → `track-state`
  - `Skeptic` → `Verifier`
  - `Sentinel` → `RiskGuard`
  - `Archivist` → `SessionRecorder`
- All scripts renamed: `verify.py` → `verify-claim.py`, `state.py` → `track-state.py`, new `track-claims.py`, `log-actions.py`, `score-risk.py`.
- **Priority order reversed.** `Verifier` now runs before `RiskGuard` when a risky action contains an unverified premise. Gating an unverified claim is theatre.
- `.veritas/` artifact names: `LEDGER.md` → `claims.jsonl` (now a DAG), `audit.log` → `actions.jsonl` (now hash-chained).
- `assess-risk` emits a `SCORE` line in its output block.
- Trigger verbs narrowed: `I think`, `probably`, `should be` removed as standalone triggers — they produced too many false positives.
- `.gitignore` no longer excludes `HANDOFF.md`. Secrets go in `.veritas/private/` (gitignored).
- Cursor adapter now emits `.mdc` flat files instead of a nested folder.

### Fixed

- Substring matches in `risky-ops.csv` now use word-boundary regex, reducing false positives on documentation text.
- `verify-claim.py` clarifies that regex hits inside comments or strings are not evidence.

### Deprecated

- Nothing yet.

### Removed

- Plain-text `audit.log` (replaced by `actions.jsonl` with hash chain).
- Markdown `LEDGER.md` (replaced by `claims.jsonl` DAG).

---

## [0.2.0] — 2026-04-17

Three roles, persistent state directory.

### Added

- Roles: `Skeptic`, `Sentinel`, `Archivist`.
- Modules: `persona`, `ledger`.
- `.veritas/` directory with `state.json`, `LEDGER.md`, `audit.log`, `HANDOFF.md`, `LESSONS.md`, `DECISIONS.md`.

---

## [0.1.0] — 2026-04-17

Initial release. Four modules: `ground-check`, `blast-radius`, `handoff`, `postmortem`. Multi-platform CLI installer.
