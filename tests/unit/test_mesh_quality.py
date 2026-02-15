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
        self.assertTrue(result["skewness"] > 0)

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


if __name__ == "__main__":
    unittest.main()
