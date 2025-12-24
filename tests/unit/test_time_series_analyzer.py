"""Unit tests for post-processing time_series_analyzer.py script."""

import json
import math
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestTimeSeriesAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "time_series_analyzer",
            "skills/simulation-workflow/post-processing/scripts/time_series_analyzer.py",
        )

    def test_compute_statistics(self):
        """Test basic statistics computation."""
        values = [1, 2, 3, 4, 5]
        stats = self.mod.compute_statistics(values)
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["min"], 1)
        self.assertEqual(stats["max"], 5)
        self.assertEqual(stats["mean"], 3.0)
        self.assertEqual(stats["first"], 1)
        self.assertEqual(stats["last"], 5)

    def test_compute_statistics_empty(self):
        """Test statistics for empty list."""
        stats = self.mod.compute_statistics([])
        self.assertEqual(stats["count"], 0)
        self.assertIsNone(stats["min"])
        self.assertIsNone(stats["mean"])

    def test_compute_statistics_single(self):
        """Test statistics for single value."""
        stats = self.mod.compute_statistics([5.0])
        self.assertEqual(stats["count"], 1)
        self.assertEqual(stats["mean"], 5.0)
        self.assertEqual(stats["std"], 0.0)

    def test_compute_statistics_std(self):
        """Test standard deviation calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = self.mod.compute_statistics(values)
        # Sample std of [1,2,3,4,5] is sqrt(2.5) ≈ 1.58
        self.assertAlmostEqual(stats["std"], 1.5811, places=3)

    def test_compute_moving_average(self):
        """Test moving average computation."""
        values = [1, 2, 3, 4, 5]
        result = self.mod.compute_moving_average(values, 3)
        self.assertEqual(len(result), 5)
        # Window of 3: first value is just itself, then 2-element avg, then 3-element avg
        self.assertEqual(result[0], 1.0)
        self.assertEqual(result[1], 1.5)
        self.assertEqual(result[2], 2.0)

    def test_compute_moving_average_large_window(self):
        """Test moving average with window larger than data."""
        values = [1, 2, 3]
        result = self.mod.compute_moving_average(values, 10)
        self.assertEqual(len(result), 3)

    def test_compute_rate_of_change(self):
        """Test rate of change computation."""
        values = [0, 1, 3, 6, 10]
        rates = self.mod.compute_rate_of_change(values)
        self.assertEqual(len(rates), 4)
        self.assertEqual(rates[0], 1)  # 1 - 0
        self.assertEqual(rates[1], 2)  # 3 - 1
        self.assertEqual(rates[2], 3)  # 6 - 3
        self.assertEqual(rates[3], 4)  # 10 - 6

    def test_compute_rate_of_change_with_times(self):
        """Test rate of change with time axis."""
        values = [0, 2, 6]
        times = [0, 1, 2]
        rates = self.mod.compute_rate_of_change(values, times)
        self.assertEqual(rates[0], 2.0)  # (2-0)/(1-0)
        self.assertEqual(rates[1], 4.0)  # (6-2)/(2-1)

    def test_detect_monotonicity_increasing(self):
        """Test monotonicity detection for increasing sequence."""
        values = [1, 2, 3, 4, 5]
        result = self.mod.detect_monotonicity(values)
        self.assertTrue(result["monotonic"])
        self.assertEqual(result["direction"], "increasing")

    def test_detect_monotonicity_decreasing(self):
        """Test monotonicity detection for decreasing sequence."""
        values = [5, 4, 3, 2, 1]
        result = self.mod.detect_monotonicity(values)
        self.assertTrue(result["monotonic"])
        self.assertEqual(result["direction"], "decreasing")

    def test_detect_monotonicity_non_monotonic(self):
        """Test monotonicity detection for non-monotonic sequence."""
        values = [1, 3, 2, 4, 3]
        result = self.mod.detect_monotonicity(values)
        self.assertFalse(result["monotonic"])
        self.assertGreater(result["violations"], 0)

    def test_detect_steady_state_reached(self):
        """Test steady state detection when reached."""
        values = [1.0, 0.5, 0.1, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001]
        result = self.mod.detect_steady_state(values, tolerance=0.01, window=5)
        self.assertTrue(result["reached"])

    def test_detect_steady_state_not_reached(self):
        """Test steady state detection when not reached."""
        values = [1.0, 0.5, 0.25, 0.125, 0.0625]
        result = self.mod.detect_steady_state(values, tolerance=0.001, window=3)
        self.assertFalse(result["reached"])

    def test_detect_steady_state_insufficient_data(self):
        """Test steady state detection with insufficient data."""
        values = [1.0, 2.0]
        result = self.mod.detect_steady_state(values, window=10)
        self.assertFalse(result["reached"])
        self.assertIn("Not enough", result["reason"])

    def test_detect_oscillations_none(self):
        """Test oscillation detection with no oscillations."""
        values = [1, 2, 3, 4, 5]
        result = self.mod.detect_oscillations(values)
        self.assertFalse(result["oscillating"])

    def test_detect_oscillations_present(self):
        """Test oscillation detection with oscillations."""
        # Sine wave crosses zero frequently
        values = [math.sin(i * 0.5) for i in range(20)]
        result = self.mod.detect_oscillations(values)
        self.assertGreater(result["zero_crossings"], 0)

    def test_compute_convergence_rate_linear(self):
        """Test convergence rate estimation for linear convergence."""
        # Geometric sequence: 1, 0.5, 0.25, 0.125, ...
        values = [1.0 * (0.5 ** i) for i in range(10)]
        result = self.mod.compute_convergence_rate(values, target=0)
        self.assertIsNotNone(result["rate"])
        self.assertLess(result["rate"], 1.0)

    def test_compute_convergence_rate_stalled(self):
        """Test convergence rate estimation for stalled convergence."""
        values = [1.0] * 10  # No change
        result = self.mod.compute_convergence_rate(values)
        # Should recognize as stalled or unknown

    def test_extract_quantity(self):
        """Test extracting quantity from data."""
        data = {"energy": [1.0, 0.9, 0.8, 0.7]}
        values = self.mod.extract_quantity(data, "energy")
        self.assertEqual(values, [1.0, 0.9, 0.8, 0.7])

    def test_extract_quantity_nested(self):
        """Test extracting nested quantity."""
        data = {"results": {"energy": [1.0, 0.9]}}
        values = self.mod.extract_quantity(data, "results.energy")
        self.assertEqual(values, [1.0, 0.9])

    def test_extract_quantity_not_found(self):
        """Test extracting non-existent quantity."""
        data = {"energy": [1.0, 0.9]}
        values = self.mod.extract_quantity(data, "missing")
        self.assertIsNone(values)

    def test_get_time_axis(self):
        """Test extracting time axis."""
        data = {"time": [0, 1, 2], "energy": [1.0, 0.9, 0.8]}
        times = self.mod.get_time_axis(data)
        self.assertEqual(times, [0, 1, 2])


class TestTimeSeriesAnalyzerIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "time_series_analyzer",
            "skills/simulation-workflow/post-processing/scripts/time_series_analyzer.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_json_time_series(self):
        """Test loading JSON time series file."""
        filepath = os.path.join(self.temp_dir, "history.json")
        data = {"time": [0, 1, 2], "energy": [1.0, 0.9, 0.8]}
        with open(filepath, "w") as f:
            json.dump(data, f)

        result = self.mod.load_time_series(filepath)
        self.assertIn("energy", result)

    def test_load_json_with_history_key(self):
        """Test loading JSON with nested history key."""
        filepath = os.path.join(self.temp_dir, "history.json")
        data = {"history": {"time": [0, 1], "energy": [1.0, 0.9]}}
        with open(filepath, "w") as f:
            json.dump(data, f)

        result = self.mod.load_time_series(filepath)
        self.assertIn("energy", result)

    def test_load_csv_time_series(self):
        """Test loading CSV time series file."""
        filepath = os.path.join(self.temp_dir, "history.csv")
        with open(filepath, "w") as f:
            f.write("time,energy,mass\n")
            f.write("0,1.0,1.0\n")
            f.write("1,0.9,1.0\n")

        result = self.mod.load_time_series(filepath)
        self.assertIn("energy", result)
        self.assertEqual(len(result["energy"]), 2)


if __name__ == "__main__":
    unittest.main()
