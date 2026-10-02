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
