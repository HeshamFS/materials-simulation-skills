"""Cross-skill integration tests.

Verify that output from one skill can be consumed by another,
testing the data pipeline between skills.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class TestCrossSkillIntegration(unittest.TestCase):
    def run_cmd(self, args, input_text=None):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            input=input_text,
        )

    def test_cfl_to_timestep_planner(self):
        """CFL recommended_dt feeds into timestep planner."""
        # Step 1: run CFL checker
        cfl_cmd = [
            str(ROOT / "skills" / "core-numerical" / "numerical-stability" / "scripts" / "cfl_checker.py"),
            "--dx", "0.01", "--dt", "0.001", "--velocity", "1.0",
            "--diffusivity", "0.01", "--json",
        ]
        cfl_result = self.run_cmd(cfl_cmd)
        self.assertEqual(cfl_result.returncode, 0, cfl_result.stderr)
        cfl_data = json.loads(cfl_result.stdout)
        recommended_dt = cfl_data["recommended_dt"]
        self.assertIsNotNone(recommended_dt)

        # Step 2: feed recommended_dt into timestep planner
        ts_cmd = [
            str(ROOT / "skills" / "core-numerical" / "time-stepping" / "scripts" / "timestep_planner.py"),
            "--dt-target", str(recommended_dt),
            "--dt-limit", str(recommended_dt * 2),
            "--safety", "0.9",
            "--ramp-steps", "3",
            "--preview-steps", "3",
            "--json",
        ]
        ts_result = self.run_cmd(ts_cmd)
        self.assertEqual(ts_result.returncode, 0, ts_result.stderr)
        ts_data = json.loads(ts_result.stdout)
        self.assertIn("results", ts_data)
        self.assertGreater(ts_data["results"]["dt_recommended"], 0)

    def test_stiffness_to_integrator_selector(self):
        """Stiffness detection result drives integrator selection."""
        # Step 1: run stiffness detector
        stiff_cmd = [
            str(ROOT / "skills" / "core-numerical" / "numerical-stability" / "scripts" / "stiffness_detector.py"),
            "--eigs=-1,-1000",
            "--json",
        ]
        stiff_result = self.run_cmd(stiff_cmd)
        self.assertEqual(stiff_result.returncode, 0, stiff_result.stderr)
        stiff_data = json.loads(stiff_result.stdout)
        is_stiff = stiff_data["results"]["stiff"]

        # Step 2: use stiffness result to select integrator
        int_cmd = [
            str(ROOT / "skills" / "core-numerical" / "numerical-integration" / "scripts" / "integrator_selector.py"),
            "--json",
        ]
        if is_stiff:
            int_cmd.append("--stiff")
            int_cmd.append("--implicit-allowed")
        int_result = self.run_cmd(int_cmd)
        self.assertEqual(int_result.returncode, 0, int_result.stderr)
        int_data = json.loads(int_result.stdout)
        self.assertIn("results", int_data)
        self.assertGreater(len(int_data["results"]["recommended"]), 0)

    def test_sweep_generator_produces_valid_configs(self):
        """Sweep generator produces valid config files with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: create base config with nested structure
            base_path = Path(tmpdir) / "base.json"
            base_path.write_text('{"solver": "CG", "tolerance": 1e-6, "nested": {"a": 1}}')
            sweep_dir = str(Path(tmpdir) / "sweep")

            # Step 2: generate sweep
            sweep_cmd = [
                str(ROOT / "skills" / "simulation-workflow" / "simulation-orchestrator" / "scripts" / "sweep_generator.py"),
                "--base-config", str(base_path),
                "--params", "dt:0.001:0.01:3",
                "--method", "linspace",
                "--output-dir", sweep_dir,
                "--json",
            ]
            sweep_result = self.run_cmd(sweep_cmd)
            self.assertEqual(sweep_result.returncode, 0, sweep_result.stderr)
            sweep_data = json.loads(sweep_result.stdout)
            self.assertEqual(sweep_data["total_runs"], 3)

            # Step 3: verify each config file is valid JSON with base keys preserved
            for config_name in sweep_data["configs"]:
                config_path = Path(sweep_dir) / config_name
                self.assertTrue(config_path.exists(), f"Config {config_name} not found")
                with open(config_path) as f:
                    config = json.load(f)
                self.assertEqual(config["solver"], "CG")
                self.assertIn("dt", config)
                # Verify nested structure preserved (deep copy fix)
                self.assertEqual(config["nested"]["a"], 1)

    def test_field_extractor_to_derived_quantities(self):
        """Field extraction output feeds derived quantities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a field data file
            field_path = Path(tmpdir) / "field.json"
            field_data = {
                "fields": {
                    "phi": {
                        "values": [[0.0, 0.25, 0.5], [0.75, 1.0, 0.8]]
                    }
                },
                "dx": 0.1,
                "dy": 0.1,
            }
            field_path.write_text(json.dumps(field_data))

            # Step 1: extract field
            ext_cmd = [
                str(ROOT / "skills" / "simulation-workflow" / "post-processing" / "scripts" / "field_extractor.py"),
                "--input", str(field_path),
                "--field", "phi",
                "--json",
            ]
            ext_result = self.run_cmd(ext_cmd)
            self.assertEqual(ext_result.returncode, 0, ext_result.stderr)

            # Step 2: compute derived quantities from the same file
            dq_cmd = [
                str(ROOT / "skills" / "simulation-workflow" / "post-processing" / "scripts" / "derived_quantities.py"),
                "--input", str(field_path),
                "--quantity", "volume_fraction",
                "--field", "phi",
                "--threshold", "0.5",
                "--json",
            ]
            dq_result = self.run_cmd(dq_cmd)
            self.assertEqual(dq_result.returncode, 0, dq_result.stderr)
            dq_data = json.loads(dq_result.stdout)
            self.assertIn("results", dq_data)
            self.assertIn("volume_fraction", dq_data["results"])
            self.assertGreater(dq_data["results"]["volume_fraction"], 0)

    def test_timing_to_bottleneck_pipeline(self):
        """Timing output consumed by bottleneck detector."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: create timing log
            log_path = Path(tmpdir) / "timing.log"
            log_path.write_text(
                "Phase: Assembly, Time: 15.00s\n"
                "Phase: Solve, Time: 70.00s\n"
                "Phase: I/O, Time: 5.00s\n"
                "Phase: PostProcess, Time: 10.00s\n"
            )

            # Step 2: run timing analyzer
            timing_cmd = [
                str(ROOT / "skills" / "simulation-workflow" / "performance-profiling" / "scripts" / "timing_analyzer.py"),
                "--log", str(log_path),
                "--json",
            ]
            timing_result = self.run_cmd(timing_cmd)
            self.assertEqual(timing_result.returncode, 0, timing_result.stderr)
            timing_data = json.loads(timing_result.stdout)

            # Step 3: create bottleneck input from timing
            bottleneck_path = Path(tmpdir) / "bottleneck_input.json"
            # Build timing_data format expected by bottleneck_detector
            phases = []
            if "results" in timing_data:
                agg = timing_data["results"].get("aggregated", timing_data["results"])
            else:
                agg = timing_data.get("aggregated", {})
            for phase_name, stats in agg.items():
                if isinstance(stats, dict) and "percentage" in stats:
                    phases.append({"name": phase_name, "percentage": stats["percentage"]})
            bottleneck_input = {"timing_data": {"phases": phases}}
            bottleneck_path.write_text(json.dumps(bottleneck_input))

            # Step 4: run bottleneck detector
            bn_cmd = [
                str(ROOT / "skills" / "simulation-workflow" / "performance-profiling" / "scripts" / "bottleneck_detector.py"),
                "--timing", str(bottleneck_path),
                "--json",
            ]
            bn_result = self.run_cmd(bn_cmd)
            self.assertEqual(bn_result.returncode, 0, bn_result.stderr)
            bn_data = json.loads(bn_result.stdout)
            self.assertIn("results", bn_data)
            self.assertIn("bottlenecks", bn_data["results"])
            self.assertIn("recommendations", bn_data["results"])


if __name__ == "__main__":
    unittest.main()
