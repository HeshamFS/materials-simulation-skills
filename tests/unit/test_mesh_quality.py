import unittest

from tests.unit._utils import load_module


class TestMeshQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "mesh_quality",
            "skills/core-numerical/mesh-generation/scripts/mesh_quality.py",
        )

    def test_quality_metrics(self):
        result = self.mod.compute_quality(1.0, 1.0, 2.0)
        self.assertAlmostEqual(result["aspect_ratio"], 2.0, places=6)
        # Orthogonal Cartesian cell: true angular skewness is 0 (regression F1).
        self.assertEqual(result["skewness"], 0.0)
        self.assertAlmostEqual(result["size_anisotropy"], 0.5, places=6)

    def test_orthogonal_cell_zero_skewness_no_flag(self):
        """F1 regression: high-AR orthogonal cell -> skewness 0, no high_skewness."""
        result = self.mod.compute_quality(1.0, 0.1, 0.1)
        self.assertAlmostEqual(result["aspect_ratio"], 10.0, places=6)
        self.assertEqual(result["skewness"], 0.0)
        self.assertAlmostEqual(result["size_anisotropy"], 0.9, places=6)
        self.assertIn("high_aspect_ratio", result["quality_flags"])
        self.assertNotIn("high_skewness", result["quality_flags"])

    def test_2d_cell_when_dz_omitted(self):
        """F2 regression: dz=None is treated as a 2D cell."""
        result = self.mod.compute_quality(1.0, 0.1)
        self.assertEqual(result["dims"], 2)
        self.assertAlmostEqual(result["aspect_ratio"], 10.0, places=6)
        self.assertEqual(result["skewness"], 0.0)
        self.assertIn("high_aspect_ratio", result["quality_flags"])

    def test_uniform_cell_excellent(self):
        result = self.mod.compute_quality(0.5, 0.5)
        self.assertAlmostEqual(result["aspect_ratio"], 1.0, places=6)
        self.assertEqual(result["skewness"], 0.0)
        self.assertEqual(result["quality_flags"], [])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            self.mod.compute_quality(0.0, 1.0, 1.0)

    def test_nan_input_raises(self):
        """NaN input must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_quality(float("nan"), 1.0, 1.0)

    def test_inf_input_raises(self):
        """Inf input must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_quality(float("inf"), 1.0, 1.0)

    def test_negative_input_raises(self):
        """Negative input must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_quality(-1.0, 1.0, 1.0)

    def test_quality_high_aspect_ratio(self):
        """High aspect ratio should flag."""
        result = self.mod.compute_quality(1.0, 1.0, 10.0)
        self.assertIn("high_aspect_ratio", result["quality_flags"])
        self.assertAlmostEqual(result["aspect_ratio"], 10.0, places=6)

    def test_exceeds_max_cell_size_raises(self):
        """Cell sizes above the upper bound must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_quality(1e13, 1.0, 1.0)

    def test_non_numeric_type_raises(self):
        """Non-numeric inputs must raise ValueError."""
        with self.assertRaises((ValueError, TypeError)):
            self.mod.compute_quality("1.0", 1.0, 1.0)


if __name__ == "__main__":
    unittest.main()
