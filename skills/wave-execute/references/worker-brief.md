# Worker brief

Build one brief per phase and pass it as the Agent call's `prompt`. The worker sees nothing else: no conversation, no plan, no other phases. Everything it needs goes in here. Replace every `<...>` with real values from `plan.md` and the spec. Do not paste the whole plan.

Agent call parameters: `subagent_type: "wave-planning:wave-worker"`, `model: "<haiku|sonnet|opus from the phase>"`, `description: "<phase id> <short title>"`, `prompt: <the brief below>`.

```
You are implementing phase <PHASE_ID> of a wave plan: <phase title>.

WORKTREE (work only here): <absolute path to .worktrees/PHASE_ID>
PHASE BRANCH: wave/<N>/<PHASE_ID>
BASE BRANCH: wave/integration

STEPS TO IMPLEMENT (from spec <SPEC_ID>, file <path to spec>):
<paste the numbered steps for this phase, e.g. F2.1 and its one-sentence description, verbatim from the spec>

SPEC EXCERPT:
<paste the spec's Summary and In/Out of scope, plus the acceptance criteria that this phase contributes to, verbatim>

YOU OWN (the only paths you may write, relative to the worktree):
<one glob per line>

DO NOT TOUCH:
<the wave's integration-owned files, one per line>
and any path not listed under YOU OWN. If you need one of these changed, report BLOCKED or list it under CONCERNS; do not edit it.

READ-ONLY CONTEXT:
<files and design screens from the spec's reads, e.g. docs/waves/design/snapshot.html#screen-cart>
<for a UI phase: implement only what the frozen design shows; do not add screens or features>

SHALLOW GATE (run inside the worktree, in this order):
format: <command or n/a>
lint: <command or n/a>
typecheck: <command or n/a>
unit: <command or n/a>

Follow your agent instructions for rules, procedure and the report format.
```

## Notes for the orchestrator

- Include the verbatim acceptance criteria, not a paraphrase. They are the definition of done.
- A retry of a failed phase uses the same brief plus a `PREVIOUS ATTEMPT` section containing the failing gate output or the validator's failure evidence, and works in the same worktree.
- A fix after a failed wave gate uses a fresh worktree (`-fix<K>`) and a brief containing the validator's evidence for the failing criteria.
- If the phase's spec has a `risk` flag, add one line: `This phase touches <risk>; be conservative and report every assumption.`
