---
name: wave-execute
description: Use when a wave-planning plan.md has been approved and is ready to build, or when resuming an interrupted wave run. Runs each wave's phases in parallel subagents inside git worktrees, gates them, merges them, and validates the merged result before starting the next wave.
disable-model-invocation: true
argument-hint: "[wave number to start from]"
---

# Wave Execute

You are the **orchestrator**. You dispatch, verify, merge, gate and report. You never write product code yourself. You are the only agent that spawns subagents: `wave-worker` and `wave-validator` are leaf nodes and must never spawn others.

All state lives in the `yaml status` block of `plan.md`, so a run can always be resumed.

## Hard rules

- Never start a wave on a red or unverified integration branch.
- Never skip or weaken a gate, and never mark a wave done on `FAIL` or `INCOMPLETE`.
- Never auto-resolve a merge conflict, and never improvise around a worker's `BLOCKED`. Either means the plan missed something: stop and show the user.
- Never use the Agent tool's `isolation: "worktree"`. You create the worktrees yourself so each phase branches from the gated integration head.
- Never push, force-push, or delete branches you did not create. Ask before opening a PR.

## 0. Preflight (once per run)

1. Read `plan.md`, then validate it:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_plan.py" --root .
   ```

   Any `ERROR` stops the run. Show it to the user and do not execute an invalid plan.
2. Confirm this is a git repository with at least one commit. If not, offer `git init` plus an initial commit and wait for a yes.
3. Run `printenv CLAUDE_CODE_SUBAGENT_MODEL_FORCE`. If it prints `1`, tell the user that model routing will be overridden and ask whether to continue.
4. Set up branches and the worktree directory: [references/worktrees.md](references/worktrees.md), section "Setup". Run the plan's `bootstrap` command in the main tree.
5. If the status block shows earlier progress, do "Resume" in [references/failure-handling.md](references/failure-handling.md) before dispatching anything.

## 1. For each wave, in order

Start at `$ARGUMENTS` if given, otherwise at the first wave that is not `done`.

1. **Announce** the wave: its phases, models, and the functional gate it must pass.
2. **Create a worktree per phase** and run `bootstrap` in each ([references/worktrees.md](references/worktrees.md), "Per phase"). Set the wave and its phases to `running` in the status block and commit it.
3. **Dispatch all phases at once.** Send one message containing one Agent call per phase, so they run in parallel (never more than `max_wave_width`). Each call uses `subagent_type: "wave-planning:wave-worker"`, `model` set to the phase's tier (`haiku`, `sonnet` or `opus`), and a self-contained brief built from [references/worker-brief.md](references/worker-brief.md).
4. **Wait for every worker** (the wave barrier). Do nothing else until all have reported.
5. **Verify each report** ([references/gates.md](references/gates.md), "Phase verification"): ownership of the diff, a clean worktree, a clean main tree, and the shallow gate re-run by you. Never trust a worker's own gate output alone. Handle `BLOCKED`, concerns, and failures with [references/failure-handling.md](references/failure-handling.md). Mark verified phases `gated`.
6. **Merge** the verified phase branches into `wave/integration` in phase-id order, then apply the wave's integration-owned edits ([references/worktrees.md](references/worktrees.md), "Merge"). Mark them `merged`.
7. **Run the wave gate**: dispatch `wave-validator` on the merged integration branch ([references/gates.md](references/gates.md), "Wave gate"). Use `opus` for the validator if any phase in the wave belongs to a risk-flagged spec, otherwise `sonnet`.
8. **PASS:** record the new integration head SHA, set the wave and its phases to `done`, remove the wave's worktrees, commit the status, and show the user a short wave report (what merged, gate evidence, any concerns).
   **FAIL or INCOMPLETE:** follow "Wave gate failed" in [references/failure-handling.md](references/failure-handling.md). Do not start the next wave.
9. **Pause for the user** after wave 1 and after any wave that contains a risk-flagged phase: show the report and wait for them to say continue. Otherwise continue to the next wave.

## 2. Finish

When every wave is `done`, summarise: waves run, phases per model tier, retries and escalations, and the integration branch name. Offer, and do not do unprompted, to open a pull request or merge `wave/integration` into the base branch.

## Status block

`plan.md` ends with a `yaml status` block. Update it with the Edit tool and commit after every state change, so the integration branch and the block never disagree.

```yaml
base_branch: main
integration_branch: wave/integration
integration_head: <sha after the last done wave, or none>
W1: pending | running | done | blocked
P1a: pending | running | gated | merged | done | blocked
```
