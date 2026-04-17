---
description: Turn a goal into a plan — brainstorm, PRD skeleton, architecture sketch, user stories. Grounds every assumption in the claim ledger.
argument-hint: "<goal>"
---

You are activating the **plan** pillar of Veritas. Read `src/veritas/pillars/plan.md` for the full contract. Produce the four artifacts below **in order**, each in its own section, concise. Do not invent facts about the codebase — when you need to state one, log it as a claim via `scripts/track-claims.py add …` first.

Goal from the user: `$ARGUMENTS`

Output sections:

1. **Brainstorm** — 3 options, one recommendation, main trade-off.
2. **PRD skeleton** — goal, users, non-goals, success criteria, risks.
3. **Architecture sketch** — components, data flow, two decisions with `Revisit when` clauses.
4. **Stories** — 3–5 user stories, each with acceptance criteria and test ideas.

After writing, append architectural decisions to `.veritas/DECISIONS.md` and any load-bearing assumptions to `.veritas/claims.jsonl` (status=unverified). Do not proceed to implementation — this pillar stops at "plan ready".
