import json
import os
import tempfile
import unittest

from tests.unit._utils import load_module


class TestPreflightChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "preflight_checker",
            "skills/simulation-workflow/simulation-validator/scripts/preflight_checker.py",
        )

    def test_missing_required_parameter(self):
        """Test missing required parameter causes BLOCK."""
        report = self.mod.preflight_check(
            config={},
            required=["dt"],
            ranges={},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertTrue(any("dt" in b for b in report["blockers"]))

    def test_multiple_missing_required(self):
        """Test multiple missing required parameters."""
        report = self.mod.preflight_check(
            config={"dx": 0.1},
            required=["dt", "velocity", "diffusivity"],
            ranges={},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertEqual(report["status"], "BLOCK")
        self.assertEqual(len(report["blockers"]), 3)

    def test_all_required_present(self):
        """Test all required parameters present passes."""
        report = self.mod.preflight_check(
            config={"dt": 0.01, "dx": 0.1},
            required=["dt", "dx"],
            ranges={},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertNotEqual(report["status"], "BLOCK")

    def test_range_check_out_of_range(self):
        """Test out-of-range parameter causes BLOCK."""
        report = self.mod.preflight_check(
            config={"dt": 2.0},
            required=[],
            ranges={"dt": (0.0, 1.0)},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertTrue(any("dt out of range" in b for b in report["blockers"]))

    def test_range_check_in_range(self):
        """Test in-range parameter passes."""
        report = self.mod.preflight_check(
            config={"dt": 0.5},
            required=[],
            ranges={"dt": (0.0, 1.0)},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertNotIn("dt", " ".join(report["blockers"]))

    def test_range_check_boundary_values(self):
        """Test boundary values are within range."""
        report = self.mod.preflight_check(
            config={"dt": 0.0, "dx": 1.0},
            required=[],
            ranges={"dt": (0.0, 1.0), "dx": (0.0, 1.0)},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertEqual(len(report["blockers"]), 0)

    def test_non_numeric_value(self):
        """Test non-numeric value for range check causes BLOCK."""
        report = self.mod.preflight_check(
            config={"dt": "not_a_number"},
            required=[],
            ranges={"dt": (0.0, 1.0)},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertTrue(any("Non-numeric" in b for b in report["blockers"]))

    def test_output_dir_not_exists_warning(self):
        """Test non-existent output dir causes warning."""
        report = self.mod.preflight_check(
            config={},
            required=[],
            ranges={},
            output_dir="/nonexistent/path/to/dir",
            min_free_gb=0.0,
        )
        self.assertTrue(any("does not exist" in w for w in report["warnings"]))

    def test_no_output_dir_warning(self):
        """Test missing output dir causes warning."""
        report = self.mod.preflight_check(
            config={},
            required=[],
            ranges={},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertTrue(any("No output directory" in w for w in report["warnings"]))

    def test_material_source_warning(self):
        """Test missing material source causes warning."""
        report = self.mod.preflight_check(
            config={"dt": 0.01},
            required=[],
            ranges={},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertTrue(any("Material" in w or "material" in w for w in report["warnings"]))

    def test_material_source_present(self):
        """Test present material source doesn't cause warning."""
        report = self.mod.preflight_check(
            config={"dt": 0.01, "material_source": "literature"},
            required=[],
            ranges={},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertFalse(any("material" in w.lower() for w in report["warnings"]))

    def test_pass_status(self):
        """Test PASS status when no issues."""
        with tempfile.TemporaryDirectory() as tmpdir:
            report = self.mod.preflight_check(
                config={"dt": 0.01, "material_source": "test"},
                required=["dt"],
                ranges={"dt": (0.0, 1.0)},
                output_dir=tmpdir,
                min_free_gb=0.0,
            )
            self.assertEqual(report["status"], "PASS")

    def test_warn_status(self):
        """Test WARN status with only warnings."""
        report = self.mod.preflight_check(
            config={"dt": 0.01},
            required=[],
            ranges={},
            output_dir=None,
            min_free_gb=0.0,
        )
        # Should have warnings but no blockers
        if not report["blockers"] and report["warnings"]:
            self.assertEqual(report["status"], "WARN")

    def test_load_config_json(self):
        """Test loading JSON config file."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump({"dt": 1.0, "dx": 0.1}, handle)
            path = handle.name
        try:
            data = self.mod.load_config(path)
            self.assertEqual(data["dt"], 1.0)
            self.assertEqual(data["dx"], 0.1)
        finally:
            os.unlink(path)

    def test_load_config_not_found(self):
        """Test loading non-existent config raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.load_config("/nonexistent/config.json")
        self.assertIn("not found", str(ctx.exception))

    def test_parse_list_empty(self):
        """Test parse_list with empty string."""
        result = self.mod.parse_list("")
        self.assertEqual(result, [])

    def test_parse_list_multiple(self):
        """Test parse_list with multiple items."""
        result = self.mod.parse_list("a, b, c")
        self.assertEqual(result, ["a", "b", "c"])

    def test_parse_ranges_valid(self):
        """Test parse_ranges with valid input."""
        result = self.mod.parse_ranges("dt:0.0:1.0, dx:0.01:0.5")
        self.assertEqual(result["dt"], (0.0, 1.0))
        self.assertEqual(result["dx"], (0.01, 0.5))

    def test_parse_ranges_empty(self):
        """Test parse_ranges with empty string."""
        result = self.mod.parse_ranges("")
        self.assertEqual(result, {})

    def test_parameters_nested(self):
        """Test required params in nested 'parameters' dict."""
        report = self.mod.preflight_check(
            config={"parameters": {"dt": 0.01}},
            required=["dt"],
            ranges={},
            output_dir=None,
            min_free_gb=0.0,
        )
        self.assertNotEqual(report["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
