# wave-planning plugin — design spec

Date: 2026-10-02 · Status: draft for review · Author: Arun Prakash G

## 1. Purpose

A Claude Code plugin that turns the *wave planning* method (see the two blog posts under "Sources") into a runnable workflow:

1. **Scope** a project with the user and write one spec per feature.
2. **Design** (UI projects only) a mockup in Claude Design, approved and then frozen.
3. **Decompose** features into steps → phases → **waves** using four graphs, write the root `plan.md`, and assign a model tier per phase.
4. **Execute** wave by wave. Phases inside a wave run in parallel, one subagent each, each in its own git worktree. Phases get a shallow gate; each wave gets a functional gate on the merged result.

Success: a user can go from "I want to build X" to a verified, merged result with every phase run on the cheapest model that is adequate for it, and with a human approving at each planning stage and reviewing each wave.

### Non-goals (v1)
- Not a scheduler or infrastructure; it is a planning discipline plus an orchestration prompt set.
- No claim of reduced total effort — only reduced wall-clock time.
- No hook-based hard write-blocking of workers (post-hoc diff verification instead; hooks are a possible v2).
- Not usable on claude.ai / Cowork: it depends on subagents, git worktrees, and shell. Claude Code only.
- No dependency on other plugins (standalone; does not require superpowers).

## 2. Method rules the plugin enforces (from the blogs)

- Hierarchy: **step → phase → wave**. A wave is a *schedule*, not a container: the largest set of phases that can run at once.
- **Dependency rule:** a phase enters a wave only when all its prerequisites are in earlier, completed waves.
- **Conflict rule:** phases with overlapping `owns` paths never share a wave, regardless of dependency.
- **Ownership rule:** each phase has exclusive write access to its declared paths.
- **Four graphs** are produced and checked: dependency, ownership, context, validation.
- **Validation rule:** shallow gate per phase (format/lint/types/unit), functional gate per wave.
- The plan is complete *before* execution starts. A human owns catching hidden dependencies; the system must surface them (BLOCKED reports), not paper over them.

## 3. Pipeline

```
/wave-planning:wave-plan
  1 Scope ──► 2 Design (if UI) ──► 3 Decompose ──► [human approves plan.md]
/wave-planning:wave-execute
  per wave: worktree per phase → parallel subagents → shallow gate each
            → merge to integration → wave functional gate → report → next wave
```

Each stage ends with explicit human approval. Design precedes decomposition because the mockup determines the components and screens, which determines the phases.

## 4. Plugin repository layout

Findings from the plugin docs changed the earlier sketch: new plugins should use `skills/` rather than `commands/` (skills are invokable as `/wave-planning:<skill>`), so there is no `commands/` directory.

```
wave-planning/
  .claude-plugin/
    plugin.json            # name: wave-planning, version, author, homepage, repository, license
    marketplace.json       # makes the repo installable as a marketplace; entry source "./"
  skills/
    wave-plan/SKILL.md     # stages 1 + 3 (scope, decompose); calls wave-design for stage 2
      references/{spec-interview.md, decomposition.md, four-graphs.md}
    wave-design/SKILL.md   # stage 2
      references/{claude-design-flow.md, html-fallback.md}
    wave-execute/SKILL.md  # orchestrator
      references/{worktrees.md, worker-brief.md, gates.md, failure-handling.md}
    model-routing/SKILL.md # rubric; loaded by wave-plan and wave-execute
  agents/
    wave-worker.md         # tools: Read, Edit, Write, Bash, Grep, Glob (no Agent)
    wave-validator.md      # tools: Read, Grep, Glob, Bash (no Edit/Write/Agent)
  scripts/validate_plan.py # stdlib-only Python 3
  templates/{spec.md, plan.md}
  evals/                   # `claude plugin eval` cases
  tests/                   # validate_plan fixtures + unit tests, sample project
  README.md  LICENSE
```

Naming: `wave-planning` passes the reserved-name check (no `claude-`/`anthropic-` prefix). The name is permanent once published; `displayName` can change.

Each `SKILL.md` stays lean; detail lives in `references/` and loads on demand.

## 5. Project-side documents

