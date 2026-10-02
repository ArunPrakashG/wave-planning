---
id: F<N>
title: <Feature name>
depends_on: []
owns: [<dir>/**, <test-dir>/**]
reads: []
risk: []
steps: [F<N>.1]
---

# F<N> <Feature name>

<!-- Frontmatter rules (flow style only, one line per field):
     id        unique feature id, e.g. F2
     depends_on feature ids that must be fully built before this one starts
     owns      globs this feature may write. Directories are written as `dir/**`.
               Use `*` within a segment, `**` across segments. No braces or char classes.
     reads     files or design screens needed as context (read-only)
     risk      any of: security, data, money, migration (forces the opus tier)
     steps     step ids, each belongs to exactly one phase in plan.md -->

## Summary

<One paragraph: what this feature does and why it exists.>

## In scope

- <what is included>

## Out of scope

- <what is explicitly not included>

## Acceptance criteria

<!-- One line per criterion: `ID: {text: "...", verify: "..."}`.
     verify must start with one of:
       test:<path or test id>           a test file or test id that must pass
       cmd:<shell command>              a command that must exit 0
       http:<request and expectation>   an HTTP check against the running app
       design-fidelity:<screen-id>      the implementation matches that frozen design screen -->

```yaml criteria
AC1: {text: "<testable statement>", verify: "test:<path>"}
```

## Steps

- F<N>.1 <What to build, in one sentence.>
