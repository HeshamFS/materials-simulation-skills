import math
import unittest

from tests.unit._utils import load_module


class TestGciCalculator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "gci_calculator",
            "skills/core-numerical/convergence-study/scripts/gci_calculator.py",
        )

    def test_standard_gci(self):
        """3 mesh levels with known 2nd-order convergence: GCI values positive."""
        # f(h) = 1.0 + 0.8*h^2 with h = 0.01, 0.02, 0.04
        exact = 1.0
        C = 0.8
        spacings = [0.04, 0.02, 0.01]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_gci(spacings, values)
        r = result["results"]
        self.assertGreater(r["gci_fine"], 0)
        self.assertGreater(r["gci_coarse"], 0)
        self.assertAlmostEqual(r["observed_order"], 2.0, places=1)

    def test_wrong_number_of_levels(self):
        """2 or 4 levels should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_gci([0.02, 0.01], [1.0, 1.0])
        with self.assertRaises(ValueError):
            self.mod.compute_gci(
                [0.08, 0.04, 0.02, 0.01], [1.0, 1.0, 1.0, 1.0],
            )

    def test_identical_solutions(self):
        """f1=f2=f3 should handle gracefully (order undefined)."""
        result = self.mod.compute_gci(
            [0.04, 0.02, 0.01], [1.0, 1.0, 1.0],
        )
        r = result["results"]
        self.assertIsNone(r["observed_order"])
        self.assertEqual(r["gci_fine"], 0.0)
        self.assertEqual(r["gci_coarse"], 0.0)

    def test_oscillatory_convergence(self):
        """Opposite signs in differences should raise ValueError."""
        # f1=1.0, f2=1.1, f3=1.05 -> e21=0.1, e32=-0.05 (opposite signs)
        with self.assertRaises(ValueError) as ctx:
            self.mod.compute_gci(
                [0.04, 0.02, 0.01], [1.05, 1.1, 1.0],
            )
        self.assertIn("Oscillatory", str(ctx.exception))

    def test_gci_fine_less_than_coarse(self):
        """GCI_fine should be less than GCI_coarse for monotone convergence."""
        exact = 1.0
        C = 0.8
        spacings = [0.04, 0.02, 0.01]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_gci(spacings, values)
        r = result["results"]
        self.assertLess(r["gci_fine"], r["gci_coarse"])

    def test_asymptotic_range_detection(self):
        """With exact 2nd-order data, asymptotic ratio should be ~1.0."""
        exact = 1.0
        C = 0.8
        spacings = [0.04, 0.02, 0.01]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_gci(spacings, values)
        r = result["results"]
        self.assertTrue(r["in_asymptotic_range"])
        self.assertAlmostEqual(r["asymptotic_ratio"], 1.0, places=1)

    def test_extrapolated_value(self):
        """Extrapolated value should be close to exact for clean data."""
        exact = 1.0
        C = 0.8
        spacings = [0.04, 0.02, 0.01]
        values = [exact + C * h ** 2 for h in spacings]
        result = self.mod.compute_gci(spacings, values)
        r = result["results"]
        self.assertAlmostEqual(r["extrapolated_value"], exact, places=4)

    def test_non_finite_input(self):
        """NaN in values should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_gci(
                [0.04, 0.02, 0.01], [1.0, float("nan"), 1.0],
            )

    def test_negative_spacing(self):
        """Negative spacing should raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_gci(
                [-0.04, 0.02, 0.01], [1.0, 1.0, 1.0],
            )


if __name__ == "__main__":
    unittest.main()
