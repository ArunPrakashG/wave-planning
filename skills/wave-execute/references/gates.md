# Gates

Two levels, as in wave planning: a **shallow** gate per phase (is it structurally sound?) and a **functional** gate per wave (does the integrated behavior actually hold?).

## Phase verification (shallow gate)

After a worker reports `DONE` or `DONE_WITH_CONCERNS`, you verify it yourself. A worker's own gate output is evidence, not proof.

1. Worktree clean, diff within ownership, main tree clean: the three commands in `worktrees.md`, "Verify a phase".
2. Re-run the phase's gate commands in the worktree, in order: format, lint, typecheck, unit.

   ```bash
   ( cd ".worktrees/$P" && <format> && <lint> && <typecheck> && <unit> )
   ```

   Skip a command that is `n/a` in the plan. Stop at the first failure.
3. Any failure is handled with the retry and escalation ladder in `failure-handling.md`. Only a phase that passes all of this is marked `gated`.

## Wave gate (functional)

Run once all phases of the wave are merged into `wave/integration` and integration-owned edits are committed, with the integration branch checked out in the main tree.

1. Confirm `git status --porcelain` is empty and bootstrap has been run.
2. Collect, from `plan.md` and the specs:
   - the wave's `criteria` (each id with its text and `verify` string, from the spec);
   - the wave's `integration_checks`;
   - the gate commands from the header;
   - a run hint if any `http:` criterion exists (how to start the app, for example `npm start`; ask the user if the plan does not say);
   - the design snapshot path if any criterion is `design-fidelity:`.
3. Dispatch one Agent call: `subagent_type: "wave-planning:wave-validator"`, `model: "sonnet"` (or `"opus"` for a wave containing a risk-flagged phase), and a prompt listing the above, one criterion per line as `<id> | <text> | <verify>`.
4. Read the validator's report. Check that `git status --porcelain` is still empty; if the validator changed anything, that is a failure to report to the user.
5. Decide:
   - `RESULT: PASS` → the wave is green.
   - `RESULT: FAIL` → trace each failing criterion to its spec and phases (`F2.AC1` is spec F2; its phases are in the plan) and follow "Wave gate failed" in `failure-handling.md`.
   - `RESULT: INCOMPLETE` → something could not be verified (for example no run hint, or visual comparison unavailable). Show the user exactly what was not verified and ask how to proceed: provide the missing information, accept it explicitly, or stop. Never treat INCOMPLETE as PASS on your own.

## What counts as passing

Every acceptance criterion in the wave and every integration check is `PASS`, observed by running it. Absence of a failure is not a pass.
