import unittest

import numpy as np

from tests.unit._utils import load_module


class TestMatrixCondition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "matrix_condition",
            "skills/core-numerical/numerical-stability/scripts/matrix_condition.py",
        )

    def test_condition_number(self):
        matrix = np.array([[1.0, 0.0], [0.0, 2.0]])
        result = self.mod.compute_condition(
            matrix=matrix,
            norm=2.0,
            symmetry_tol=1e-8,
            skip_eigs=False,
        )
        self.assertAlmostEqual(result["condition_number"], 2.0, places=6)
        self.assertTrue(result["is_symmetric"])
        self.assertAlmostEqual(result["eigenvalue_spread"], 2.0, places=6)

    def test_non_square_error(self):
        matrix = np.zeros((2, 3))
        with self.assertRaises(ValueError):
            self.mod.compute_condition(
                matrix=matrix,
                norm=2.0,
                symmetry_tol=1e-8,
                skip_eigs=True,
            )

    def test_skip_eigs(self):
        matrix = np.eye(3)
        result = self.mod.compute_condition(
            matrix=matrix,
            norm=2.0,
            symmetry_tol=1e-8,
            skip_eigs=True,
        )
        self.assertIsNone(result["eigenvalue_spread"])

    def test_non_finite_error(self):
        matrix = np.array([[1.0, 0.0], [0.0, float("nan")]])
        with self.assertRaises(ValueError):
            self.mod.compute_condition(
                matrix=matrix,
                norm=2.0,
                symmetry_tol=1e-8,
                skip_eigs=True,
            )

    def test_symmetry_tolerance(self):
        matrix = np.array([[1.0, 1e-9], [0.0, 1.0]])
        result = self.mod.compute_condition(
            matrix=matrix,
            norm=2.0,
            symmetry_tol=1e-8,
            skip_eigs=True,
        )
        self.assertTrue(result["is_symmetric"])

    def test_invalid_norm(self):
        with self.assertRaises(ValueError):
            self.mod.parse_norm("bad")


if __name__ == "__main__":
    unittest.main()
