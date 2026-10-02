# Plan: Shop Demo

## Header

```yaml header
design: docs/waves/design/shop.html
bootstrap: npm ci
gates: {format: "npx prettier --check .", lint: "npx eslint .", typecheck: "npx tsc --noEmit", unit: "npx vitest run"}
max_wave_width: 4
```

## Feature index

| Feature | Spec |
|---|---|
| F1 Data layer | docs/waves/specs/F1.md |
| F2 Checkout API | docs/waves/specs/F2.md |
| F3 Cart UI | docs/waves/specs/F3.md |
| F4 Design tokens | docs/waves/specs/F4.md |

## Phases

```yaml phase
id: P1a
spec: F1
steps: [F1.1]
owns: [src/db/schema/**, tests/db/schema/**]
depends_on: []
model: sonnet
score: {scope: 1, ambiguity: 0, risk: 1, reasoning: 1}
rationale: "schema is shared behavior but fully specified"
```

```yaml phase
id: P1b
spec: F1
steps: [F1.2]
owns: [src/db/seed/**, tests/db/seed/**]
depends_on: []
model: haiku
score: {scope: 0, ambiguity: 0, risk: 0, reasoning: 0}
rationale: "mechanical seed data from a complete list"
```

```yaml phase
id: P4a
spec: F4
steps: [F4.1]
owns: [src/ui/tokens/**, tests/ui/tokens/**]
depends_on: []
model: haiku
score: {scope: 1, ambiguity: 0, risk: 0, reasoning: 0}
rationale: "token file from the frozen design"
```

```yaml phase
id: P2a
spec: F2
steps: [F2.1]
owns: [src/api/checkout/**, tests/api/checkout/**]
depends_on: [P1a]
model: opus
score: {scope: 1, ambiguity: 1, risk: 2, reasoning: 1}
rationale: "money handling forces opus"
```

```yaml phase
id: P2b
spec: F2
steps: [F2.2]
owns: [src/api/cart/**, tests/api/cart/**]
depends_on: [P1a]
model: opus
score: {scope: 1, ambiguity: 0, risk: 2, reasoning: 1}
rationale: "cart totals feed payment"
```

```yaml phase
id: P3a
spec: F3
steps: [F3.1]
owns: [src/ui/cart/**, tests/ui/cart/**]
depends_on: [P2a, P2b, P4a]
model: sonnet
score: {scope: 1, ambiguity: 1, risk: 0, reasoning: 1}
rationale: "standard UI work against a frozen design"
```

## Waves

```yaml wave
wave: 1
phases: [P1a, P1b, P4a]
integration_owned: [package-lock.json]
criteria: [F1.AC1, F1.AC2, F4.AC1]
integration_checks: ["cmd:npx vitest run tests/db"]
```

```yaml wave
wave: 2
phases: [P2a, P2b]
integration_owned: [src/api/routes.ts]
criteria: [F2.AC1, F2.AC2]
integration_checks: ["cmd:npx vitest run tests/api"]
```

```yaml wave
wave: 3
phases: [P3a]
integration_owned: []
criteria: [F3.AC1]
integration_checks: ["cmd:npx vitest run"]
```

## Status

```yaml status
base_branch: main
integration_branch: wave/integration
integration_head: none
W1: pending
W2: pending
W3: pending
```
