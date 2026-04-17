# Veritas

A guardrail skill for AI-assisted coding. Three personas, six modules, one persistent state directory:

1. **Ground claims** — before the assistant states a fact about your code, verify it. *Persona: Skeptic.*
2. **Gate actions** — before a destructive or shared-state action, check blast radius and reversibility. *Persona: Sentinel.*
3. **Hand off and resume** — write a canonical scroll on pause; read it first on resume. *Persona: Archivist.*
4. **Carry context across sessions** — a per-project `.veritas/` directory holds the ledger, audit log, handoff, lessons, and decisions so state survives compactions and tool switches.

Veritas does not plan features, generate designs, or run workflows. It sits above any planning or execution layer you already use and intervenes at four specific moments.

---

## Install

### Any supported platform

```bash
npx veritas-cli init --ai <platform>
```

Supported platforms: `claude`, `cursor`, `windsurf`, `copilot`, `codex`, `gemini`, `continue`, `roocode`, `kilocode`, `opencode`, `trae`, `warp`, `kiro`.

To see targets and notes:

```bash
npx veritas-cli list
```

### Manual (Claude Code)

```bash
git clone https://github.com/TuongHuy0603/veritas.git
mkdir -p ~/.claude/skills/veritas
cp -r veritas/src/veritas/* ~/.claude/skills/veritas/
```

### Initialize per-project state (optional but recommended)

```bash
cd your-project/
python path/to/veritas/src/veritas/scripts/state.py init
```

This creates `.veritas/` with empty scaffolding. The assistant can create it lazily too, but running `init` up front makes the ledger visible immediately.

### Uninstall

```bash
npx veritas-cli uninstall --ai <platform>
```

---

## Personas

Each turn routes to at most one persona. A persona is a disposition — a stance, opening moves, and a set of refusals — not a separate agent.

| Persona | Activates on | Default module | Writes to |
|---|---|---|---|
| **[Skeptic](src/veritas/personas/skeptic.md)** | Load-bearing claim about code | `ground-check` | `.veritas/LEDGER.md` |
| **[Sentinel](src/veritas/personas/sentinel.md)** | Risky or irreversible action | `blast-radius` | `.veritas/audit.log` |
| **[Archivist](src/veritas/personas/archivist.md)** | Session boundary, decision, correction | `handoff`, `postmortem`, `ledger` | `.veritas/HANDOFF.md`, `LESSONS.md`, `DECISIONS.md` |

Priority when two triggers fire: **Sentinel → Skeptic → Archivist**. Routing logic lives in [`modules/persona.md`](src/veritas/modules/persona.md).

---

## How activation works

Veritas auto-activates when the assistant's next action matches a trigger. You do not invoke it with a slash command — it invokes itself.

| Trigger | Persona | Module |
|---|---|---|
| Assistant is about to state a factual claim about code | Skeptic | `ground-check` |
| Assistant is about to execute a risky or irreversible operation | Sentinel | `blast-radius` |
| User pauses, resumes, or switches tools | Archivist | `handoff` |
| Task completed, or a mistake was just corrected | Archivist | `postmortem` |
| Decision made with a real reason | Archivist | `ledger` |

Trigger verbs are in [`src/veritas/data/trigger-verbs.csv`](src/veritas/data/trigger-verbs.csv). Risky-op patterns are in [`src/veritas/data/risky-ops.csv`](src/veritas/data/risky-ops.csv).

---

## The six modules

### `ground-check` — anti-hallucination

Before asserting "function X does Y" or "file Z contains W", verify. Uses file-read and code-search, not recall. Produces a `CLAIM / GROUNDED / EVIDENCE / GAPS` block. If a claim cannot be grounded, the output is "not verified", not a confident guess. See [`modules/ground-check.md`](src/veritas/modules/ground-check.md).

### `blast-radius` — risk gate

Before `rm -rf`, `DROP TABLE`, `git push --force`, `terraform destroy`, or any shared-state action, answer four questions: scope, reversibility, blast, authorization. Irreversible actions pause for confirmation even when authorized. See [`modules/blast-radius.md`](src/veritas/modules/blast-radius.md).

