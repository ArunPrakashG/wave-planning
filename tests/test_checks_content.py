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
