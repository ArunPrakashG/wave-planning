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
