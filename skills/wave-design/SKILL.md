---
name: wave-design
description: Use when an approved wave-plan scope includes a user interface and a mockup must be designed, approved, and frozen before the work is decomposed into phases.
---

# Wave Design

The design stage of wave planning. It turns the approved scope into a mockup the user signs off on. After sign-off the design is **frozen**: execution builds exactly that and nothing else, so UI phases can run in parallel without arguing about what the screens look like.

You are normally invoked by `wave-plan`. You can also be invoked directly to redo the design before a plan is approved.

## Preconditions

- Feature specs exist under `docs/waves/specs/` and the user has approved them. If not, stop and return to `wave-plan`.
- At least one feature has UI. Backend-only or CLI-only projects skip this skill; `wave-plan` records `design: none`.

## Process

1. **Gather direction.** Ask one question at a time: who the users are, the tone or brand, any references or an existing design system, target platform and breakpoints. Check the repository for existing styles, tokens, or components first and reuse them.
2. **List the screens.** Give every screen an id of the form `screen-<name>` (for example `screen-cart`) and map each to the feature spec it belongs to. Always add a `tokens` artboard for colour, spacing and type. Show the user this list and get a yes before you draw anything.
3. **Build the mockup.** Prefer Claude Design (see [references/claude-design-flow.md](references/claude-design-flow.md)). If the Artifact tool is not available, build the HTML fallback (see [references/html-fallback.md](references/html-fallback.md)). One labelled artboard or section per screen id.
4. **Iterate.** Show the user the result and revise until they say it is approved. Approval must be explicit; silence is not approval.
5. **Freeze.** On approval:
   - Save a snapshot to `docs/waves/design/snapshot.html` (the procedure and fallback are in the Claude Design reference). Workers read the snapshot, so it must contain every screen id and `tokens`.
   - Write `docs/waves/design/DESIGN.md`: the Claude Design URL and approval date (or "HTML fallback"), a table of screen id → feature id, a short token summary, and the line `FROZEN: changes after approval require replanning.`
   - Add each screen a spec uses to that spec's `reads` list as `docs/waves/design/snapshot.html#screen-<name>`.
   - Return control to `wave-plan` with `design: docs/waves/design/snapshot.html` for the plan header.

## Rules

- Never edit the design after approval. If the user wants a change later, including mid-execution, stop and send them back to `wave-plan` to replan; do not patch it silently.
- Design only what the approved specs need. No extra screens.
- Do not write application code. This stage produces design artifacts and documentation only.
