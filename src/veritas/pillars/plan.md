# Pillar: plan

**Purpose** — turn a goal into an executable plan without fabricating facts. Every load-bearing assumption becomes a claim in the DAG so later work can verify or invalidate it.

## When this pillar activates

- User says: "plan", "PRD", "spec", "break this down", "architecture for".
- Explicit slash: `/plan <goal>`.
- A new feature is about to start with no written plan.

## The four artifacts, in order

Each artifact is short and grounded. If any section would be filler, omit it.

### 1. Brainstorm

Three options, one recommendation, the main trade-off. 2–3 sentences each, not a wall of text. Purpose: surface the decision space so the user can redirect before the plan commits.

### 2. PRD skeleton

```
Goal:        <one paragraph, user-centric>
Users:       <who, specifically>
Non-goals:   <what this does not try to do>
Success:     <3–5 measurable criteria>
Risks:       <the 2–3 ways this fails>
```

Every `Risks` line is a candidate for the claim DAG — we will want evidence that each risk is or isn't real.

### 3. Architecture sketch

- **Components** — the 3–7 units that do the work. Name, responsibility, one line each.
- **Data flow** — where inputs come from, where outputs go. Prefer a numbered list to ASCII art.
- **Decisions** — at most 3, each with `Why:` and `Revisit when:` (see `src/veritas/modules/track-state.md` for the DECISIONS.md format).

Large decisions get their own entry in `.veritas/DECISIONS.md`.

### 4. Stories

3–5 user stories. Each:

```
As a <user>
I want <capability>
So that <outcome>
Acceptance:
  - <observable condition>
  - <observable condition>
Test ideas:
  - <a test that would fail today and pass when done>
```

A story without a failing-test idea is speculation. Kill it or sharpen it.

## State effects

- Every assumption whose truth affects the plan → append to `.veritas/claims.jsonl` with `status: unverified`.
- Every architectural decision → append to `.veritas/DECISIONS.md` with `Revisit when`.
- No HANDOFF.md, no LESSONS.md yet — this pillar stops at "plan ready".

## Handoff

The plan pillar feeds `execute`. The execute pillar reads the plan, grounds the claims, and gates each step.

## Anti-patterns

- Writing a PRD that restates the goal in fancier words.
- Architecture diagrams with boxes for things the codebase does not have yet.
- Stories without acceptance criteria (= wishes).
- Risks that cannot be falsified (= horoscopes).
