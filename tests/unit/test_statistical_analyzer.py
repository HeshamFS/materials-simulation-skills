"""Unit tests for post-processing statistical_analyzer.py script."""

import json
import math
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestStatisticalAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "statistical_analyzer",
            "skills/simulation-workflow/post-processing/scripts/statistical_analyzer.py",
        )

    def test_flatten_field_1d(self):
        """Test flattening 1D field."""
        result = self.mod.flatten_field([1, 2, 3])
        self.assertEqual(result, [1.0, 2.0, 3.0])

    def test_flatten_field_2d(self):
        """Test flattening 2D field."""
        result = self.mod.flatten_field([[1, 2], [3, 4]])
        self.assertEqual(result, [1.0, 2.0, 3.0, 4.0])

    def test_compute_basic_statistics(self):
        """Test basic statistics computation."""
        values = [1, 2, 3, 4, 5]
        stats = self.mod.compute_basic_statistics(values)
        self.assertEqual(stats["count"], 5)
        self.assertEqual(stats["min"], 1)
        self.assertEqual(stats["max"], 5)
        self.assertEqual(stats["mean"], 3.0)
        self.assertEqual(stats["range"], 4)

    def test_compute_basic_statistics_empty(self):
        """Test statistics for empty list."""
        stats = self.mod.compute_basic_statistics([])
        self.assertEqual(stats["count"], 0)
        self.assertIsNone(stats["min"])
        self.assertIsNone(stats["mean"])

    def test_compute_basic_statistics_variance(self):
        """Test variance and std calculation."""
        values = [2, 4, 4, 4, 5, 5, 7, 9]
        stats = self.mod.compute_basic_statistics(values)
        self.assertAlmostEqual(stats["mean"], 5.0)
        # Sample variance should be 4.57 approx
        self.assertAlmostEqual(stats["variance"], 4.571, places=2)

    def test_compute_percentiles_default(self):
        """Test default percentiles computation."""
        values = list(range(1, 101))  # 1 to 100
        result = self.mod.compute_percentiles(values)
        self.assertEqual(result["p0"], 1)
        self.assertEqual(result["p100"], 100)
        self.assertAlmostEqual(result["p50"], 50.5, places=1)

    def test_compute_percentiles_custom(self):
        """Test custom percentiles."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = self.mod.compute_percentiles(values, [10, 90])
        self.assertIn("p10", result)
        self.assertIn("p90", result)

    def test_compute_percentiles_empty(self):
        """Test percentiles for empty list."""
        result = self.mod.compute_percentiles([])
        self.assertIsNone(result["p0"])

    def test_compute_median_odd(self):
        """Test median for odd-length list."""
        result = self.mod.compute_median([1, 2, 3, 4, 5])
        self.assertEqual(result, 3)

    def test_compute_median_even(self):
        """Test median for even-length list."""
        result = self.mod.compute_median([1, 2, 3, 4])
        self.assertEqual(result, 2.5)

    def test_compute_median_empty(self):
        """Test median for empty list."""
        result = self.mod.compute_median([])
        self.assertIsNone(result)

    def test_compute_skewness_symmetric(self):
        """Test skewness for symmetric distribution."""
        values = [1, 2, 3, 4, 5]
        stats = self.mod.compute_basic_statistics(values)
        skew = self.mod.compute_skewness(values, stats["mean"], stats["std"])
        self.assertAlmostEqual(skew, 0.0, places=5)

    def test_compute_skewness_right(self):
        """Test skewness for right-skewed distribution."""
        values = [1, 1, 1, 1, 1, 10]
        stats = self.mod.compute_basic_statistics(values)
        skew = self.mod.compute_skewness(values, stats["mean"], stats["std"])
        self.assertGreater(skew, 0)  # Right-skewed

    def test_compute_kurtosis_normal(self):
        """Test excess kurtosis (should be ~0 for normal-like)."""
        values = [1, 2, 3, 4, 5]
        stats = self.mod.compute_basic_statistics(values)
        kurt = self.mod.compute_kurtosis(values, stats["mean"], stats["std"])
        self.assertIsNotNone(kurt)
        # Uniform distribution has negative excess kurtosis
        self.assertLess(kurt, 0)

    def test_compute_histogram(self):
        """Test histogram computation."""
        values = [0.1, 0.2, 0.3, 0.8, 0.9]
        result = self.mod.compute_histogram(values, num_bins=5)
        self.assertEqual(len(result["counts"]), 5)
        self.assertEqual(sum(result["counts"]), 5)
        self.assertEqual(result["total"], 5)

    def test_compute_histogram_density(self):
        """Test histogram density normalization."""
        values = [0.0, 0.25, 0.5, 0.75, 1.0]
        result = self.mod.compute_histogram(values, num_bins=2, range_min=0, range_max=1)
        # Densities should integrate to approximately 1
        area = sum(d * result["bin_width"] for d in result["densities"])
        self.assertAlmostEqual(area, 1.0, places=5)

    def test_compute_histogram_custom_range(self):
        """Test histogram with custom range."""
        values = [0.5]
        result = self.mod.compute_histogram(values, num_bins=10, range_min=0, range_max=1)
        self.assertEqual(len(result["bin_edges"]), 11)

    def test_detect_distribution_type_uniform(self):
        """Test detecting uniform distribution."""
        values = list(range(100))
        hist = self.mod.compute_histogram(values, num_bins=10)
        result = self.mod.detect_distribution_type(values, hist)
        # Should detect as roughly uniform or monotonic

    def test_detect_distribution_type_bimodal(self):
        """Test detecting bimodal distribution."""
        values = [0.0] * 50 + [1.0] * 50
        hist = self.mod.compute_histogram(values, num_bins=10)
        result = self.mod.detect_distribution_type(values, hist)
        self.assertEqual(result["type"], "bimodal")

    def test_analyze_spatial_variation_2d(self):
        """Test spatial variation analysis for 2D field."""
        # Field with x-variation only
        field = [[1, 2, 3], [1, 2, 3]]
        result = self.mod.analyze_spatial_variation(field)
        self.assertEqual(result["dimensions"], 2)
        self.assertTrue(result["is_y_uniform"])

    def test_analyze_spatial_variation_1d(self):
        """Test spatial variation for 1D field."""
        field = [1, 2, 3, 4, 5]
        result = self.mod.analyze_spatial_variation(field)
        self.assertEqual(result["type"], "1D")


class TestStatisticalAnalyzerIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "statistical_analyzer",
            "skills/simulation-workflow/post-processing/scripts/statistical_analyzer.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_get_field_data_direct(self):
        """Test getting field data directly."""
        data = {"phi": [1, 2, 3]}
        result = self.mod.get_field_data(data, "phi")
        self.assertEqual(result, [1, 2, 3])

    def test_get_field_data_nested(self):
        """Test getting nested field data."""
        data = {"fields": {"phi": [1, 2, 3]}}
        result = self.mod.get_field_data(data, "phi")
        self.assertEqual(result, [1, 2, 3])

    def test_get_field_shape_nested(self):
        """Test getting shape of deeply nested field."""
        field = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
        shape = self.mod.get_field_shape(field)
        self.assertEqual(shape, [2, 2, 2])


if __name__ == "__main__":
    unittest.main()
