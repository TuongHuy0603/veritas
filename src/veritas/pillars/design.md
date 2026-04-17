# Pillar: design

**Purpose** — produce a grounded, accessible UI/UX design system for the **current** project, not a generic template. Every prescription traces to either the project's existing stack or `data/design-rules.csv`.

## When this pillar activates

- User says: "design", "landing page", "UI for", "style guide", "design system", "palette", "typography".
- Explicit slash: `/design <brief>`.
- A frontend phase is about to start with no design contract.

## Ground first

Before prescribing anything, detect the project's existing system:

- Read `package.json` / `pyproject.toml` / `Gemfile` for frontend framework.
- Read `tailwind.config.*`, `tokens.css`, `styles/*.css`, `theme.ts` for existing tokens.
- If tokens exist, **extend** them; do not override.
- If Figma tokens are exported, honor them.

State the detection result as the first section of output. If detection fails, say so — do not invent a stack.

## The four sections

### 1. Detected context

```
Framework: <React | Next | Vue | Svelte | plain | unknown>
Styling:   <Tailwind | CSS modules | styled-components | vanilla | unknown>
Existing tokens: <present | absent — short list if present>
Notes: <any constraint the user should know>
```

### 2. Design system (minimum viable)

```
Colors:
  primary:    <hex>  (contrast vs background: <ratio>:1, WCAG <AA|AAA>)
  secondary:  <hex>  (contrast: <ratio>:1)
  accent:     <hex>  (contrast: <ratio>:1)
  neutral:    <5-stop scale>
  semantic:   success <hex>, warning <hex>, danger <hex>
Typography:
  heading:    <font>, weights, scale
  body:       <font>, weights, line-height
Spacing:      <scale — 4, 8, 12, 16, 24, 32, 48, 64>
Radii:        <scale — 4, 8, 12, 16>
```

No 20-color palettes. No 12-font stacks. Ship what the brief asks for.

### 3. Component inventory

Only the components the brief actually needs. For each:

```
<Name> — <purpose, one line>
  variants:   <default / hover / active / disabled>
  a11y:       <keyboard model + ARIA role>
```

### 4. Accessibility notes

One line per interactive component:

- Focus ring is visible against every background it appears on.
- Every icon button has a text label (visible or `aria-label`).
- Every color pair meets WCAG AA (4.5:1 for body, 3:1 for large text or UI chrome).
- Motion: respect `prefers-reduced-motion`.

### 5. Open questions

Anything the user must decide before build begins. If the list is empty, the brief was underspecified and you have been guessing.

## State effects

- Detected context and chosen tokens → `.veritas/DECISIONS.md` (why: this token choice, revisit when: brand changes).
- No claims go in the DAG from this pillar — design is a contract, not a fact about code.

## Anti-patterns

- Prescribing Tailwind when the project has CSS modules.
- Shipping a color palette without contrast ratios.
- 8-variant component specs for a brief that needs 2.
- "Modern, clean, minimal" — these words mean nothing; name specific values.
- Ignoring the project's existing tokens "to start fresh".
