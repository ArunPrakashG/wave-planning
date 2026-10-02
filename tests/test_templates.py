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