### `handoff` — cross-session continuity

One page, canonical format, written to `HANDOFF.md`. Goal, state, decisions with reasons, open questions, exact next step, and a **do-not** list (rediscovering dead ends is the most expensive part of resuming). Portable across tools. See [`modules/handoff.md`](src/veritas/modules/handoff.md).

### `postmortem` — lesson capture

The filter: *would a future session, with no memory of today, be worse off without this entry?* If no, write nothing. Record only what contradicts a default, encodes a hidden constraint, or cost real time. Every entry has an `EXPIRES` field. See [`modules/postmortem.md`](src/veritas/modules/postmortem.md).

### `persona` — routing

One turn, zero or one persona. Specifies the priority order when multiple triggers fire and the state effects each persona writes. See [`modules/persona.md`](src/veritas/modules/persona.md).

### `ledger` — persistent state

Reads and writes the `.veritas/` directory: assumption ledger with active/stale/retired promotion, append-only audit log for gate decisions, handoff scroll, lessons, decisions journal. Specifies the resume read-order. See [`modules/ledger.md`](src/veritas/modules/ledger.md).

---

## Persistent state (`.veritas/`)

Auto-created on first write. Plain text and JSON so any future reader — human or assistant — can use it without a live session.

```
.veritas/
├── state.json       # active persona, turn counter, last decision, open questions
├── LEDGER.md        # rolling assumption ledger: active / stale / retired
├── audit.log        # append-only Sentinel gate decisions
├── HANDOFF.md       # canonical session scroll (overwritten per snapshot)
├── LESSONS.md       # postmortem entries with EXPIRES
└── DECISIONS.md     # architectural decisions with "revisit when"
```

**Promotion rules:** `unverified` ledger entries older than 24 hours become `stale`; `stale` older than 7 days becomes `retired`. `verified` stays active until a code change contradicts it, then moves straight to `retired`.

**Schema** for `state.json`: [`src/veritas/state/schema.json`](src/veritas/state/schema.json).

---

## Helper scripts

`src/veritas/scripts/verify.py` — zero-dependency grounding helpers:

```bash
python verify.py path src/foo.py
python verify.py symbol src/foo.py my_function
python verify.py version package.json react
```

`src/veritas/scripts/state.py` — zero-dependency state helpers:

```bash
python state.py init
python state.py set-persona sentinel
python state.py audit pause-for-confirmation "DROP TABLE sessions" --rev NONE --authz ambiguous
python state.py show
```

Exit `0` on success, `1` on not-verified or bad input.

---

## Repository layout

```
veritas/
├── .claude-plugin/plugin.json
├── cli/
│   ├── adapters.json
│   ├── index.js
│   └── package.json
├── src/veritas/
│   ├── SKILL.md
│   ├── personas/
│   │   ├── skeptic.md
│   │   ├── sentinel.md
│   │   └── archivist.md
│   ├── modules/
│   │   ├── ground-check.md
│   │   ├── blast-radius.md
│   │   ├── handoff.md
│   │   ├── postmortem.md
│   │   ├── persona.md
│   │   └── ledger.md
│   ├── data/
│   │   ├── risky-ops.csv
│   │   └── trigger-verbs.csv
│   ├── state/
│   │   └── schema.json
│   └── scripts/
│       ├── verify.py
│       └── state.py
├── docs/
│   └── ACTIVATION.md
├── package.json
├── skill.json
├── README.md
├── LICENSE
└── .gitignore
```

---

## Design principles

- **Small surface.** Six modules, three personas, one decision tree. If a task does not hit a trigger, the skill stays dormant.
- **No fabrication.** If a claim cannot be grounded, the correct answer is "not verified".
- **Reversibility is a real reference.** A rollback plan must point to a commit, backup, or compensating action — never a hypothesis.
- **State is plaintext.** `.veritas/` is human-readable markdown and JSON; no database, no daemon, no network.
- **Silence beats noise.** Most sessions produce zero postmortem entries. That is the target.
- **Append-only where it matters.** `audit.log` records declined actions — history of things *not* done is itself evidence.

---

## License

MIT. See [LICENSE](LICENSE).
