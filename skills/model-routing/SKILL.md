---
name: model-routing
description: Use when assigning a model tier (haiku, sonnet, or opus) to a wave-plan phase, or when reviewing, overriding, or escalating a phase's model assignment.
user-invocable: false
---

# Model Routing

Every phase in a wave plan runs on the cheapest model that is adequate for it. You decide that with a score, not a feeling, so the choice is reproducible and reviewable.

## Score the phase

Rate each signal 0, 1 or 2 from the phase's spec and the code it touches:

| Signal | 0 | 1 | 2 |
|---|---|---|---|
| **scope** | 1–2 files | several files, one module | cross-module |
| **ambiguity** | fully specified, nothing left to decide | minor judgment calls | open design questions |
| **risk** | none | touches shared behavior | security, data, money, or migrations |
| **reasoning** | mechanical | standard feature logic | novel or algorithmic |

## Derive the tier

Run the script instead of adding in your head:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/routing.py" --scope 1 --ambiguity 0 --risk 2 --reasoning 1
```

It prints `haiku`, `sonnet` or `opus`. The rules it applies:

- Sum 0–2 → **haiku**. Sum 3–5 → **sonnet**. Sum 6 or more → **opus**.
- **risk = 2 forces opus**, whatever the sum is.
- **ambiguity = 2 is not routed to a bigger model.** The script exits 2 with `NEEDS-PLANNING`. Go back to the spec, resolve the open question with the user, and score again. A stronger model guessing at an unspecified requirement is still a guess.

Write the result into the phase block as `model: <tier>`, the four-signal `score: {...}`, and a one-line `rationale` that names the signal that decided it ("money handling forces opus").

## Overrides

The plan validator rejects a `model` that disagrees with its `score`, unless the phase carries `override: "reason"`. Use an override only when you know something the four signals cannot see (for example, a flaky legacy script a smaller model keeps getting wrong). Always give the reason. If the user asks for a different tier at plan approval, set the override and record their reason.

## Tiers at run time

- The orchestrator passes the tier as the Agent call's `model` parameter (`haiku`, `sonnet`, `opus`).
- A phase that fails its gate retries once on the same tier with the failure output, then moves up exactly one tier, then stops and asks the user. Haiku → sonnet → opus. A failure on opus is never retried on a lower tier.
- `wave-validator` never runs below sonnet. Run it on opus for any wave that contains a phase whose spec has a `risk` flag.
- If the user has forced a single subagent model with `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`, every subagent runs on that model and routing has no effect. `wave-execute` warns them before running.

## Sanity examples

| Phase | Score (scope, ambiguity, risk, reasoning) | Tier |
|---|---|---|
| Rename a config key across 3 files | 0, 0, 0, 0 | haiku |
| Standard CRUD settings page from a finished design | 1, 1, 0, 1 | sonnet |
| Payment capture endpoint | 1, 1, 2, 1 | opus (risk) |
| Query planner with caching, nothing specified yet | 2, 2, 1, 2 | planning first (ambiguity) |
