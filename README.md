# Veritas

> Umbrella builder and guardrail for AI-assisted software work.

Five pillars. Eight slash commands. One shared state directory. Fabrication-proof by construction.

| Pillar | What it does | Slash |
|---|---|---|
| **plan** | Brainstorm → PRD skeleton → architecture sketch → stories. Every assumption logged as a claim. | `/plan <goal>` |
| **design** | Grounded design system (colors with contrast, typography, spacing, components, a11y). No generic templates. | `/design <brief>` |
| **execute** | Atomic-commit loop with per-step risk gate and hash-chained action log. | `/execute <phase>` |
| **verify** | TDD for features, bisect-driven debug for bugs, tests linked to claims in the DAG. | `/verify <target>` |
| **guardrail** | Verifier, RiskGuard, SessionRecorder — interrupts other pillars on assertion, risky action, or session boundary. | `/gate`, `/ground`, `/handoff`, `/resume` |

Priority across pillars: **Verifier → RiskGuard → SessionRecorder**. Guardrail triggers interrupt the active pillar.

---

## Install

### Any supported platform (multi-platform CLI)

```bash
npx veritas-cli init --ai <platform>
```

Platforms: `claude`, `cursor`, `windsurf`, `copilot`, `codex`, `gemini`, `continue`, `roocode`, `kilocode`, `opencode`, `trae`, `warp`, `kiro`.

```bash
npx veritas-cli list          # show target paths and notes
npx veritas-cli uninstall --ai <platform>
```

### Manual (Claude Code)

```bash
git clone https://github.com/TuongHuy0603/veritas.git
mkdir -p ~/.claude/skills/veritas ~/.claude/commands
cp -r veritas/src/veritas/* ~/.claude/skills/veritas/
cp veritas/commands/*.md ~/.claude/commands/
```

### Initialize per-project state

```bash
cd your-project/
python path/to/veritas/src/veritas/scripts/track-state.py init
```

Creates `.veritas/` scaffolding. Safe to commit everything except `.veritas/private/`.

---

## How activation works

Two paths:

1. **Auto-activate.** The assistant reads `src/veritas/SKILL.md` and matches the current turn against `data/trigger-verbs.csv` (intent phrases) and `data/risky-ops.csv` (action gate). The matched pillar runs.
2. **Explicit slash.** `/plan`, `/design`, `/execute`, `/verify`, `/gate`, `/ground`, `/handoff`, `/resume` each invoke their pillar unambiguously.

Exactly one pillar per turn. Guardrail interrupts the others.

---

## The three guardrail roles

| Role | Responsibility | Default module |
|---|---|---|
| **[Verifier](src/veritas/personas/verifier.md)** | Ground claims in real code before asserting | [`verify-claim`](src/veritas/modules/verify-claim.md) |
| **[RiskGuard](src/veritas/personas/risk-guard.md)** | Gate destructive or shared-state actions (risk score + 4-question gate) | [`assess-risk`](src/veritas/modules/assess-risk.md) |
| **[SessionRecorder](src/veritas/personas/session-recorder.md)** | Snapshot / resume session, record non-obvious lessons | [`save-session`](src/veritas/modules/save-session.md), [`record-lesson`](src/veritas/modules/record-lesson.md), [`track-state`](src/veritas/modules/track-state.md) |

---

## Persistent state: `.veritas/`

Shared by every pillar. Plain markdown + JSON so any future reader — human or assistant — can use it without a live session.

```
.veritas/
├── state.json        # active role, turn counters, active pillar, phase, step
├── claims.jsonl      # provenance DAG: claims with depends_on + evidence.fingerprint
├── actions.jsonl     # hash-chained gate decisions (tamper-evident)
├── history.jsonl     # approved-action history (feeds recency component of risk score)
├── HANDOFF.md        # canonical session scroll (committed to git)
├── LESSONS.md        # non-obvious lessons with EXPIRES
├── DECISIONS.md      # architectural decisions with "Revisit when"
└── private/          # gitignored — user-scoped secrets only
```

### Two things that don't exist elsewhere

