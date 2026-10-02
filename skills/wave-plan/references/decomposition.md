# Decomposing specs into phases and waves

## 1. Steps → phases

- A **phase** is the unit one subagent runs. It should fit one agent's context: roughly up to ten files and a coherent piece of behavior.
- Steps that edit the same files, or that call into each other tightly, belong in one phase. A step never spans two phases.
- Give each phase narrow `owns` globs, inside its spec's `owns`. Split by directory so two phases never share a file. If two steps need the same file, merge them into one phase or move that file to integration-owned (see below).
- Every phase owns the files it writes, including its tests. A phase that owns nothing is a planning error.

## 2. Dependencies between phases

Phase B depends on phase A when B imports, calls, reads, or needs the output of A. Typical chains: schema before API before UI; shared types before their users; test infrastructure before tests; migrations in order.

- Record only real edges. Extra edges only reduce parallelism.
- A phase may depend on a phase of another feature only if its spec lists that feature in `depends_on`. Add the feature dependency to the spec first.
- **Feature rule:** if feature F depends on feature G, every phase of G finishes in an earlier wave than any phase of F starts. If that serialises too much, split G into smaller features.

## 3. Phases → waves

1. **Earliest wave.** `wave(p) = 1` if `p` has no dependencies, otherwise `1 + max(wave(d))` over its dependencies. Also apply the feature rule: `wave(p)` must be greater than the wave of every phase in every feature `p`'s feature depends on.
2. **Conflict rule.** If two phases in one wave have overlapping `owns`, they cannot share a wave. Prefer, in this order: re-split the ownership so they no longer overlap; merge the two phases; move the one that is off the critical path to the next wave (then recompute everything that depends on it).
3. **Width.** If a wave has more phases than `max_wave_width` (default 8), move the phases that are off the critical path to the next wave.
4. Waves are numbered 1..N with no gaps. No wave may be empty.

Wave planning's "waves" are an output of this analysis, not a place you put things. If you find yourself deciding a wave first and fitting phases in, stop and recompute from the dependencies.

## 4. Integration-owned files

Some files legitimately need a change from several phases in a wave: lockfiles, route registries, barrel or index files, dependency-injection containers, a global stylesheet index, translation key files. List them per wave in `integration_owned`. Workers never edit them; they report what they need, and the orchestrator applies it after merging. If a project has many of these, suggest a structure that avoids them (auto-registration, per-feature files).

## 5. Gates

- **Shallow gate commands** (header `gates`): detect them and confirm with the user.
  - Node: `package.json` scripts (prettier or `format`, `eslint` or `lint`, `tsc --noEmit`, `test`).
  - Python: `ruff format --check` or `black --check`, `ruff check`, `mypy`, `pytest`.
  - Rust: `cargo fmt --check`, `cargo clippy`, `cargo test`.
  - Go: `gofmt -l .`, `go vet ./...`, `go test ./...`.
  - Or the targets in a `Makefile`.
- **`bootstrap`**: the command that makes a fresh worktree runnable (`npm ci`, `pip install -e .`, copying an env template). Fresh worktrees have no installed dependencies and no ignored files.
- **Wave gate:** each acceptance criterion is gated in one wave: the earliest wave in which all its feature's phases are done. Add `integration_checks` for behavior that spans phases in the wave (for example, API plus database end to end), as `test:`/`cmd:`/`http:` strings. UI criteria use `design-fidelity:<screen-id>`.

## 6. Check the shape

Report: number of waves, widest wave, and the **critical path** (the longest chain of dependent phases, which sets the minimum number of waves). If one wave holds nearly everything, the work may be less parallel than hoped; say so honestly.

## 7. Write and validate

Write `plan.md` from the template, including the four tables from [four-graphs.md](four-graphs.md), then run `validate_plan.py` and fix every error before showing the plan to the user.
