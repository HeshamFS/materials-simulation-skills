"""Unit tests for post-processing derived_quantities.py script."""

import json
import math
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestDerivedQuantities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "derived_quantities",
            "skills/simulation-workflow/post-processing/scripts/derived_quantities.py",
        )

    def test_flatten_field_1d(self):
        """Test flattening 1D field."""
        result = self.mod.flatten_field([1, 2, 3])
        self.assertEqual(result, [1.0, 2.0, 3.0])

    def test_flatten_field_2d(self):
        """Test flattening 2D field."""
        result = self.mod.flatten_field([[1, 2], [3, 4]])
        self.assertEqual(result, [1.0, 2.0, 3.0, 4.0])

    def test_compute_volume_fraction_above(self):
        """Test volume fraction above threshold."""
        field = [0.0, 0.3, 0.5, 0.7, 1.0]
        result = self.mod.compute_volume_fraction(field, threshold=0.5, above=True)
        self.assertEqual(result["volume_fraction"], 0.6)  # 3 out of 5
        self.assertEqual(result["count"], 3)

    def test_compute_volume_fraction_below(self):
        """Test volume fraction below threshold."""
        field = [0.0, 0.3, 0.5, 0.7, 1.0]
        result = self.mod.compute_volume_fraction(field, threshold=0.5, above=False)
        self.assertEqual(result["volume_fraction"], 0.4)  # 2 out of 5

    def test_compute_volume_fraction_2d(self):
        """Test volume fraction for 2D field."""
        field = [[0.0, 0.0], [1.0, 1.0]]
        result = self.mod.compute_volume_fraction(field, threshold=0.5)
        self.assertEqual(result["volume_fraction"], 0.5)

    def test_compute_volume_fraction_empty(self):
        """Test volume fraction for empty field."""
        result = self.mod.compute_volume_fraction([], threshold=0.5)
        self.assertIsNone(result["volume_fraction"])

    def test_compute_interface_area_2d_single(self):
        """Test interface area for single interface."""
        # Horizontal interface at y=0.5
        field = [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]]
        result = self.mod.compute_interface_area_2d(field, 0.5, 1.0, 1.0)
        self.assertGreater(result["cells_crossed"], 0)

    def test_compute_interface_area_2d_no_interface(self):
        """Test interface area with no interface."""
        field = [[0.0, 0.0], [0.0, 0.0]]
        result = self.mod.compute_interface_area_2d(field, 0.5, 1.0, 1.0)
        self.assertEqual(result["cells_crossed"], 0)

    def test_compute_interface_area_1d(self):
        """Test interface crossing count in 1D."""
        field = [0.0, 0.25, 0.75, 1.0]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_interface_area(field, 0.5, spacing)
        self.assertEqual(result["crossings"], 1)

    def test_compute_gradient_2d(self):
        """Test 2D gradient computation."""
        # Linear field in x direction
        field = [[0.0, 1.0, 2.0], [0.0, 1.0, 2.0]]
        grad_x, grad_y = self.mod.compute_gradient_2d(field, 1.0, 1.0)
        # Gradient in x should be 1.0, in y should be 0
        self.assertAlmostEqual(grad_x[0][1], 1.0)
        self.assertAlmostEqual(grad_y[0][1], 0.0)

    def test_compute_gradient_2d_y_direction(self):
        """Test gradient in y direction."""
        field = [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]]
        grad_x, grad_y = self.mod.compute_gradient_2d(field, 1.0, 1.0)
        self.assertAlmostEqual(grad_y[1][0], 1.0)
        self.assertAlmostEqual(grad_x[1][0], 0.0)

    def test_compute_gradient_magnitude_1d(self):
        """Test gradient magnitude in 1D."""
        field = [0.0, 1.0, 2.0, 3.0]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_gradient_magnitude(field, spacing)
        self.assertAlmostEqual(result["mean"], 1.0)

    def test_compute_gradient_magnitude_2d(self):
        """Test gradient magnitude in 2D."""
        # Linear gradient field
        field = [[0.0, 1.0, 2.0], [0.0, 1.0, 2.0]]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_gradient_magnitude(field, spacing)
        self.assertAlmostEqual(result["mean"], 1.0, places=1)

    def test_compute_integral_1d(self):
        """Test 1D integral."""
        field = [1.0, 1.0, 1.0, 1.0]  # Constant field
        spacing = {"dx": 0.25, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_integral(field, spacing)
        self.assertAlmostEqual(result["integral"], 1.0)  # 4 * 0.25 * 1.0

    def test_compute_integral_2d(self):
        """Test 2D integral."""
        field = [[1.0, 1.0], [1.0, 1.0]]  # 2x2 constant field
        spacing = {"dx": 0.5, "dy": 0.5, "dz": 1.0}
        result = self.mod.compute_integral(field, spacing)
        self.assertAlmostEqual(result["integral"], 1.0)  # 4 * 0.5 * 0.5 * 1.0

    def test_compute_total_variation_1d(self):
        """Test total variation in 1D."""
        field = [0.0, 1.0, 0.0, 1.0]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_total_variation(field, spacing)
        self.assertEqual(result["total_variation"], 3.0)  # |1-0| + |0-1| + |1-0|

    def test_compute_total_variation_2d(self):
        """Test total variation in 2D."""
        field = [[0.0, 1.0], [0.0, 1.0]]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_total_variation(field, spacing)
        # Two horizontal differences of 1 each row
        self.assertGreater(result["total_variation"], 0)

    def test_compute_mass(self):
        """Test mass computation."""
        field = [1.0, 2.0, 3.0]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_mass(field, spacing)
        self.assertEqual(result["total_mass"], 6.0)
        self.assertEqual(result["mean_density"], 2.0)

    def test_compute_centroid_1d(self):
        """Test 1D centroid computation."""
        field = [0.0, 0.0, 1.0, 0.0, 0.0]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_centroid(field, spacing)
        self.assertEqual(result["centroid_x"], 2.0)

    def test_compute_centroid_2d(self):
        """Test 2D centroid computation."""
        field = [[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_centroid(field, spacing)
        self.assertEqual(result["centroid_x"], 1.0)
        self.assertEqual(result["centroid_y"], 1.0)

    def test_compute_centroid_zero_mass(self):
        """Test centroid with zero mass."""
        field = [0.0, 0.0, 0.0]
        spacing = {"dx": 1.0, "dy": 1.0, "dz": 1.0}
        result = self.mod.compute_centroid(field, spacing)
        self.assertIsNone(result["centroid_x"])


class TestDerivedQuantitiesIO(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "derived_quantities",
            "skills/simulation-workflow/post-processing/scripts/derived_quantities.py",
        )

    def test_get_grid_spacing_from_data(self):
        """Test extracting grid spacing from data."""
        data = {"dx": 0.1, "dy": 0.2}
        shape = [10, 20]
        result = self.mod.get_grid_spacing(data, shape)
        self.assertEqual(result["dx"], 0.1)
        self.assertEqual(result["dy"], 0.2)

    def test_get_grid_spacing_computed(self):
        """Test computing grid spacing from domain size."""
        # shape = [ny, nx] = [11, 21] means 10 y-intervals and 20 x-intervals
        data = {"Lx": 1.0, "Ly": 2.0}
        shape = [11, 21]
        result = self.mod.get_grid_spacing(data, shape)
        # dx = Lx / (nx - 1) = 1.0 / 20 = 0.05
        # dy = Ly / (ny - 1) = 2.0 / 10 = 0.2
        self.assertAlmostEqual(result["dx"], 0.05)
        self.assertAlmostEqual(result["dy"], 0.2)

    def test_get_grid_spacing_default(self):
        """Test default grid spacing."""
        result = self.mod.get_grid_spacing({}, [10])
        self.assertEqual(result["dx"], 1.0)
        self.assertEqual(result["dy"], 1.0)


if __name__ == "__main__":
    unittest.main()