```
plan.md                      # repo root: combines specs, defines dependencies + execution
docs/waves/specs/<feature>.md
docs/waves/design/           # design reference, or HTML fallback files
```

### 5.1 Feature spec (`docs/waves/specs/<feature>.md`)

YAML frontmatter:

```yaml
id: F2
title: Checkout API
depends_on: [F1]           # feature ids
owns: [src/api/checkout/**, tests/api/checkout/**]
reads: [docs/waves/design#screen-cart]   # context-graph inputs
risk: [money]              # any of: security, data, money, migration
```

Body: summary; in/out of scope; **acceptance criteria**; numbered steps (`F2.1`, `F2.2`, …).

Rule: every acceptance criterion declares its verification method (a test path, a command, an HTTP check, or `design-fidelity:<screen>`). A criterion without one makes the plan invalid.

### 5.2 Root `plan.md`

Sections, in order:

1. **Header** — goal; frozen design reference (URL + version, or HTML fallback path); `bootstrap` command run in each new worktree; shallow-gate commands (`format`, `lint`, `typecheck`, `unit`) auto-detected from `package.json` / `pyproject.toml` / `Makefile` and user-confirmed; `max_wave_width` (default 8; the platform default concurrent-subagent cap is 20).
2. **Feature index** — table linking each spec.
3. **Phases** — one fenced YAML block per phase:
   ```yaml
   id: P2a
   spec: F2
   steps: [F2.1, F2.2]
   owns: [src/api/checkout/**]      # subset of the spec's owns
   depends_on: [P1a]
   model: sonnet                    # haiku | sonnet | opus
   score: {scope: 1, ambiguity: 1, risk: 2, reasoning: 1}
   rationale: "money handling forces opus"
   gate: shallow                    # resolved from header commands
   ```
4. **Four graphs** — dependency table, ownership table, context table, validation table.
5. **Waves** — per wave: its phases, why each is in this wave, integration-owned files, and the wave's functional gate (acceptance criteria drawn from the member specs + cross-phase integration checks + design-fidelity checks for UI).
6. **Execution protocol** — the procedure in §7, retry/escalation rules in §8.
7. **Status** — machine-updated block: per phase and wave state (`pending|running|gated|merged|done|blocked`), integration head SHA after each wave.

**Single source of truth.** Spec frontmatter (`depends_on`, `owns`, acceptance criteria) is canonical. `plan.md` derives from specs and never restates them freehand. To change a dependency, edit the spec and regenerate the plan. `validate_plan.py` fails on any disagreement.

### 5.3 `validate_plan.py`

