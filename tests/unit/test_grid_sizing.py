import unittest

from tests.unit._utils import load_module


class TestGridSizing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "grid_sizing",
            "skills/core-numerical/mesh-generation/scripts/grid_sizing.py",
        )

    def test_compute_grid(self):
        result = self.mod.compute_grid(length=1.0, resolution=10, dims=2, dx=None)
        self.assertAlmostEqual(result["dx"], 0.1, places=6)
        self.assertEqual(result["counts"], [10, 10])

    def test_invalid_length(self):
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=0, resolution=10, dims=2, dx=None)

    def test_negative_length_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=-1.0, resolution=10, dims=2, dx=None)

    def test_nan_length_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=float("nan"), resolution=10, dims=2, dx=None)

    def test_inf_length_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=float("inf"), resolution=10, dims=2, dx=None)

    def test_exceeds_max_length_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=1e13, resolution=10, dims=2, dx=None)

    def test_exceeds_max_resolution_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=1.0, resolution=100_000_000, dims=2, dx=None)

    def test_invalid_dims_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=1.0, resolution=10, dims=4, dx=None)
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=1.0, resolution=10, dims=0, dx=None)

    def test_negative_dx_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_grid(length=1.0, resolution=10, dims=2, dx=-0.1)

    def test_valid_dims(self):
        for d in (1, 2, 3):
            result = self.mod.compute_grid(length=1.0, resolution=10, dims=d, dx=None)
            self.assertEqual(len(result["counts"]), d)


if __name__ == "__main__":
    unittest.main()
