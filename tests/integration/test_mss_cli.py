import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestMssCli(unittest.TestCase):
    def run_mss(self, args):
        return subprocess.run(
            [sys.executable, "-m", "materials_simulation_skills.cli", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_list_json_contains_new_skill(self):
        result = self.run_mss(["list", "--json"])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        names = {item["name"] for item in payload}
        self.assertIn("simulation-failure-triage", names)
        self.assertIn("fair-simulation-packager", names)

    def test_validate_single_skill_json(self):
        result = self.run_mss(["validate", "--skill", "md-analysis-planner", "--json"])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"], payload["errors"])

    def test_run_existing_skill_script(self):
        result = self.run_mss(
            [
                "run",
                "numerical-stability",
                "cfl_checker",
                "--",
                "--dx",
                "0.1",
                "--dt",
                "0.01",
                "--velocity",
                "1.0",
                "--json",
            ]
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("stable", payload)

    def test_install_to_temp_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_mss(
                [
                    "install",
                    "--agent",
                    "codex",
                    "--scope",
                    "user",
                    "--skill",
                    "md-analysis-planner",
                    "--dest",
                    tmp,
                    "--json",
                ]
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = Path(tmp) / "md-analysis-planner" / "SKILL.md"
            self.assertTrue(installed.exists())

    def test_validate_unknown_skill_fails(self):
        result = self.run_mss(["validate", "--skill", "not-a-skill"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unknown skill", result.stderr)


if __name__ == "__main__":
    unittest.main()
