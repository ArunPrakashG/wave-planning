# Wave Planning Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and release v0.1.0 of the `wave-planning` Claude Code plugin: scope → design → decompose → execute, with per-feature specs, a root `plan.md`, worktree-isolated parallel subagents, model routing, and phase/wave gates.

**Architecture:** A Claude Code plugin made of four skills (`wave-plan`, `wave-design`, `wave-execute`, `model-routing`), two leaf-node agents (`wave-worker`, `wave-validator`), and a small stdlib-only Python toolkit (`validate_plan.py`, `routing.py`, `check_owned.py`) that makes the safety-critical rules deterministic. Skills are prompts; the scripts are the only executable logic and are developed test-first.

**Tech Stack:** Markdown skills/agents, JSON manifests, Python 3 standard library only (`unittest` for tests), `claude plugin validate` / `claude plugin eval`, git worktrees.

**Spec:** `docs/specs/2026-10-02-wave-planning-plugin-design.md`

## How this plan was prepared

All Python code and tests in this plan (Tasks 2–10 and the Task 15 rehearsal test) were first written and run in a scratch copy of the finished plugin: **143 tests passed**, and `claude plugin validate --strict` passed on the manifests, agents and skills. The code below is exactly that code. What has *not* been run is the behavior of the skills in a live session: that is what the evals (Task 16) and the end-to-end dry run (Task 17) are for.

## Decisions in this plan that refine the spec

1. **`unittest`, not pytest.** pytest is not installed by default; the Python toolkit stays dependency-free, including for tests.
2. **YAML subset.** The Python standard library has no YAML parser, so machine-readable blocks use a documented flow-style subset (`miniyaml.py`): one `key: value` per line, lists as `[a, b]`, maps as `{k: v}`, no indentation, no inline comments.
3. **Machine-readable blocks are tagged fences.** `plan.md` uses ` ```yaml header | phase | wave | status `; specs use ` ```yaml criteria ` plus `---` frontmatter. All other text is for humans. The spec gains a `steps: [F2.1, …]` frontmatter field.
4. **Extra validator checks** beyond spec §5.3: `owns-empty`, `owns-glob` (quoted brace globs), `owns-integration`, `wave-empty`, `feature-order`, `drift-feature-dep`, `owns-dir`, `model-invalid`, `score-invalid`.
5. **`check_owned.py`** is added: it is the deterministic implementation of the spec's post-hoc ownership enforcement (diff of a phase branch vs owned globs).
6. **Design snapshot** (spec §13 item 1) is resolved as *snapshot preferred*: `wave-design` saves an HTML snapshot under `docs/waves/design/` and workers read that, with the Claude Design URL recorded for humans.
7. **Plugin agents ignore `permissionMode`** (plugin docs). Workers need Edit/Write/Bash permission from the user's own permission mode or settings; the README documents this and the dry run (Task 17) checks it.
8. **No `commands/` directory** (docs prefer skills); `wave-execute` is `disable-model-invocation: true` so a long parallel run only starts when the user invokes it.

## Global Constraints

- Plugin name is exactly `wave-planning` (kebab-case; no `claude-`/`anthropic-` prefix); it is permanent once published.
- Claude Code only. No dependency on other plugins (not superpowers, not opencode).
- Python: standard library only; developed and tested on Python 3.14; syntax targets 3.8+ but is untested below 3.14.
- Machine-readable YAML is flow style only (see decision 2). Globs: `*` within a segment, `**` across segments, directories written as `dir/**`, no braces or character classes.
- Each `SKILL.md` ≤ 500 lines (docs guidance); detail goes in `references/`. Skill `description` starts with "Use when" and is ≤ 1,536 characters.
- `wave-worker` and `wave-validator` declare an explicit `tools` allowlist that omits `Agent` (only the orchestrator spawns subagents). `wave-validator` also omits `Edit`, `Write`, `NotebookEdit`.
- Model tiers are exactly `haiku`, `sonnet`, `opus`. Routing: sum 0–2 → haiku, 3–5 → sonnet, ≥6 → opus; risk 2 forces opus; ambiguity 2 returns the phase to planning.
- `plan.md` lives at the project root; specs at `docs/waves/specs/<id>.md`; design at `docs/waves/design/`.
- Branches: `wave/integration` and `wave/<n>/<phase-id>`. Worktrees in `.worktrees/` (gitignored). `max_wave_width` default 8.
- `claude plugin validate --strict .` must pass before any release.

## Review Focus

Inputs and conditions the spec implies but no single task's happy path exercises, most likely first:

1. **CRLF line endings** in `plan.md` / specs (Windows editors): must parse exactly like LF. Pinned by `test_crlf_files_parse_like_lf_files` (Task 6).
2. **A quoted brace glob** like `"src/{a,b}/**"` passes the parser but would match nothing, silently defeating ownership checks. Pinned by the `owns-glob` tests (Task 8).
3. **A phase that owns nothing, or a wave with no phases.** Pinned by `owns-empty` (Task 8) and `wave-empty` (Task 7) tests.
4. **A phase that depends on itself.** Pinned by `test_phase_depending_on_itself` (Task 7).
5. **Background workers blocked by permission prompts**, and **a Claude Design artifact that cannot be exported as a snapshot.** Neither is unit-testable; both are explicit items in the dry-run checklist (Task 17).

## File Structure

| Path | Responsibility |
|---|---|
| `.claude-plugin/plugin.json`, `marketplace.json` | Manifest; makes the repo installable as a marketplace |
| `scripts/miniyaml.py` | Parse the flow-style YAML subset |
| `scripts/globs.py` | Glob → regex, `matches`, `overlaps`, `covers` |
| `scripts/routing.py` | Score → model tier (`derive_model`) and CLI |
| `scripts/check_owned.py` | Verify a diff's paths against owned globs (CLI) |
| `scripts/plan_loader.py` | Load `plan.md` + specs into dataclasses |
| `scripts/findings.py` | `Finding(code, message)` |
| `scripts/checks_graph.py` | Reference, cycle, wave-layout, width, step-coverage checks |
| `scripts/checks_content.py` | Ownership, acceptance-criteria, routing checks |
| `scripts/validate_plan.py` | Run all checks; CLI |
| `templates/spec.md`, `templates/plan.md` | Annotated templates used by `wave-plan` |
| `agents/wave-worker.md`, `agents/wave-validator.md` | Leaf-node subagents |
| `skills/model-routing/` | Rubric skill |
| `skills/wave-design/` | Design stage skill (+ references) |
| `skills/wave-plan/` | Scope + decompose skill (+ references) |
| `skills/wave-execute/` | Orchestrator skill (+ references) |
| `tests/` | `unittest` suite, `fixtures/valid/` sample project |
| `evals/` | `claude plugin eval` cases (planning side) |
| `README.md`, `LICENSE`, `docs/` | Docs, spec, this plan, dry-run log |

Run the whole suite from the repo root with `python3 -m unittest discover -s tests`. Run one file with `python3 -m unittest discover -s tests -p 'test_globs.py' -v`.

---

### Task 1: Plugin scaffold, manifest, marketplace

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.claude-plugin/marketplace.json`
- Create: `.gitignore`
- Create: `LICENSE`

**Interfaces:**
- Produces: plugin name `wave-planning`; marketplace name `arunprakashg-plugins` (install id `wave-planning@arunprakashg-plugins`).

- [ ] **Step 1: Write the manifest**

`.claude-plugin/plugin.json`:

```json
{
  "name": "wave-planning",
  "displayName": "Wave Planning",
  "version": "0.1.0",
  "description": "Plan software as dependency-ordered waves, then execute each wave's phases in parallel subagents in git worktrees, with automatic model routing and validation gates.",
  "author": { "name": "Arun Prakash G", "url": "https://arunprakashg.com" },
  "homepage": "https://arunprakashg.com/blogs/wave-planning-parallel-ai-development/",
  "license": "MIT",
  "keywords": ["wave-planning", "parallel-agents", "subagents", "git-worktrees", "planning", "orchestration"]
}
```

`repository` is deliberately omitted until the GitHub repo exists (Task 17).

- [ ] **Step 2: Write the marketplace file**

`.claude-plugin/marketplace.json`:

```json
{
  "name": "arunprakashg-plugins",
  "description": "Plugins by Arun Prakash G",
  "owner": { "name": "Arun Prakash G" },
  "plugins": [
    {
      "name": "wave-planning",
      "source": "./",
      "description": "Wave planning for parallel AI development: specs, waves, worktree-isolated subagents, model routing, validation gates."
    }
  ]
}
```

- [ ] **Step 3: Write `.gitignore` and `LICENSE`**

`.gitignore`:

```
.worktrees/
__pycache__/
*.pyc
evals/results/
.DS_Store
```

`LICENSE` is the standard MIT license text with the line `Copyright (c) 2026 Arun Prakash G`.

- [ ] **Step 4: Validate**

Run: `claude plugin validate --strict .`
Expected: `✔ Validation passed`. If it reports a problem, fix exactly what the message names (it is authoritative) and re-run. Note: with no skills or agents yet it may warn about nothing to load; that is acceptable only if it does not fail.

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin .gitignore LICENSE
git commit -m "feat: plugin manifest and marketplace"
```

---

### Task 2: `miniyaml` parser

**Files:**
- Create: `tests/helpers.py`
- Create: `tests/test_miniyaml.py`
- Create: `scripts/miniyaml.py`

**Interfaces:**
- Produces: `parse_document(text) -> dict`, `parse_value(text, lineno=0) -> Any`, `MiniYamlError(ValueError)`. Values: `str`, `int`, `bool`, `None`, `list`, `dict`.
- Produces (test helper): `helpers.REPO`, `helpers.SCRIPTS`, `helpers.FIXTURE`, `helpers.ProjectTestCase` (gives each test `self.root`, `self.edit(relpath, old, new)`, `self.codes(findings)`).

- [ ] **Step 1: Write the test helper**

```python
"""Shared test helpers: puts scripts/ on sys.path and builds mutable fixture copies."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
FIXTURE = REPO / "tests" / "fixtures" / "valid"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


class ProjectTestCase(unittest.TestCase):
    """Gives each test a private, editable copy of the valid fixture project."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "project"
        shutil.copytree(FIXTURE, self.root)

    def edit(self, relpath, old, new):
        """Replace the first occurrence of `old` in a project file; fail if absent."""
        path = self.root / relpath
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture drifted: {old!r} not found in {relpath}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def codes(self, findings):
        return {f.code for f in findings}
```

- [ ] **Step 2: Write the failing tests**

```python
import unittest

import helpers  # noqa: F401  (sets sys.path)
from miniyaml import MiniYamlError, parse_document, parse_value


class ScalarTests(unittest.TestCase):
    def test_plain_string(self):
        self.assertEqual(parse_document("id: F1"), {"id": "F1"})

    def test_integer_bool_null(self):
        doc = parse_document("a: 3\nb: true\nc: false\nd: null\ne:\nf: ~")
        self.assertEqual(doc, {"a": 3, "b": True, "c": False, "d": None, "e": None, "f": None})

    def test_top_level_plain_keeps_commas_and_colons(self):
        self.assertEqual(parse_document("goal: Build X, then Y: done")["goal"], "Build X, then Y: done")

    def test_quoted_preserves_commas_and_colons(self):
        self.assertEqual(parse_value('"cmd:pytest -q, then more"'), "cmd:pytest -q, then more")

    def test_double_quote_escape(self):
        self.assertEqual(parse_value(r'"say \"hi\""'), 'say "hi"')

    def test_single_quote_doubling(self):
        self.assertEqual(parse_value("'it''s'"), "it's")


class CollectionTests(unittest.TestCase):
    def test_list_of_globs(self):
        self.assertEqual(
            parse_document("owns: [src/api/**, tests/api/**]")["owns"],
            ["src/api/**", "tests/api/**"],
        )

    def test_empty_list_and_map(self):
        self.assertEqual(parse_document("a: []\nb: {}"), {"a": [], "b": {}})

    def test_map_with_ints(self):
        self.assertEqual(
            parse_document("score: {scope: 1, risk: 2}")["score"], {"scope": 1, "risk": 2}
        )

    def test_nested_map_in_map_with_quoted_values(self):
        doc = parse_document('AC1: {text: "adds, removes", verify: "test:a.py::t"}')
        self.assertEqual(doc["AC1"], {"text": "adds, removes", "verify": "test:a.py::t"})

    def test_list_of_maps(self):
        self.assertEqual(parse_value("[{a: 1}, {a: 2}]"), [{"a": 1}, {"a": 2}])

    def test_trailing_comma_allowed(self):
        self.assertEqual(parse_value("[a, b,]"), ["a", "b"])


class DocumentTests(unittest.TestCase):
    def test_blank_lines_and_comments_ignored(self):
        self.assertEqual(parse_document("# hi\n\nid: F1\n  \n# bye\n"), {"id": "F1"})


class ErrorTests(unittest.TestCase):
    def test_indentation_rejected(self):
        with self.assertRaisesRegex(MiniYamlError, "line 2: indentation"):
            parse_document("a: 1\n  b: 2")

    def test_block_list_rejected(self):
        with self.assertRaisesRegex(MiniYamlError, "expected 'key: value'"):
            parse_document("- a\n- b")

    def test_duplicate_key(self):
        with self.assertRaisesRegex(MiniYamlError, "duplicate key 'a'"):
            parse_document("a: 1\na: 2")

    def test_unterminated_list(self):
        with self.assertRaisesRegex(MiniYamlError, "expected ',' or ']'"):
            parse_document("a: [x, y")

    def test_unterminated_quote(self):
        with self.assertRaisesRegex(MiniYamlError, "unterminated"):
            parse_document('a: "oops')

    def test_empty_list_item(self):
        with self.assertRaisesRegex(MiniYamlError, "empty value"):
            parse_document("a: [x,,y]")

    def test_trailing_text_after_list(self):
        with self.assertRaisesRegex(MiniYamlError, "trailing text"):
            parse_document("a: [x] junk")

    def test_missing_space_after_colon(self):
        with self.assertRaisesRegex(MiniYamlError, "expected 'key: value'"):
            parse_document("a:b")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_miniyaml.py' -v`
Expected: error `ModuleNotFoundError: No module named 'miniyaml'`.

- [ ] **Step 4: Implement**

```python
"""Parser for the small YAML subset used in wave-planning documents.

Supported: top-level `key: value` lines, blank lines, `#` comment lines.
Values: flow lists `[a, b]`, flow maps `{k: v}`, quoted strings, integers,
true/false, null, and plain strings. Flow collections may nest.

