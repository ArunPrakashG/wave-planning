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
