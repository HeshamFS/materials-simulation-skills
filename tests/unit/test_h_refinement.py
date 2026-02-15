import math
import unittest

from tests.unit._utils import load_module


class TestHRefinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "h_refinement",
            "skills/core-numerical/convergence-study/scripts/h_refinement.py",
        )

    def test_second_order_convergence(self):
        """Spacings with f(h) = 1.0 + 0.1*h^2 should give order ~2."""
        exact = 1.0
        C = 0.1
        spacings = [0.4, 0.2, 0.1]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_h_refinement(spacings, values, expected_order=2.0)
        r = result["results"]
        self.assertAlmostEqual(r["mean_order"], 2.0, places=1)
        self.assertIn("PASS", r["convergence_assessment"])

    def test_first_order_convergence(self):
        """Spacings with f(h) = 1.0 + 0.1*h should give order ~1."""
        exact = 1.0
        C = 0.1
        spacings = [0.4, 0.2, 0.1]
        values = [exact + C * h for h in spacings]
        result = self.mod.compute_h_refinement(spacings, values, expected_order=1.0)
        r = result["results"]
        self.assertAlmostEqual(r["mean_order"], 1.0, places=1)
        self.assertIn("PASS", r["convergence_assessment"])

    def test_too_few_levels_for_order(self):
        """With only 2 levels, observed_orders should be empty."""
        result = self.mod.compute_h_refinement(
            [0.2, 0.1], [1.004, 1.001], expected_order=2.0,
        )
        r = result["results"]
        self.assertEqual(r["observed_orders"], [])
        self.assertIsNone(r["mean_order"])
        # Richardson extrapolation should still be computed using expected order
        self.assertIsNotNone(r["richardson_extrapolated_value"])

    def test_mismatched_lengths(self):
        """Different lengths should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_h_refinement([0.4, 0.2, 0.1], [1.0, 2.0])

    def test_nan_input_raises(self):
        """NaN in values should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_h_refinement(
                [0.4, 0.2, 0.1], [1.0, float("nan"), 1.0],
            )

    def test_extrapolated_accuracy(self):
        """Richardson extrapolated value should be closer to exact than finest grid."""
        exact = 1.0
        C = 0.1
        spacings = [0.4, 0.2, 0.1]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_h_refinement(spacings, values)
        r = result["results"]
        finest_error = abs(values[-1] - exact)
        extrap_error = abs(r["richardson_extrapolated_value"] - exact)
        self.assertLess(extrap_error, finest_error)

    def test_unsorted_input(self):
        """Inputs in arbitrary order should be sorted internally."""
        exact = 1.0
        C = 0.1
        spacings = [0.1, 0.4, 0.2]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_h_refinement(spacings, values, expected_order=2.0)
        # Should still compute correct order
        r = result["results"]
        self.assertAlmostEqual(r["mean_order"], 2.0, places=1)

    def test_single_level_raises(self):
        """Single level should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_h_refinement([0.1], [1.0])

    def test_zero_spacing_raises(self):
        """Zero spacing should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_h_refinement([0.0, 0.1], [1.0, 2.0])

    def test_negative_spacing_raises(self):
        """Negative spacing should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_h_refinement([-0.1, 0.1], [1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