Deterministic checks, exit non-zero on failure:
- Dependency graph (phases and features) is acyclic; every `depends_on` resolves.
- Wave assignment is consistent with dependencies (no phase before a prerequisite's wave).
- No two phases in one wave have overlapping `owns` globs (pairwise glob-intersection check; where intersection cannot be decided statically, treat as overlap).
- Every phase's `owns` ⊆ its spec's `owns`; every spec step is covered by exactly one phase.
- Every acceptance criterion has a verification method.
- Wave width ≤ `max_wave_width`.
- plan ↔ spec drift (derived fields match canonical ones).
- Every `risk: [security|data|money|migration]` phase is assigned `opus`.

## 6. Model routing (`model-routing` skill)

The planner scores each phase 0–2 on four signals:

| Signal | 0 | 1 | 2 |
|---|---|---|---|
| Scope | 1–2 files | several files, one module | cross-module |
| Ambiguity | fully specified | minor judgment calls | open design questions |
| Risk | none | touches shared behavior | security / data / money / migration |
| Reasoning | mechanical | standard feature logic | novel or algorithmic |

- Sum 0–2 → **haiku**; 3–5 → **sonnet**; ≥6 → **opus**.
- Overrides: Risk = 2 forces opus. Ambiguity = 2 is not routed to a bigger model — the phase returns to planning to be specified.
- The planner proposes; the user may override at plan approval; the rationale is recorded per phase.
- Dispatch passes `model` per Agent call (`haiku` | `sonnet` | `opus` aliases; resolution order is per-invocation param, then agent frontmatter, then `CLAUDE_CODE_SUBAGENT_MODEL`, then the main model). Users who set `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` will defeat routing; `wave-execute` warns if it detects that.
- The orchestrator runs on the user's session model. `wave-validator` never runs below sonnet and uses opus for waves containing a risk-flagged phase.
- Escalation (§8): retry once on the same model, then move up one tier, then stop and ask.

## 7. Execution (`wave-execute`)

The orchestrator is the main session. It never writes product code; it dispatches, verifies, merges, gates, and reports.

**Invariant: only the orchestrator spawns subagents.** `wave-worker` and `wave-validator` are leaf nodes: their `tools` allowlists omit `Agent`, and their briefs forbid delegation. This keeps ownership, model routing, and gating in one place and makes every phase map to exactly one subagent. State lives only in `plan.md`'s status block, so a run is resumable.

**Branches and worktrees.** The orchestrator keeps branch `wave/integration` checked out in the main working tree. For each phase it creates a worktree itself:

```
git worktree add -b wave/<n>/<phase-id> <worktrees-dir>/<phase-id> wave/integration
```

It does not use the Agent tool's `isolation: "worktree"`: per the sub-agents docs that option branches from the default branch, not from the session's current branch, which would break "wave N+1 builds on the gated result of wave N". `<worktrees-dir>` is `.worktrees/` (added to `.gitignore`) by default.

**Per wave:**
1. For each phase: create worktree, run `bootstrap` inside it (dependencies and `.env`-like files are not carried by a new worktree).
2. Dispatch all phases in **one message** of N Agent calls, each with `subagent_type: wave-worker`, the routed `model`, and a self-contained brief (§7.1). Respect `max_wave_width`.
3. Wait for all workers (the wave barrier). Collect their reports.
4. For each `DONE` / `DONE_WITH_CONCERNS` report, the orchestrator itself:
   - verifies `git diff --name-only wave/integration...wave/<n>/<phase>` ⊆ the phase's `owns` (post-hoc ownership enforcement), and that the main working tree is clean (no stray writes);
   - re-runs the phase's shallow gate in its worktree;
   - on failure: §8.
5. Merge verified phase branches into `wave/integration` (no-ff, one by one). Files marked **integration-owned** (lockfiles, route registries, barrel files) are edited by the orchestrator at this step, never by workers. A merge conflict means the ownership graph missed something: stop and surface it (do not auto-resolve).
6. Dispatch `wave-validator` (read/run only) on the merged integration branch to run the **wave functional gate** (§9).
7. Green: record the integration head SHA, mark the wave done, remove its worktrees, show the user a wave report (what merged, gate evidence, concerns), and proceed to the next wave (with an optional pause for human review — default on for the first wave and any wave with risk-flagged phases).
8. Red: §8.

At the end, `wave/integration` holds the finished work; the orchestrator offers to open a PR or merge to the base branch. If the project is not a git repo, the plugin offers `git init` first.

### 7.1 Worker brief (self-contained)
Phase block; spec path and relevant spec excerpt; owned paths; read-only context paths; design reference + screen ids (UI phases); shallow-gate commands; absolute worktree path; rules:
- Work only inside the worktree path; use absolute paths / `git -C <path>`.
- Write only to owned paths; never touch integration-owned files; never merge, rebase, or switch branches.
- Do not spawn subagents (the agent definition also omits the `Agent` tool; the platform otherwise allows nesting up to 3 layers).
- Commit on the phase branch. Run the shallow gate and report its output.
- Report format: `DONE` | `DONE_WITH_CONCERNS` | `BLOCKED`, plus commit SHA, gate output, deviations, and any dependency or file the plan missed.

## 8. Failure handling and resume

- `BLOCKED`, or a reported missing dependency: the wave **pauses**. The orchestrator shows the finding and offers a replan (return to the decompose stage with the discovered dependency). It does not improvise a fix.
- Shallow-gate failure: retry once on the same model with the gate output; then escalate one tier; then stop and ask the user.
- Wave gate red: the validator's failure report is traced to a phase; the fix runs in a fresh worktree off the integration head on the same escalation ladder, is merged, and the gate re-runs. The next wave never starts on a red integration branch.
- Resume: `/wave-planning:wave-execute` reads the status block, reconciles it against `git worktree list` and `git branch --list 'wave/*'`, removes orphaned worktrees, and restarts at the first incomplete wave. A phase left `running` is restarted from a fresh worktree.
- Background subagents run with a reduced tool set that still includes Read, Edit, Write, Bash, Grep, Glob; the worker needs nothing else.

## 9. Gates

- **Phase gate (shallow):** format, lint, typecheck, and unit tests for owned files; commands come from the plan header. Runs in the phase worktree before merge.
- **Wave gate (functional)** on the merged integration branch:
  1. every acceptance criterion from the wave's specs via its declared verification method;
  2. cross-phase integration checks defined in `plan.md`;
  3. design fidelity for UI waves (§10).
  The validator reports pass/fail with evidence per criterion. It has no write tools and cannot patch what it finds.

## 10. Design stage (`wave-design`)

Runs only when approved scope includes UI. Builds the mockup in **Claude Design** (the Artifact "Design" type). It discovers the type at runtime via the Artifact tool's `quickstart` (`intent: design`) and never hardcodes a type URL, since those are per-account. Fallback when the Artifact tool is unavailable: static HTML mockups under `docs/waves/design/`.

After the user approves, the design URL + version (or fallback path) is written into the `plan.md` header and the design is **frozen**. Frontend phases receive screen ids as context-graph inputs and implement only what the design shows. The UI wave's functional gate includes a design-fidelity check per screen. A mid-execution design change triggers a replan; the frozen design is never edited silently.

Open implementation detail: how workers read a Claude Design artifact at execution time (Artifact `read` of the URL vs an exported snapshot committed to `docs/waves/design/`). Decide during implementation planning; prefer the snapshot, since it is versioned with the code and works for background subagents.

## 11. Testing the plugin

1. **Unit tests** for `validate_plan.py` with fixtures: cycle, ownership overlap, uncovered step, unverifiable criterion, plan↔spec drift, risk-not-opus.
2. **Plugin evals** via `claude plugin eval` (`evals/`), covering skill triggering and key behaviors (e.g. planner refuses a criterion with no verification method; orchestrator pauses on BLOCKED).
3. **End-to-end dry run** on a small sample project (UI + API + data layer): two or more waves, a design freeze, and a deliberately injected hidden dependency to confirm the pause-and-replan path and the merge-conflict stop.
4. `claude plugin validate --strict` clean, and an install from a local marketplace (`claude plugin marketplace add ./`) before every release.

## 12. Publishing

- **Own marketplace (first):** push to GitHub; `.claude-plugin/marketplace.json` with one entry (`name: wave-planning`, `source: "./"`) so users run `claude plugin marketplace add <owner>/<repo>` then `claude plugin install wave-planning@<marketplace>`. Entry name must equal the manifest name. Set `version` and bump it on every release (otherwise users stay on the old copy), or omit it to track commit SHAs.
- **Anthropic's directory:** submit via the developer portal at claude.ai/directory/manage (requires a paid claude.ai plan). The portal applies rules the CLI does not check, so a clean local `--strict` run is necessary but not sufficient. `claude-plugins-official` does not accept portal submissions. Set `icon`, `documentationUrl`, `supportUrl`, `privacyPolicyUrl`, `termsOfServiceUrl` in `plugin.json` for the listing. Directory listing reaches claude.ai/Cowork too, where this plugin's subagent/worktree components do not apply — the README and listing must say it is for Claude Code.

## 13. Open items (resolve in the implementation plan)

1. Worker access to the frozen design (snapshot vs live read) — §10.
2. Where `.worktrees/` lives for repos on unusual filesystems (default stays `.worktrees/` in the project, gitignored).
3. Whether to ship an optional PreToolUse hook that hard-blocks writes outside a worker's `owns` (v2).
4. Whether the worktrees doc's base-branch setting would let us use `isolation: "worktree"` and drop manual worktree creation. Not verified; manual creation is the v1 design.

## Sources

- Wave Planning: Parallel AI Development — https://arunprakashg.com/blogs/wave-planning-parallel-ai-development/
- Wave Planning: What a Wave Actually Is — https://arunprakashg.com/blogs/wave-planning-what-a-wave-actually-is/
- Claude Code docs: plugins reference, plugin marketplaces, publish, sub-agents (code.claude.com/docs).
