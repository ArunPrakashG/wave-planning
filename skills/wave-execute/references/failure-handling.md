# Failure handling and resume

The principle: wave planning puts the plan owner in charge of what the dependency tree misses. When something unexpected happens, you surface it with evidence and let the user decide. You do not improvise.

## Model ladder

`haiku` → `sonnet` → `opus`. For a failed phase: retry once on the same tier with the failure output added to the brief; if it fails again, move up exactly one tier; if it fails on `opus`, stop and ask the user. Never retry on a lower tier.

## Worker reports

- **`BLOCKED`** or a CONCERNS entry that names a dependency, file, or assumption the plan did not mention: **pause the wave.** Do not merge anything from it. Show the user the worker's words, which phase, and what the plan would need (a new dependency edge, a file moved to integration-owned, a spec question answered). Offer a replan. Mark the phase `blocked`.
- **`DONE_WITH_CONCERNS`**: read the concerns. If they are only notes, continue and include them in the wave report. If they describe something the plan missed, treat as `BLOCKED`.

## Verification failures

- **Shallow gate fails** (your re-run, or the worker's report): apply the model ladder. Re-dispatch into the same worktree with the failing output in the brief.
- **`NOT-OWNED` lines** from `check_owned.py`: the worker wrote outside its ownership. Do not merge. Show the user the paths. Either the plan's ownership is wrong (replan) or the worker misbehaved (re-dispatch with an explicit reminder, on the next tier).
- **Uncommitted changes in the worktree**: re-dispatch the worker with the instruction to commit. If the worker cannot, treat it as a failure.
- **Dirty main tree** at the barrier: something wrote outside the worktrees. Stop, show `git status`, and ask the user before touching it.

## Merge conflict

`git merge --abort`, list the conflicting files and which two phases produced them, and stop. The ownership graph missed an overlap. Offer a replan: usually split ownership differently or mark the file integration-owned. Never resolve it yourself.

## Wave gate failed

1. For each failing criterion, find its spec and phases. If a criterion spans several phases, the cause may be in any of them; read the validator's evidence before choosing.
2. Create a fix worktree from the current integration head (`worktrees.md`, "Fix worktrees") and dispatch a worker with a brief containing the validator's evidence. Start on the failing phase's own tier; the ladder applies across attempts.
3. Verify the fix as in "Phase verification", merge it, and run the wave gate again from scratch.
4. After the ladder is exhausted, stop and ask the user.

## Permission denials

If a worker reports that a tool or command was denied, do not loop. Tell the user which permission is missing (editing files, running a gate command), and ask them to allow it in their Claude Code permission settings or choose a more permissive mode for this run, then re-dispatch.

## Replanning

Completed (`done`) waves stay as they are. Show the user what changed, return to the `wave-plan` decomposition stage with the new information, and have it regenerate only the pending part of `plan.md` from the specs, preserving the status of everything already `done`. The new plan must pass `validate_plan.py`, and the user approves it again before you continue.

## Resume

When the status block shows earlier progress, or `$ARGUMENTS` names a wave:

1. List what is on disk: `git worktree list`, `git branch --list 'wave/*'`, and `git log --oneline -5 wave/integration`.
2. Compare it with the status block. The integration branch is the truth for what is merged: a wave counts as `done` only if its status says so **and** its merge commits are on `wave/integration`.
3. Remove orphans: worktrees and `wave/<n>/…` branches for phases that are not `running` or `blocked`, using `git worktree remove --force` and `git branch -D` after you have checked the branch has no unmerged commits you need (`git log wave/integration..<branch>`). Ask the user if a branch holds work you cannot account for.
4. A phase left `running` has no trustworthy state: delete its worktree and branch and start it again from a fresh worktree.
5. Continue at the first wave that is not `done`. Tell the user what you found and what you cleaned up before dispatching.
