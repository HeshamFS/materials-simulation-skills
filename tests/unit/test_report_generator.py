"""Unit tests for post-processing report_generator.py script."""

import json
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestReportGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "report_generator",
            "skills/simulation-workflow/post-processing/scripts/report_generator.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create a typical simulation output directory structure
        self.results_dir = os.path.join(self.temp_dir, "results")
        os.makedirs(self.results_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _create_field_file(self, filename, data):
        """Helper to create field file."""
        filepath = os.path.join(self.results_dir, filename)
        with open(filepath, "w") as f:
            json.dump(data, f)
        return filepath

    def test_find_data_files_empty(self):
        """Test finding files in empty directory."""
        result = self.mod.find_data_files(self.results_dir)
        self.assertEqual(result["field_files"], [])
        self.assertEqual(result["history_files"], [])

    def test_find_data_files_categorizes(self):
        """Test file categorization."""
        # Create various file types
        self._create_field_file("field_0001.json", {"phi": [1, 2]})
        self._create_field_file("history.json", {"time": [1, 2]})
        self._create_field_file("config.json", {"dt": 0.01})

        with open(os.path.join(self.results_dir, "sim.log"), "w") as f:
            f.write("log content")

        result = self.mod.find_data_files(self.results_dir)
        self.assertIn("field_0001.json", result["field_files"])
        self.assertIn("history.json", result["history_files"])
        self.assertIn("config.json", result["config_files"])
        self.assertIn("sim.log", result["log_files"])

    def test_find_data_files_sorts(self):
        """Test file sorting."""
        for i in [3, 1, 2]:
            self._create_field_file(f"field_{i:04d}.json", {"phi": [i]})

        result = self.mod.find_data_files(self.results_dir)
        self.assertEqual(result["field_files"],
                        ["field_0001.json", "field_0002.json", "field_0003.json"])

    def test_extract_simulation_info_with_config(self):
        """Test extracting simulation info from config."""
        self._create_field_file("config.json", {
            "dt": 0.01,
            "dx": 0.1,
            "dy": 0.1,
            "nx": 100,
            "ny": 100,
            "t_max": 1.0
        })

        files = self.mod.find_data_files(self.results_dir)
        result = self.mod.extract_simulation_info(self.results_dir, files)

        self.assertTrue(result["config_found"])
        self.assertEqual(result["grid"]["dx"], 0.1)
        self.assertEqual(result["time"]["dt"], 0.01)

    def test_extract_simulation_info_no_config(self):
        """Test extracting info without config."""
        files = {"config_files": [], "field_files": [], "history_files": []}
        result = self.mod.extract_simulation_info(self.results_dir, files)
        self.assertFalse(result["config_found"])

    def test_analyze_field_files_empty(self):
        """Test analyzing empty field list."""
        result = self.mod.analyze_field_files(self.results_dir, [])
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["first_file"])

    def test_analyze_field_files_with_data(self):
        """Test analyzing field files."""
        for i in range(3):
            self._create_field_file(f"field_{i:04d}.json", {
                "phi": [0.0, 0.5, 1.0],
                "timestep": i
            })

        files = [f"field_{i:04d}.json" for i in range(3)]
        result = self.mod.analyze_field_files(self.results_dir, files)

        self.assertEqual(result["count"], 3)
        self.assertEqual(result["first_file"], "field_0000.json")
        self.assertEqual(result["last_file"], "field_0002.json")
        self.assertEqual(result["timesteps"], [0, 1, 2])

    def test_analyze_field_files_final_state(self):
        """Test final state analysis."""
        self._create_field_file("field_final.json", {
            "phi": [0.0, 0.5, 1.0, 0.5, 0.0]
        })

        result = self.mod.analyze_field_files(self.results_dir, ["field_final.json"])

        self.assertIn("phi", result["final_state"])
        self.assertEqual(result["final_state"]["phi"]["min"], 0.0)
        self.assertEqual(result["final_state"]["phi"]["max"], 1.0)

    def test_analyze_history_files_empty(self):
        """Test analyzing empty history list."""
        result = self.mod.analyze_history_files(self.results_dir, [])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["quantities"], [])

    def test_analyze_history_files_with_data(self):
        """Test analyzing history files."""
        self._create_field_file("history.json", {
            "time": [0, 1, 2, 3, 4],
            "energy": [1.0, 0.9, 0.8, 0.7, 0.6],
            "residual": [1e-1, 1e-2, 1e-3, 1e-4, 1e-5]
        })

        result = self.mod.analyze_history_files(self.results_dir, ["history.json"])

        self.assertIn("time", result["quantities"])
        self.assertIn("energy", result["quantities"])
        self.assertIn("energy", result["convergence"])
        self.assertEqual(result["convergence"]["energy"]["initial"], 1.0)
        self.assertEqual(result["convergence"]["energy"]["final"], 0.6)

    def test_analyze_history_files_nested(self):
        """Test analyzing history files with nested structure."""
        self._create_field_file("history.json", {
            "history": {
                "time": [0, 1, 2],
                "residual": [1e-1, 1e-2, 1e-3]
            }
        })

        result = self.mod.analyze_history_files(self.results_dir, ["history.json"])
        self.assertIn("residual", result["quantities"])

    def test_flatten_list_1d(self):
        """Test flattening 1D list."""
        result = self.mod.flatten_list([1, 2, 3])
        self.assertEqual(result, [1.0, 2.0, 3.0])

    def test_flatten_list_2d(self):
        """Test flattening 2D list."""
        result = self.mod.flatten_list([[1, 2], [3, 4]])
        self.assertEqual(result, [1.0, 2.0, 3.0, 4.0])

    def test_generate_summary_section(self):
        """Test summary section generation."""
        files = {
            "field_files": ["f1.json", "f2.json"],
            "history_files": ["h1.json"],
            "config_files": [],
            "log_files": [],
            "other_files": []
        }
        sim_info = {"config_found": False}

        result = self.mod.generate_summary_section(self.results_dir, files, sim_info)

        self.assertIn("directory", result)
        self.assertIn("files_found", result)
        self.assertEqual(result["files_found"]["field_files"], 2)
        self.assertEqual(result["files_found"]["history_files"], 1)

    def test_generate_statistics_section(self):
        """Test statistics section generation."""
        field_analysis = {
            "count": 5,
            "timesteps": [0, 1, 2, 3, 4],
            "final_state": {
                "phi": {"min": 0.0, "max": 1.0, "mean": 0.5}
            }
        }

        result = self.mod.generate_statistics_section(field_analysis)

        self.assertEqual(result["field_files_analyzed"], 5)
        self.assertIn("phi", result["final_state_fields"])

    def test_generate_convergence_section(self):
        """Test convergence section generation."""
        history_analysis = {
            "quantities": ["time", "energy", "residual"],
            "convergence": {
                "energy": {"initial": 1.0, "final": 0.1, "converged": True},
                "residual": {"initial": 1.0, "final": 1e-6, "converged": True}
            }
        }

        result = self.mod.generate_convergence_section(history_analysis)

        self.assertEqual(result["overall_assessment"], "converged")
        self.assertIn("energy", result["analysis"])

    def test_generate_convergence_section_not_converged(self):
        """Test convergence section when not converged."""
        history_analysis = {
            "quantities": ["residual"],
            "convergence": {
                "residual": {"converged": False}
            }
        }

        result = self.mod.generate_convergence_section(history_analysis)
        self.assertEqual(result["overall_assessment"], "not_converged")

    def test_generate_validation_section_pass(self):
        """Test validation section when all pass."""
        field_analysis = {
            "final_state": {
                "phi": {"min": 0.0, "max": 1.0, "mean": 0.5}
            }
        }
        history_analysis = {
            "convergence": {}
        }

        result = self.mod.generate_validation_section(field_analysis, history_analysis)

        self.assertTrue(result["passed"])
        self.assertEqual(len(result["warnings"]), 0)

    def test_generate_validation_section_nan(self):
        """Test validation detects NaN values."""
        field_analysis = {
            "final_state": {
                "phi": {"min": float('nan'), "max": 1.0}
            }
        }
        history_analysis = {"convergence": {}}

        result = self.mod.generate_validation_section(field_analysis, history_analysis)

        self.assertFalse(result["passed"])
        self.assertTrue(any("NaN" in w for w in result["warnings"]))

    def test_generate_report_all_sections(self):
        """Test generating full report."""
        # Create minimal test data
        self._create_field_file("config.json", {"dt": 0.01})
        self._create_field_file("field_0001.json", {"phi": [0.5]})
        self._create_field_file("history.json", {"energy": [1.0, 0.9]})

        result = self.mod.generate_report(self.results_dir, ["all"])

        self.assertIn("summary", result)
        self.assertIn("statistics", result)
        self.assertIn("convergence", result)
        self.assertIn("validation", result)
        self.assertIn("files", result)

    def test_generate_report_specific_sections(self):
        """Test generating report with specific sections."""
        result = self.mod.generate_report(self.results_dir, ["summary"])

        self.assertIn("summary", result)
        self.assertNotIn("statistics", result)

    def test_format_report_text(self):
        """Test text formatting of report."""
        report = {
            "summary": {
                "directory": "/test",
                "generated_at": "2024-01-01T00:00:00",
                "files_found": {"total": 5, "field_files": 3, "history_files": 1, "config_files": 1}
            }
        }

        text = self.mod.format_report_text(report)

        self.assertIn("SIMULATION ANALYSIS REPORT", text)
        self.assertIn("/test", text)
        self.assertIn("Files found: 5", text)


if __name__ == "__main__":
    unittest.main()