Not supported: indentation, block lists/maps, inline comments, multi-line values.
In double-quoted strings a backslash makes the next character literal.
In single-quoted strings a doubled quote ('') is a literal quote.
"""
import re


class MiniYamlError(ValueError):
    pass


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.\-]*)\s*:(?:\s+(.*))?$")
_MAP_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]*")
_INT_RE = re.compile(r"^-?\d+$")


def parse_document(text):
    """Parse `key: value` lines into a dict."""
    result = {}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            raise MiniYamlError(
                f"line {lineno}: indentation is not supported; "
                "write lists and maps in flow style on one line"
            )
        match = _KEY_RE.match(line)
        if not match:
            raise MiniYamlError(f"line {lineno}: expected 'key: value', got {line!r}")
        key, rest = match.group(1), match.group(2)
        if key in result:
            raise MiniYamlError(f"line {lineno}: duplicate key {key!r}")
        result[key] = parse_value(rest or "", lineno)
    return result


def parse_value(text, lineno=0):
    """Parse a single value (the part after `key: `)."""
    flow = _Flow(text.strip(), lineno)
    value = flow.value(top=True)
    flow.skip_ws()
    if flow.i != len(flow.s):
        flow.fail(f"unexpected trailing text {flow.s[flow.i:]!r}")
    return value


def _scalar(text):
    if text in ("", "null", "~"):
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    if _INT_RE.match(text):
        return int(text)
    return text


class _Flow:
    def __init__(self, text, lineno):
        self.s = text
        self.i = 0
        self.lineno = lineno

    def fail(self, message):
        raise MiniYamlError(f"line {self.lineno}: {message}")

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def skip_ws(self):
        while self.peek() == " ":
            self.i += 1

    def value(self, top=False):
        self.skip_ws()
        c = self.peek()
        if c == "":
            return None
        if c == "[":
            return self.sequence()
        if c == "{":
            return self.mapping()
        if c in ("'", '"'):
            return self.quoted()
        return self.plain(top)

    def sequence(self):
        self.i += 1
        items = []
        self.skip_ws()
        if self.peek() == "]":
            self.i += 1
            return items
        while True:
            items.append(self.value())
            self.skip_ws()
            c = self.peek()
            if c == ",":
                self.i += 1
                self.skip_ws()
                if self.peek() == "]":
                    self.i += 1
                    return items
                continue
            if c == "]":
                self.i += 1
                return items
            self.fail("expected ',' or ']' in list")

    def mapping(self):
        self.i += 1
        out = {}
        self.skip_ws()
        if self.peek() == "}":
            self.i += 1
            return out
        while True:
            self.skip_ws()
            match = _MAP_KEY_RE.match(self.s, self.i)
            if not match:
                self.fail("expected a map key")
            key = match.group(0)
            self.i = match.end()
            self.skip_ws()
            if self.peek() != ":":
                self.fail(f"expected ':' after key {key!r}")
            self.i += 1
            if key in out:
                self.fail(f"duplicate key {key!r}")
            out[key] = self.value()
            self.skip_ws()
            c = self.peek()
            if c == ",":
                self.i += 1
                self.skip_ws()
                if self.peek() == "}":
                    self.i += 1
                    return out
                continue
            if c == "}":
                self.i += 1
                return out
            self.fail("expected ',' or '}' in map")

    def quoted(self):
        quote = self.peek()
        self.i += 1
        buf = []
        while self.i < len(self.s):
            c = self.s[self.i]
            if quote == '"' and c == "\\" and self.i + 1 < len(self.s):
                buf.append(self.s[self.i + 1])
                self.i += 2
                continue
            if c == quote:
                if quote == "'" and self.s[self.i + 1 : self.i + 2] == "'":
                    buf.append("'")
                    self.i += 2
                    continue
                self.i += 1
                return "".join(buf)
            buf.append(c)
            self.i += 1
        self.fail("unterminated quoted string")

    def plain(self, top):
        if top:
            text = self.s[self.i :]
            self.i = len(self.s)
        else:
            start = self.i
            while self.peek() not in ("", ",", "]", "}"):
                self.i += 1
            text = self.s[start : self.i]
        text = text.strip()
        if text == "" and not top:
            self.fail("empty value in a list or map; use null or quotes")
        return _scalar(text)
```

- [ ] **Step 5: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_miniyaml.py' -v`
Expected: `Ran 21 tests` … `OK`.

- [ ] **Step 6: Commit**

```bash
git add tests/helpers.py tests/test_miniyaml.py scripts/miniyaml.py
git commit -m "feat(scripts): flow-style YAML subset parser"
```

---

### Task 3: Glob matching and overlap

**Files:**
- Create: `tests/test_globs.py`
- Create: `scripts/globs.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `matches(glob, path) -> bool`, `overlaps(a, b) -> bool` (conservative: undecidable → `True`), `covers(outer, inner) -> bool`, `has_wildcard(glob)`, `literal_prefix(glob)`, `to_regex(glob)`.

- [ ] **Step 1: Write the failing tests**

```python
import unittest

import helpers  # noqa: F401
from globs import covers, matches, overlaps


class MatchTests(unittest.TestCase):
    def test_double_star_crosses_directories(self):
        self.assertTrue(matches("src/api/**", "src/api/checkout/pay.ts"))

    def test_single_star_stays_in_segment(self):
        self.assertTrue(matches("src/*.ts", "src/a.ts"))
        self.assertFalse(matches("src/*.ts", "src/deep/a.ts"))

    def test_double_star_slash_matches_zero_dirs(self):
        self.assertTrue(matches("src/**/index.ts", "src/index.ts"))
        self.assertTrue(matches("src/**/index.ts", "src/a/b/index.ts"))

    def test_literal(self):
        self.assertTrue(matches("package-lock.json", "package-lock.json"))
        self.assertFalse(matches("package-lock.json", "a/package-lock.json"))

    def test_question_mark(self):
        self.assertTrue(matches("a?.ts", "ab.ts"))
        self.assertFalse(matches("a?.ts", "a/.ts"))


class OverlapTests(unittest.TestCase):
    def test_nested_globs_overlap(self):
        self.assertTrue(overlaps("src/api/**", "src/api/checkout/**"))

    def test_sibling_globs_do_not_overlap(self):
        self.assertFalse(overlaps("src/api/**", "src/web/**"))

    def test_literal_inside_glob(self):
        self.assertTrue(overlaps("src/api/**", "src/api/index.ts"))
        self.assertFalse(overlaps("src/api/**", "src/web/index.ts"))

    def test_two_literals(self):
        self.assertTrue(overlaps("a/b.ts", "a/b.ts"))
        self.assertFalse(overlaps("a/b.ts", "a/c.ts"))

    def test_leading_double_star_is_undecidable_so_overlaps(self):
        self.assertTrue(overlaps("**/x.ts", "src/**"))

    def test_same_dir_different_extensions_is_conservative_overlap(self):
        self.assertTrue(overlaps("src/*.py", "src/*.ts"))

    def test_symmetric(self):
        self.assertEqual(overlaps("src/a/**", "src/**"), overlaps("src/**", "src/a/**"))


class CoverTests(unittest.TestCase):
    def test_subtree_is_covered(self):
        self.assertTrue(covers("src/api/**", "src/api/checkout/**"))

    def test_equal_is_covered(self):
        self.assertTrue(covers("src/api/**", "src/api/**"))

    def test_outside_is_not_covered(self):
        self.assertFalse(covers("src/api/**", "src/web/**"))

    def test_double_star_not_covered_by_single_star(self):
        self.assertFalse(covers("src/api/*", "src/api/**"))

    def test_literal_file_covered_by_glob(self):
        self.assertTrue(covers("src/api/**", "src/api/index.ts"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_globs.py' -v`
Expected: error `ModuleNotFoundError: No module named 'globs'`.

- [ ] **Step 3: Implement**

```python
"""Path-glob helpers for ownership checks.

Glob dialect: `*` matches within one path segment, `**` matches across segments,
`**/` matches zero or more directories, `?` matches one non-slash character.
No character classes or brace expansion; `[`, `{` and friends are literal.
Directories must be written as `dir/**`, never as `dir/`.
"""
import re


def has_wildcard(glob):
    return "*" in glob or "?" in glob


def to_regex(glob):
    out = []
    i = 0
    while i < len(glob):
        c = glob[i]
        if c == "*":
            if glob.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
            elif glob.startswith("**", i):
                out.append(".*")
                i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def matches(glob, path):
    return to_regex(glob).match(path) is not None


def literal_prefix(glob):
    """Leading path segments that contain no wildcard."""
    segments = []
    for segment in glob.split("/"):
        if has_wildcard(segment):
            break
        segments.append(segment)
    return segments


def overlaps(a, b):
    """True if two globs may match a common path. Conservative: undecidable -> True."""
    wild_a, wild_b = has_wildcard(a), has_wildcard(b)
    if not wild_a and not wild_b:
        return a == b
    if not wild_a:
        return matches(b, a)
    if not wild_b:
        return matches(a, b)
    prefix_a, prefix_b = literal_prefix(a), literal_prefix(b)
    n = min(len(prefix_a), len(prefix_b))
    return prefix_a[:n] == prefix_b[:n]


def covers(outer, inner):
    """True if every path `inner` can match is also matched by `outer` (conservative)."""
    if outer == inner:
        return True
    if "**" in inner and "**" not in outer:
        return False
    return matches(outer, inner)
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_globs.py' -v`
Expected: `Ran 17 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_globs.py scripts/globs.py
git commit -m "feat(scripts): glob matching, overlap and coverage"
```

---

### Task 4: Model routing

**Files:**
- Create: `tests/test_routing.py`
- Create: `scripts/routing.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `derive_model(score: dict) -> "haiku"|"sonnet"|"opus"`; `NeedsPlanningError(ValueError)` raised when `ambiguity == 2`; `validate_score(score)`; constants `SIGNALS = ("scope","ambiguity","risk","reasoning")`, `MODELS = ("haiku","sonnet","opus")`; CLI `python3 routing.py --scope N --ambiguity N --risk N --reasoning N` (prints the model; exit 2 + `NEEDS-PLANNING` on stderr when ambiguity is 2).

- [ ] **Step 1: Write the failing tests**

```python
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

import helpers  # noqa: F401
import routing
from routing import NeedsPlanningError, derive_model


def score(scope=0, ambiguity=0, risk=0, reasoning=0):
    return {"scope": scope, "ambiguity": ambiguity, "risk": risk, "reasoning": reasoning}


class DeriveModelTests(unittest.TestCase):
    def test_all_zero_is_haiku(self):
        self.assertEqual(derive_model(score()), "haiku")

    def test_sum_two_is_haiku(self):
        self.assertEqual(derive_model(score(scope=1, reasoning=1)), "haiku")

    def test_sum_three_is_sonnet(self):
        self.assertEqual(derive_model(score(scope=1, ambiguity=1, reasoning=1)), "sonnet")

    def test_sum_five_is_sonnet(self):
        self.assertEqual(derive_model(score(scope=2, ambiguity=1, risk=1, reasoning=1)), "sonnet")

    def test_sum_six_is_opus(self):
        self.assertEqual(derive_model(score(scope=2, ambiguity=1, risk=1, reasoning=2)), "opus")

    def test_risk_two_forces_opus_even_when_sum_is_low(self):
        self.assertEqual(derive_model(score(risk=2)), "opus")

    def test_ambiguity_two_needs_planning(self):
        with self.assertRaises(NeedsPlanningError):
            derive_model(score(ambiguity=2))

    def test_ambiguity_two_beats_risk_two(self):
        with self.assertRaises(NeedsPlanningError):
            derive_model(score(ambiguity=2, risk=2))


class ValidationTests(unittest.TestCase):
    def test_missing_signal(self):
        with self.assertRaisesRegex(ValueError, "missing"):
            derive_model({"scope": 1})

    def test_out_of_range(self):
        with self.assertRaisesRegex(ValueError, "0-2"):
            derive_model(score(scope=3))

    def test_bool_is_not_an_int(self):
        with self.assertRaisesRegex(ValueError, "0-2"):
            derive_model(score(scope=True))

    def test_not_a_map(self):
        with self.assertRaisesRegex(ValueError, "must be a map"):
            derive_model([1, 2])


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = routing.main(list(args))
        return code, out.getvalue().strip(), err.getvalue().strip()

    def test_prints_model(self):
        code, out, _ = self.run_cli("--scope", "1", "--ambiguity", "0", "--risk", "2", "--reasoning", "1")
        self.assertEqual((code, out), (0, "opus"))

    def test_needs_planning_exit_code(self):
        code, out, err = self.run_cli("--scope", "0", "--ambiguity", "2", "--risk", "0", "--reasoning", "0")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("NEEDS-PLANNING", err)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_routing.py' -v`
Expected: error `ModuleNotFoundError: No module named 'routing'`.

- [ ] **Step 3: Implement**

```python
"""Model routing: score a phase on four signals and derive the model tier.

Usage: python3 routing.py --scope 1 --ambiguity 0 --risk 2 --reasoning 1
Prints the model (haiku | sonnet | opus). Exit 2 if the phase needs more planning.
"""
import argparse
import sys

SIGNALS = ("scope", "ambiguity", "risk", "reasoning")
MODELS = ("haiku", "sonnet", "opus")


class NeedsPlanningError(ValueError):
    """Ambiguity 2: the phase must be specified further, not routed to a bigger model."""


def validate_score(score):
    if not isinstance(score, dict):
        raise ValueError("score must be a map like {scope: 1, ambiguity: 0, risk: 0, reasoning: 1}")
    missing = [s for s in SIGNALS if s not in score]
    extra = [k for k in score if k not in SIGNALS]
    if missing or extra:
        raise ValueError(f"score needs exactly {SIGNALS}; missing={missing} unexpected={extra}")
    for name in SIGNALS:
        value = score[name]
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 2:
            raise ValueError(f"score.{name} must be an integer 0-2, got {value!r}")


def derive_model(score):
    validate_score(score)
    if score["ambiguity"] == 2:
        raise NeedsPlanningError("ambiguity 2: return this phase to planning and specify it further")
    if score["risk"] == 2:
        return "opus"
    total = sum(score[s] for s in SIGNALS)
    if total <= 2:
        return "haiku"
    if total <= 5:
        return "sonnet"
    return "opus"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in SIGNALS:
        parser.add_argument(f"--{name}", type=int, required=True, choices=(0, 1, 2))
    args = parser.parse_args(argv)
    score = {name: getattr(args, name) for name in SIGNALS}
    try:
        print(derive_model(score))
    except NeedsPlanningError as exc:
        print(f"NEEDS-PLANNING: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_routing.py' -v`
Expected: `Ran 14 tests` … `OK`.

- [ ] **Step 5: Smoke-test the CLI**

Run: `python3 scripts/routing.py --scope 1 --ambiguity 0 --risk 2 --reasoning 1`
Expected output: `opus`

- [ ] **Step 6: Commit**

```bash
git add tests/test_routing.py scripts/routing.py
git commit -m "feat(scripts): model routing rubric and CLI"
```

---

### Task 5: Ownership diff checker

**Files:**
- Create: `tests/test_check_owned.py`
- Create: `scripts/check_owned.py`

**Interfaces:**
- Consumes: `globs.matches`.
- Produces: `violations(paths, owns) -> list[str]`; CLI `git diff --name-only … | python3 check_owned.py --owns 'glob' …` printing `NOT-OWNED <path>` per violation and exiting 1, or `OK <n> path(s) within owned globs` and exiting 0.

- [ ] **Step 1: Write the failing tests**

```python
import io
import unittest
from contextlib import redirect_stdout

import helpers  # noqa: F401
import check_owned


def run(owns, paths):
    out = io.StringIO()
    with redirect_stdout(out):
        code = check_owned.main(["--owns", *owns], stdin=io.StringIO("\n".join(paths) + "\n"))
    return code, out.getvalue()


class CheckOwnedTests(unittest.TestCase):
    def test_all_inside(self):
        code, out = run(["src/a/**", "tests/a/**"], ["src/a/x.ts", "tests/a/deep/y.ts"])
        self.assertEqual(code, 0)
        self.assertIn("OK 2 path(s)", out)

    def test_outside_path_is_reported(self):
        code, out = run(["src/a/**"], ["src/a/x.ts", "src/b/y.ts"])
        self.assertEqual(code, 1)
        self.assertIn("NOT-OWNED src/b/y.ts", out)
        self.assertNotIn("src/a/x.ts", out)

    def test_empty_diff_is_ok(self):
        code, out = run(["src/a/**"], [])
        self.assertEqual(code, 0)
        self.assertIn("OK 0 path(s)", out)

    def test_lockfile_not_owned_unless_listed(self):
        code, _ = run(["src/a/**"], ["package-lock.json"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_check_owned.py' -v`
Expected: error `ModuleNotFoundError: No module named 'check_owned'`.

- [ ] **Step 3: Implement**

```python
"""Verify changed paths stay inside a phase's owned globs.

