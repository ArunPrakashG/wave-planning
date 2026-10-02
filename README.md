# wave-planning

A Claude Code plugin for **wave planning**: plan software as dependency-ordered *waves*, then build each wave's *phases* in parallel with subagents, each in its own git worktree, on the cheapest model that is adequate for the job.

Background: [Wave Planning: Parallel AI Development](https://arunprakashg.com/blogs/wave-planning-parallel-ai-development/) and [What a Wave Actually Is](https://arunprakashg.com/blogs/wave-planning-what-a-wave-actually-is/).

> Claude Code only. It depends on subagents, git worktrees and a shell, so it does not run on claude.ai or Cowork.

## The idea in one minute

- **Step → phase → wave.** A phase is one agent's unit of work. A wave is the largest set of phases that can run at once because none waits on another and none writes the same files.
- Waves run one after another. Phases inside a wave run in parallel.
- A **phase** gets a shallow gate (format, lint, types, unit tests). A **wave** gets a functional gate, run on the merged result.
- The plan is written and approved before any code. You own what the dependency tree misses.

## Install

```bash
claude plugin marketplace add <owner>/<repo>
claude plugin install wave-planning@arunprakashg-plugins
```

## Use

1. `/wave-planning:wave-plan <your idea>`: scope the project, write one spec per feature, design the UI if there is one (mockup in Claude Design, then frozen), and decompose into waves. You approve at each stage. Output: `plan.md` at the project root and specs under `docs/waves/specs/`.
2. `/wave-planning:wave-execute`: runs the plan wave by wave. It validates the plan, creates a worktree per phase, dispatches one subagent per phase on the model the plan assigned (haiku, sonnet or opus), gates each phase, merges, runs the wave's functional gate, and only then moves on. You can stop and resume: progress lives in the `plan.md` status block.

## Model routing

Each phase is scored 0–2 on scope, ambiguity, risk and reasoning. Sum 0–2 → haiku, 3–5 → sonnet, 6 or more → opus. Risk 2 (security, data, money, migrations) forces opus. Ambiguity 2 sends the phase back to planning instead of to a bigger model. A failed phase retries once, then moves up one tier, then asks you.

## Requirements

- Claude Code (recent enough to support plugins, subagents and skills)
- git, with a repository that has at least one commit (the plugin offers `git init`)
- Python 3 on `PATH` (standard library only) for the plan validator
- **Permissions:** workers edit files and run your gate commands. Plugin agents cannot set their own permission mode, so run with a permission mode, or allow rules in your settings, that let subagents edit files and run your format, lint, typecheck and test commands. If a worker is denied, the orchestrator stops and tells you what is missing.

## Limits

- It saves wall-clock time, not total work. Total tokens and effort are about the same or higher.
- The plan is the product. A plan with a hidden dependency fails at merge or at the wave gate; the validator catches structural problems, not what nobody wrote down.
- A feature that depends on another waits for all of that feature's phases. Split features finer for finer parallelism.
- Machine-readable blocks use a small flow-style YAML subset (one `key: value` per line, lists as `[a, b]`).

## Development

```bash
python3 -m unittest discover -s tests      # unit tests for the Python toolkit
claude plugin validate --strict .          # manifest, skills, agents
claude plugin eval .                       # behavior evals (costs tokens)
```

Design spec: `docs/specs/2026-10-02-wave-planning-plugin-design.md`. License: MIT.
