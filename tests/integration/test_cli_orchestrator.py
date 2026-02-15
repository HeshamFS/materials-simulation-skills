"""CLI integration tests for simulation-orchestrator scripts.

Tests JSON output schema and error handling for sweep_generator, campaign_manager,
job_tracker, and result_aggregator.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "simulation-workflow" / "simulation-orchestrator" / "scripts"


class TestCliOrchestrator(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    # ---- sweep_generator.py ----

    def test_sweep_generator_linspace_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.json"
            base_path.write_text('{"solver": "CG"}')
            out_dir = str(Path(tmpdir) / "sweep")
            cmd = [
                str(SCRIPTS / "sweep_generator.py"),
                "--base-config", str(base_path),
                "--params", "dt:0.001:0.01:3",
                "--method", "linspace",
                "--output-dir", out_dir,
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["total_runs"], 3)
            self.assertEqual(data["sweep_method"], "linspace")
            self.assertIn("configs", data)

    def test_sweep_generator_lhs_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.json"
            base_path.write_text('{"solver": "CG"}')
            out_dir = str(Path(tmpdir) / "sweep")
            cmd = [
                str(SCRIPTS / "sweep_generator.py"),
                "--base-config", str(base_path),
                "--params", "dt:0.001:0.01,kappa:0.1:1.0",
                "--method", "lhs",
                "--output-dir", out_dir,
                "--samples", "5",
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual(data["total_runs"], 5)

    def test_sweep_generator_reversed_range(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir) / "base.json"
            base_path.write_text('{"solver": "CG"}')
            out_dir = str(Path(tmpdir) / "sweep")
            cmd = [
                str(SCRIPTS / "sweep_generator.py"),
                "--base-config", str(base_path),
                "--params", "dt:0.01:0.001:3",
                "--method", "linspace",
                "--output-dir", out_dir,
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)

    def test_sweep_generator_missing_base(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                str(SCRIPTS / "sweep_generator.py"),
                "--base-config", "/nonexistent.json",
                "--params", "dt:0.001:0.01:3",
                "--method", "linspace",
                "--output-dir", str(Path(tmpdir) / "sweep"),
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)

    # ---- campaign_manager.py ----

    def test_campaign_manager_init_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # campaign_manager expects a sweep directory with manifest.json
            # First generate a sweep to create proper structure
            base_path = Path(tmpdir) / "base.json"
            base_path.write_text('{"solver": "CG"}')
            sweep_dir = str(Path(tmpdir) / "sweep")
            sweep_cmd = [
                str(SCRIPTS / "sweep_generator.py"),
                "--base-config", str(base_path),
                "--params", "dt:0.001:0.01:3",
                "--method", "linspace",
                "--output-dir", sweep_dir,
                "--json",
            ]
            sweep_result = self.run_cmd(sweep_cmd)
            self.assertEqual(sweep_result.returncode, 0, sweep_result.stderr)

            # Now init campaign from the sweep directory
            cmd = [
                str(SCRIPTS / "campaign_manager.py"),
                "--action", "init",
                "--config-dir", sweep_dir,
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("campaign_id", data)
            self.assertEqual(data["total_jobs"], 3)

    def test_campaign_manager_status_no_campaign(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                str(SCRIPTS / "campaign_manager.py"),
                "--action", "status",
                "--config-dir", tmpdir,
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)

    # ---- job_tracker.py ----

    def test_job_tracker_no_campaign(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                str(SCRIPTS / "job_tracker.py"),
                "--campaign-dir", tmpdir,
                "--update",
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)

    # ---- result_aggregator.py ----

    def test_result_aggregator_no_campaign(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = [
                str(SCRIPTS / "result_aggregator.py"),
                "--campaign-dir", tmpdir,
                "--metric", "energy",
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
