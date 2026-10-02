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