Usage: git diff --name-only <base>...<branch> | python3 check_owned.py --owns 'src/a/**' 'tests/a/**'
Reads one path per line on stdin. Exit 0 if every path matches an owned glob,
exit 1 (and list the violations on stdout) otherwise.
"""
import argparse
import sys

from globs import matches


def violations(paths, owns):
    return [p for p in paths if not any(matches(glob, p) for glob in owns)]


def main(argv=None, stdin=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owns", nargs="+", required=True, help="owned globs")
    args = parser.parse_args(argv)
    lines = (stdin or sys.stdin).read().splitlines()
    paths = [line.strip() for line in lines if line.strip()]
    bad = violations(paths, args.owns)
    for path in bad:
        print(f"NOT-OWNED {path}")
    if bad:
        return 1
    print(f"OK {len(paths)} path(s) within owned globs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_check_owned.py' -v`
Expected: `Ran 4 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add tests/test_check_owned.py scripts/check_owned.py
git commit -m "feat(scripts): post-hoc ownership checker for phase diffs"
```

---

### Task 6: Plan and spec loader (with the valid fixture project)

**Files:**
- Create: `tests/fixtures/valid/plan.md`
- Create: `tests/fixtures/valid/docs/waves/specs/F1.md`, `F2.md`, `F3.md`, `F4.md`
- Create: `tests/test_plan_loader.py`
- Create: `scripts/plan_loader.py`

**Interfaces:**
- Consumes: `miniyaml.parse_document`.
- Produces: `load_project(root) -> Project(root, plan, specs)`, `parse_spec(path) -> Spec`, `parse_plan(path) -> Plan`, `fenced_blocks(text, kind)`, `PlanFormatError(ValueError)`. Dataclasses: `Criterion(id, text, verify)`, `Spec(id, title, depends_on, owns, reads, risk, steps, criteria, path)`, `Phase(id, spec, steps, owns, depends_on, model, score, rationale, override)`, `Wave(number, phases, integration_owned, criteria, integration_checks)`, `Header(design, bootstrap, gates, max_wave_width)`, `Plan(header, phases, waves, path)`, `Project(root, plan, specs)`. Global criterion ids are `<spec id>.<key>`, e.g. `F2.AC1`.

The fixture is a small shop project: 4 features, 6 phases, 3 waves (wave 1: `P1a`,`P1b`,`P4a`; wave 2: `P2a`,`P2b`; wave 3: `P3a`). Every later test mutates a private copy of it.

- [ ] **Step 1: Create the fixture project**

`tests/fixtures/valid/plan.md`:

````markdown
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
````

`tests/fixtures/valid/docs/waves/specs/F1.md`:

````markdown
---
id: F1
title: Data layer
depends_on: []
owns: [src/db/**, tests/db/**]
reads: []
risk: []
steps: [F1.1, F1.2]
---

# F1 Data layer

## Summary

Database schema and seed data for products and carts.

## Acceptance criteria

```yaml criteria
AC1: {text: "Schema migrates cleanly on an empty database", verify: "cmd:npx vitest run tests/db/schema"}
AC2: {text: "Seed script loads the sample products", verify: "test:tests/db/seed/seed.test.ts"}
```

## Steps

- F1.1 Write the schema and migration.
- F1.2 Write the seed script.
````

`tests/fixtures/valid/docs/waves/specs/F2.md`:

````markdown
---
id: F2
title: Checkout API
depends_on: [F1]
owns: [src/api/**, tests/api/**]
reads: []
risk: [money]
steps: [F2.1, F2.2]
---

# F2 Checkout API

## Summary

HTTP endpoints for the cart and for checkout totals.

## Acceptance criteria

```yaml criteria
AC1: {text: "Checkout total includes tax and discounts", verify: "test:tests/api/checkout/total.test.ts"}
AC2: {text: "Adding an item to the cart returns 201", verify: "http:POST /cart/items returns 201"}
```

## Steps

- F2.1 Checkout total calculation and endpoint.
- F2.2 Cart item endpoints.
````

`tests/fixtures/valid/docs/waves/specs/F3.md`:

````markdown
---
id: F3
title: Cart UI
depends_on: [F2, F4]
owns: [src/ui/cart/**, tests/ui/cart/**]
reads: [docs/waves/design/shop.html#screen-cart]
risk: []
steps: [F3.1]
---

# F3 Cart UI

## Summary

The cart screen, implemented from the frozen design.

## Acceptance criteria

```yaml criteria
AC1: {text: "Cart screen matches the approved design", verify: "design-fidelity:screen-cart"}
```

## Steps

- F3.1 Build the cart screen.
````

`tests/fixtures/valid/docs/waves/specs/F4.md`:

````markdown
---
id: F4
title: Design tokens
depends_on: []
owns: [src/ui/tokens/**, tests/ui/tokens/**]
reads: [docs/waves/design/shop.html#tokens]
risk: []
steps: [F4.1]
---

# F4 Design tokens

## Summary

Colour, spacing and type tokens extracted from the frozen design.

## Acceptance criteria

```yaml criteria
AC1: {text: "Tokens compile and match the design values", verify: "cmd:npx vitest run tests/ui/tokens"}
```

## Steps

- F4.1 Create the token module.
````

- [ ] **Step 2: Write the failing tests**

````python
import unittest

import helpers
from helpers import ProjectTestCase
from plan_loader import PlanFormatError, load_project, parse_plan, parse_spec


class LoadValidFixtureTests(ProjectTestCase):
    def test_loads_specs_and_plan(self):
        project = load_project(self.root)
        self.assertEqual(sorted(project.specs), ["F1", "F2", "F3", "F4"])
        self.assertEqual([p.id for p in project.plan.phases], ["P1a", "P1b", "P4a", "P2a", "P2b", "P3a"])
        self.assertEqual([w.number for w in project.plan.waves], [1, 2, 3])

    def test_header_fields(self):
        header = load_project(self.root).plan.header
        self.assertEqual(header.bootstrap, "npm ci")
        self.assertEqual(header.max_wave_width, 4)
        self.assertEqual(header.gates["lint"], "npx eslint .")

    def test_spec_fields(self):
        f2 = load_project(self.root).specs["F2"]
        self.assertEqual(f2.depends_on, ["F1"])
        self.assertEqual(f2.risk, ["money"])
        self.assertEqual([c.id for c in f2.criteria], ["F2.AC1", "F2.AC2"])
        self.assertEqual(f2.criteria[1].verify, "http:POST /cart/items returns 201")

    def test_phase_fields(self):
        p2a = {p.id: p for p in load_project(self.root).plan.phases}["P2a"]
        self.assertEqual(p2a.model, "opus")
        self.assertEqual(p2a.score["risk"], 2)
        self.assertEqual(p2a.depends_on, ["P1a"])

    def test_wave_fields(self):
        w1 = load_project(self.root).plan.waves[0]
        self.assertEqual(w1.phases, ["P1a", "P1b", "P4a"])
        self.assertEqual(w1.integration_owned, ["package-lock.json"])
        self.assertEqual(w1.criteria, ["F1.AC1", "F1.AC2", "F4.AC1"])

    def test_status_block_is_ignored(self):
        self.edit("plan.md", "W1: pending", "W1: whatever: we: like")
        load_project(self.root)  # does not raise


class LineEndingTests(ProjectTestCase):
    def test_crlf_files_parse_like_lf_files(self):
        for path in [self.root / "plan.md", *(self.root / "docs/waves/specs").glob("*.md")]:
            text = path.read_text(encoding="utf-8")
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
        project = load_project(self.root)
        self.assertEqual(len(project.plan.phases), 6)
        self.assertEqual(project.specs["F2"].criteria[1].verify, "http:POST /cart/items returns 201")


class FormatErrorTests(ProjectTestCase):
    def assertFormatError(self, pattern):
        with self.assertRaisesRegex(PlanFormatError, pattern):
            load_project(self.root)

    def test_missing_plan(self):
        (self.root / "plan.md").unlink()
        self.assertFormatError("plan.md: not found")

    def test_no_specs(self):
        for f in (self.root / "docs/waves/specs").glob("*.md"):
            f.unlink()
        self.assertFormatError("no spec files found")

    def test_spec_without_frontmatter(self):
        self.edit("docs/waves/specs/F1.md", "---\nid: F1", "id: F1")
        self.assertFormatError("missing '---' frontmatter")

    def test_spec_missing_required_field(self):
        self.edit("docs/waves/specs/F1.md", "owns: [src/db/**, tests/db/**]\n", "")
        self.assertFormatError("missing required field 'owns'")

    def test_indented_yaml_in_spec(self):
        self.edit("docs/waves/specs/F1.md", "risk: []", "risk:\n  - data")
        self.assertFormatError("indentation is not supported")

    def test_list_field_must_be_flow_list(self):
        self.edit("docs/waves/specs/F1.md", "steps: [F1.1, F1.2]", "steps: F1.1")
        self.assertFormatError("must be a flow list")

    def test_duplicate_spec_id(self):
        self.edit("docs/waves/specs/F4.md", "id: F4", "id: F1")
        self.assertFormatError("duplicate spec id")

    def test_criterion_must_be_a_map(self):
        self.edit("docs/waves/specs/F1.md", 'AC1: {text: "Schema migrates cleanly on an empty database", verify: "cmd:npx vitest run tests/db/schema"}', "AC1: nope")
        self.assertFormatError("criterion AC1")

    def test_missing_header_block(self):
        self.edit("plan.md", "```yaml header", "```yaml heading")
        self.assertFormatError("exactly one ```yaml header block")

    def test_phase_missing_score(self):
        self.edit("plan.md", 'score: {scope: 1, ambiguity: 0, risk: 1, reasoning: 1}\n', "")
        self.assertFormatError("phase P1a: missing required field 'score'")

    def test_wave_number_must_be_int(self):
        self.edit("plan.md", "wave: 1", "wave: one")
        self.assertFormatError("'wave' must be an integer")

    def test_bad_max_wave_width(self):
        self.edit("plan.md", "max_wave_width: 4", "max_wave_width: zero")
        self.assertFormatError("max_wave_width")


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 3: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_plan_loader.py' -v`
Expected: error `ModuleNotFoundError: No module named 'plan_loader'`.

- [ ] **Step 4: Implement**

````python
"""Load a wave-planning project: root plan.md plus docs/waves/specs/*.md.

Machine-readable data lives in fenced blocks tagged with an info string:
  ```yaml header | phase | wave | status   (in plan.md)
  ```yaml criteria                          (in specs)
and in the `---` frontmatter of each spec. Everything else is prose for humans.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from miniyaml import MiniYamlError, parse_document

DEFAULT_MAX_WAVE_WIDTH = 8

_FENCE_RE = re.compile(r"^```yaml (\w+)[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*$", re.S | re.M)


class PlanFormatError(ValueError):
    pass


@dataclass
class Criterion:
    id: str  # global id, e.g. "F2.AC1"
    text: str
    verify: str


@dataclass
class Spec:
    id: str
    title: str
    depends_on: list
    owns: list
    reads: list
    risk: list
    steps: list
    criteria: list
    path: str


@dataclass
class Phase:
    id: str
    spec: str
    steps: list
    owns: list
    depends_on: list
    model: str
    score: dict
    rationale: str
    override: str = None


@dataclass
class Wave:
    number: int
    phases: list
    integration_owned: list
    criteria: list
    integration_checks: list


@dataclass
class Header:
    design: str
    bootstrap: str
    gates: dict
    max_wave_width: int


@dataclass
class Plan:
    header: Header
    phases: list
    waves: list
    path: str


@dataclass
class Project:
    root: Path
    plan: Plan
    specs: dict = field(default_factory=dict)


def _read(path):
    """Read a UTF-8 file with newlines normalised, so CRLF files parse like LF files."""
    return Path(path).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def fenced_blocks(text, kind):
    return [body for tag, body in _FENCE_RE.findall(text) if tag == kind]


def _parse(body, where):
    try:
        return parse_document(body)
    except MiniYamlError as exc:
        raise PlanFormatError(f"{where}: {exc}") from exc


def _need(doc, key, where):
    if key not in doc or doc[key] is None:
        raise PlanFormatError(f"{where}: missing required field {key!r}")
    return doc[key]


def _need_str(doc, key, where):
    value = _need(doc, key, where)
    if not isinstance(value, str):
        raise PlanFormatError(f"{where}: {key!r} must be text, got {value!r}")
    return value


def _str_list(doc, key, where, required=True):
    if key not in doc or doc[key] is None:
        if required:
            raise PlanFormatError(f"{where}: missing required field {key!r}")
        return []
    value = doc[key]
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise PlanFormatError(f"{where}: {key!r} must be a flow list of text, e.g. [a, b]")
    return value


def parse_spec(path):
    path = Path(path)
    where = str(path)
    text = _read(path)
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise PlanFormatError(f"{where}: missing '---' frontmatter at the top of the file")
    front = _parse(match.group(1), f"{where} frontmatter")
    spec_id = _need_str(front, "id", where)
    criteria = []
    for body in fenced_blocks(text, "criteria"):
        for key, entry in _parse(body, f"{where} criteria").items():
            label = f"{where} criterion {key}"
            if not isinstance(entry, dict):
                raise PlanFormatError(f"{label}: expected {{text: ..., verify: ...}}")
            criteria.append(
                Criterion(
                    id=f"{spec_id}.{key}",
                    text=_need_str(entry, "text", label),
                    verify=str(entry.get("verify") or ""),
                )
            )
    return Spec(
        id=spec_id,
        title=_need_str(front, "title", where),
        depends_on=_str_list(front, "depends_on", where),
        owns=_str_list(front, "owns", where),
        reads=_str_list(front, "reads", where, required=False),
        risk=_str_list(front, "risk", where, required=False),
        steps=_str_list(front, "steps", where),
        criteria=criteria,
        path=where,
    )


def parse_plan(path):
    path = Path(path)
    where = str(path)
    text = _read(path)

    headers = fenced_blocks(text, "header")
    if len(headers) != 1:
        raise PlanFormatError(f"{where}: expected exactly one ```yaml header block, found {len(headers)}")
    h = _parse(headers[0], f"{where} header")
    gates = h.get("gates") or {}
    if not isinstance(gates, dict):
        raise PlanFormatError(f"{where} header: 'gates' must be a map like {{lint: \"...\"}}")
    width = h.get("max_wave_width", DEFAULT_MAX_WAVE_WIDTH)
    if isinstance(width, bool) or not isinstance(width, int) or width < 1:
        raise PlanFormatError(f"{where} header: 'max_wave_width' must be a positive integer")
    header = Header(design=h.get("design"), bootstrap=h.get("bootstrap"), gates=gates, max_wave_width=width)

    phases = []
    for body in fenced_blocks(text, "phase"):
        p = _parse(body, f"{where} phase")
        pid = _need_str(p, "id", f"{where} phase")
        label = f"{where} phase {pid}"
        score = _need(p, "score", label)
        if not isinstance(score, dict):
            raise PlanFormatError(f"{label}: 'score' must be a map")
        override = p.get("override")
        phases.append(
            Phase(
                id=pid,
                spec=_need_str(p, "spec", label),
                steps=_str_list(p, "steps", label),
                owns=_str_list(p, "owns", label),
                depends_on=_str_list(p, "depends_on", label),
                model=_need_str(p, "model", label),
                score=score,
                rationale=str(p.get("rationale") or ""),
                override=None if override is None else str(override),
            )
        )

    waves = []
    for body in fenced_blocks(text, "wave"):
        w = _parse(body, f"{where} wave")
        number = _need(w, "wave", f"{where} wave")
        if isinstance(number, bool) or not isinstance(number, int):
            raise PlanFormatError(f"{where} wave: 'wave' must be an integer, got {number!r}")
        label = f"{where} wave {number}"
        waves.append(
            Wave(
                number=number,
                phases=_str_list(w, "phases", label),
                integration_owned=_str_list(w, "integration_owned", label, required=False),
                criteria=_str_list(w, "criteria", label, required=False),
                integration_checks=_str_list(w, "integration_checks", label, required=False),
            )
        )
    if not phases:
        raise PlanFormatError(f"{where}: no ```yaml phase blocks found")
    if not waves:
        raise PlanFormatError(f"{where}: no ```yaml wave blocks found")
    return Plan(header=header, phases=phases, waves=waves, path=where)


def load_project(root):
    root = Path(root)
    plan_path = root / "plan.md"
    if not plan_path.is_file():
        raise PlanFormatError(f"{plan_path}: not found (run from the project root or pass --root)")
    specs_dir = root / "docs" / "waves" / "specs"
    paths = sorted(specs_dir.glob("*.md")) if specs_dir.is_dir() else []
    if not paths:
        raise PlanFormatError(f"{specs_dir}: no spec files found")
    specs = {}
    for path in paths:
        spec = parse_spec(path)
        if spec.id in specs:
            raise PlanFormatError(f"{path}: duplicate spec id {spec.id!r}")
        specs[spec.id] = spec
    return Project(root=root, plan=parse_plan(plan_path), specs=specs)
````

- [ ] **Step 5: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_plan_loader.py' -v`
Expected: `Ran 19 tests` … `OK`.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures tests/test_plan_loader.py scripts/plan_loader.py
git commit -m "feat(scripts): load plan.md and feature specs; add valid fixture project"
```


### Task 7: Graph checks (references, cycles, waves, width, step coverage)

**Files:**
- Create: `scripts/findings.py`
- Create: `tests/test_checks_graph.py`
- Create: `scripts/checks_graph.py`

**Interfaces:**
- Consumes: `plan_loader.Project` and its dataclasses; `findings.Finding`.
- Produces: `Finding(code, message)` (frozen dataclass; `str(f)` → `ERROR [code] message`). Check functions, each `check_x(project) -> list[Finding]`: `check_refs` (codes `dup-id`, `dep-unresolved`, `step-coverage`), `check_cycles` (`dep-cycle`), `check_waves` (`wave-numbering`, `wave-empty`, `wave-coverage`, `wave-order`, `drift-feature-dep`, `feature-order`), `check_width` (`wave-width`), `check_step_coverage` (`step-coverage`).

Semantics worth knowing: a feature dependency means **all** phases of the dependency finish in earlier waves than **any** phase of the dependent feature (`feature-order`); split features finer if you want finer parallelism. A phase-level dependency on another feature's phase must be declared in the spec's `depends_on` (`drift-feature-dep`).

- [ ] **Step 1: Write the failing tests**

```python
import unittest

from helpers import ProjectTestCase
from plan_loader import load_project
import checks_graph as g


class GraphCheckTests(ProjectTestCase):
    def run_check(self, check):
        return check(load_project(self.root))

    def test_valid_fixture_has_no_graph_findings(self):
        project = load_project(self.root)
        for check in (g.check_refs, g.check_cycles, g.check_waves, g.check_width, g.check_step_coverage):
            self.assertEqual(check(project), [], check.__name__)

    # refs
    def test_unknown_phase_dependency(self):
        self.edit("plan.md", "depends_on: [P1a]", "depends_on: [P9z]")
        self.assertIn("dep-unresolved", self.codes(self.run_check(g.check_refs)))

    def test_unknown_spec_dependency(self):
        self.edit("docs/waves/specs/F2.md", "depends_on: [F1]", "depends_on: [F9]")
        self.assertIn("dep-unresolved", self.codes(self.run_check(g.check_refs)))

    def test_phase_with_unknown_spec(self):
        self.edit("plan.md", "spec: F1\nsteps: [F1.1]", "spec: F9\nsteps: [F1.1]")
        self.assertIn("dep-unresolved", self.codes(self.run_check(g.check_refs)))

    def test_wave_lists_unknown_phase(self):
        self.edit("plan.md", "phases: [P3a]", "phases: [P3a, P7q]")
        self.assertIn("dep-unresolved", self.codes(self.run_check(g.check_refs)))

    def test_duplicate_phase_id(self):
        self.edit("plan.md", "id: P1b", "id: P1a")
        self.assertIn("dup-id", self.codes(self.run_check(g.check_refs)))

    def test_phase_step_not_declared_by_spec(self):
        self.edit("plan.md", "steps: [F1.1]", "steps: [F1.9]")
        self.assertIn("step-coverage", self.codes(self.run_check(g.check_refs)))

    # cycles
    def test_feature_cycle(self):
        self.edit("docs/waves/specs/F1.md", "depends_on: []", "depends_on: [F2]")
        findings = self.run_check(g.check_cycles)
        self.assertIn("dep-cycle", self.codes(findings))
        self.assertIn("feature dependency cycle", findings[0].message)

    def test_phase_depending_on_itself(self):
        self.edit("plan.md", "owns: [src/db/schema/**, tests/db/schema/**]\ndepends_on: []", "owns: [src/db/schema/**, tests/db/schema/**]\ndepends_on: [P1a]")
        findings = self.run_check(g.check_cycles)
        self.assertIn("P1a -> P1a", " ".join(f.message for f in findings))

    def test_phase_cycle(self):
        self.edit("plan.md", "owns: [src/db/schema/**, tests/db/schema/**]\ndepends_on: []", "owns: [src/db/schema/**, tests/db/schema/**]\ndepends_on: [P2a]")
        findings = self.run_check(g.check_cycles)
        self.assertIn("phase dependency cycle", " ".join(f.message for f in findings))

    # waves
    def test_wave_numbering_gap(self):
        self.edit("plan.md", "wave: 3", "wave: 4")
        self.assertIn("wave-numbering", self.codes(self.run_check(g.check_waves)))

    def test_wave_with_no_phases(self):
        self.edit("plan.md", "phases: [P3a]", "phases: []")
        self.assertIn("wave-empty", self.codes(self.run_check(g.check_waves)))

    def test_phase_missing_from_all_waves(self):
        self.edit("plan.md", "phases: [P1a, P1b, P4a]", "phases: [P1a, P1b]")
        findings = self.run_check(g.check_waves)
        self.assertIn("wave-coverage", self.codes(findings))
        self.assertIn("P4a", " ".join(f.message for f in findings))

    def test_phase_in_two_waves(self):
        self.edit("plan.md", "phases: [P3a]", "phases: [P3a, P1b]")
        self.assertIn("wave-coverage", self.codes(self.run_check(g.check_waves)))

    def test_prerequisite_in_same_wave(self):
        self.edit("plan.md", "phases: [P1a, P1b, P4a]", "phases: [P1a, P1b, P4a, P2a]")
        self.edit("plan.md", "phases: [P2a, P2b]", "phases: [P2b]")
        self.assertIn("wave-order", self.codes(self.run_check(g.check_waves)))

    def test_phase_dependency_not_in_spec_dependencies(self):
        self.edit("docs/waves/specs/F2.md", "depends_on: [F1]", "depends_on: []")
        self.assertIn("drift-feature-dep", self.codes(self.run_check(g.check_waves)))

    def test_feature_dependency_must_finish_first(self):
        self.edit("plan.md", "phases: [P1a, P1b, P4a]", "phases: [P1a, P4a]")
        self.edit("plan.md", "phases: [P2a, P2b]", "phases: [P1b, P2a, P2b]")
        self.assertIn("feature-order", self.codes(self.run_check(g.check_waves)))

    # width
    def test_wave_wider_than_limit(self):
        self.edit("plan.md", "max_wave_width: 4", "max_wave_width: 2")
        findings = self.run_check(g.check_width)
        self.assertEqual(self.codes(findings), {"wave-width"})
        self.assertIn("wave 1 has 3 phases", findings[0].message)

    # step coverage
    def test_spec_step_without_phase(self):
        self.edit("docs/waves/specs/F1.md", "steps: [F1.1, F1.2]", "steps: [F1.1, F1.2, F1.3]")
        findings = self.run_check(g.check_step_coverage)
        self.assertIn("F1.3", findings[0].message)

    def test_step_in_two_phases(self):
        self.edit("plan.md", "steps: [F1.2]", "steps: [F1.1, F1.2]")
        self.assertIn("step-coverage", self.codes(self.run_check(g.check_step_coverage)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_checks_graph.py' -v`
Expected: error `ModuleNotFoundError: No module named 'checks_graph'`.

- [ ] **Step 3: Implement `Finding` and the graph checks**

`scripts/findings.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    code: str
    message: str

    def __str__(self):
        return f"ERROR [{self.code}] {self.message}"
```

`scripts/checks_graph.py`:

```python
"""Structure checks: references, cycles, wave layout, widths, step coverage, feature drift."""
from collections import Counter

from findings import Finding


def _phase_map(project):
    return {p.id: p for p in project.plan.phases}


def check_refs(project):
    findings = []
    phases = project.plan.phases
    ids = Counter(p.id for p in phases)
    for pid, count in ids.items():
        if count > 1:
            findings.append(Finding("dup-id", f"phase id {pid} is defined {count} times"))
    by_id = _phase_map(project)
    for phase in phases:
        spec = project.specs.get(phase.spec)
        if spec is None:
            findings.append(Finding("dep-unresolved", f"phase {phase.id} references unknown spec {phase.spec}"))
        else:
            for step in phase.steps:
                if step not in spec.steps:
                    findings.append(
                        Finding("step-coverage", f"phase {phase.id} lists step {step}, which spec {spec.id} does not declare")
                    )
        for dep in phase.depends_on:
            if dep not in by_id:
                findings.append(Finding("dep-unresolved", f"phase {phase.id} depends on unknown phase {dep}"))
    for spec in project.specs.values():
        for dep in spec.depends_on:
            if dep not in project.specs:
                findings.append(Finding("dep-unresolved", f"spec {spec.id} depends on unknown spec {dep}"))
    for wave in project.plan.waves:
        for pid in wave.phases:
            if pid not in by_id:
                findings.append(Finding("dep-unresolved", f"wave {wave.number} lists unknown phase {pid}"))
    return findings


def _find_cycle(graph):
    white, grey, black = 0, 1, 2
    color = {node: white for node in graph}
    stack = []

    def visit(node):
        color[node] = grey
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in color:
                continue
            if color[nxt] == grey:
                return stack[stack.index(nxt) :] + [nxt]
            if color[nxt] == white:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = black
        return None

    for node in list(graph):
        if color[node] == white:
            found = visit(node)
            if found:
                return found
    return None


def check_cycles(project):
    findings = []
    feature_graph = {s.id: list(s.depends_on) for s in project.specs.values()}
    phase_graph = {p.id: list(p.depends_on) for p in project.plan.phases}
    for label, graph in (("feature", feature_graph), ("phase", phase_graph)):
        cycle = _find_cycle(graph)
        if cycle:
            findings.append(Finding("dep-cycle", f"{label} dependency cycle: {' -> '.join(cycle)}"))
    return findings


def _wave_of(project):
    mapping = {}
    for wave in project.plan.waves:
        for pid in wave.phases:
            mapping.setdefault(pid, wave.number)
    return mapping


def check_waves(project):
    findings = []
    waves = project.plan.waves
    numbers = [w.number for w in waves]
    if sorted(numbers) != list(range(1, len(waves) + 1)):
        findings.append(Finding("wave-numbering", f"waves must be numbered 1..{len(waves)} without gaps or repeats, got {sorted(numbers)}"))

    for wave in waves:
        if not wave.phases:
            findings.append(Finding("wave-empty", f"wave {wave.number} has no phases"))

    seen = Counter(pid for w in waves for pid in w.phases)
    for phase in project.plan.phases:
        if seen[phase.id] == 0:
            findings.append(Finding("wave-coverage", f"phase {phase.id} is not in any wave"))
        elif seen[phase.id] > 1:
            findings.append(Finding("wave-coverage", f"phase {phase.id} is in {seen[phase.id]} waves"))

    wave_of = _wave_of(project)
    by_id = _phase_map(project)
    for phase in project.plan.phases:
        mine = wave_of.get(phase.id)
        if mine is None:
            continue
        for dep in phase.depends_on:
            theirs = wave_of.get(dep)
            if theirs is not None and theirs >= mine:
                findings.append(
                    Finding("wave-order", f"phase {phase.id} (wave {mine}) depends on {dep} (wave {theirs}); a prerequisite must be in an earlier wave")
                )
        spec = project.specs.get(phase.spec)
        for dep in phase.depends_on:
            dep_phase = by_id.get(dep)
            if spec and dep_phase and dep_phase.spec != phase.spec and dep_phase.spec not in spec.depends_on:
                findings.append(
                    Finding("drift-feature-dep", f"phase {phase.id} depends on {dep} (spec {dep_phase.spec}) but spec {spec.id} does not list {dep_phase.spec} in depends_on")
                )

    for spec in project.specs.values():
        mine = [wave_of[p.id] for p in project.plan.phases if p.spec == spec.id and p.id in wave_of]
        for dep_id in spec.depends_on:
            theirs = [wave_of[p.id] for p in project.plan.phases if p.spec == dep_id and p.id in wave_of]
            if mine and theirs and min(mine) <= max(theirs):
                findings.append(
                    Finding("feature-order", f"spec {spec.id} depends on {dep_id}, so all of {dep_id}'s phases (last in wave {max(theirs)}) must finish before {spec.id}'s first phase (wave {min(mine)})")
                )
    return findings


def check_width(project):
    limit = project.plan.header.max_wave_width
    return [
        Finding("wave-width", f"wave {w.number} has {len(w.phases)} phases; max_wave_width is {limit}")
        for w in project.plan.waves
        if len(w.phases) > limit
    ]


def check_step_coverage(project):
    findings = []
    covered = Counter()
    for phase in project.plan.phases:
        for step in phase.steps:
            covered[(phase.spec, step)] += 1
    for spec in project.specs.values():
        for step in spec.steps:
            count = covered[(spec.id, step)]
            if count == 0:
                findings.append(Finding("step-coverage", f"step {step} of spec {spec.id} is not in any phase"))
            elif count > 1:
                findings.append(Finding("step-coverage", f"step {step} of spec {spec.id} is in {count} phases"))
    return findings
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_checks_graph.py' -v`
Expected: `Ran 20 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add scripts/findings.py scripts/checks_graph.py tests/test_checks_graph.py
git commit -m "feat(scripts): graph checks for plan validation"
```

---

### Task 8: Content checks (ownership, criteria, routing)

**Files:**
- Create: `tests/test_checks_content.py`
- Create: `scripts/checks_content.py`

**Interfaces:**
- Consumes: `globs.covers`, `globs.overlaps`, `routing.derive_model`, `routing.MODELS`, `routing.NeedsPlanningError`, `findings.Finding`, `plan_loader.Project`.
- Produces: `check_ownership` (codes `owns-empty`, `owns-glob`, `owns-dir`, `owns-subset`, `owns-overlap`, `owns-integration`), `check_criteria` (`criteria-verify`, `criteria-wave`), `check_routing` (`model-invalid`, `needs-planning`, `score-invalid`, `model-drift`, `risk-not-opus`); constant `VERIFY_PREFIXES = ("test:", "cmd:", "http:", "design-fidelity:")`.

- [ ] **Step 1: Write the failing tests**

```python
import unittest

from helpers import ProjectTestCase
from plan_loader import load_project
import checks_content as c


class ContentCheckTests(ProjectTestCase):
    def run_check(self, check):
        return check(load_project(self.root))

    def test_valid_fixture_has_no_content_findings(self):
        project = load_project(self.root)
        for check in (c.check_ownership, c.check_criteria, c.check_routing):
            self.assertEqual(check(project), [], check.__name__)

    # ownership
    def test_overlapping_ownership_in_one_wave(self):
        self.edit("plan.md", "owns: [src/db/seed/**, tests/db/seed/**]", "owns: [src/db/schema/migrations/**, tests/db/seed/**]")
        findings = self.run_check(c.check_ownership)
        self.assertEqual(self.codes(findings), {"owns-overlap"})
        self.assertIn("P1a", findings[0].message)
        self.assertIn("P1b", findings[0].message)

    def test_overlap_across_different_waves_is_fine(self):
        # P2a (wave 2) and P1a (wave 1) may legitimately touch neighbouring code.
        self.edit("docs/waves/specs/F2.md", "owns: [src/api/**, tests/api/**]", "owns: [src/api/**, tests/api/**, src/db/schema/**]")
        self.edit("plan.md", "owns: [src/api/checkout/**, tests/api/checkout/**]", "owns: [src/db/schema/**, tests/api/checkout/**]")
        self.assertNotIn("owns-overlap", self.codes(self.run_check(c.check_ownership)))

    def test_phase_owns_outside_spec_owns(self):
        self.edit("plan.md", "owns: [src/db/schema/**, tests/db/schema/**]", "owns: [src/other/**, tests/db/schema/**]")
        self.assertIn("owns-subset", self.codes(self.run_check(c.check_ownership)))

    def test_phase_that_owns_nothing(self):
        self.edit("plan.md", "owns: [src/db/seed/**, tests/db/seed/**]", "owns: []")
        self.assertIn("owns-empty", self.codes(self.run_check(c.check_ownership)))

    def test_quoted_brace_glob_is_rejected_because_it_would_match_nothing(self):
        self.edit("plan.md", "owns: [src/db/seed/**, tests/db/seed/**]", 'owns: ["src/db/{seed,fixtures}/**"]')
        self.assertIn("owns-glob", self.codes(self.run_check(c.check_ownership)))

    def test_quoted_brace_glob_in_a_spec_is_rejected(self):
        self.edit("docs/waves/specs/F1.md", "owns: [src/db/**, tests/db/**]", 'owns: ["src/db/{a,b}/**", tests/db/**]')
        self.assertIn("owns-glob", self.codes(self.run_check(c.check_ownership)))

    def test_directory_written_without_glob(self):
        self.edit("plan.md", "owns: [src/db/seed/**, tests/db/seed/**]", "owns: [src/db/seed/, tests/db/seed/**]")
        self.assertIn("owns-dir", self.codes(self.run_check(c.check_ownership)))

    def test_integration_owned_file_inside_a_phase(self):
        self.edit("plan.md", "integration_owned: [package-lock.json]", "integration_owned: [src/db/schema/index.ts]")
        self.assertIn("owns-integration", self.codes(self.run_check(c.check_ownership)))

    # criteria
    def test_criterion_without_verify(self):
        self.edit("docs/waves/specs/F1.md", ', verify: "test:tests/db/seed/seed.test.ts"', "")
        findings = self.run_check(c.check_criteria)
        self.assertIn("criteria-verify", self.codes(findings))
        self.assertIn("F1.AC2", findings[0].message)

    def test_criterion_with_vague_verify(self):
        self.edit("docs/waves/specs/F1.md", 'verify: "test:tests/db/seed/seed.test.ts"', 'verify: "looks good"')
        self.assertIn("criteria-verify", self.codes(self.run_check(c.check_criteria)))

    def test_verify_prefix_with_nothing_after_it(self):
        self.edit("docs/waves/specs/F1.md", 'verify: "test:tests/db/seed/seed.test.ts"', 'verify: "test:"')
        self.assertIn("criteria-verify", self.codes(self.run_check(c.check_criteria)))

    def test_criterion_not_assigned_to_a_wave(self):
        self.edit("plan.md", "criteria: [F3.AC1]", "criteria: []")
        self.assertIn("criteria-wave", self.codes(self.run_check(c.check_criteria)))

    def test_criterion_assigned_twice(self):
        self.edit("plan.md", "criteria: [F2.AC1, F2.AC2]", "criteria: [F2.AC1, F2.AC2, F3.AC1]")
        self.assertIn("criteria-wave", self.codes(self.run_check(c.check_criteria)))

    def test_criterion_gated_before_its_feature_is_built(self):
        self.edit("plan.md", "criteria: [F1.AC1, F1.AC2, F4.AC1]", "criteria: [F1.AC1, F1.AC2, F4.AC1, F2.AC1]")
        self.edit("plan.md", "criteria: [F2.AC1, F2.AC2]", "criteria: [F2.AC2]")
        self.assertIn("criteria-wave", self.codes(self.run_check(c.check_criteria)))

    def test_wave_lists_unknown_criterion(self):
        self.edit("plan.md", "criteria: [F3.AC1]", "criteria: [F3.AC1, F3.AC9]")
        self.assertIn("criteria-wave", self.codes(self.run_check(c.check_criteria)))

    # routing
    def test_model_that_disagrees_with_score(self):
        self.edit("plan.md", "model: haiku\nscore: {scope: 0,", "model: opus\nscore: {scope: 0,")
        self.assertIn("model-drift", self.codes(self.run_check(c.check_routing)))

    def test_override_with_reason_allows_disagreement(self):
        self.edit("plan.md", "model: haiku\nscore: {scope: 0, ambiguity: 0, risk: 0, reasoning: 0}", 'model: sonnet\nscore: {scope: 0, ambiguity: 0, risk: 0, reasoning: 0}\noverride: "touches a flaky legacy script"')
        self.assertNotIn("model-drift", self.codes(self.run_check(c.check_routing)))

    def test_ambiguity_two_returns_to_planning(self):
        self.edit("plan.md", "score: {scope: 1, ambiguity: 0, risk: 1, reasoning: 1}", "score: {scope: 1, ambiguity: 2, risk: 1, reasoning: 1}")
        self.assertIn("needs-planning", self.codes(self.run_check(c.check_routing)))

    def test_risk_flagged_spec_must_be_opus(self):
        self.edit("docs/waves/specs/F1.md", "risk: []", "risk: [data]")
        self.assertIn("risk-not-opus", self.codes(self.run_check(c.check_routing)))

    def test_unknown_model(self):
        self.edit("plan.md", "model: haiku\nscore: {scope: 0,", "model: gpt\nscore: {scope: 0,")
        self.assertIn("model-invalid", self.codes(self.run_check(c.check_routing)))

    def test_bad_score(self):
        self.edit("plan.md", "score: {scope: 1, ambiguity: 0, risk: 1, reasoning: 1}", "score: {scope: 1}")
        self.assertIn("score-invalid", self.codes(self.run_check(c.check_routing)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_checks_content.py' -v`
Expected: error `ModuleNotFoundError: No module named 'checks_content'`.

- [ ] **Step 3: Implement**

```python
"""Content checks: ownership, acceptance criteria, model routing."""
from itertools import combinations

from findings import Finding
from globs import covers, overlaps
from routing import MODELS, NeedsPlanningError, derive_model

VERIFY_PREFIXES = ("test:", "cmd:", "http:", "design-fidelity:")


def check_ownership(project):
    findings = []
    for spec in project.specs.values():
        for glob in spec.owns:
            if "{" in glob or "}" in glob:
                findings.append(Finding("owns-glob", f"spec {spec.id} owns {glob!r}; braces are not supported, list each path separately"))
    phases = {p.id: p for p in project.plan.phases}
    for phase in project.plan.phases:
        spec = project.specs.get(phase.spec)
        if not phase.owns:
            findings.append(Finding("owns-empty", f"phase {phase.id} owns no paths; every phase must own what it writes"))
        for glob in phase.owns:
            if "{" in glob or "}" in glob:
                findings.append(Finding("owns-glob", f"phase {phase.id} owns {glob!r}; braces are not supported, list each path separately"))
                continue
            if not glob or glob.endswith("/"):
                findings.append(Finding("owns-dir", f"phase {phase.id} owns {glob!r}; write directories as 'dir/**'"))
                continue
            if spec and not any(covers(outer, glob) for outer in spec.owns):
                findings.append(Finding("owns-subset", f"phase {phase.id} owns {glob}, which is outside spec {spec.id}'s owns {spec.owns}"))
    for wave in project.plan.waves:
        members = [phases[pid] for pid in wave.phases if pid in phases]
        for a, b in combinations(members, 2):
            for ga in a.owns:
                for gb in b.owns:
                    if overlaps(ga, gb):
                        findings.append(Finding("owns-overlap", f"wave {wave.number}: {a.id} ({ga}) and {b.id} ({gb}) may write the same files"))
        for shared in wave.integration_owned:
            for member in members:
                if any(overlaps(shared, g) for g in member.owns):
                    findings.append(Finding("owns-integration", f"wave {wave.number}: integration-owned {shared} overlaps {member.id}'s owns; workers must not touch it"))
    return findings


def check_criteria(project):
    findings = []
    wave_of = {}
    for wave in project.plan.waves:
        for pid in wave.phases:
            wave_of.setdefault(pid, wave.number)
    known = {}
    for spec in project.specs.values():
        for criterion in spec.criteria:
            known[criterion.id] = spec
            verify = criterion.verify.strip()
            prefix = next((p for p in VERIFY_PREFIXES if verify.startswith(p)), None)
            if prefix is None or not verify[len(prefix) :].strip():
                findings.append(Finding("criteria-verify", f"{criterion.id} needs verify: starting with one of {VERIFY_PREFIXES} followed by something concrete; got {criterion.verify!r}"))

    listed = {}
    for wave in project.plan.waves:
        for cid in wave.criteria:
            listed.setdefault(cid, []).append(wave.number)
    for cid, spec in known.items():
        waves = listed.get(cid, [])
        if not waves:
            findings.append(Finding("criteria-wave", f"{cid} is not assigned to any wave's criteria"))
            continue
        if len(waves) > 1:
            findings.append(Finding("criteria-wave", f"{cid} is assigned to several waves: {waves}"))
        feature_waves = [wave_of[p.id] for p in project.plan.phases if p.spec == spec.id and p.id in wave_of]
        if feature_waves and waves[0] < max(feature_waves):
            findings.append(Finding("criteria-wave", f"{cid} is gated in wave {waves[0]} but spec {spec.id} has phases through wave {max(feature_waves)}"))
    for cid in listed:
        if cid not in known:
            findings.append(Finding("criteria-wave", f"wave criteria list unknown criterion {cid}"))
    return findings


def check_routing(project):
    findings = []
    for phase in project.plan.phases:
        if phase.model not in MODELS:
            findings.append(Finding("model-invalid", f"phase {phase.id} model {phase.model!r} must be one of {MODELS}"))
            continue
        try:
            derived = derive_model(phase.score)
        except NeedsPlanningError as exc:
            findings.append(Finding("needs-planning", f"phase {phase.id}: {exc}"))
            continue
        except ValueError as exc:
            findings.append(Finding("score-invalid", f"phase {phase.id}: {exc}"))
            continue
        if phase.model != derived and not phase.override:
            findings.append(Finding("model-drift", f"phase {phase.id} is {phase.model} but its score derives {derived}; fix the score or add 'override: \"reason\"'"))
        spec = project.specs.get(phase.spec)
        if spec and spec.risk and phase.model != "opus":
            findings.append(Finding("risk-not-opus", f"phase {phase.id} is {phase.model} but spec {spec.id} is risk-flagged {spec.risk}; risk-flagged work runs on opus"))
    return findings
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_checks_content.py' -v`
Expected: `Ran 22 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add scripts/checks_content.py tests/test_checks_content.py
git commit -m "feat(scripts): ownership, criteria and routing checks"
```

---

### Task 9: `validate_plan.py` CLI

**Files:**
- Create: `tests/test_validate_plan.py`
- Create: `scripts/validate_plan.py`

**Interfaces:**
- Consumes: every `check_*` function, `plan_loader.load_project`, `findings.Finding`.
- Produces: `run(root) -> list[Finding]` (a parse problem becomes a single `format` finding); CLI `python3 validate_plan.py [--root DIR] [--json]`, exit 0 and `OK: plan is valid`, or exit 1 with one `ERROR [code] message` line per finding and `FAILED: N error(s)`.

- [ ] **Step 1: Write the failing tests**

````python
import io
import json
import subprocess
import sys
import unittest

import helpers
from helpers import ProjectTestCase, SCRIPTS
import validate_plan


class ValidatePlanTests(ProjectTestCase):
    def test_valid_fixture_passes(self):
        self.assertEqual(validate_plan.run(self.root), [])

    def test_format_error_is_reported_as_a_single_finding(self):
        self.edit("plan.md", "```yaml header", "```yaml heading")
        findings = validate_plan.run(self.root)
        self.assertEqual([f.code for f in findings], ["format"])

    def test_unquoted_brace_glob_is_a_format_error(self):
        self.edit("plan.md", "owns: [src/db/seed/**, tests/db/seed/**]", "owns: [src/db/{seed,fixtures}/**]")
        self.assertEqual([f.code for f in validate_plan.run(self.root)], ["format"])

    def test_findings_from_several_checks_are_combined(self):
        self.edit("plan.md", "max_wave_width: 4", "max_wave_width: 2")
        self.edit("plan.md", "model: haiku\nscore: {scope: 0,", "model: opus\nscore: {scope: 0,")
        self.assertEqual(self.codes(validate_plan.run(self.root)), {"wave-width", "model-drift"})

    def test_main_returns_zero_and_prints_ok(self):
        out = io.StringIO()
        code = validate_plan.main(["--root", str(self.root)], stdout=out)
        self.assertEqual(code, 0)
        self.assertIn("OK: plan is valid", out.getvalue())

    def test_main_returns_one_and_lists_errors(self):
        self.edit("plan.md", "max_wave_width: 4", "max_wave_width: 2")
        out = io.StringIO()
        code = validate_plan.main(["--root", str(self.root)], stdout=out)
        self.assertEqual(code, 1)
        self.assertIn("ERROR [wave-width]", out.getvalue())
        self.assertIn("FAILED: 1 error(s)", out.getvalue())

    def test_json_output(self):
        self.edit("plan.md", "max_wave_width: 4", "max_wave_width: 2")
        out = io.StringIO()
        validate_plan.main(["--root", str(self.root), "--json"], stdout=out)
        data = json.loads(out.getvalue())
        self.assertEqual(data[0]["code"], "wave-width")

    def test_runs_as_a_script_from_any_directory(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_plan.py"), "--root", str(self.root)],
            capture_output=True,
            text=True,
            cwd="/",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
````

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_validate_plan.py' -v`
Expected: error `ModuleNotFoundError: No module named 'validate_plan'`.

- [ ] **Step 3: Implement**

```python
"""Validate a wave-planning project.

Usage: python3 validate_plan.py [--root DIR] [--json]
Exit 0 when the plan is valid, 1 when there are findings or the files cannot be parsed.
"""
import argparse
import json
import sys
from pathlib import Path

from checks_content import check_criteria, check_ownership, check_routing
from checks_graph import check_cycles, check_refs, check_step_coverage, check_waves, check_width
from findings import Finding
from plan_loader import PlanFormatError, load_project

CHECKS = (
    check_refs,
    check_cycles,
    check_waves,
    check_width,
    check_step_coverage,
    check_ownership,
    check_criteria,
    check_routing,
)


def run(root):
    """Return a list of Findings for the project at `root`."""
    try:
        project = load_project(root)
    except PlanFormatError as exc:
        return [Finding("format", str(exc))]
    findings = []
    for check in CHECKS:
        findings.extend(check(project))
    return findings


def main(argv=None, stdout=None):
    out = stdout or sys.stdout
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root containing plan.md (default: .)")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)
    findings = run(Path(args.root))
    if args.json:
        print(json.dumps([{"code": f.code, "message": f.message} for f in findings], indent=2), file=out)
    else:
        for finding in findings:
            print(finding, file=out)
        if findings:
            print(f"FAILED: {len(findings)} error(s)", file=out)
        else:
            print("OK: plan is valid", file=out)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_validate_plan.py' -v`
Expected: `Ran 8 tests` … `OK`.

- [ ] **Step 5: Run it against the fixture as a user would**

Run: `python3 scripts/validate_plan.py --root tests/fixtures/valid`
Expected output: `OK: plan is valid` and exit code 0.

- [ ] **Step 6: Run the whole suite**

Run: `python3 -m unittest discover -s tests`
Expected: all tests pass (`OK`), none failing.

- [ ] **Step 7: Commit**

```bash
git add scripts/validate_plan.py tests/test_validate_plan.py
git commit -m "feat(scripts): validate_plan CLI"
```

---

### Task 10: Spec and plan templates

**Files:**
- Create: `templates/spec.md`
- Create: `templates/plan.md`
- Create: `tests/test_templates.py`

**Interfaces:**
- Consumes: `plan_loader.parse_spec`, `plan_loader.parse_plan`.
- Produces: the two annotated templates `wave-plan` fills in. They must stay parseable by the loader (placeholders such as `F<N>` and `<dir>/**` are valid plain scalars).

- [ ] **Step 1: Write the failing test**

```python
import unittest

import helpers
from plan_loader import parse_plan, parse_spec


class TemplateTests(unittest.TestCase):
    def test_spec_template_parses(self):
        spec = parse_spec(helpers.REPO / "templates" / "spec.md")
        self.assertEqual(spec.id, "F<N>")
        self.assertEqual(spec.criteria[0].id, "F<N>.AC1")
        self.assertTrue(spec.criteria[0].verify.startswith("test:"))

    def test_plan_template_parses(self):
        plan = parse_plan(helpers.REPO / "templates" / "plan.md")
        self.assertEqual([p.id for p in plan.phases], ["P1a"])
        self.assertEqual([w.number for w in plan.waves], [1])
        self.assertEqual(plan.header.max_wave_width, 8)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify failure**

Run: `python3 -m unittest discover -s tests -p 'test_templates.py' -v`
Expected: both tests error (the template files do not exist: `FileNotFoundError`).

- [ ] **Step 3: Write the templates**

`templates/spec.md`:

````markdown
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
````

`templates/plan.md`:

````markdown
# Plan: <Project name>

<!-- Generated by wave-plan from docs/waves/specs/*.md. The specs own the "what" (depends_on,
     owns, acceptance criteria); this file owns the "when and how". Do not restate spec fields
     freehand: edit the spec and regenerate. Machine-readable data lives only in the fenced
     blocks below (flow-style YAML, one line per field); everything else is for humans. -->

## Header

```yaml header
design: none
bootstrap: <command run in every fresh worktree, e.g. npm ci>
gates: {format: "<cmd>", lint: "<cmd>", typecheck: "<cmd>", unit: "<cmd>"}
max_wave_width: 8
```

## Feature index

| Feature | Spec |
|---|---|
| F1 <name> | docs/waves/specs/F1.md |

## Phases

<!-- model is haiku | sonnet | opus. It must equal the model derived from score by
     `python3 scripts/routing.py` unless `override: "reason"` is present. -->

```yaml phase
id: P1a
spec: F1
steps: [F1.1]
owns: [<dir>/**]
depends_on: []
model: haiku
score: {scope: 0, ambiguity: 0, risk: 0, reasoning: 0}
rationale: "<why this tier>"
```

## Four graphs

### Dependency graph

| Phase | Depends on |
|---|---|
| P1a | none |

### Ownership graph

| Phase | Owns |
|---|---|
| P1a | <dir>/** |

### Context graph

| Phase | Reads |
|---|---|
| P1a | <files, design screens> |

### Validation graph

| Phase | Shallow gate | Wave gate criteria |
|---|---|---|
| P1a | format, lint, typecheck, unit | F1.AC1 |

## Waves

```yaml wave
wave: 1
phases: [P1a]
integration_owned: []
criteria: [F1.AC1]
integration_checks: []
```

## Execution protocol

Executed by `/wave-planning:wave-execute`. See that skill for the worktree, dispatch, gate and merge procedure.

## Status

```yaml status
base_branch: none
integration_branch: wave/integration
integration_head: none
W1: pending
P1a: pending
```
````

- [ ] **Step 4: Run to verify pass**

Run: `python3 -m unittest discover -s tests -p 'test_templates.py' -v`
Expected: `Ran 2 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add templates tests/test_templates.py
git commit -m "feat: spec and plan templates"
```

---

### Task 11: Plugin structure tests and the two agents

**Files:**
- Create: `tests/test_plugin_structure.py`
- Create: `agents/wave-worker.md`
- Create: `agents/wave-validator.md`

**Interfaces:**
- Consumes: `miniyaml.parse_document` (agent and skill frontmatter are single-line `key: value`).
- Produces: structure tests that guard the plugin's own invariants: agents are leaf nodes (explicit `tools` allowlist without `Agent`), the validator is read-only, every skill's `name` equals its directory and its `description` starts with "Use when" (≤ 1,536 chars), `SKILL.md` ≤ 500 lines, every `references/…md` mentioned exists, and the manifest and marketplace agree. Agent names (as dispatched by the orchestrator): `wave-planning:wave-worker`, `wave-planning:wave-validator`.

- [ ] **Step 1: Write the structure tests**

```python
"""Structural invariants of the plugin itself (not of a user's wave plan)."""
import json
import re
import unittest

import helpers
from miniyaml import parse_document

REPO = helpers.REPO
FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*$", re.S | re.M)
REFERENCE = re.compile(r"\breferences/[A-Za-z0-9_.\-]+\.md\b")


def frontmatter(path):
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        raise AssertionError(f"{path}: no frontmatter")
    return parse_document(match.group(1))


def tool_list(front, key="tools"):
    return [t.strip() for t in str(front.get(key, "")).split(",") if t.strip()]


class AgentTests(unittest.TestCase):
    def agents(self):
        return sorted((REPO / "agents").glob("*.md"))

    def test_agents_are_leaf_nodes(self):
        for path in self.agents():
            tools = tool_list(frontmatter(path))
            self.assertTrue(tools, f"{path.name} must declare an explicit tools allowlist")
            self.assertNotIn("Agent", tools, f"{path.name} must not be able to spawn subagents")

    def test_validator_is_read_only(self):
        path = REPO / "agents" / "wave-validator.md"
        if not path.exists():
            self.skipTest("wave-validator not created yet")
        tools = tool_list(frontmatter(path))
        for forbidden in ("Edit", "Write", "NotebookEdit"):
            self.assertNotIn(forbidden, tools)

    def test_agents_have_name_matching_file_and_description(self):
        for path in self.agents():
            front = frontmatter(path)
            self.assertEqual(front.get("name"), path.stem)
            self.assertTrue(front.get("description"), f"{path.name} needs a description")


class SkillTests(unittest.TestCase):
    def skills(self):
        return sorted((REPO / "skills").glob("*/SKILL.md"))

    def test_name_matches_directory_and_description_fits(self):
        for path in self.skills():
            front = frontmatter(path)
            self.assertEqual(front.get("name"), path.parent.name)
            description = str(front.get("description", ""))
            self.assertTrue(description.startswith("Use when"), f"{path}: description should start with 'Use when'")
            self.assertLessEqual(len(description), 1536)

    def test_skill_body_is_lean(self):
        for path in self.skills():
            lines = path.read_text(encoding="utf-8").count("\n")
            self.assertLessEqual(lines, 500, f"{path} is {lines} lines; move detail into references/")

    def test_referenced_files_exist(self):
        for path in self.skills():
            for ref in set(REFERENCE.findall(path.read_text(encoding="utf-8"))):
                self.assertTrue((path.parent / ref).is_file(), f"{path}: references missing file {ref}")


