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

    def test_non_uniform_ratio_observed_order(self):
        """F1 regression: non-constant refinement ratios must use the iterative
        ASME V&V 20 / Celik solver, not the simple equal-ratio formula.

        spacings 0.08,0.02,0.01 -> r21=2, r32=4. The correct iterative order is
        ~1.98 (simple formula wrongly gives ~4.29).
        """
        result = self.mod.compute_gci(
            [0.08, 0.02, 0.01], [1.05, 1.0032, 1.0008],
        )
        r = result["results"]
        self.assertAlmostEqual(r["observed_order"], 1.9797, places=3)
        self.assertNotEqual(r["refinement_ratio_21"], r["refinement_ratio_32"])
        # Asymptotic ratio should be near 1.0 for these data.
        self.assertAlmostEqual(r["asymptotic_ratio"], 1.0, delta=0.01)
        # A note must flag the non-uniform-ratio iterative solve.
        self.assertTrue(any("Non-uniform" in n for n in r["notes"]))

    def test_constant_ratio_emits_caveat_note(self):
        """F3 regression: constant refinement ratios emit the f1/f2 caveat note."""
        result = self.mod.compute_gci(
            [0.04, 0.02, 0.01], [1.0128, 1.0032, 1.0008],
        )
        r = result["results"]
        self.assertEqual(r["refinement_ratio_21"], r["refinement_ratio_32"])
        self.assertTrue(any("Constant refinement ratio" in n for n in r["notes"]))

    def test_gci_fine_value_matches_roache(self):
        """F2 regression: GCI_fine for the reference report example is ~0.0999%."""
        result = self.mod.compute_gci(
            [0.04, 0.02, 0.01], [1.0128, 1.0032, 1.0008],
        )
        r = result["results"]
        self.assertAlmostEqual(r["gci_fine"], 0.0009992, places=6)

    def test_safety_factor_below_one_rejected(self):
        """F4 regression: safety factor < 1.0 must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_gci(
                [0.04, 0.02, 0.01], [1.0128, 1.0032, 1.0008], safety_factor=0.5,
            )

    def test_safety_factor_non_finite_rejected(self):
        """F4 regression: NaN/inf safety factor must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.compute_gci(
                [0.04, 0.02, 0.01], [1.0128, 1.0032, 1.0008],
                safety_factor=float("inf"),
            )

    def test_safety_factor_one_accepted(self):
        """F4: safety factor of exactly 1.0 is the meaningful floor and accepted."""
        result = self.mod.compute_gci(
            [0.04, 0.02, 0.01], [1.0128, 1.0032, 1.0008], safety_factor=1.0,
        )
        self.assertGreater(result["results"]["gci_fine"], 0)

    def test_too_many_levels_rejected(self):
        """F4 regression: >10000 entries must raise ValueError before the
        exactly-3 check."""
        big = [1.0] * 10001
        with self.assertRaises(ValueError) as ctx:
            self.mod.compute_gci(big, big)
        self.assertIn("too many", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
