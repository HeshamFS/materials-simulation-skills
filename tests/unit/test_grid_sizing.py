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

    def test_resolution_exact_no_off_by_one(self):
        """F3 regression: resolution-derived counts must equal the request."""
        r500 = self.mod.compute_grid(length=0.001, resolution=500, dims=2, dx=None)
        self.assertEqual(r500["counts"], [500, 500])
        r1000 = self.mod.compute_grid(length=0.001, resolution=1000, dims=2, dx=None)
        self.assertEqual(r1000["counts"], [1000, 1000])

    def test_explicit_dx_snaps_integer_count(self):
        """F3 regression: explicit dx with integer length/dx must not over-count."""
        result = self.mod.compute_grid(length=0.001, resolution=1, dims=2, dx=2e-6)
        self.assertEqual(result["counts"], [500, 500])

    def test_explicit_dx_preserves_partial_cell(self):
        """A genuine partial cell still rounds up."""
        result = self.mod.compute_grid(length=0.0010005, resolution=1, dims=2, dx=2e-6)
        self.assertEqual(result["counts"], [501, 501])

    def test_explicit_dx_notes_resolution_ignored(self):
        """F8 regression: explicit dx surfaces a note that resolution is ignored."""
        result = self.mod.compute_grid(length=1.0, resolution=1000, dims=2, dx=0.1)
        self.assertEqual(result["counts"], [10, 10])
        self.assertTrue(
            any("ignored for spacing" in n for n in result["notes"]),
            result["notes"],
        )

    def test_resolution_one_is_valid(self):
        """F5: resolution=1 is a valid single-cell mesh, not an error."""
        result = self.mod.compute_grid(length=2.0, resolution=1, dims=1, dx=None)
        self.assertEqual(result["counts"], [1])
        self.assertAlmostEqual(result["dx"], 2.0, places=6)

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