class ManifestTests(unittest.TestCase):
    def test_manifest_and_marketplace_agree(self):
        plugin_path = REPO / ".claude-plugin" / "plugin.json"
        market_path = REPO / ".claude-plugin" / "marketplace.json"
        if not (plugin_path.exists() and market_path.exists()):
            self.skipTest("manifests not created yet")
        plugin = json.loads(plugin_path.read_text())
        market = json.loads(market_path.read_text())
        self.assertEqual(plugin["name"], "wave-planning")
        self.assertIn("version", plugin)
        entry_names = [p["name"] for p in market["plugins"]]
        self.assertEqual(entry_names, [plugin["name"]])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run (passes vacuously, which is the point of this step)**

Run: `python3 -m unittest discover -s tests -p 'test_plugin_structure.py' -v`
Expected: `OK (skipped=1)` or similar; with no agents and no skills yet nothing can violate the invariants. The tests become load-bearing as the next steps add files.

- [ ] **Step 3: Write `agents/wave-worker.md`**

````markdown
---
name: wave-worker
description: Implements exactly one wave-planning phase inside a git worktree it is given. Dispatched only by the wave-execute orchestrator with a self-contained brief; do not invoke it directly.
model: sonnet
tools: Read, Edit, Write, Bash, Grep, Glob
maxTurns: 80
---

