"""Unit tests for post-processing profile_extractor.py script."""

import json
import math
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestProfileExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "profile_extractor",
            "skills/simulation-workflow/post-processing/scripts/profile_extractor.py",
        )

    def test_get_field_shape_1d(self):
        """Test getting shape of 1D field."""
        field = [1, 2, 3, 4, 5]
        shape = self.mod.get_field_shape(field)
        self.assertEqual(shape, [5])

    def test_get_field_shape_2d(self):
        """Test getting shape of 2D field."""
        field = [[1, 2, 3], [4, 5, 6]]
        shape = self.mod.get_field_shape(field)
        self.assertEqual(shape, [2, 3])

    def test_interpolate_1d_interior(self):
        """Test 1D interpolation at interior point."""
        values = [0.0, 1.0, 2.0, 3.0, 4.0]
        result = self.mod.interpolate_1d(values, 0.5)
        self.assertEqual(result, 2.0)  # Middle of array

    def test_interpolate_1d_boundaries(self):
        """Test 1D interpolation at boundaries."""
        values = [0.0, 1.0, 2.0]
        self.assertEqual(self.mod.interpolate_1d(values, 0.0), 0.0)
        self.assertEqual(self.mod.interpolate_1d(values, 1.0), 2.0)

    def test_interpolate_1d_outside(self):
        """Test 1D interpolation outside range."""
        values = [0.0, 1.0, 2.0]
        self.assertEqual(self.mod.interpolate_1d(values, -0.5), 0.0)  # Clamp to first
        self.assertEqual(self.mod.interpolate_1d(values, 1.5), 2.0)  # Clamp to last

    def test_get_value_2d(self):
        """Test getting value from 2D field."""
        field = [[1, 2, 3], [4, 5, 6]]
        self.assertEqual(self.mod.get_value_2d(field, 0, 0), 1)
        self.assertEqual(self.mod.get_value_2d(field, 1, 0), 2)
        self.assertEqual(self.mod.get_value_2d(field, 0, 1), 4)

    def test_get_value_2d_bounds(self):
        """Test getting value with bounds checking."""
        field = [[1, 2], [3, 4]]
        # Out of bounds should clamp
        self.assertEqual(self.mod.get_value_2d(field, 10, 0), 2)  # Clamp x
        self.assertEqual(self.mod.get_value_2d(field, 0, 10), 3)  # Clamp y

    def test_interpolate_2d(self):
        """Test bilinear interpolation."""
        field = [[0.0, 1.0], [2.0, 3.0]]
        # Center should be average of all four
        result = self.mod.interpolate_2d(field, 0.5, 0.5)
        self.assertAlmostEqual(result, 1.5, places=5)

    def test_interpolate_2d_corners(self):
        """Test interpolation at corners."""
        field = [[0.0, 1.0], [2.0, 3.0]]
        self.assertAlmostEqual(self.mod.interpolate_2d(field, 0.0, 0.0), 0.0)
        self.assertAlmostEqual(self.mod.interpolate_2d(field, 1.0, 0.0), 1.0)
        self.assertAlmostEqual(self.mod.interpolate_2d(field, 0.0, 1.0), 2.0)
        self.assertAlmostEqual(self.mod.interpolate_2d(field, 1.0, 1.0), 3.0)

    def test_extract_axis_profile_x(self):
        """Test extracting profile along x-axis."""
        field = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10]]
        result = self.mod.extract_axis_profile(field, "x", 0.0, {})
        self.assertEqual(result["values"], [1, 2, 3, 4, 5])
        self.assertEqual(result["axis"], "x")
        self.assertEqual(result["points"], 5)

    def test_extract_axis_profile_y(self):
        """Test extracting profile along y-axis."""
        field = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        result = self.mod.extract_axis_profile(field, "y", 0.5, {})
        self.assertEqual(result["axis"], "y")
        self.assertEqual(result["points"], 3)
        self.assertEqual(result["values"], [2, 5, 8])

    def test_extract_line_profile_diagonal(self):
        """Test extracting diagonal line profile."""
        field = [[0.0, 0.5, 1.0], [0.5, 1.0, 1.5], [1.0, 1.5, 2.0]]
        result = self.mod.extract_line_profile(
            field, (0, 0), (1, 1), 3, {}
        )
        self.assertEqual(result["points"], 3)
        # Diagonal from (0,0) to (1,1)
        self.assertAlmostEqual(result["values"][0], 0.0, places=4)
        self.assertAlmostEqual(result["values"][-1], 2.0, places=4)

    def test_extract_line_profile_horizontal(self):
        """Test extracting horizontal line profile."""
        field = [[0, 1, 2], [3, 4, 5]]
        result = self.mod.extract_line_profile(
            field, (0, 0), (1, 0), 5, {}
        )
        self.assertEqual(result["points"], 5)
        self.assertAlmostEqual(result["values"][0], 0.0)
        self.assertAlmostEqual(result["values"][-1], 2.0)

    def test_parse_point_2d(self):
        """Test parsing 2D point string."""
        result = self.mod.parse_point("0.5, 0.5")
        self.assertEqual(result, (0.5, 0.5))

    def test_parse_point_3d(self):
        """Test parsing 3D point string."""
        result = self.mod.parse_point("0.1, 0.2, 0.3")
        self.assertEqual(result, (0.1, 0.2, 0.3))

    def test_compute_profile_statistics(self):
        """Test computing profile statistics."""
        values = [1, 2, 3, 4, 5]
        stats = self.mod.compute_profile_statistics(values)
        self.assertEqual(stats["min"], 1)
        self.assertEqual(stats["max"], 5)
        self.assertEqual(stats["mean"], 3.0)
        self.assertEqual(stats["range"], 4)

    def test_compute_profile_statistics_empty(self):
        """Test statistics for empty profile."""
        stats = self.mod.compute_profile_statistics([])
        self.assertEqual(stats, {})

    def test_detect_interface(self):
        """Test interface detection."""
        values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        coords = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        result = self.mod.detect_interface(values, coords, threshold=0.5)
        self.assertEqual(result["count"], 1)
        self.assertAlmostEqual(result["crossings"][0]["position"], 0.5, places=1)
        self.assertEqual(result["crossings"][0]["direction"], "rising")

    def test_detect_interface_multiple(self):
        """Test detecting multiple interfaces."""
        values = [0, 1, 0, 1, 0]
        coords = [0, 1, 2, 3, 4]
        result = self.mod.detect_interface(values, coords, threshold=0.5)
        self.assertEqual(result["count"], 4)

    def test_detect_interface_none(self):
        """Test when no interface present."""
        values = [0.1, 0.2, 0.3]
        coords = [0, 1, 2]
        result = self.mod.detect_interface(values, coords, threshold=0.5)
        self.assertEqual(result["count"], 0)


class TestProfileExtractorIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "profile_extractor",
            "skills/simulation-workflow/post-processing/scripts/profile_extractor.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_get_field_data_direct(self):
        """Test getting field data directly."""
        data = {"phi": [[1, 2], [3, 4]]}
        field = self.mod.get_field_data(data, "phi")
        self.assertEqual(field, [[1, 2], [3, 4]])

    def test_get_field_data_nested(self):
        """Test getting nested field data."""
        data = {"fields": {"phi": [[1, 2], [3, 4]]}}
        field = self.mod.get_field_data(data, "phi")
        self.assertEqual(field, [[1, 2], [3, 4]])

    def test_get_field_data_with_values(self):
        """Test getting field data with values key."""
        data = {"fields": {"phi": {"values": [[1, 2]], "units": "none"}}}
        field = self.mod.get_field_data(data, "phi")
        self.assertEqual(field, [[1, 2]])

    def test_get_grid_info(self):
        """Test extracting grid info."""
        data = {"dx": 0.01, "dy": 0.02, "Lx": 1.0, "Ly": 2.0}
        info = self.mod.get_grid_info(data)
        self.assertEqual(info["dx"], 0.01)
        self.assertEqual(info["dy"], 0.02)
        self.assertEqual(info["Lx"], 1.0)


if __name__ == "__main__":
    unittest.main()
