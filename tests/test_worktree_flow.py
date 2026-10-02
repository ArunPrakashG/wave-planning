"""Rehearses the exact git flow documented in skills/wave-execute/references/worktrees.md
in a throwaway repository, so the documented commands are known to behave as described."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import helpers

CHECK_OWNED = helpers.SCRIPTS / "check_owned.py"


def run(*args, cwd, stdin=None, check=True):
    result = subprocess.run(args, cwd=cwd, input=stdin, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise AssertionError(f"{' '.join(args)} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result


class WorktreeFlowTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        (self.repo / "plan.md").write_text("plan\n")
        self.git("add", "plan.md")
        self.git("commit", "-qm", "docs(wave): approved wave plan")
        (self.repo / ".gitignore").write_text(".worktrees/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "chore: ignore .worktrees")
        self.git("switch", "-q", "-c", "wave/integration")
        (self.repo / ".worktrees").mkdir()

    def git(self, *args, cwd=None, check=True, stdin=None):
        return run("git", *args, cwd=cwd or self.repo, check=check, stdin=stdin)

    def add_phase(self, wave, phase):
        wt = self.repo / ".worktrees" / phase
        self.git("worktree", "add", "-q", "-b", f"wave/{wave}/{phase}", str(wt), "wave/integration")
        return wt

    def commit_file(self, wt, rel, text, message):
        path = wt / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.git("-C", str(wt), "add", "-A")
        self.git("-C", str(wt), "commit", "-qm", message)

    def owned_check(self, wt, *owns):
        diff = self.git("-C", str(wt), "diff", "--name-only", "wave/integration...HEAD").stdout
        return run(sys.executable, str(CHECK_OWNED), "--owns", *owns, cwd=self.repo, stdin=diff, check=False)

    def test_worktree_is_cut_from_integration_not_main(self):
        (self.repo / "marker.txt").write_text("m\n")
        self.git("add", "marker.txt")
        self.git("commit", "-qm", "integration-only commit")
        wt = self.add_phase(1, "P1")
        self.assertTrue((wt / "marker.txt").exists(), "worktree must contain integration's commits")

    def test_worktree_dir_is_ignored_so_main_tree_stays_clean(self):
        self.add_phase(1, "P1")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")

    def test_clean_phase_passes_ownership_check_and_merges(self):
        wt = self.add_phase(1, "P1")
        self.commit_file(wt, "src/a/x.txt", "x\n", "feat(P1): x")
        self.assertEqual(self.git("-C", str(wt), "status", "--porcelain").stdout, "")
        result = self.owned_check(wt, "src/a/**")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.git("merge", "--no-ff", "wave/1/P1", "-m", "merge(wave-1): P1")
        self.assertTrue((self.repo / "src/a/x.txt").exists())
        self.assertIn("merge(wave-1): P1", self.git("log", "-1", "--format=%s").stdout)

    def test_write_outside_ownership_is_caught(self):
        wt = self.add_phase(1, "P1")
        self.commit_file(wt, "src/a/x.txt", "x\n", "feat(P1): x")
        self.commit_file(wt, "package-lock.json", "{}\n", "feat(P1): lockfile")
        result = self.owned_check(wt, "src/a/**")
        self.assertEqual(result.returncode, 1)
        self.assertIn("NOT-OWNED package-lock.json", result.stdout)

    def test_uncommitted_work_shows_in_worktree_status(self):
        wt = self.add_phase(1, "P1")
        (wt / "stray.txt").write_text("s\n")
        self.assertIn("stray.txt", self.git("-C", str(wt), "status", "--porcelain").stdout)

    def test_conflicting_merge_can_be_aborted_cleanly(self):
        (self.repo / "shared.txt").write_text("base\n")
        self.git("add", "shared.txt")
        self.git("commit", "-qm", "add shared")
        w3, w4 = self.add_phase(1, "P3"), self.add_phase(1, "P4")
        self.commit_file(w3, "shared.txt", "from P3\n", "feat(P3)")
        self.commit_file(w4, "shared.txt", "from P4\n", "feat(P4)")
        self.git("merge", "--no-ff", "wave/1/P3", "-m", "merge(wave-1): P3")
        conflict = self.git("merge", "--no-ff", "wave/1/P4", "-m", "merge(wave-1): P4", check=False)
        self.assertNotEqual(conflict.returncode, 0)
        self.git("merge", "--abort")
        self.assertEqual(self.git("status", "--porcelain").stdout, "")
        self.assertEqual((self.repo / "shared.txt").read_text(), "from P3\n")

    def test_cleanup_after_merge_and_next_wave_builds_on_it(self):
        wt = self.add_phase(1, "P1")
        self.commit_file(wt, "src/a/x.txt", "x\n", "feat(P1): x")
        self.git("merge", "--no-ff", "wave/1/P1", "-m", "merge(wave-1): P1")
        self.git("worktree", "remove", "--force", str(wt))
        self.git("branch", "-d", "wave/1/P1")
        self.git("worktree", "prune")
        self.assertFalse(wt.exists())
        self.assertNotIn("wave/1/P1", self.git("branch", "--list", "wave/*").stdout)
        nxt = self.add_phase(2, "P2")
        self.assertTrue((nxt / "src/a/x.txt").exists(), "wave 2 must build on wave 1's merged result")

    def test_unmerged_branch_refuses_soft_delete(self):
        wt = self.add_phase(1, "P1")
        self.commit_file(wt, "src/a/x.txt", "x\n", "feat(P1): x")
        self.git("worktree", "remove", "--force", str(wt))
        result = self.git("branch", "-d", "wave/1/P1", check=False)
        self.assertNotEqual(result.returncode, 0, "git branch -d must protect unmerged work")


if __name__ == "__main__":
    unittest.main()
