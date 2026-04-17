# Veritas

A guardrail skill for AI-assisted coding. One install, four responsibilities:

1. **Ground claims** — before the assistant states a fact about your code, verify it.
2. **Gate actions** — before a destructive or shared-state action, check blast radius and reversibility.
3. **Hand off cleanly** — when a session ends, write a canonical scroll; on resume, read it first.
4. **Capture lessons** — only record what was actually surprising. Most sessions produce none.

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

### Uninstall

```bash
npx veritas-cli uninstall --ai <platform>
```

---

## How activation works

Veritas auto-activates when the assistant's next action matches one of four triggers. You do not invoke it with a slash command — it invokes itself.

| Trigger | Module |
|---|---|
| Assistant is about to state a factual claim about code | `ground-check` |
| Assistant is about to execute a risky or irreversible operation | `blast-radius` |
| User pauses, resumes, or switches tools | `handoff` |
| Task completed, or a mistake was just corrected | `postmortem` |

Trigger verbs and risky-operation patterns are in [`src/veritas/data/`](src/veritas/data/). The main routing logic is in [`src/veritas/SKILL.md`](src/veritas/SKILL.md).

---

## The four modules

### `ground-check` — anti-hallucination

Before asserting "function X does Y" or "file Z contains W", verify. Uses file-read and code-search, not recall. Produces a `CLAIM / GROUNDED / EVIDENCE / GAPS` block. If a claim cannot be grounded, the output is "not verified", not a confident guess. See [`modules/ground-check.md`](src/veritas/modules/ground-check.md).

### `blast-radius` — risk gate

Before `rm -rf`, `DROP TABLE`, `git push --force`, `terraform destroy`, or any shared-state action, answer four questions: scope, reversibility, blast, authorization. Irreversible actions pause for confirmation even when authorized. See [`modules/blast-radius.md`](src/veritas/modules/blast-radius.md).

### `handoff` — cross-session continuity

One page, canonical format, written to `HANDOFF.md`. Includes goal, state, decisions with reasons, open questions, exact next step, and a **do-not** list (the most expensive part of resuming is rediscovering dead ends). Portable across tools. See [`modules/handoff.md`](src/veritas/modules/handoff.md).

### `postmortem` — lesson capture

The filter: *would a future session, with no memory of today, be worse off without this entry?* If no, write nothing. Record only what contradicts a default, encodes a hidden constraint, or cost real time. Every entry has an `EXPIRES` field. See [`modules/postmortem.md`](src/veritas/modules/postmortem.md).

---

## Helper script

`src/veritas/scripts/verify.py` — zero-dependency grounding helpers:

```bash
python verify.py path src/foo.py
python verify.py symbol src/foo.py my_function
python verify.py version package.json react
```

Exit `0` if verified, `1` if not.

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
│   ├── modules/
│   │   ├── ground-check.md
│   │   ├── blast-radius.md
│   │   ├── handoff.md
│   │   └── postmortem.md
│   ├── data/
│   │   ├── risky-ops.csv
│   │   └── trigger-verbs.csv
│   └── scripts/
│       └── verify.py
├── package.json
├── skill.json
├── README.md
├── LICENSE
└── .gitignore
```

---

## Design principles

- **Small surface.** Four modules, one decision tree. If a task does not hit a trigger, the skill stays dormant.
- **No fabrication.** If a claim cannot be grounded, the correct answer is "not verified".
- **Reversibility is a real reference.** A rollback plan must point to a commit, backup, or compensating action — never a hypothesis.
- **Silence beats noise.** Most sessions produce zero postmortem entries. That is the target.

---

## License

MIT. See [LICENSE](LICENSE).