You implement ONE phase of a wave plan. Your brief names the phase, its spec, the worktree you must work in, the paths you own, and the gate commands to run. You have no other context. Do not go looking for more than the brief names.

## Rules (non-negotiable)

1. Work only inside the worktree path in your brief. Use absolute paths under it for every file operation and `git -C <worktree>` for every git command. Never touch the main checkout or any other worktree.
2. Write only to paths matched by your `owns` globs. If the work needs a file you do not own, or an integration-owned file such as a lockfile or route registry, STOP and report BLOCKED with the path and the reason. Do not edit it.
3. Never merge, rebase, switch branches, push, or delete branches. Commit only on the phase branch you were given.
4. Never spawn subagents or delegate. You are a leaf node.
5. Implement only what your steps and the frozen design describe. If the spec is ambiguous or contradicts the code you find, report BLOCKED with the question. Do not guess at anything that changes behavior.
6. Never weaken, skip, or delete a test to make a gate pass.

## Procedure

1. Read your spec excerpt and the read-only context paths from the brief.
2. For testable behavior, write the failing test first, then the implementation.
3. Run the shallow-gate commands from the brief inside the worktree, in this order: format, lint, typecheck, unit. Fix failures within your owned paths. If a gate fails for a reason outside your paths, report it; do not fix it.
4. Commit on the phase branch with the message `feat(<phase-id>): <summary>`. One or a few commits is fine.
5. Before reporting, run `git -C <worktree> status --porcelain` (it must print nothing) and `git -C <worktree> diff --name-only <base>...HEAD` (every path must match your owns globs).

## Report

