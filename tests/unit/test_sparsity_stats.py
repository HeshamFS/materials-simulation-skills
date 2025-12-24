import unittest

import numpy as np

from tests.unit._utils import load_module


class TestSparsityStats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "sparsity_stats",
            "skills/core-numerical/linear-solvers/scripts/sparsity_stats.py",
        )

    def test_identity(self):
        matrix = np.eye(4)
        stats = self.mod.compute_stats(matrix, symmetry_tol=1e-8)
        self.assertEqual(stats["nnz"], 4)
        self.assertTrue(stats["symmetry"])
        self.assertEqual(stats["bandwidth"], 0)

    def test_bandwidth(self):
        matrix = np.array([[1, 1, 0], [1, 1, 1], [0, 1, 1]], dtype=float)
        stats = self.mod.compute_stats(matrix, symmetry_tol=1e-8)
        self.assertEqual(stats["bandwidth"], 1)

    def test_non_finite(self):
        matrix = np.array([[1.0, float("nan")]])
        with self.assertRaises(ValueError):
            self.mod.compute_stats(matrix, symmetry_tol=1e-8)


if __name__ == "__main__":
    unittest.main()
