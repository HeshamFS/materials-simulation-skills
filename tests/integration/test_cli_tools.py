import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "core-numerical" / "numerical-stability" / "scripts"


class TestCliTools(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cfl_checker_json(self):
        cmd = [
            str(SCRIPTS / "cfl_checker.py"),
            "--dx",
            "0.1",
            "--dt",
            "0.01",
            "--velocity",
            "1.0",
            "--diffusivity",
            "0.1",
            "--dimensions",
            "2",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("metrics", payload)
        self.assertIn("cfl", payload["metrics"])

    def test_von_neumann_json(self):
        cmd = [
            str(SCRIPTS / "von_neumann_analyzer.py"),
            "--coeffs",
            "0.2,0.6,0.2",
            "--nk",
            "64",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("results", payload)
        self.assertIn("max_amplification", payload["results"])

    def test_matrix_condition_json(self):
        matrix_path = ROOT / "tests" / "integration" / "matrix.txt"
        matrix_path.write_text("1 0\n0 2\n")
        try:
            cmd = [
                str(SCRIPTS / "matrix_condition.py"),
                "--matrix",
                str(matrix_path),
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["results"]["status"], "ok")
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_stiffness_detector_json(self):
        cmd = [
            str(SCRIPTS / "stiffness_detector.py"),
            "--eigs=-1,-1000",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["results"]["stiff"])

    def test_invalid_inputs_return_error(self):
        cmd = [
            str(SCRIPTS / "cfl_checker.py"),
            "--dx",
            "0.0",
            "--dt",
            "0.1",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dx and dt must be positive", result.stderr)


if __name__ == "__main__":
    unittest.main()
