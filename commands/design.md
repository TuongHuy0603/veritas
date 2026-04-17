---
description: Produce a grounded UI/UX design system for the current project — colors, typography, spacing, components, accessibility checks. No generic templates.
argument-hint: "<screen or product description>"
---

You are activating the **design** pillar of Veritas. Read `src/veritas/pillars/design.md` for the full contract.

Brief from the user: `$ARGUMENTS`

Rules:

- **Ground first.** Before prescribing a color palette or font pair, detect the project's existing stack (read `package.json`, `tailwind.config.*`, `tokens.css`, Figma tokens if available). Match the existing system; do not overwrite.
- **Minimum viable system.** Output only what the request needs: primary/secondary colors, heading + body font pair, spacing scale, 3–5 core components. No 20-color palettes "just in case".
- **Accessibility is not optional.** Every color pair ships with its WCAG contrast ratio. Every interactive component ships with keyboard + screen-reader notes.
- **Rules, not opinions.** Reference `src/veritas/data/design-rules.csv` for industry-specific patterns. Do not invent.

Output sections:

1. **Detected context** — stack and any existing design tokens.
2. **Design system** — colors (with contrast), typography, spacing, radii.
3. **Component inventory** — minimal set needed for the brief.
4. **Accessibility notes** — one line per interactive component.
5. **Open questions** — anything the user must decide before build.
