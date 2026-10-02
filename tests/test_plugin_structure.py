"""Structural invariants of the plugin itself (not of a user's wave plan)."""
import json
import re
import unittest

import helpers
from miniyaml import parse_document

REPO = helpers.REPO
FRONTMATTER = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*$", re.S | re.M)
REFERENCE = re.compile(r"\breferences/[A-Za-z0-9_.\-]+\.md\b")

REQUIRED_FILES = [
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    "skills/wave-plan/SKILL.md",
    "skills/wave-design/SKILL.md",
    "skills/wave-execute/SKILL.md",
    "skills/model-routing/SKILL.md",
    "agents/wave-worker.md",
    "agents/wave-validator.md",
    "scripts/validate_plan.py",
    "scripts/routing.py",
    "scripts/check_owned.py",
    "scripts/http_check.py",
    "templates/spec.md",
    "templates/plan.md",
    "README.md",
    "LICENSE",
]


def frontmatter(path):
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        raise AssertionError(f"{path}: no frontmatter")
    return parse_document(match.group(1))


def tool_list(front, key="tools"):
    return [t.strip() for t in str(front.get(key, "")).split(",") if t.strip()]


class AgentTests(unittest.TestCase):
    def agents(self):
        return sorted((REPO / "agents").glob("*.md"))

    def test_agents_are_leaf_nodes(self):
        for path in self.agents():
            tools = tool_list(frontmatter(path))
            self.assertTrue(tools, f"{path.name} must declare an explicit tools allowlist")
            self.assertNotIn("Agent", tools, f"{path.name} must not be able to spawn subagents")

    def test_validator_is_read_only(self):
        path = REPO / "agents" / "wave-validator.md"
        if not path.exists():
            self.skipTest("wave-validator not created yet")
        tools = tool_list(frontmatter(path))
        for forbidden in ("Edit", "Write", "NotebookEdit"):
            self.assertNotIn(forbidden, tools)

    def test_agents_have_name_matching_file_and_description(self):
        for path in self.agents():
            front = frontmatter(path)
            self.assertEqual(front.get("name"), path.stem)
            self.assertTrue(front.get("description"), f"{path.name} needs a description")


class SkillTests(unittest.TestCase):
    def skills(self):
        return sorted((REPO / "skills").glob("*/SKILL.md"))

    def test_name_matches_directory_and_description_fits(self):
        for path in self.skills():
            front = frontmatter(path)
            self.assertEqual(front.get("name"), path.parent.name)
            description = str(front.get("description", ""))
            self.assertTrue(description.startswith("Use when"), f"{path}: description should start with 'Use when'")
            self.assertLessEqual(len(description), 1536)

    def test_skill_body_is_lean(self):
        for path in self.skills():
            lines = path.read_text(encoding="utf-8").count("\n")
            self.assertLessEqual(lines, 500, f"{path} is {lines} lines; move detail into references/")

    def test_referenced_files_exist(self):
        for path in self.skills():
            for ref in set(REFERENCE.findall(path.read_text(encoding="utf-8"))):
                self.assertTrue((path.parent / ref).is_file(), f"{path}: references missing file {ref}")


class ManifestTests(unittest.TestCase):
    def test_manifest_and_marketplace_agree(self):
        plugin_path = REPO / ".claude-plugin" / "plugin.json"
        market_path = REPO / ".claude-plugin" / "marketplace.json"
        if not (plugin_path.exists() and market_path.exists()):
            self.skipTest("manifests not created yet")
        plugin = json.loads(plugin_path.read_text())
        market = json.loads(market_path.read_text())
        self.assertEqual(plugin["name"], "wave-planning")
        self.assertIn("version", plugin)
        entry_names = [p["name"] for p in market["plugins"]]
        self.assertEqual(entry_names, [plugin["name"]])


class RequiredComponentsTests(unittest.TestCase):
    def test_all_required_files_exist(self):
        missing = [f for f in REQUIRED_FILES if not (REPO / f).exists()]
        self.assertEqual(missing, [], f"missing plugin files: {missing}")


if __name__ == "__main__":
    unittest.main()
