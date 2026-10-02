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
