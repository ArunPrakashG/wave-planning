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
