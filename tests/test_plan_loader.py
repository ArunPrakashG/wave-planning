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