Your final message must be exactly this shape:

```
STATUS: DONE | DONE_WITH_CONCERNS | BLOCKED
PHASE: <phase id>
COMMIT: <sha of HEAD in the worktree, or none>
GATES: format=<pass|fail|n/a> lint=<...> typecheck=<...> unit=<...>
FILES: <changed paths, comma separated>
CONCERNS: <anything surprising or any deviation from the spec; above all any dependency, file or assumption the plan did not mention; or "none">
BLOCKER: <what you need, only when STATUS is BLOCKED>
```

If a gate failed, add the last 30 lines of its output after the report.
````

- [ ] **Step 4: Write `agents/wave-validator.md`**

````markdown
---
name: wave-validator
description: Runs a wave's functional gate against the merged integration branch and reports evidence per acceptance criterion. Read-only; dispatched only by the wave-execute orchestrator.
model: sonnet
tools: Read, Grep, Glob, Bash
maxTurns: 60
---

You validate ONE wave. The integration branch is checked out in the main working tree. Your brief lists the wave's acceptance criteria (each with a verification method), its integration checks, the gate commands, and the design snapshot path if the wave has UI.

You verify; you never repair. If something fails, report it with evidence and stop. The orchestrator decides what happens next.

## Rules (non-negotiable)

1. Do not modify, create, or delete any file in the repository. Run commands only to observe. Do not run `git checkout`, `git commit`, `git merge`, `git reset`, `git stash`, or any command that changes the repository.
2. Never spawn subagents.
3. Never report PASS for something you did not actually run and observe. If you cannot run a check, report UNVERIFIED with the reason.
4. Before you start and after you finish, run `git status --porcelain`. Both outputs must be empty; if the second is not, say so loudly in CONCERNS.

## How to check each verification method

- `test:<path or id>`: run the unit-test command from the brief scoped to that path or id. PASS only if it passes and at least one test actually ran.
- `cmd:<command>`: run exactly that command. PASS only on exit code 0.
- `http:<request and expectation>`: use the run hint in the brief to start the app, make the request with `curl`, compare the response to the expectation, then stop the server you started. If the brief has no run hint, report UNVERIFIED.
- `design-fidelity:<screen-id>`: compare the implemented screen to that screen in the design snapshot (copy, structure, hierarchy, spacing and colour tokens). If browser tools are available, render the screen and compare visually. If not, compare structure and tokens statically and report UNVERIFIED with `visual not checked`.

Then run every integration check in the brief the same way.

## Report

Your final message must be exactly this shape:

```
WAVE: <number>
RESULT: PASS | FAIL | INCOMPLETE
| Criterion | Method | Result | Evidence |
|---|---|---|---|
| <id> | <verify string> | PASS/FAIL/UNVERIFIED | <command, exit code, the key output lines> |
INTEGRATION CHECKS: <each check with PASS/FAIL/UNVERIFIED and evidence>
CONCERNS: <anything surprising, flaky, or outside the criteria; or "none">
```

RESULT is PASS only if every criterion and integration check is PASS. Any FAIL makes it FAIL. Otherwise, if anything is UNVERIFIED, it is INCOMPLETE.
````

- [ ] **Step 5: Run the structure tests (now load-bearing)**

Run: `python3 -m unittest discover -s tests -p 'test_plugin_structure.py' -v`
Expected: `OK` with the manifest test running (Task 1 created the manifests) and the three agent tests running over two agent files; no failures.

- [ ] **Step 6: Validate the plugin**

Run: `claude plugin validate --strict .`
Expected: `✔ Validation passed`. If the validator flags an agent frontmatter field, fix exactly what it names.

- [ ] **Step 7: Commit**

```bash
git add tests/test_plugin_structure.py agents
git commit -m "feat: wave-worker and wave-validator agents; plugin structure tests"
```


### Task 12: `model-routing` skill

**Files:**
- Create: `skills/model-routing/SKILL.md`

**Interfaces:**
- Consumes: `scripts/routing.py` (CLI), invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/routing.py" --scope N --ambiguity N --risk N --reasoning N`.
- Produces: the rubric that `wave-plan` and `wave-execute` rely on. `user-invocable: false`: it loads when Claude decides it applies, not from the `/` menu.

The skill's behavior is exercised by the `model-routing-assigns-tiers` eval (Task 16). Its numbers are exercised now, in Step 3.

- [ ] **Step 1: Write the skill**

`skills/model-routing/SKILL.md`:

````markdown
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
- If the environment sets `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1`, every subagent runs on one model and routing has no effect. Warn the user before executing.

## Sanity examples

| Phase | Score (scope, ambiguity, risk, reasoning) | Tier |
|---|---|---|
| Rename a config key across 3 files | 0, 0, 0, 0 | haiku |
| Standard CRUD settings page from a finished design | 1, 1, 0, 1 | sonnet |
| Payment capture endpoint | 1, 1, 2, 1 | opus (risk) |
| Query planner with caching, nothing specified yet | 2, 2, 1, 2 | planning first (ambiguity) |
````

- [ ] **Step 2: Run the structure tests**

