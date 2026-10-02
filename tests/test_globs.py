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
