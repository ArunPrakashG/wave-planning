# The four graphs

A wave is only safe if all four of these hold. Checking the dependency graph alone misses real collisions: two phases can be independent on paper and still break each other by editing the same config file.

| Graph | Question it answers | Where it lives |
|---|---|---|
| **Dependency** | What must exist before this phase can start? | `depends_on` in specs and phases |
| **Ownership** | Which files may this phase write? Does any other phase in the wave write them too? | `owns` in specs and phases; `integration_owned` per wave |
| **Context** | What must this phase read to do its work correctly? | `reads` in specs, design screens |
| **Validation** | How do we know this phase, and this wave, is correct? | phase gate commands, wave `criteria` and `integration_checks` |

The machine-readable blocks in `plan.md` are the source of truth. The four tables in the plan's "Four graphs" section are a human-readable rendering of them: regenerate them from the blocks, one row per phase. The validator checks the blocks and does not parse the tables, so a stale table misleads people without failing validation. Keep them in sync.

## Table shapes

- **Dependency:** `| Phase | Depends on |`, with `none` for phases that start immediately.
- **Ownership:** `| Phase | Owns |`, the exact globs.
- **Context:** `| Phase | Reads |`, files and design screens (`docs/waves/design/snapshot.html#screen-cart`).
- **Validation:** `| Phase | Shallow gate | Wave gate criteria |`, the criteria ids gated by the wave the phase is in.

## Hidden-dependency checklist

Ask about each of these before approval. They are the usual things a dependency tree misses.

- Shared configuration files, environment variables, secrets handling
- Database migrations and their order
- Feature flags and their defaults
- Generated code (clients, types, schemas) and who regenerates it
- Shared test fixtures, mocks, and test infrastructure
- Route tables, registries, barrel files, dependency-injection containers
- Lockfiles and package manifests
- Build or CI configuration
- Documentation that must change together with code

Anything on this list that more than one phase touches is either split so each phase has its own file, or marked `integration_owned` for the wave.
