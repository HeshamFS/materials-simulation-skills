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
            accuracy=1,
            scheme="central",
            dx=1.0,
            offsets=[-2, 0, 2],
        )
        self.assertEqual(result["offsets"], [-2, 0, 2])
        coeffs = result["coefficients"]
        self.assertAlmostEqual(coeffs[0], -0.25, places=6)
        self.assertAlmostEqual(coeffs[1], 0.0, places=6)
        self.assertAlmostEqual(coeffs[2], 0.25, places=6)


if __name__ == "__main__":
    unittest.main()
