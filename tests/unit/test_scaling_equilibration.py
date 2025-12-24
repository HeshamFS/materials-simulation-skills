import unittest

import numpy as np

from tests.unit._utils import load_module


class TestScalingEquilibration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "scaling_equilibration",
            "skills/core-numerical/linear-solvers/scripts/scaling_equilibration.py",
        )

    def test_basic_scaling(self):
        matrix = np.array([[2.0, 0.0], [0.0, 4.0]])
        result = self.mod.compute_scaling(matrix, symmetry_tol=1e-8, symmetric=True)
        self.assertEqual(result["row_scale"], [0.5, 0.25])
        self.assertEqual(result["col_scale"], [0.5, 0.25])
        self.assertAlmostEqual(result["symmetric_scale"][0], 1.0 / np.sqrt(2.0), places=6)
        self.assertAlmostEqual(result["symmetric_scale"][1], 0.5, places=6)

    def test_zero_row(self):
        matrix = np.array([[0.0, 0.0], [1.0, 0.0]])
        result = self.mod.compute_scaling(matrix, symmetry_tol=1e-8, symmetric=False)
        self.assertIn(0, result["zero_rows"])

    def test_symmetric_requires_square(self):
        matrix = np.zeros((2, 3))
        with self.assertRaises(ValueError):
            self.mod.compute_scaling(matrix, symmetry_tol=1e-8, symmetric=True)


if __name__ == "__main__":
    unittest.main()
