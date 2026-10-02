# Branches and worktrees

Conventions: integration branch `wave/integration`; phase branches `wave/<n>/<phase-id>`; fix branches `wave/<n>/<phase-id>-fix<k>`; worktrees live in `.worktrees/<phase-id>` (gitignored).

Why you create worktrees yourself: the Agent tool's built-in `isolation: "worktree"` branches from the default branch, not from your current branch. Phases in wave N+1 must build on the gated result of wave N, so every worktree is cut from `wave/integration` explicitly.

## Setup

```bash
git rev-parse --is-inside-work-tree
git branch --show-current            # record this as base_branch in the status block
git status --porcelain               # must be empty, apart from files you commit below
```

If there are unrelated uncommitted changes, ask the user to commit or stash them first. Do not stash for them.

Commit the plan, specs, and design so every worktree contains them (ask the user before committing):

```bash
git add plan.md docs/waves
git commit -m "docs(wave): approved wave plan"
grep -qxF '.worktrees/' .gitignore 2>/dev/null || echo '.worktrees/' >> .gitignore
git add .gitignore
git commit -m "chore: ignore .worktrees"
```

Create or resume the integration branch and the worktree directory:

```bash
git switch -c wave/integration       # fresh run
# git switch wave/integration        # resuming
mkdir -p .worktrees
```

Record `base_branch` and `integration_head` (`git rev-parse HEAD`) in the status block, commit it, then run `bootstrap` in the main tree.

## Per phase

```bash
N=<wave number>; P=<phase id>
git worktree add -b "wave/$N/$P" ".worktrees/$P" wave/integration
( cd ".worktrees/$P" && <bootstrap command from the plan header> )
```

A fresh worktree has the committed files only. Installed dependencies and ignored files such as `.env` are not there, which is what `bootstrap` is for. If bootstrap fails, stop and show the user; do not dispatch a worker into a broken worktree.

Use the absolute path of `.worktrees/$P` in the worker's brief.

## Verify a phase (after its worker reports)

```bash
git -C ".worktrees/$P" status --porcelain     # must print nothing
git -C ".worktrees/$P" diff --name-only wave/integration...HEAD \
  | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/check_owned.py" --owns '<glob1>' '<glob2>'
git status --porcelain                        # main tree must print nothing
```

Quote the globs so the shell does not expand them. Take them from the phase's `owns` in `plan.md`. A non-empty worktree status means uncommitted work; a `NOT-OWNED` line means the worker wrote outside its ownership; a non-empty main-tree status means a stray write. Each is a failure: see `failure-handling.md`.

## Merge

In the main tree, with `wave/integration` checked out, in phase-id order:

```bash
git merge --no-ff "wave/$N/$P" -m "merge(wave-$N): $P"
```

If a merge conflicts, run `git merge --abort`, list the conflicting files, and stop. The ownership graph missed something; this is never auto-resolved.

After all phases are merged, apply the wave's `integration_owned` edits yourself (lockfile updates, route registrations, index exports, using what workers listed under CONCERNS), then:

```bash
git add -A
git commit -m "chore(wave-$N): integration-owned updates"
```

If a lockfile or manifest changed, re-run `bootstrap` in the main tree so the wave gate runs against installed dependencies.

## Clean up after a green wave

```bash
git worktree remove --force ".worktrees/$P"
git branch -d "wave/$N/$P"
git worktree prune
```

## Fix worktrees

When a gate failure needs another attempt, cut a fresh worktree from the current integration head:

```bash
git worktree add -b "wave/$N/$P-fix$K" ".worktrees/$P-fix$K" wave/integration
```

## Finish

Only after the user agrees: `git push -u origin wave/integration`, then open a PR. Never push on your own.
