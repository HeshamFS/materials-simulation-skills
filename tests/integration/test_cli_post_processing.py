"""CLI integration tests for post-processing scripts.

Tests JSON output schema and error handling for all 7 post-processing scripts.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.integration._schema import assert_schema

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "simulation-workflow" / "post-processing" / "scripts"


def _make_field_file(tmpdir, data=None):
    """Create a temp field file and return its path."""
    if data is None:
        data = {
            "fields": {
                "phi": {"values": [[0.0, 0.25, 0.5], [0.75, 1.0, 0.8]]},
                "concentration": {"values": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]},
            },
            "dx": 0.1,
            "dy": 0.1,
        }
    path = Path(tmpdir) / "field_data.json"
    path.write_text(json.dumps(data))
    return str(path)


class TestCliPostProcessing(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    # ---- field_extractor.py ----

    def test_field_extractor_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = _make_field_file(tmpdir)
            cmd = [str(SCRIPTS / "field_extractor.py"), "--input", fpath, "--field", "phi", "--json"]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("field", data)
            self.assertIn("found", data)
            self.assertTrue(data["found"])

    def test_field_extractor_missing_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = _make_field_file(tmpdir)
            cmd = [str(SCRIPTS / "field_extractor.py"), "--input", fpath, "--field", "nonexistent", "--json"]
            result = self.run_cmd(cmd)
            # Script exits with error for missing field
            self.assertNotEqual(result.returncode, 0)

    # ---- time_series_analyzer.py ----

    def test_time_series_analyzer_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ts_path = Path(tmpdir) / "timeseries.json"
            ts_data = {"energy": [1.0, 0.9, 0.85, 0.82, 0.81, 0.805, 0.803, 0.802, 0.801, 0.8005]}
            ts_path.write_text(json.dumps(ts_data))
            cmd = [
                str(SCRIPTS / "time_series_analyzer.py"),
                "--input", str(ts_path), "--quantity", "energy",
                "--detect-steady-state", "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("statistics", data)
            self.assertIn("count", data["statistics"])

    # ---- profile_extractor.py ----

    def test_profile_extractor_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = _make_field_file(tmpdir)
            cmd = [
                str(SCRIPTS / "profile_extractor.py"),
                "--input", fpath, "--field", "phi", "--axis", "x", "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("values", data)
            self.assertIn("field", data)

    # ---- statistical_analyzer.py ----

    def test_statistical_analyzer_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = _make_field_file(tmpdir)
            cmd = [
                str(SCRIPTS / "statistical_analyzer.py"),
                "--input", fpath, "--field", "phi", "--histogram", "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("basic_statistics", data)
            self.assertIn("count", data["basic_statistics"])

    # ---- comparison_tool.py ----

    def test_comparison_tool_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sim_path = Path(tmpdir) / "sim.json"
            ref_path = Path(tmpdir) / "ref.json"
            sim_data = {"x": [0.0, 0.5, 1.0], "y": [0.1, 0.5, 0.9]}
            ref_data = {"x": [0.0, 0.5, 1.0], "y": [0.0, 0.5, 1.0]}
            sim_path.write_text(json.dumps(sim_data))
            ref_path.write_text(json.dumps(ref_data))
            cmd = [
                str(SCRIPTS / "comparison_tool.py"),
                "--simulation", str(sim_path), "--reference", str(ref_path),
                "--all-metrics", "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("metrics", data)

    # ---- report_generator.py ----

    def test_report_generator_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal simulation directory
            field_path = Path(tmpdir) / "field_0100.json"
            field_path.write_text(json.dumps({
                "phi": [[0.0, 0.5], [0.5, 1.0]],
                "dx": 0.1,
                "dy": 0.1,
                "time": 1.0,
                "timestep": 100,
            }))
            cmd = [
                str(SCRIPTS / "report_generator.py"),
                "--input", tmpdir, "--sections", "summary,files", "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("summary", data)

    # ---- derived_quantities.py ----

    def test_derived_quantities_volume_fraction_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = _make_field_file(tmpdir)
            cmd = [
                str(SCRIPTS / "derived_quantities.py"),
                "--input", fpath, "--quantity", "volume_fraction",
                "--field", "phi", "--threshold", "0.5", "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("inputs", data)
            self.assertIn("results", data)
            self.assertIn("volume_fraction", data["results"])
            self.assertIn("count", data["results"])

    def test_derived_quantities_gradient_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fpath = _make_field_file(tmpdir)
            cmd = [
                str(SCRIPTS / "derived_quantities.py"),
                "--input", fpath, "--quantity", "gradient_magnitude",
                "--field", "phi", "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(result.stdout)
            self.assertIn("inputs", data)
            self.assertIn("results", data)
            self.assertIn("max", data["results"])
            self.assertIn("mean", data["results"])

    def test_derived_quantities_missing_file(self):
        cmd = [
            str(SCRIPTS / "derived_quantities.py"),
            "--input", "/nonexistent/file.json",
            "--quantity", "volume_fraction", "--field", "phi",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
