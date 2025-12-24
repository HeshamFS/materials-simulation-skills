"""Unit tests for post-processing comparison_tool.py script."""

import json
import math
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestComparisonTool(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "comparison_tool",
            "skills/simulation-workflow/post-processing/scripts/comparison_tool.py",
        )

    def test_compute_l1_error_zero(self):
        """Test L1 error for identical data."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 3.0]
        result = self.mod.compute_l1_error(sim, ref)
        self.assertEqual(result, 0.0)

    def test_compute_l1_error_nonzero(self):
        """Test L1 error for different data."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.1, 2.1, 3.1]
        result = self.mod.compute_l1_error(sim, ref)
        self.assertGreater(result, 0)

    def test_compute_l2_error_zero(self):
        """Test L2 error for identical data."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 3.0]
        result = self.mod.compute_l2_error(sim, ref)
        self.assertEqual(result, 0.0)

    def test_compute_l2_error_nonzero(self):
        """Test L2 error for different data."""
        sim = [1.0, 2.0, 3.0]
        ref = [2.0, 3.0, 4.0]
        result = self.mod.compute_l2_error(sim, ref)
        self.assertGreater(result, 0)

    def test_compute_linf_error_zero(self):
        """Test L-inf error for identical data."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 3.0]
        result = self.mod.compute_linf_error(sim, ref)
        self.assertEqual(result, 0.0)

    def test_compute_linf_error_max(self):
        """Test L-inf error captures maximum."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 6.0]  # Max diff is 3 at index 2
        result = self.mod.compute_linf_error(sim, ref)
        self.assertEqual(result, 0.5)  # 3/6

    def test_compute_rmse_zero(self):
        """Test RMSE for identical data."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 3.0]
        result = self.mod.compute_rmse(sim, ref)
        self.assertEqual(result, 0.0)

    def test_compute_rmse_nonzero(self):
        """Test RMSE computation."""
        sim = [1.0, 2.0, 3.0]
        ref = [2.0, 3.0, 4.0]  # Each diff is 1
        result = self.mod.compute_rmse(sim, ref)
        self.assertEqual(result, 1.0)

    def test_compute_mae_zero(self):
        """Test MAE for identical data."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 3.0]
        result = self.mod.compute_mae(sim, ref)
        self.assertEqual(result, 0.0)

    def test_compute_mae_nonzero(self):
        """Test MAE computation."""
        sim = [1.0, 2.0, 3.0]
        ref = [2.0, 4.0, 6.0]
        result = self.mod.compute_mae(sim, ref)
        self.assertEqual(result, 2.0)  # Average of [1, 2, 3]

    def test_compute_max_difference(self):
        """Test maximum difference computation."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 10.0]
        result = self.mod.compute_max_difference(sim, ref)
        self.assertEqual(result, 7.0)

    def test_compute_correlation_perfect(self):
        """Test correlation for perfectly correlated data."""
        sim = [1.0, 2.0, 3.0, 4.0, 5.0]
        ref = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = self.mod.compute_correlation(sim, ref)
        self.assertAlmostEqual(result, 1.0)

    def test_compute_correlation_negative(self):
        """Test correlation for negatively correlated data."""
        sim = [1.0, 2.0, 3.0, 4.0, 5.0]
        ref = [5.0, 4.0, 3.0, 2.0, 1.0]
        result = self.mod.compute_correlation(sim, ref)
        self.assertAlmostEqual(result, -1.0)

    def test_compute_correlation_scaled(self):
        """Test correlation for scaled data."""
        sim = [1.0, 2.0, 3.0, 4.0, 5.0]
        ref = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = self.mod.compute_correlation(sim, ref)
        self.assertAlmostEqual(result, 1.0)

    def test_compute_r_squared_perfect(self):
        """Test R² for perfect prediction."""
        sim = [1.0, 2.0, 3.0, 4.0, 5.0]
        ref = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = self.mod.compute_r_squared(sim, ref)
        self.assertAlmostEqual(result, 1.0)

    def test_compute_r_squared_zero(self):
        """Test R² for mean prediction."""
        sim = [3.0, 3.0, 3.0, 3.0, 3.0]  # Constant mean
        ref = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = self.mod.compute_r_squared(sim, ref)
        self.assertAlmostEqual(result, 0.0)

    def test_interpolate_1d_exact(self):
        """Test interpolation at exact points."""
        x_new = [0.0, 1.0, 2.0]
        x_old = [0.0, 1.0, 2.0]
        y_old = [0.0, 1.0, 2.0]
        result = self.mod.interpolate_1d(x_new, x_old, y_old)
        self.assertEqual(result, [0.0, 1.0, 2.0])

    def test_interpolate_1d_intermediate(self):
        """Test interpolation at intermediate points."""
        x_new = [0.5]
        x_old = [0.0, 1.0]
        y_old = [0.0, 2.0]
        result = self.mod.interpolate_1d(x_new, x_old, y_old)
        self.assertEqual(result, [1.0])

    def test_interpolate_1d_outside(self):
        """Test interpolation outside range."""
        x_new = [-1.0, 3.0]
        x_old = [0.0, 1.0, 2.0]
        y_old = [0.0, 1.0, 2.0]
        result = self.mod.interpolate_1d(x_new, x_old, y_old)
        self.assertEqual(result[0], 0.0)  # Clamp to first
        self.assertEqual(result[1], 2.0)  # Clamp to last

    def test_interpret_error_excellent(self):
        """Test error interpretation: excellent."""
        result = self.mod.interpret_error("l2_error", 0.005)
        self.assertEqual(result, "excellent")

    def test_interpret_error_good(self):
        """Test error interpretation: good."""
        result = self.mod.interpret_error("l2_error", 0.03)
        self.assertEqual(result, "good")

    def test_interpret_error_moderate(self):
        """Test error interpretation: moderate."""
        result = self.mod.interpret_error("l2_error", 0.07)
        self.assertEqual(result, "moderate")

    def test_interpret_error_poor(self):
        """Test error interpretation: poor."""
        result = self.mod.interpret_error("l2_error", 0.15)
        self.assertEqual(result, "poor")

    def test_interpret_correlation_excellent(self):
        """Test correlation interpretation: excellent."""
        result = self.mod.interpret_error("correlation", 0.995)
        self.assertEqual(result, "excellent")

    def test_compare_data_multiple_metrics(self):
        """Test comparing with multiple metrics."""
        sim = [1.0, 2.0, 3.0]
        ref = [1.0, 2.0, 3.0]
        metrics = ["l1_error", "l2_error", "rmse"]
        result = self.mod.compare_data(sim, ref, metrics)
        self.assertIn("l1_error", result)
        self.assertIn("l2_error", result)
        self.assertIn("rmse", result)
        self.assertEqual(result["l1_error"]["value"], 0.0)

    def test_flatten_list(self):
        """Test flattening nested list."""
        result = self.mod.flatten_list([[1, 2], [3, 4]])
        self.assertEqual(result, [1.0, 2.0, 3.0, 4.0])


class TestComparisonToolIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "comparison_tool",
            "skills/simulation-workflow/post-processing/scripts/comparison_tool.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_json_file(self):
        """Test loading JSON file."""
        filepath = os.path.join(self.temp_dir, "test.json")
        data = {"values": [1, 2, 3]}
        with open(filepath, "w") as f:
            json.dump(data, f)

        result = self.mod.load_data(filepath)
        self.assertEqual(result["values"], [1, 2, 3])

    def test_load_csv_file(self):
        """Test loading CSV file."""
        filepath = os.path.join(self.temp_dir, "test.csv")
        with open(filepath, "w") as f:
            f.write("x,y\n")
            f.write("1,2\n")
            f.write("3,4\n")

        result = self.mod.load_data(filepath)
        self.assertEqual(result["x"], [1.0, 3.0])
        self.assertEqual(result["y"], [2.0, 4.0])

    def test_extract_values_direct(self):
        """Test extracting values directly."""
        data = {"values": [1.0, 2.0, 3.0]}
        values, coords = self.mod.extract_values(data)
        self.assertEqual(values, [1.0, 2.0, 3.0])

    def test_extract_values_with_coords(self):
        """Test extracting values with coordinates."""
        data = {"x": [0, 1, 2], "y": [1.0, 2.0, 3.0]}
        values, coords = self.mod.extract_values(data)
        self.assertEqual(coords, [0, 1, 2])

    def test_extract_values_field(self):
        """Test extracting specific field."""
        data = {"phi": [1.0, 2.0], "psi": [3.0, 4.0]}
        values, coords = self.mod.extract_values(data, field="phi")
        self.assertEqual(values, [1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