Run: `python3 -m unittest discover -s tests -p 'test_plugin_structure.py' -v`
Expected: `OK` (the skill's name equals its directory, its description starts with "Use when", it is under 500 lines).

- [ ] **Step 3: Check the skill's example table against the real script**

Run each of these and compare with the skill's "Sanity examples" table:

```bash
python3 scripts/routing.py --scope 0 --ambiguity 0 --risk 0 --reasoning 0   # haiku
python3 scripts/routing.py --scope 1 --ambiguity 1 --risk 0 --reasoning 1   # sonnet
python3 scripts/routing.py --scope 1 --ambiguity 1 --risk 2 --reasoning 1   # opus
python3 scripts/routing.py --scope 2 --ambiguity 2 --risk 1 --reasoning 2; echo "exit=$?"   # NEEDS-PLANNING on stderr, exit=2
```

Expected: `haiku`, `sonnet`, `opus`, then a `NEEDS-PLANNING: …` line and `exit=2`. If any differs, fix the skill's table (the script is the authority).

- [ ] **Step 4: Validate and commit**

Run: `claude plugin validate --strict .` → `✔ Validation passed`.

```bash
git add skills/model-routing
git commit -m "feat: model-routing skill"
```

---

### Task 13: `wave-design` skill

**Files:**
- Create: `skills/wave-design/SKILL.md`
- Create: `skills/wave-design/references/claude-design-flow.md`
- Create: `skills/wave-design/references/html-fallback.md`

**Interfaces:**
- Consumes: the Artifact tool (`quickstart` with `intent: "design"`, publish with `type_url`, `read` with `page: true`); approved specs in `docs/waves/specs/`.
- Produces: `docs/waves/design/snapshot.html` (contains `<section id="screen-…">` per screen and `<section id="tokens">`), `docs/waves/design/DESIGN.md`, `reads` entries in specs of the form `docs/waves/design/snapshot.html#screen-<name>`, and the plan header value `design: docs/waves/design/snapshot.html` (or `design: none` when there is no UI, decided by `wave-plan`).

Whether a Claude Design artifact can be exported as a usable snapshot is not verified yet. The skill is written so that failure is explicit and has a fallback; Task 17's dry run checks it for real.

- [ ] **Step 1: Write the skill and its references**

`skills/wave-design/SKILL.md`:

```markdown
---
name: wave-design
description: Use when an approved wave-plan scope includes a user interface and a mockup must be designed, approved, and frozen before the work is decomposed into phases.
---

# Wave Design

The design stage of wave planning. It turns the approved scope into a mockup the user signs off on. After sign-off the design is **frozen**: execution builds exactly that and nothing else, so UI phases can run in parallel without arguing about what the screens look like.

You are normally invoked by `wave-plan`. You can also be invoked directly to redo the design before a plan is approved.

## Preconditions

- Feature specs exist under `docs/waves/specs/` and the user has approved them. If not, stop and return to `wave-plan`.
- At least one feature has UI. Backend-only or CLI-only projects skip this skill; `wave-plan` records `design: none`.

## Process

1. **Gather direction.** Ask one question at a time: who the users are, the tone or brand, any references or an existing design system, target platform and breakpoints. Check the repository for existing styles, tokens, or components first and reuse them.
2. **List the screens.** Give every screen an id of the form `screen-<name>` (for example `screen-cart`) and map each to the feature spec it belongs to. Always add a `tokens` artboard for colour, spacing and type. Show the user this list and get a yes before you draw anything.
3. **Build the mockup.** Prefer Claude Design (see [references/claude-design-flow.md](references/claude-design-flow.md)). If the Artifact tool is not available, build the HTML fallback (see [references/html-fallback.md](references/html-fallback.md)). One labelled artboard or section per screen id.
4. **Iterate.** Show the user the result and revise until they say it is approved. Approval must be explicit; silence is not approval.
5. **Freeze.** On approval:
   - Save a snapshot to `docs/waves/design/snapshot.html` (the procedure and fallback are in the Claude Design reference). Workers read the snapshot, so it must contain every screen id and `tokens`.
   - Write `docs/waves/design/DESIGN.md`: the Claude Design URL and approval date (or "HTML fallback"), a table of screen id → feature id, a short token summary, and the line `FROZEN: changes after approval require replanning.`
   - Add each screen a spec uses to that spec's `reads` list as `docs/waves/design/snapshot.html#screen-<name>`.
   - Return control to `wave-plan` with `design: docs/waves/design/snapshot.html` for the plan header.

## Rules

- Never edit the design after approval. If the user wants a change later, including mid-execution, stop and send them back to `wave-plan` to replan; do not patch it silently.
- Design only what the approved specs need. No extra screens.
- Do not write application code. This stage produces design artifacts and documentation only.
```

`skills/wave-design/references/claude-design-flow.md`:

````markdown
# Building and freezing the design in Claude Design

Claude Design is the Artifact tool's "Design" type: a canvas of live artboards. The type's URL is per account, so never hardcode one. Discover it at run time.

## 1. Create the design artifact

1. Call the Artifact tool with `action: "quickstart"` and `intent: "design"`. The result lists the Design type and its `type_url`. If it lists no Design type, use the HTML fallback instead.
2. Publish to start the artifact: Artifact with `type_url` set to the one returned, a short `title` (the project name plus " design"), no files, and `auto_open: "after_first_write"`.
3. The create result carries the type's own instructions and how to fill it. Follow them. Do not assume them from memory; they are the authority on how artboards are laid out.
4. Draw one artboard per approved screen and one for `tokens`. Label each artboard with its id exactly (`screen-cart`, `tokens`). Updating the artifact later means publishing again to the same `url`.

Tell the user the artifact link after the first write so they can open it and review.

## 2. Snapshot at freeze time

Workers cannot rely on a live link, so on approval save a snapshot:

1. Read the artifact with the Artifact tool: `action: "read"`, the artifact `url`, and `page: true` so the rendered page is returned. The result names the local file where the page was saved.
2. Copy that file to `docs/waves/design/snapshot.html`.
3. Check the snapshot: it must be a self-contained HTML file, and it must contain every screen id and `tokens` (search the file for each id). Report to the user which ids were found.
4. If the read returns something unusable (no screen ids, or only a shell page), do not pretend it worked. Tell the user plainly. Offer two ways forward: they export the design themselves and put it at `docs/waves/design/snapshot.html`, or you rebuild the approved design as the HTML fallback with the same screen ids. Do not continue to decomposition until a usable snapshot exists.

## 3. Record the freeze

`docs/waves/design/DESIGN.md` is the human-readable freeze record:

```markdown
# Design (FROZEN)

- Source: <Claude Design URL, or "HTML fallback">
- Approved: <YYYY-MM-DD>
- Snapshot: docs/waves/design/snapshot.html

| Screen id | Feature |
|---|---|
| screen-cart | F3 |

## Tokens
<colours, spacing scale, type scale in a few lines>

FROZEN: changes after approval require replanning.
```
````

`skills/wave-design/references/html-fallback.md`:

````markdown
# HTML fallback design

Use this when the Artifact tool or the Design type is unavailable, or when a Claude Design snapshot could not be exported. It produces the same thing the rest of the pipeline needs: one file, `docs/waves/design/snapshot.html`, with a section per screen id.

## Rules

- One self-contained file. Inline CSS, no external fonts, scripts, images or CDNs, so it renders offline and workers can read it as text.
- One `<section>` per screen, with `id` equal to the screen id (`screen-cart`), plus one `<section id="tokens">`.
- Tokens are CSS custom properties on `:root`, and every screen uses them. Do not hardcode colours or spacing inside screens.
- Static markup is enough. Show realistic copy and the states that matter (empty, filled, error) as separate screens only when the specs need them.
- Keep it small enough to read in one pass. This is a reference for building, not a prototype.

## Skeleton

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Design snapshot</title>
<style>
  :root {
    --color-bg: #ffffff;
    --color-text: #111827;
    --color-accent: #2563eb;
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 16px;
    --font-body: system-ui, sans-serif;
    --font-size-base: 16px;
  }
  body { font-family: var(--font-body); color: var(--color-text); background: var(--color-bg); }
  section { padding: var(--space-3); border-bottom: 1px solid #e5e7eb; }
</style>
</head>
<body>
<section id="tokens">
  <h2>Tokens</h2>
  <p>Colours, spacing and type shown as swatches and samples.</p>
</section>
<section id="screen-cart">
  <h2>Cart</h2>
  <p>Markup for the cart screen using only the tokens above.</p>
</section>
</body>
</html>
```

After the user approves, write `docs/waves/design/DESIGN.md` exactly as in the Claude Design reference, with `Source: HTML fallback`.
````

- [ ] **Step 2: Run the structure tests**

Run: `python3 -m unittest discover -s tests -p 'test_plugin_structure.py' -v`
Expected: `OK`, including `test_referenced_files_exist` (both `references/…md` files named in `SKILL.md` exist).

- [ ] **Step 3: Validate and commit**

Run: `claude plugin validate --strict .` → `✔ Validation passed`.

```bash
git add skills/wave-design
git commit -m "feat: wave-design skill (Claude Design mockup, snapshot, freeze)"
```

---

### Task 14: `wave-plan` skill

**Files:**
- Create: `skills/wave-plan/SKILL.md`
- Create: `skills/wave-plan/references/spec-interview.md`
- Create: `skills/wave-plan/references/decomposition.md`
- Create: `skills/wave-plan/references/four-graphs.md`

**Interfaces:**
- Consumes: `templates/spec.md`, `templates/plan.md`, `scripts/validate_plan.py`, the `wave-design` and `model-routing` skills.
- Produces: `docs/waves/specs/<id>.md` and `plan.md` that pass `validate_plan.py`, an approved plan, and the instruction to run `/wave-planning:wave-execute`.

- [ ] **Step 1: Write the skill and its references**

`skills/wave-plan/SKILL.md`:

````markdown
---
name: wave-plan
description: Use when planning a software project or large change to be built in parallel by AI agents using wave planning. Scopes features, writes one spec per feature, designs the UI if there is one, then decomposes the work into dependency-ordered waves with gates and model assignments, all before any code is written.
argument-hint: "[project idea or path to a brief]"
---

# Wave Plan

Wave planning groups work by **dependency**, not by time. Steps roll up into phases. Phases are scheduled into **waves**: a wave is the largest set of phases that can run at the same time because none of them waits on another and none of them writes the same files. Waves run one after another. Phases inside a wave run in parallel.

This skill is the whole planning stage. It ends with an approved `plan.md`; building starts only when the user runs `/wave-planning:wave-execute`.

<HARD-GATE>
Do not write product code, scaffold the project, or install anything during planning. The only files you may create or edit are `plan.md` and files under `docs/waves/`. Do not start a later stage until the user has approved the earlier one. A plan the user has not approved is a draft.
</HARD-GATE>

The plan is only as good as its dependency map. The user owns scoping the work and catching what the map misses; your job is to make hidden dependencies visible, not to hide them behind a tidy table.

## Stage 1: Scope

Follow [references/spec-interview.md](references/spec-interview.md).

1. If the request points at an existing repository, read its structure first. Greenfield and existing code are planned differently.
2. Ask one question at a time: purpose and users, what success looks like, constraints (stack, hosting, deadlines).
3. Propose the **feature list** (a name and one line each) and get the user's approval before writing any spec.
4. For each feature, write `docs/waves/specs/<id>.md` from `${CLAUDE_PLUGIN_ROOT}/templates/spec.md`. Every acceptance criterion needs a verification method (`test:`, `cmd:`, `http:` or `design-fidelity:`). A criterion you cannot verify gets rewritten into one you can, or dropped.
5. Show the user the specs and get approval.

## Stage 2: Design (only if any feature has UI)

Invoke the `wave-design` skill and wait for the frozen design. If no feature has UI, write `design: none` in the plan header. Do not decompose until the design is approved and frozen.

## Stage 3: Decompose

Follow [references/decomposition.md](references/decomposition.md) and [references/four-graphs.md](references/four-graphs.md).

1. Turn each spec's steps into **phases**: tightly coupled steps become one phase, and each phase has its own narrow `owns` globs.
2. Add real dependency edges between phases.
3. Assign phases to **waves** (earliest possible wave, then resolve ownership conflicts and width).
4. Mark **integration-owned** files: files several phases legitimately need, which the orchestrator edits at merge time.
5. Define the **gates**: detect and confirm the shallow-gate commands and the bootstrap command; assign each acceptance criterion to the wave that gates it; add cross-phase integration checks.
6. Score every phase with the `model-routing` skill and record `model`, `score` and `rationale`.
7. Write `plan.md` at the project root from `${CLAUDE_PLUGIN_ROOT}/templates/plan.md`.
8. Validate:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_plan.py" --root .
   ```

   Fix every `ERROR` and re-run until it prints `OK: plan is valid`. Never present an invalid plan.
9. Report the plan's shape: number of waves, widest wave, the critical path (the longest dependency chain), and the model mix.

## Approval

Before asking for approval, ask the user directly: **"What does this plan assume that isn't written down?"** Shared config, environment variables, migration order, feature flags, generated code, CI. Add anything they name and revalidate.

Then show the summary and ask for explicit approval. When they approve, tell them to run `/wave-planning:wave-execute`.

Spec fields (`depends_on`, `owns`, acceptance criteria) are canonical. To change a dependency, edit the spec and regenerate the plan; never hand-edit the plan's copy of a spec field.
````

`skills/wave-plan/references/spec-interview.md`:

```markdown
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
```

`skills/wave-plan/references/decomposition.md`:

```markdown
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
```

`skills/wave-plan/references/four-graphs.md`:

```markdown
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
```

- [ ] **Step 2: Run the structure tests**

Run: `python3 -m unittest discover -s tests -p 'test_plugin_structure.py' -v`
Expected: `OK` (three references named in `SKILL.md` exist; `argument-hint` is a quoted string so frontmatter parses).

- [ ] **Step 3: Check the skill's referenced paths exist**

Run: `ls templates/spec.md templates/plan.md scripts/validate_plan.py skills/wave-design/SKILL.md skills/model-routing/SKILL.md`
Expected: all five listed, no errors.

- [ ] **Step 4: Validate and commit**

Run: `claude plugin validate --strict .` → `✔ Validation passed`.

```bash
git add skills/wave-plan
git commit -m "feat: wave-plan skill (scope, specs, decompose, approve)"
```

---

### Task 15: `wave-execute` skill (and a rehearsal test of its git flow)

**Files:**
- Create: `tests/test_worktree_flow.py`
- Create: `skills/wave-execute/SKILL.md`
- Create: `skills/wave-execute/references/worktrees.md`
- Create: `skills/wave-execute/references/worker-brief.md`
- Create: `skills/wave-execute/references/gates.md`
- Create: `skills/wave-execute/references/failure-handling.md`

**Interfaces:**
- Consumes: `scripts/validate_plan.py`, `scripts/check_owned.py`, the agents `wave-planning:wave-worker` and `wave-planning:wave-validator`, the plan's `yaml status` block.
- Produces: the orchestration procedure. Branch names `wave/integration`, `wave/<n>/<phase-id>`, `wave/<n>/<phase-id>-fix<k>`; worktrees at `.worktrees/<phase-id>`; status values `pending|running|gated|merged|done|blocked`.

- [ ] **Step 1: Write the rehearsal test**

It runs the git commands `references/worktrees.md` documents, in a throwaway repository: worktrees cut from the integration branch (not `main`), the ownership pipeline, a clean merge, a conflicting merge aborted cleanly, cleanup, and wave N+1 building on wave N. It checks the documented commands, not new code, so it should **pass on its first run**; a failure means the documented flow is wrong.

```python
"""Rehearses the exact git flow documented in skills/wave-execute/references/worktrees.md
in a throwaway repository, so the documented commands are known to behave as described."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import helpers

CHECK_OWNED = helpers.SCRIPTS / "check_owned.py"


def run(*args, cwd, stdin=None, check=True):
    result = subprocess.run(args, cwd=cwd, input=stdin, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise AssertionError(f"{' '.join(args)} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result


class WorktreeFlowTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        (self.repo / "plan.md").write_text("plan\n")
        self.git("add", "plan.md")
        self.git("commit", "-qm", "docs(wave): approved wave plan")
        (self.repo / ".gitignore").write_text(".worktrees/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "chore: ignore .worktrees")
        self.git("switch", "-q", "-c", "wave/integration")
        (self.repo / ".worktrees").mkdir()

    def git(self, *args, cwd=None, check=True, stdin=None):
        return run("git", *args, cwd=cwd or self.repo, check=check, stdin=stdin)

    def add_phase(self, wave, phase):
        wt = self.repo / ".worktrees" / phase
        self.git("worktree", "add", "-q", "-b", f"wave/{wave}/{phase}", str(wt), "wave/integration")
        return wt

    def commit_file(self, wt, rel, text, message):
        path = wt / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.git("-C", str(wt), "add", "-A")
        self.git("-C", str(wt), "commit", "-qm", message)

    def owned_check(self, wt, *owns):
        diff = self.git("-C", str(wt), "diff", "--name-only", "wave/integration...HEAD").stdout
        return run(sys.executable, str(CHECK_OWNED), "--owns", *owns, cwd=self.repo, stdin=diff, check=False)

    def test_worktree_is_cut_from_integration_not_main(self):
        (self.repo / "marker.txt").write_text("m\n")
        self.git("add", "marker.txt")
        self.git("commit", "-qm", "integration-only commit")
        wt = self.add_phase(1, "P1")
        self.assertTrue((wt / "marker.txt").exists(), "worktree must contain integration's commits")

    def test_worktree_dir_is_ignored_so_main_tree_stays_clean(self):
        self.add_phase(1, "P1")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_clean_phase_passes_ownership_check_and_merges(self):
        wt = self.add_phase(1, "P1")
        self.commit_file(wt, "src/a/x.txt", "x\n", "feat(P1): x")
        self.assertEqual(self.git("-C", str(wt), "status", "--porcelain").stdout, "")
        result = self.owned_check(wt, "src/a/**")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.git("merge", "--no-ff", "wave/1/P1", "-m", "merge(wave-1): P1")
        self.assertTrue((self.repo / "src/a/x.txt").exists())
        self.assertIn("merge(wave-1): P1", self.git("log", "-1", "--format=%s").stdout)

    def test_write_outside_ownership_is_caught(self):
        wt = self.add_phase(1, "P1")
        self.commit_file(wt, "src/a/x.txt", "x\n", "feat(P1): x")
        self.commit_file(wt, "package-lock.json", "{}\n", "feat(P1): lockfile")
        result = self.owned_check(wt, "src/a/**")
        self.assertEqual(result.returncode, 1)
        self.assertIn("NOT-OWNED package-lock.json", result.stdout)

    def test_uncommitted_work_shows_in_worktree_status(self):
        wt = self.add_phase(1, "P1")
        (wt / "stray.txt").write_text("s\n")
        self.assertIn("stray.txt", self.git("-C", str(wt), "status", "--porcelain").stdout)

    def test_conflicting_merge_can_be_aborted_cleanly(self):
        (self.repo / "shared.txt").write_text("base\n")
        self.git("add", "shared.txt")
        self.git("commit", "-qm", "add shared")
        w3, w4 = self.add_phase(1, "P3"), self.add_phase(1, "P4")
        self.commit_file(w3, "shared.txt", "from P3\n", "feat(P3)")
        self.commit_file(w4, "shared.txt", "from P4\n", "feat(P4)")
        self.git("merge", "--no-ff", "wave/1/P3", "-m", "merge(wave-1): P3")
        conflict = self.git("merge", "--no-ff", "wave/1/P4", "-m", "merge(wave-1): P4", check=False)
        self.assertNotEqual(conflict.returncode, 0)
        self.git("merge", "--abort")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertEqual((self.repo / "shared.txt").read_text(), "from P3\n")

    def test_cleanup_after_merge_and_next_wave_builds_on_it(self):
        wt = self.add_phase(1, "P1")
        self.commit_file(wt, "src/a/x.txt", "x\n", "feat(P1): x")
        self.git("merge", "--no-ff", "wave/1/P1", "-m", "merge(wave-1): P1")
        self.git("worktree", "remove", "--force", str(wt))
        self.git("branch", "-d", "wave/1/P1")
        self.git("worktree", "prune")
        self.assertFalse(wt.exists())
        self.assertNotIn("wave/1/P1", self.git("branch", "--list", "wave/*").stdout)
        nxt = self.add_phase(2, "P2")
        self.assertTrue((nxt / "src/a/x.txt").exists(), "wave 2 must build on wave 1's merged result")

    def test_unmerged_branch_refuses_soft_delete(self):
        wt = self.add_phase(1, "P1")
        self.commit_file(wt, "src/a/x.txt", "x\n", "feat(P1): x")
        self.git("worktree", "remove", "--force", str(wt))
        result = self.git("branch", "-d", "wave/1/P1", check=False)
        self.assertNotEqual(result.returncode, 0, "git branch -d must protect unmerged work")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it**

Run: `python3 -m unittest discover -s tests -p 'test_worktree_flow.py' -v`
Expected: `Ran 8 tests` … `OK`. (Needs `git` on `PATH`; it was developed against git 2.55.)

- [ ] **Step 3: Write the skill and its references**

`skills/wave-execute/SKILL.md`:

````markdown
---
name: wave-execute
description: Use when a wave-planning plan.md has been approved and is ready to build, or when resuming an interrupted wave run. Runs each wave's phases in parallel subagents inside git worktrees, gates them, merges them, and validates the merged result before starting the next wave.
disable-model-invocation: true
argument-hint: "[wave number to start from]"
---

# Wave Execute

You are the **orchestrator**. You dispatch, verify, merge, gate and report. You never write product code yourself. You are the only agent that spawns subagents: `wave-worker` and `wave-validator` are leaf nodes and must never spawn others.

All state lives in the `yaml status` block of `plan.md`, so a run can always be resumed.

## Hard rules

- Never start a wave on a red or unverified integration branch.
- Never skip or weaken a gate, and never mark a wave done on `FAIL` or `INCOMPLETE`.
- Never auto-resolve a merge conflict, and never improvise around a worker's `BLOCKED`. Either means the plan missed something: stop and show the user.
- Never use the Agent tool's `isolation: "worktree"`. You create the worktrees yourself so each phase branches from the gated integration head.
- Never push, force-push, or delete branches you did not create. Ask before opening a PR.

## 0. Preflight (once per run)

1. Read `plan.md`, then validate it:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/validate_plan.py" --root .
   ```

   Any `ERROR` stops the run. Show it to the user and do not execute an invalid plan.
2. Confirm this is a git repository with at least one commit. If not, offer `git init` plus an initial commit and wait for a yes.
3. Run `printenv CLAUDE_CODE_SUBAGENT_MODEL_FORCE`. If it prints `1`, tell the user that model routing will be overridden and ask whether to continue.
4. Set up branches and the worktree directory: [references/worktrees.md](references/worktrees.md), section "Setup". Run the plan's `bootstrap` command in the main tree.
5. If the status block shows earlier progress, do "Resume" in [references/failure-handling.md](references/failure-handling.md) before dispatching anything.

## 1. For each wave, in order

Start at `$ARGUMENTS` if given, otherwise at the first wave that is not `done`.

1. **Announce** the wave: its phases, models, and the functional gate it must pass.
2. **Create a worktree per phase** and run `bootstrap` in each ([references/worktrees.md](references/worktrees.md), "Per phase"). Set the wave and its phases to `running` in the status block and commit it.
3. **Dispatch all phases at once.** Send one message containing one Agent call per phase, so they run in parallel (never more than `max_wave_width`). Each call uses `subagent_type: "wave-planning:wave-worker"`, `model` set to the phase's tier (`haiku`, `sonnet` or `opus`), and a self-contained brief built from [references/worker-brief.md](references/worker-brief.md).
4. **Wait for every worker** (the wave barrier). Do nothing else until all have reported.
5. **Verify each report** ([references/gates.md](references/gates.md), "Phase verification"): ownership of the diff, a clean worktree, a clean main tree, and the shallow gate re-run by you. Never trust a worker's own gate output alone. Handle `BLOCKED`, concerns, and failures with [references/failure-handling.md](references/failure-handling.md). Mark verified phases `gated`.
6. **Merge** the verified phase branches into `wave/integration` in phase-id order, then apply the wave's integration-owned edits ([references/worktrees.md](references/worktrees.md), "Merge"). Mark them `merged`.
7. **Run the wave gate**: dispatch `wave-validator` on the merged integration branch ([references/gates.md](references/gates.md), "Wave gate"). Use `opus` for the validator if any phase in the wave belongs to a risk-flagged spec, otherwise `sonnet`.
8. **PASS:** record the new integration head SHA, set the wave and its phases to `done`, remove the wave's worktrees, commit the status, and show the user a short wave report (what merged, gate evidence, any concerns).
   **FAIL or INCOMPLETE:** follow "Wave gate failed" in [references/failure-handling.md](references/failure-handling.md). Do not start the next wave.
9. **Pause for the user** after wave 1 and after any wave that contains a risk-flagged phase: show the report and wait for them to say continue. Otherwise continue to the next wave.

## 2. Finish

When every wave is `done`, summarise: waves run, phases per model tier, retries and escalations, and the integration branch name. Offer, and do not do unprompted, to open a pull request or merge `wave/integration` into the base branch.

## Status block

`plan.md` ends with a `yaml status` block. Update it with the Edit tool and commit after every state change, so the integration branch and the block never disagree.

```yaml
base_branch: main
integration_branch: wave/integration
integration_head: <sha after the last done wave, or none>
W1: pending | running | done | blocked
P1a: pending | running | gated | merged | done | blocked
```
````

`skills/wave-execute/references/worktrees.md`:

````markdown
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
````

`skills/wave-execute/references/worker-brief.md`:

````markdown
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
````

`skills/wave-execute/references/gates.md`:

````markdown
# Gates

Two levels, as in wave planning: a **shallow** gate per phase (is it structurally sound?) and a **functional** gate per wave (does the integrated behavior actually hold?).

## Phase verification (shallow gate)

After a worker reports `DONE` or `DONE_WITH_CONCERNS`, you verify it yourself. A worker's own gate output is evidence, not proof.

1. Worktree clean, diff within ownership, main tree clean: the three commands in `worktrees.md`, "Verify a phase".
2. Re-run the phase's gate commands in the worktree, in order: format, lint, typecheck, unit.

   ```bash
   ( cd ".worktrees/$P" && <format> && <lint> && <typecheck> && <unit> )
   ```

   Skip a command that is `n/a` in the plan. Stop at the first failure.
3. Any failure is handled with the retry and escalation ladder in `failure-handling.md`. Only a phase that passes all of this is marked `gated`.

## Wave gate (functional)

Run once all phases of the wave are merged into `wave/integration` and integration-owned edits are committed, with the integration branch checked out in the main tree.

1. Confirm `git status --porcelain` is empty and bootstrap has been run.
2. Collect, from `plan.md` and the specs:
   - the wave's `criteria` (each id with its text and `verify` string, from the spec);
   - the wave's `integration_checks`;
   - the gate commands from the header;
   - a run hint if any `http:` criterion exists (how to start the app, for example `npm start`; ask the user if the plan does not say);
   - the design snapshot path if any criterion is `design-fidelity:`.
3. Dispatch one Agent call: `subagent_type: "wave-planning:wave-validator"`, `model: "sonnet"` (or `"opus"` for a wave containing a risk-flagged phase), and a prompt listing the above, one criterion per line as `<id> | <text> | <verify>`.
4. Read the validator's report. Check that `git status --porcelain` is still empty; if the validator changed anything, that is a failure to report to the user.
5. Decide:
   - `RESULT: PASS` → the wave is green.
   - `RESULT: FAIL` → trace each failing criterion to its spec and phases (`F2.AC1` is spec F2; its phases are in the plan) and follow "Wave gate failed" in `failure-handling.md`.
   - `RESULT: INCOMPLETE` → something could not be verified (for example no run hint, or visual comparison unavailable). Show the user exactly what was not verified and ask how to proceed: provide the missing information, accept it explicitly, or stop. Never treat INCOMPLETE as PASS on your own.

## What counts as passing

Every acceptance criterion in the wave and every integration check is `PASS`, observed by running it. Absence of a failure is not a pass.
````

`skills/wave-execute/references/failure-handling.md`:

```markdown
# Failure handling and resume

The principle: wave planning puts the plan owner in charge of what the dependency tree misses. When something unexpected happens, you surface it with evidence and let the user decide. You do not improvise.

## Model ladder

`haiku` → `sonnet` → `opus`. For a failed phase: retry once on the same tier with the failure output added to the brief; if it fails again, move up exactly one tier; if it fails on `opus`, stop and ask the user. Never retry on a lower tier.

## Worker reports

- **`BLOCKED`** or a CONCERNS entry that names a dependency, file, or assumption the plan did not mention: **pause the wave.** Do not merge anything from it. Show the user the worker's words, which phase, and what the plan would need (a new dependency edge, a file moved to integration-owned, a spec question answered). Offer a replan. Mark the phase `blocked`.
- **`DONE_WITH_CONCERNS`**: read the concerns. If they are only notes, continue and include them in the wave report. If they describe something the plan missed, treat as `BLOCKED`.

## Verification failures

- **Shallow gate fails** (your re-run, or the worker's report): apply the model ladder. Re-dispatch into the same worktree with the failing output in the brief.
- **`NOT-OWNED` lines** from `check_owned.py`: the worker wrote outside its ownership. Do not merge. Show the user the paths. Either the plan's ownership is wrong (replan) or the worker misbehaved (re-dispatch with an explicit reminder, on the next tier).
- **Uncommitted changes in the worktree**: re-dispatch the worker with the instruction to commit. If the worker cannot, treat it as a failure.
- **Dirty main tree** at the barrier: something wrote outside the worktrees. Stop, show `git status`, and ask the user before touching it.

## Merge conflict

`git merge --abort`, list the conflicting files and which two phases produced them, and stop. The ownership graph missed an overlap. Offer a replan: usually split ownership differently or mark the file integration-owned. Never resolve it yourself.

## Wave gate failed

1. For each failing criterion, find its spec and phases. If a criterion spans several phases, the cause may be in any of them; read the validator's evidence before choosing.
2. Create a fix worktree from the current integration head (`worktrees.md`, "Fix worktrees") and dispatch a worker with a brief containing the validator's evidence. Start on the failing phase's own tier; the ladder applies across attempts.
3. Verify the fix as in "Phase verification", merge it, and run the wave gate again from scratch.
4. After the ladder is exhausted, stop and ask the user.

## Permission denials

If a worker reports that a tool or command was denied, do not loop. Tell the user which permission is missing (editing files, running a gate command), and ask them to allow it in their Claude Code permission settings or choose a more permissive mode for this run, then re-dispatch.

## Replanning

Completed (`done`) waves stay as they are. Show the user what changed, return to the `wave-plan` decomposition stage with the new information, and have it regenerate only the pending part of `plan.md` from the specs, preserving the status of everything already `done`. The new plan must pass `validate_plan.py`, and the user approves it again before you continue.

## Resume

When the status block shows earlier progress, or `$ARGUMENTS` names a wave:

1. List what is on disk: `git worktree list`, `git branch --list 'wave/*'`, and `git log --oneline -5 wave/integration`.
2. Compare it with the status block. The integration branch is the truth for what is merged: a wave counts as `done` only if its status says so **and** its merge commits are on `wave/integration`.
3. Remove orphans: worktrees and `wave/<n>/…` branches for phases that are not `running` or `blocked`, using `git worktree remove --force` and `git branch -D` after you have checked the branch has no unmerged commits you need (`git log wave/integration..<branch>`). Ask the user if a branch holds work you cannot account for.
4. A phase left `running` has no trustworthy state: delete its worktree and branch and start it again from a fresh worktree.
5. Continue at the first wave that is not `done`. Tell the user what you found and what you cleaned up before dispatching.
```

- [ ] **Step 4: Run the structure tests and the whole suite**

Run: `python3 -m unittest discover -s tests`
Expected: all tests pass (`OK`), except that `RequiredComponentsTests` does not exist yet (Task 16).

- [ ] **Step 5: Validate and commit**

Run: `claude plugin validate --strict .` → `✔ Validation passed`.

```bash
git add tests/test_worktree_flow.py skills/wave-execute
git commit -m "feat: wave-execute orchestrator skill; rehearsal test of its git flow"
```

---

### Task 16: Evals, README, and the final structure check

**Files:**
- Create: `evals/plan-triggers-on-wave-request/prompt.md`
- Create: `evals/plan-triggers-on-wave-request/graders/skill-fired.md`
- Create: `evals/plan-triggers-on-wave-request/graders/starts-by-scoping.md`
- Create: `evals/plan-pushes-back-on-unverifiable-criterion/prompt.md`
- Create: `evals/plan-pushes-back-on-unverifiable-criterion/graders/skill-fired.md`
- Create: `evals/plan-pushes-back-on-unverifiable-criterion/graders/asks-how-to-verify.md`
- Create: `evals/model-routing-assigns-tiers/prompt.md`
- Create: `evals/model-routing-assigns-tiers/graders/tiers-correct.md`
- Create: `README.md`
- Modify: `tests/test_plugin_structure.py` (add the required-components check)

**Interfaces:**
- Consumes: everything built so far.
- Produces: `claude plugin eval` cases (layout from the plugin-evals docs: `evals/<case>/prompt.md` frontmatter plus body, `evals/<case>/graders/<name>.md` with `type:`), the README, and `RequiredComponentsTests`, which fails whenever a shipped component is missing.

v1 evals cover the **planning side** only. Execution evals need a git workspace and the case-setup (`case.yaml`) features, and execution is covered by the end-to-end dry run (Task 17) instead.

- [ ] **Step 1: Write the eval cases**

`evals/plan-triggers-on-wave-request/prompt.md`:

```markdown
---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---

I want to build a small bookmarking web app: a Node API, a SQLite store and a React UI. I want AI agents to build it in parallel, so plan it out with waves before anything gets coded.
```

`evals/plan-triggers-on-wave-request/graders/skill-fired.md`:

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?wave-plan"'
---
```

`evals/plan-triggers-on-wave-request/graders/starts-by-scoping.md`:

```markdown
---
type: llm
---

PASS if the response begins scoping the project: it asks one focused question about purpose, users, success criteria or constraints, or it restates its understanding and invites correction.
FAIL if it writes application code, scaffolds files, or presents a finished plan with waves without first asking about or confirming the scope.
```

`evals/plan-pushes-back-on-unverifiable-criterion/prompt.md`:

```markdown
---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill, Write]
---

Use wave planning for my notes app. I've already agreed the feature list with myself, so go straight to the spec for the search feature. Acceptance criteria: search should feel fast and the results page should look clean.
```

`evals/plan-pushes-back-on-unverifiable-criterion/graders/skill-fired.md`:

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?wave-plan"'
---
```

`evals/plan-pushes-back-on-unverifiable-criterion/graders/asks-how-to-verify.md`:

```markdown
---
type: llm
---

PASS if the response objects to the vague criteria ("feel fast", "look clean") and asks how each could be verified, or proposes concrete checkable versions (for example a latency threshold, or a comparison against an approved design).
FAIL if it writes those criteria into a spec exactly as given, without questioning how they would be verified.
```

`evals/model-routing-assigns-tiers/prompt.md`:

```markdown
---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---

In a wave plan I have three phases. Assign each one a model tier (haiku, sonnet or opus) using the wave-planning routing rubric and say why: (a) rename one config key across three files; (b) implement the payment capture endpoint; (c) build a standard CRUD settings page from a finished design.
```

`evals/model-routing-assigns-tiers/graders/tiers-correct.md`:

```markdown
---
type: llm
---

PASS if (a) the rename is assigned haiku, (b) the payment endpoint is assigned opus with money or risk given as the reason, and (c) the CRUD settings page is assigned sonnet.
FAIL if any of the three is assigned a different tier, or if a tier is not stated for each.
```

- [ ] **Step 2: Write the README**

`README.md`:

````markdown
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
````

Note: the install snippet contains `<owner>/<repo>`; Task 17 replaces it once the GitHub repository exists.

- [ ] **Step 3: Add the required-components test (it must pass now; it guards the future)**

In `tests/test_plugin_structure.py`, insert this block directly after the `REFERENCE = re.compile(...)` line:

```python
REQUIRED_FILES = [
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "skills/wave-plan/SKILL.md",
    "skills/wave-design/SKILL.md",
    "skills/wave-execute/SKILL.md",
    "skills/model-routing/SKILL.md",
    "agents/wave-worker.md",
    "agents/wave-validator.md",
    "scripts/validate_plan.py",
    "scripts/routing.py",
    "scripts/check_owned.py",
    "templates/spec.md",
    "templates/plan.md",
    "README.md",
    "LICENSE",
]
```

And insert this class directly before the final `if __name__ == "__main__":` line:

```python
class RequiredComponentsTests(unittest.TestCase):
    def test_all_required_files_exist(self):
        missing = [f for f in REQUIRED_FILES if not (REPO / f).exists()]
        self.assertEqual(missing, [], f"missing plugin files: {missing}")
```

Run: `python3 -m unittest discover -s tests -p 'test_plugin_structure.py' -v`
Expected: `OK`, including `test_all_required_files_exist`. It checks every shipped component, including `README.md` (Step 2) and `LICENSE` (Task 1).

- [ ] **Step 4: Run the whole suite and validate**

Run: `python3 -m unittest discover -s tests`
Expected: `Ran 143 tests` … `OK`.

Run: `claude plugin validate --strict .`
Expected: `✔ Validation passed`.

- [ ] **Step 5: Run the evals (costs tokens, ask the user first)**

`claude plugin eval` calls the model with the user's credentials and counts against their usage. Tell the user the cost scales with cases × runs, and get a yes. Then, from the repo root:

```bash
claude plugin eval . --runs 1 --ablation none
```

(The first run may ask `Trust this plugin directory?`; answer `y`. Requires Claude Code v2.1.269 or later; if the command reports that plugin eval is unavailable or in early access, record that in `docs/dry-run-log.md` and continue.)

Expected: a summary table with one row per case and a `SCORE` near 1.00. A single run is noisy. For a case that scores low, open the printed `Report:` path and read which grader failed.

- `skill-fired` fails → Claude did not pick the skill from natural phrasing. Rewrite that skill's `description` (keep it starting with "Use when", name the triggering situations, not the workflow), re-run only that case with `--case <name> --runs 1 --ablation none`, then confirm at the default three runs.
- An `llm` grader fails but the response looks right → tighten the rubric's PASS/FAIL wording, or re-run with `--judge-model sonnet`.

`evals/results/` is already in `.gitignore`, so reports are not committed.

- [ ] **Step 6: Commit**

```bash
git add evals README.md tests/test_plugin_structure.py
git commit -m "feat: planning-side evals, README, required-components check"
```


### Task 17: End-to-end dry run, fixes, and release preparation

**Files:**
- Create: `docs/dry-run-log.md`
- Modify: whatever the dry run shows to be wrong (skills, agents, templates, scripts, README)
- Modify: `.claude-plugin/plugin.json` (add `repository`), `README.md` (install snippet): only after the user confirms the GitHub repository

**Interfaces:**
- Consumes: the whole plugin, loaded from the working tree with `claude --plugin-dir`.
- Produces: evidence that the pipeline works on a real project (or a list of defects fixed), a release-ready tree.

This task is run by the human and the main agent together, in a **separate sandbox project outside this repository**. It cannot be unit-tested; it is the test. It spends real tokens: tell the user before starting, and expect the plan, design and one or two waves to be the bulk of the cost.

- [ ] **Step 1: Create the sandbox**

```bash
mkdir -p /mnt/workspace/Projects/wave-planning-sandbox
cd /mnt/workspace/Projects/wave-planning-sandbox
git init -b main
echo "# bookmark sandbox" > README.md
git add README.md && git commit -m "chore: init sandbox"
```

- [ ] **Step 2: Start Claude Code with the plugin loaded from source**

```bash
claude --plugin-dir /mnt/workspace/Projects/wave-planning
```

Run `/help` or type `/wave-planning:` and confirm `wave-plan`, `wave-design`, `wave-execute` appear (`model-routing` should not, it is not user-invocable). If a skill is missing, run `claude plugin validate --strict /mnt/workspace/Projects/wave-planning` and fix what it reports before continuing.

- [ ] **Step 3: Plan a small project**

Run `/wave-planning:wave-plan` with this brief:

> A bookmark manager. A Node HTTP API (save, list, delete bookmarks; tag them; search by text) backed by SQLite, and a single-page HTML UI that uses the API. No auth.

Answer the interview as a user would. The aim is a plan with at least two waves, at least two model tiers, and one UI feature so the design stage runs.

- [ ] **Step 4: Record observations against this checklist in `docs/dry-run-log.md`**

Create `docs/dry-run-log.md` in the plugin repo with a table like the one below, and fill the **Observed** column honestly as the run proceeds. A "no" is a finding, not a failure of the dry run.

```markdown
# Dry-run log

Date: <YYYY-MM-DD> · Claude Code version: <output of `claude --version`> · Sandbox: bookmark manager

| # | Check | Pass condition | Observed |
|---|---|---|---|
| 1 | Scope interview | One question at a time; feature list approved before specs are written | |
| 2 | Specs | Every criterion has a `verify:` (`test:`/`cmd:`/`http:`/`design-fidelity:`); weak criteria were questioned | |
| 3 | Claude Design mockup | A Design artifact is created via `quickstart`, one artboard per screen id plus `tokens`, link shown | |
| 4 | Design snapshot | `docs/waves/design/snapshot.html` saved and contains every screen id and `tokens`; if not, the failure was reported and the fallback offered | |
| 5 | Freeze | `DESIGN.md` written; specs' `reads` point at the snapshot; design not edited afterwards | |
| 6 | Plan validity | `validate_plan.py` prints `OK` before the plan is shown; waves ≥ 2; ≥ 2 model tiers used; risk-free phases not on opus | |
| 7 | Hidden-dependency question | Asked before approval | |
| 8 | Preflight | Plan validated again; commit of plan/specs asked first; `.worktrees/` ignored; `wave/integration` created | |
| 9 | Worktrees | One per phase, cut from `wave/integration`, bootstrap run in each | |
| 10 | Dispatch | All phases of a wave dispatched in one message (parallel), each with the planned `model` | |
| 11 | Permissions | Workers could edit files and run gate commands without being blocked by prompts; if blocked, note exactly which permission | |
| 12 | Verification | Orchestrator ran `check_owned.py` and re-ran each shallow gate itself before merging | |
| 13 | Merge and wave gate | Phases merged `--no-ff`; `wave-validator` ran on the merged branch and reported per-criterion evidence | |
| 14 | Pause policy | Paused for the user after wave 1 | |
| 15 | Status block | `plan.md` status kept in step with reality and committed | |
| 16 | Tokens and time | Rough total tokens and wall-clock per wave, for the README's honesty section | |
```

- [ ] **Step 5: Inject a hidden dependency (the key behavioral test)**

After the plan is approved and before executing wave N (N ≥ 1), pick two phases in the same wave, A (owns the API) and B (owns the UI). Edit B's spec step text so it quietly needs a file A owns, for example "read the API base URL from `src/api/config.ts`". Commit the change, then run `/wave-planning:wave-execute`.

Expected: B's worker reports `BLOCKED` (or `DONE_WITH_CONCERNS` naming the file); the orchestrator **pauses the wave, merges nothing from B, shows the finding, and offers a replan**. It does not edit the file itself and does not carry on. Record what happened as check 17 in the log.

If instead the worker edited a file it does not own, check whether `check_owned.py` caught it (it should: a `NOT-OWNED` line, nothing merged). Record that as the finding.

- [ ] **Step 6: Test resume**

Start another wave, interrupt the run (Ctrl+C) after workers are dispatched, then run `/wave-planning:wave-execute` again.

Expected: the orchestrator lists worktrees and branches, compares them with the status block, removes the orphaned worktree and branch for the phase left `running`, tells you what it found, and restarts that phase from a fresh worktree. Record as check 18.

- [ ] **Step 7 (optional, spends more): Test a red wave gate**

In a copy of the sandbox plan, change one pending criterion's `verify` to a command that can never pass (`cmd:test -f does-not-exist`), run that wave, and watch the fix loop: fix worktree, same tier, then one tier up, then a stop that asks you. Record as check 19. Revert the change afterwards.

- [ ] **Step 8: Fix what the run found**

For each finding, fix the smallest thing that is wrong (usually a skill's wording or a missing step), add a unit test first if it is script logic, re-run `python3 -m unittest discover -s tests` and `claude plugin validate --strict .`, and commit with a message that names the dry-run check: `fix: <what> (dry-run check <n>)`. Re-run only the affected checks. Update the README's Limits section with measured token/time numbers and any permission requirement actually observed.

- [ ] **Step 9: Commit the log**

```bash
git add docs/dry-run-log.md
git commit -m "docs: end-to-end dry-run log"
```

- [ ] **Step 10: Release preparation (stop and ask before any outward-facing action)**

Everything above is local. These steps publish things and need the user's explicit go-ahead at each one; do not do them on your own:

1. Ask the user for the GitHub repository (`<owner>/<repo>`). Creating a remote repository, pushing, and tagging are outward-facing: confirm each.
2. Once confirmed: add `"repository": "https://github.com/<owner>/<repo>"` to `.claude-plugin/plugin.json`, and replace `<owner>/<repo>` in the README's install snippet. Run `claude plugin validate --strict .`. Commit.
3. Tag the release from the plugin directory: `claude plugin tag` (creates `wave-planning--v0.1.0`); add `--push` only after the user agrees to push.
4. From a clean shell, test installation exactly as a user would: `claude plugin marketplace add <owner>/<repo>`, `claude plugin install wave-planning@arunprakashg-plugins`, start a session, and confirm `/wave-planning:wave-plan` is available.
5. **Anthropic's directory** (optional, user-driven): submit at `claude.ai/directory/manage` (needs a paid claude.ai plan). Before that, add the listing fields to `plugin.json` (`icon` as a path to an image inside the plugin; `documentationUrl`, `supportUrl`, `privacyPolicyUrl`, `termsOfServiceUrl` as `https://` URLs) and re-validate. The portal applies rules the CLI does not check, so a clean local validation is necessary but not sufficient. The listing must say the plugin is for Claude Code only.

---

## Self-review

**Spec coverage.** §1–3 purpose, rules and pipeline → Tasks 12–15 (skills). §4 layout → Tasks 1, 10–16 (with `commands/` dropped; see decision 8). §5.1–5.3 specs, `plan.md`, validator → Tasks 6–10. §6 routing → Tasks 4, 12. §7–7.1 execution and worker brief → Task 15 (skill, `worktrees.md`, `worker-brief.md`, rehearsal test), Task 11 (worker agent). §8 failure and resume → Task 15 (`failure-handling.md`). §9 gates → Task 15 (`gates.md`), Task 11 (validator). §10 design → Task 13. §11 testing → Tasks 2–10, 15 (unit), 16 (evals), 17 (end to end). §12 publishing → Task 17. §13 open items: snapshot vs live read resolved (decision 6); `.worktrees/` default kept; PreToolUse hook deferred to v2 (not built); `isolation: "worktree"` base-branch setting not used (manual worktrees, with the reason in `worktrees.md`).

**Placeholder scan.** No `TBD`/`TODO`/"add error handling" steps. The only literal `<…>` markers are in the templates and worker-brief (fill-in fields by design) and the README's `<owner>/<repo>` (resolved in Task 17 Step 10).

**Type and name consistency.** The names used across tasks are the ones defined in the Interfaces blocks: `Finding`, `check_refs`/`check_cycles`/`check_waves`/`check_width`/`check_step_coverage`, `check_ownership`/`check_criteria`/`check_routing`, `derive_model`, `NeedsPlanningError`, `load_project`/`parse_spec`/`parse_plan`, `matches`/`overlaps`/`covers`, `violations`. Skills refer to `scripts/validate_plan.py`, `scripts/routing.py`, `scripts/check_owned.py` and agents `wave-planning:wave-worker` / `wave-planning:wave-validator`, all of which exist. Branch and status vocabulary match between `SKILL.md`, `worktrees.md`, `failure-handling.md` and the template's status block.
