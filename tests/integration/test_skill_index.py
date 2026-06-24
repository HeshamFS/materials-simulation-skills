"""Tests for the machine-readable skill index, bundles, and marketplace manifest.

Guards that the committed skills_index.json / .claude-plugin/marketplace.json are
**fresh** (regenerate-and-diff), structurally valid, internally consistent, and
that every skill belongs to its category bundle.
"""
import json
import unittest
from pathlib import Path

from materials_simulation_skills.skill_index import build_index, build_marketplace, dumps
from materials_simulation_skills.skill_utils import find_repo_root, resolve_bundle

ROOT = find_repo_root()


class TestIndexFreshness(unittest.TestCase):
    def test_skills_index_is_up_to_date(self):
        committed = (ROOT / "skills_index.json").read_text(encoding="utf-8")
        self.assertEqual(committed, dumps(build_index(ROOT)),
                         msg="skills_index.json is stale — run `python tools/build_index.py`")

    def test_marketplace_is_up_to_date(self):
        committed = (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        self.assertEqual(committed, dumps(build_marketplace(build_index(ROOT))),
                         msg="marketplace.json is stale — run `python tools/build_index.py`")


class TestIndexStructure(unittest.TestCase):
    def setUp(self):
        self.index = build_index(ROOT)

    def test_summary_matches_skills(self):
        s = self.index["summary"]
        self.assertEqual(s["skills"], len(self.index["skills"]))
        self.assertEqual(s["scripts"], sum(r["scripts"] for r in self.index["skills"]))
        self.assertEqual(s["deterministic_checks"],
                         sum(r["deterministic_checks"] for r in self.index["skills"]))

    def test_every_skill_record_is_complete(self):
        required = {"name", "category", "path", "description", "version",
                    "security_tier", "allowed_tools", "scripts", "eval_cases",
                    "deterministic_checks", "eval_coverage", "standards"}
        for r in self.index["skills"]:
            self.assertTrue(required.issubset(r), msg=f"{r.get('name')} missing fields")
            self.assertTrue(r["standards"], msg=f"{r['name']} has no cited standards")
            self.assertTrue((ROOT / r["path"] / "SKILL.md").exists())
            self.assertIn(r["security_tier"], ("low", "medium", "high", ""))
            self.assertGreaterEqual(r["eval_coverage"], 0.0)
            self.assertLessEqual(r["eval_coverage"], 1.0)

    def test_full_deterministic_coverage(self):
        # The repo's headline claim: every eval case is deterministically checked.
        self.assertEqual(self.index["summary"]["eval_coverage"], 1.0)


class TestBundles(unittest.TestCase):
    def setUp(self):
        self.index = build_index(ROOT)
        self.names = {r["name"] for r in self.index["skills"]}

    def test_bundle_members_exist(self):
        for b in self.index["bundles"]:
            self.assertTrue(b["skills"], msg=f"empty bundle {b['name']}")
            for n in b["skills"]:
                self.assertIn(n, self.names, msg=f"bundle {b['name']} -> unknown skill {n}")

    def test_every_skill_in_its_category_bundle(self):
        cat_bundles = {b["name"]: set(b["skills"]) for b in self.index["bundles"] if b["kind"] == "category"}
        for r in self.index["skills"]:
            self.assertIn(r["name"], cat_bundles[r["category"]])

    def test_resolve_bundle(self):
        members = resolve_bundle(ROOT, "verification-and-validation")
        self.assertIn("numerical-stability", members)


class TestMarketplace(unittest.TestCase):
    def test_marketplace_plugins_point_at_real_skills(self):
        market = build_marketplace(build_index(ROOT))
        self.assertTrue(market["plugins"])
        for plugin in market["plugins"]:
            for skill_path in plugin["skills"]:
                rel = skill_path.lstrip("./")
                self.assertTrue((ROOT / rel / "SKILL.md").exists(),
                                msg=f"{plugin['name']} -> missing {skill_path}")


if __name__ == "__main__":
    unittest.main()
