---
name: wave-plan
description: Use when planning a software project or large change to be built in parallel by AI agents using wave planning. Scopes features, writes one spec per feature, designs the UI if there is one, then decomposes the work into dependency-ordered waves with gates and model assignments, all before any code is written.
argument-hint: "[project idea or path to a brief]"
---

# Wave Plan

Wave planning groups work by **dependency**, not by time. Steps roll up into phases. Phases are scheduled into **waves**: a wave is the largest set of phases that can run at the same time because none of them waits on another and none of them writes the same files. Waves run one after another. Phases inside a wave run in parallel.

This skill is the whole planning stage. It ends with an approved `plan.md`; building starts only when the user runs `/wave-planning:wave-execute`.

<HARD-GATE>
Do not write product code, scaffold the project, or install anything during planning. The only files you may create or edit are `plan.md` and files under `docs/waves/`. Do not start a later stage until the user has approved the earlier one. A plan the user has not approved is a draft.
</HARD-GATE>

The plan is only as good as its dependency map. The user owns scoping the work and catching what the map misses; your job is to make hidden dependencies visible, not to hide them behind a tidy table.

## Stage 1: Scope

Follow [references/spec-interview.md](references/spec-interview.md).

1. If the request points at an existing repository, read its structure first. Greenfield and existing code are planned differently.
2. Ask one question at a time: purpose and users, what success looks like, constraints (stack, hosting, deadlines).
3. Propose the **feature list** (a name and one line each) and get the user's approval before writing any spec.
4. For each feature, write `docs/waves/specs/<id>.md` from `${CLAUDE_PLUGIN_ROOT}/templates/spec.md`. Every acceptance criterion needs a verification method (`test:`, `cmd:`, `http:` or `design-fidelity:`). A criterion you cannot verify gets rewritten into one you can, or dropped.
5. Show the user the specs and get approval.

## Stage 2: Design (only if any feature has UI)

Invoke the `wave-design` skill and wait for the frozen design. If no feature has UI, write `design: none` in the plan header. Do not decompose until the design is approved and frozen.

## Stage 3: Decompose

Follow [references/decomposition.md](references/decomposition.md) and [references/four-graphs.md](references/four-graphs.md).

1. Turn each spec's steps into **phases**: tightly coupled steps become one phase, and each phase has its own narrow `owns` globs.
2. Add real dependency edges between phases.
3. Assign phases to **waves** (earliest possible wave, then resolve ownership conflicts and width).
4. Mark **integration-owned** files: files several phases legitimately need, which the orchestrator edits at merge time.
5. Define the **gates**: detect and confirm the shallow-gate commands and the bootstrap command; assign each acceptance criterion to the wave that gates it; add cross-phase integration checks.
6. Score every phase with the `model-routing` skill and record `model`, `score` and `rationale`.
7. Write `plan.md` at the project root from `${CLAUDE_PLUGIN_ROOT}/templates/plan.md`.
8. Validate:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_plan.py" --root .
   ```

   Fix every `ERROR` and re-run until it prints `OK: plan is valid`. Never present an invalid plan.
9. Report the plan's shape: number of waves, widest wave, the critical path (the longest dependency chain), and the model mix.

## Approval

Before asking for approval, ask the user directly: **"What does this plan assume that isn't written down?"** Shared config, environment variables, migration order, feature flags, generated code, CI. Add anything they name and revalidate.

Then show the summary and ask for explicit approval. When they approve, tell them to run `/wave-planning:wave-execute`.

Spec fields (`depends_on`, `owns`, acceptance criteria) are canonical. To change a dependency, edit the spec and regenerate the plan; never hand-edit the plan's copy of a spec field.
