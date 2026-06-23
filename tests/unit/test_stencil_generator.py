import unittest

from tests.unit._utils import load_module


class TestStencilGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "stencil_generator",
            "skills/core-numerical/differentiation-schemes/scripts/stencil_generator.py",
        )

    def test_central_first_derivative(self):
        result = self.mod.generate_stencil(
            order=1,
            accuracy=2,
            scheme="central",
            dx=1.0,
            offsets=None,
        )
        self.assertEqual(result["offsets"], [-1, 0, 1])
        coeffs = result["coefficients"]
        self.assertAlmostEqual(coeffs[0], -0.5, places=6)
        self.assertAlmostEqual(coeffs[1], 0.0, places=6)
        self.assertAlmostEqual(coeffs[2], 0.5, places=6)

    def test_central_second_derivative(self):
        result = self.mod.generate_stencil(
            order=2,
            accuracy=2,
            scheme="central",
            dx=1.0,
            offsets=None,
        )
        self.assertEqual(result["offsets"], [-1, 0, 1])
        coeffs = result["coefficients"]
        self.assertAlmostEqual(coeffs[0], 1.0, places=6)
        self.assertAlmostEqual(coeffs[1], -2.0, places=6)
        self.assertAlmostEqual(coeffs[2], 1.0, places=6)

    def test_forward_first_derivative(self):
        result = self.mod.generate_stencil(
            order=1,
            accuracy=1,
            scheme="forward",
            dx=1.0,
            offsets=None,
        )
        self.assertEqual(result["offsets"], [0, 1])
        coeffs = result["coefficients"]
        self.assertAlmostEqual(coeffs[0], -1.0, places=6)
        self.assertAlmostEqual(coeffs[1], 1.0, places=6)

    def test_custom_offsets(self):
        result = self.mod.generate_stencil(
            order=1,
            accuracy=2,
            scheme="central",
            dx=1.0,
            offsets=[-2, 0, 2],
        )
        self.assertEqual(result["offsets"], [-2, 0, 2])
        coeffs = result["coefficients"]
        self.assertAlmostEqual(coeffs[0], -0.25, places=6)
        self.assertAlmostEqual(coeffs[1], 0.0, places=6)
        self.assertAlmostEqual(coeffs[2], 0.25, places=6)

    # --- Regression tests for v1.2.0 fixes ---

    def test_central_odd_accuracy_rejected(self):
        # F3: central scheme must reject odd accuracy instead of silently
        # rounding up and mislabeling the achieved order.
        with self.assertRaises(ValueError) as ctx:
            self.mod.stencil_offsets(order=1, accuracy=3, scheme="central")
        self.assertEqual(str(ctx.exception), "accuracy must be even for central")

    def test_central_even_accuracy_allowed(self):
        offsets = self.mod.stencil_offsets(order=1, accuracy=4, scheme="central")
        self.assertEqual(offsets, [-2, -1, 0, 1, 2])

    def test_order_upper_bound(self):
        # F4: derivative order must be bounded.
        with self.assertRaises(ValueError) as ctx:
            self.mod.stencil_offsets(order=7, accuracy=2, scheme="central")
        self.assertEqual(str(ctx.exception), "order must be <= 6")

    def test_accuracy_upper_bound(self):
        with self.assertRaises(ValueError):
            self.mod.stencil_offsets(order=1, accuracy=10, scheme="central")

    def test_forward_odd_accuracy_allowed(self):
        # Even-accuracy restriction applies only to the central scheme.
        offsets = self.mod.stencil_offsets(order=1, accuracy=1, scheme="forward")
        self.assertEqual(offsets, [0, 1])

    def test_custom_offsets_must_be_distinct(self):
        with self.assertRaises(ValueError):
            self.mod.generate_stencil(
                order=1, accuracy=2, scheme="central", dx=1.0, offsets=[0, 0, 1]
            )

    def test_custom_offsets_must_exceed_order(self):
        with self.assertRaises(ValueError):
            self.mod.generate_stencil(
                order=2, accuracy=2, scheme="central", dx=1.0, offsets=[0, 1]
            )

    def test_custom_offsets_length_capped(self):
        too_many = list(range(self.mod.MAX_OFFSETS + 1))
        with self.assertRaises(ValueError):
            self.mod.generate_stencil(
                order=1, accuracy=2, scheme="central", dx=1.0, offsets=too_many
            )

    def test_non_finite_dx_rejected(self):
        with self.assertRaises(ValueError):
            self.mod.generate_stencil(
                order=1, accuracy=2, scheme="central", dx=float("inf"), offsets=None
            )

    def test_parse_offsets_length_capped(self):
        raw = ",".join(str(i) for i in range(self.mod.MAX_OFFSETS + 1))
        with self.assertRaises(ValueError):
            self.mod.parse_offsets(raw)


if __name__ == "__main__":
    unittest.main()
