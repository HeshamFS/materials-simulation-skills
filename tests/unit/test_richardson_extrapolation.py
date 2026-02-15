import math
import unittest

from tests.unit._utils import load_module


class TestRichardsonExtrapolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "richardson_extrapolation",
            "skills/core-numerical/convergence-study/scripts/richardson_extrapolation.py",
        )

    def test_two_level_extrapolation(self):
        """Two levels with known 2nd-order: extrapolated value near exact."""
        exact = 1.0
        C = 0.1
        spacings = [0.2, 0.1]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_richardson_extrapolation(spacings, values, order=2.0)
        r = result["results"]
        self.assertAlmostEqual(r["extrapolated_value"], exact, places=4)

    def test_three_level_with_observed_order(self):
        """Three levels should compute observed_order."""
        exact = 1.0
        C = 0.1
        spacings = [0.4, 0.2, 0.1]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_richardson_extrapolation(spacings, values, order=2.0)
        r = result["results"]
        self.assertIn("observed_order", r)
        self.assertAlmostEqual(r["observed_order"], 2.0, places=1)
        self.assertTrue(r["order_consistent"])

    def test_error_estimate_accuracy(self):
        """Error estimate should match actual error within factor of 2."""
        exact = 1.0
        C = 0.1
        spacings = [0.2, 0.1]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_richardson_extrapolation(spacings, values, order=2.0)
        r = result["results"]
        actual_error = abs(values[-1] - exact)
        estimated_error = r["error_estimate"]
        # The estimate should be within a factor of 2 of the actual error
        ratio = estimated_error / actual_error if actual_error > 0 else float("inf")
        self.assertGreater(ratio, 0.5)
        self.assertLess(ratio, 2.0)

    def test_non_finite_inputs(self):
        """NaN/Inf in inputs should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_richardson_extrapolation(
                [0.2, 0.1], [float("nan"), 1.0], order=2.0,
            )
        with self.assertRaises(ValueError):
            self.mod.compute_richardson_extrapolation(
                [0.2, 0.1], [float("inf"), 1.0], order=2.0,
            )

    def test_too_few_levels(self):
        """Fewer than 2 levels should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_richardson_extrapolation([0.1], [1.0], order=2.0)

    def test_negative_order_raises(self):
        """Negative order should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_richardson_extrapolation(
                [0.2, 0.1], [1.004, 1.001], order=-1.0,
            )

    def test_zero_order_raises(self):
        """Zero order should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_richardson_extrapolation(
                [0.2, 0.1], [1.004, 1.001], order=0.0,
            )

    def test_mismatched_lengths(self):
        """Different lengths should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_richardson_extrapolation(
                [0.4, 0.2, 0.1], [1.0, 2.0], order=2.0,
            )


if __name__ == "__main__":
    unittest.main()
