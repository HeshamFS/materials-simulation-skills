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


if __name__ == "__main__":
    unittest.main()
