import unittest

import numpy as np

from tests.unit._utils import load_module


class TestJacobianDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "jacobian_diagnostics",
            "skills/core-numerical/nonlinear-solvers/scripts/jacobian_diagnostics.py",
        )

    def test_well_conditioned_matrix(self):
        """Test analysis of well-conditioned matrix."""
        matrix = np.array([[2.0, 0.0], [0.0, 3.0]])
        result = self.mod.diagnose_jacobian(matrix)
        self.assertEqual(result["shape"], [2, 2])
        self.assertAlmostEqual(result["condition_number"], 1.5, places=5)
        self.assertFalse(result["rank_deficient"])
        self.assertEqual(result["jacobian_quality"], "good")

    def test_ill_conditioned_matrix(self):
        """Test detection of ill-conditioned matrix."""
        # Create ill-conditioned matrix with condition number > 10^10
        matrix = np.diag([1e12, 1.0])
        result = self.mod.diagnose_jacobian(matrix)
        self.assertGreater(result["condition_number"], 1e10)
        self.assertEqual(result["jacobian_quality"], "ill-conditioned")

    def test_near_singular_matrix(self):
        """Test detection of near-singular matrix."""
        matrix = np.array([[1.0, 1.0], [1.0, 1.0 + 1e-15]])
        result = self.mod.diagnose_jacobian(matrix)
        self.assertEqual(result["jacobian_quality"], "near-singular")

    def test_rank_deficient_matrix(self):
        """Test detection of rank deficiency."""
        # Rank 1 matrix
        matrix = np.array([[1.0, 2.0, 3.0], [2.0, 4.0, 6.0], [3.0, 6.0, 9.0]])
        result = self.mod.diagnose_jacobian(matrix)
        self.assertTrue(result["rank_deficient"])
        self.assertEqual(result["estimated_rank"], 1)

    def test_singular_values(self):
        """Test that singular values are correctly reported."""
        matrix = np.diag([5.0, 3.0, 1.0])
        result = self.mod.diagnose_jacobian(matrix)
        self.assertAlmostEqual(result["singular_value_max"], 5.0, places=5)
        self.assertAlmostEqual(result["singular_value_min"], 1.0, places=5)

    def test_finite_diff_comparison_good(self):
        """Test finite difference comparison with matching matrices."""
        matrix = np.array([[1.0, 2.0], [3.0, 4.0]])
        fd_matrix = matrix + 1e-8 * np.ones_like(matrix)  # Tiny perturbation
        result = self.mod.diagnose_jacobian(matrix, finite_diff_matrix=fd_matrix)
        self.assertIsNotNone(result["finite_diff_error"])
        self.assertLess(result["finite_diff_error"], 0.01)

    def test_finite_diff_comparison_bad(self):
        """Test finite difference comparison with different matrices."""
        matrix = np.array([[1.0, 2.0], [3.0, 4.0]])
        fd_matrix = np.array([[2.0, 1.0], [4.0, 3.0]])  # Wrong Jacobian
        result = self.mod.diagnose_jacobian(matrix, finite_diff_matrix=fd_matrix)
        self.assertIsNotNone(result["finite_diff_error"])
        self.assertGreater(result["finite_diff_error"], 0.1)

    def test_moderately_conditioned(self):
        """Test detection of moderately conditioned matrix."""
        # Condition number ~ 10^7
        matrix = np.diag([1e7, 1.0])
        result = self.mod.diagnose_jacobian(matrix)
        # Should be moderately conditioned (10^6 - 10^10)
        self.assertIn(result["jacobian_quality"], ["moderately-conditioned", "ill-conditioned"])

    def test_1d_matrix_handling(self):
        """Test handling of 1D matrix (single row)."""
        matrix = np.array([[1.0, 2.0, 3.0]])
        result = self.mod.diagnose_jacobian(matrix)
        self.assertEqual(result["shape"], [1, 3])

    def test_empty_matrix_raises(self):
        """Test that empty matrix raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.diagnose_jacobian(np.array([[]]))

    def test_invalid_tolerance_raises(self):
        """Test that non-positive tolerance raises ValueError."""
        matrix = np.eye(3)
        with self.assertRaises(ValueError):
            self.mod.diagnose_jacobian(matrix, tolerance=0)


if __name__ == "__main__":
    unittest.main()
