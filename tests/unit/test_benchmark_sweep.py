import unittest

import numpy as np

from tests.unit._utils import load_module
from tests.unit.benchmark_matrices import diag_with_condition, poisson_1d, stiffness_eigs


class TestBenchmarkSweep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cond = load_module(
            "matrix_condition",
            "skills/core-numerical/numerical-stability/scripts/matrix_condition.py",
        )
        cls.stiff = load_module(
            "stiffness_detector",
            "skills/core-numerical/numerical-stability/scripts/stiffness_detector.py",
        )

    def test_condition_monotonic_diagonal(self):
        prev = 0.0
        for cond in [10, 100, 1e3, 1e4]:
            matrix = diag_with_condition(5, cond)
            result = self.cond.compute_condition(
                matrix=matrix,
                norm=2.0,
                symmetry_tol=1e-8,
                skip_eigs=True,
            )
            self.assertGreater(result["condition_number"], prev)
            prev = result["condition_number"]

    def test_poisson_condition_increases_with_size(self):
        prev = 0.0
        for size in [4, 6, 8, 10]:
            matrix = poisson_1d(size)
            result = self.cond.compute_condition(
                matrix=matrix,
                norm=2.0,
                symmetry_tol=1e-8,
                skip_eigs=True,
            )
            self.assertGreater(result["condition_number"], prev)
            prev = result["condition_number"]

    def test_stiffness_threshold_sweep(self):
        ratios = [1e2, 1e3, 1e4]
        for ratio in ratios:
            eigs = stiffness_eigs(ratio)
            result = self.stiff.compute_stiffness(eigs, threshold=1e3)
            expected = ratio >= 1e3
            self.assertEqual(result["stiff"], expected)

    def test_poisson_symmetric(self):
        matrix = poisson_1d(5)
        result = self.cond.compute_condition(
            matrix=matrix,
            norm=2.0,
            symmetry_tol=1e-8,
            skip_eigs=True,
        )
        self.assertTrue(result["is_symmetric"])

    def test_random_spd_condition_finite(self):
        rng = np.random.default_rng(4)
        for size in [5, 10, 20]:
            mat = rng.normal(size=(size, size))
            spd = mat.T @ mat + size * np.eye(size)
            result = self.cond.compute_condition(
                matrix=spd,
                norm=2.0,
                symmetry_tol=1e-8,
                skip_eigs=True,
            )
            self.assertTrue(np.isfinite(result["condition_number"]))
            self.assertGreaterEqual(result["condition_number"], 1.0)
            self.assertTrue(result["is_symmetric"])

    def test_sparse_banded_condition(self):
        rng = np.random.default_rng(5)
        size = 30
        diag = rng.uniform(2.0, 3.0, size)
        off = rng.uniform(-0.2, 0.2, size - 1)
        matrix = np.zeros((size, size))
        idx = np.arange(size)
        matrix[idx, idx] = diag
        matrix[idx[:-1], idx[1:]] = off
        matrix[idx[1:], idx[:-1]] = off
        result = self.cond.compute_condition(
            matrix=matrix,
            norm=2.0,
            symmetry_tol=1e-8,
            skip_eigs=True,
        )
        self.assertTrue(np.isfinite(result["condition_number"]))
        self.assertTrue(result["is_symmetric"])


if __name__ == "__main__":
    unittest.main()