**Provenance DAG (`claims.jsonl`).** Every claim records `depends_on`, `evidence[].fingerprint` (sha1 of the cited file at verification time), and `touched_files`. When a cited file changes, `track-claims.py invalidate-changed` cascades `stale` to every dependent claim. This is how verified knowledge survives code drift.

**Hash-chained action log (`actions.jsonl`).** Each entry has `prev_hash` and `hash` (SHA-256 of the entry minus the hash field). `log-actions.py verify` walks the chain and reports the first break. Tamper evidence, not convention.

---

## Risk scoring

`score-risk.py "<action>" --rev <ref> --authz <yes|no|ambiguous>` returns a `[0.0, 1.0]` score with explainable components:

| Component | Weight | Signal |
|---|---|---|
| `base_score` | 0.40 | Pattern hit in `data/risky-ops.csv` |
| `reversibility` | 0.25 | `NONE` → 1.0, commit hash → 0.0 |
| `branch` | 0.15 | Shared branch (`main`, `master`, `release/*`, `prod`, `staging`) → 1.0 |
| `authorization` | 0.10 | `no` → 1.0, `ambiguous` → 0.7, `yes` → 0.0 |
| `recency` | 0.10 | Familiar approved action < 1h ago → −0.5 |

Thresholds: `< 0.30` proceed, `0.30–0.70` pause, `≥ 0.70` abort. No ML. Deterministic and auditable.

---

## Scripts

Zero-dependency Python. Runnable directly.

```bash
python src/veritas/scripts/verify-claim.py path src/foo.py
python src/veritas/scripts/verify-claim.py symbol src/foo.py my_function
python src/veritas/scripts/verify-claim.py version package.json react

python src/veritas/scripts/track-claims.py add --text "..." --file src/foo.py --line 42
python src/veritas/scripts/track-claims.py verify c_ab12
python src/veritas/scripts/track-claims.py invalidate-changed
python src/veritas/scripts/track-claims.py list --status stale

python src/veritas/scripts/log-actions.py append pause-for-confirmation "DROP TABLE sessions" --rev NONE --authz ambiguous
python src/veritas/scripts/log-actions.py verify
python src/veritas/scripts/log-actions.py tail 10

python src/veritas/scripts/score-risk.py "terraform destroy" --authz no

python src/veritas/scripts/track-state.py init
python src/veritas/scripts/track-state.py migrate
python src/veritas/scripts/track-state.py show
```

---

## Tests

```bash
pip install pytest
pytest tests/
```

Subprocess tests for the DAG, the hash chain, and the risk scorer.

---

## Repository layout

```
veritas/
├── .claude-plugin/plugin.json
├── commands/                   # slash commands (/plan, /design, /execute, /verify, /gate, /ground, /handoff, /resume)
├── cli/
│   ├── adapters.json           # per-platform install targets
│   ├── index.js                # CLI installer
│   └── package.json
├── src/veritas/
│   ├── SKILL.md                # umbrella router
│   ├── pillars/                # plan, design, execute, verify, guardrail
│   ├── personas/               # verifier, risk-guard, session-recorder
│   ├── modules/                # verify-claim, assess-risk, save-session, record-lesson, route-role, track-state
│   ├── data/                   # trigger-verbs, risky-ops, pillar-intents, design-rules
│   ├── state/schema.json       # JSON schema for state.json
│   └── scripts/                # verify-claim, track-claims, log-actions, score-risk, track-state
├── tests/
├── docs/ACTIVATION.md
├── CHANGELOG.md
├── README.md
├── LICENSE
├── package.json
└── skill.json
```

---

## Design principles

- **Small surface, sharp edges.** Five pillars, three roles, six modules. If a turn does not match a trigger, nothing activates.
- **No fabrication.** Unverifiable claims are marked unverified, not hedged with "probably".
- **Evidence beats assertion.** Every claim carries a file fingerprint; every gate decision carries a hash.
- **Silence beats noise.** Most sessions produce zero lessons. That is the target.
- **Local plaintext.** `.veritas/` is markdown + JSON; no database, no daemon, no telemetry.

## License

MIT. See [LICENSE](LICENSE).
