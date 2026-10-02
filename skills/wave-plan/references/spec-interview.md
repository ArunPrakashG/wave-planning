# Scoping interview and spec writing

## Order of questions

Ask one question per message. Prefer multiple choice when the options are knowable. Skip a question the user's brief already answers; restate your understanding instead and ask them to correct it.

1. **Purpose and users.** What is this for, and who uses it?
2. **Success.** What would make this a success when it is finished? How would they know?
3. **Constraints.** Language and framework, hosting, existing code that must be kept, hard deadlines, things that must not change.
4. **Feature list.** Propose a list of features, each a short name and one sentence. Aim for features that map to separable pieces of code: a data layer, an API area, a screen, an integration. Too coarse ("the backend") hides parallelism; too fine produces dozens of tiny specs. Get approval of the list.
5. **Per feature**, in this order:
   - Scope in and out.
   - **Acceptance criteria**, each with how it will be verified.
   - Risk flags: `security`, `data`, `money`, `migration`. Flag generously; it only forces a stronger model.
   - Owned paths: propose globs from the repository's structure (or from the structure you and the user agreed for a greenfield project). Directories are written `dir/**`.
   - Read-only context the work needs.
   - Dependencies on other features.

## Writing acceptance criteria

A criterion is a statement a command or a test can answer yes or no to.

| Weak | Strong | verify |
|---|---|---|
| Checkout works | Checkout total includes tax and discounts | `test:tests/api/checkout/total.test.ts` |
| It should feel fast | The product list responds in under 200 ms for 1,000 items | `cmd:npm run bench:list -- --max-ms 200` |
| The page looks right | The cart screen matches the approved design | `design-fidelity:screen-cart` |
| The API handles adds | Adding an item returns 201 | `http:POST /cart/items returns 201` |

When the user gives you a weak one, do not write it down as is. Ask how they would check it, and propose a strong version. If nothing can check it, say so and drop it or move it to out of scope.

## Spec files

- One file per feature at `docs/waves/specs/<id>.md`, ids `F1`, `F2`, …
- Start from `${CLAUDE_PLUGIN_ROOT}/templates/spec.md`.
- Frontmatter is flow-style YAML, one line per field. Lists look like `[a, b]`. No indentation. Quote a value that contains a comma or a colon.
- Do not use braces in globs.
- `steps` lists every step id; the body describes each step in a sentence.
- Every step ends up in exactly one phase later, so write steps at the size of "one agent could do this in one sitting".
