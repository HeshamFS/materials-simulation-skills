import unittest

from tests.unit._utils import load_module


class TestLinearSolverSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "solver_selector",
            "skills/core-numerical/linear-solvers/scripts/solver_selector.py",
        )

    def test_spd_sparse_large(self):
        result = self.mod.select_solver(
            symmetric=True,
            positive_definite=True,
            sparse=True,
            size=1_000_000,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=True,
        )
        self.assertIn("CG", result["recommended"])
        self.assertTrue(any("IC/AMG" in note for note in result["notes"]))

    def test_symmetric_indefinite(self):
        result = self.mod.select_solver(
            symmetric=True,
            positive_definite=False,
            sparse=False,
            size=1000,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=False,
        )
        self.assertIn("MINRES", result["recommended"])

    def test_nonsymmetric(self):
        result = self.mod.select_solver(
            symmetric=False,
            positive_definite=False,
            sparse=True,
            size=10000,
            nearly_symmetric=False,
            ill_conditioned=True,
            complex_valued=False,
            memory_limited=False,
        )
        self.assertIn("GMRES (restarted)", result["recommended"])
        self.assertTrue(any("preconditioning" in note for note in result["notes"]))

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            self.mod.select_solver(
                symmetric=False,
                positive_definite=False,
                sparse=False,
                size=0,
                nearly_symmetric=False,
                ill_conditioned=False,
                complex_valued=False,
                memory_limited=False,
            )

    def test_exceeds_max_size(self):
        """Size exceeding upper bound must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.select_solver(
                symmetric=False,
                positive_definite=False,
                sparse=False,
                size=20_000_000_000,
                nearly_symmetric=False,
                ill_conditioned=False,
                complex_valued=False,
                memory_limited=False,
            )

    def test_negative_size(self):
        """Negative size must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.select_solver(
                symmetric=False,
                positive_definite=False,
                sparse=False,
                size=-100,
                nearly_symmetric=False,
                ill_conditioned=False,
                complex_valued=False,
                memory_limited=False,
            )


class TestSparsityStats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "sparsity_stats",
            "skills/core-numerical/linear-solvers/scripts/sparsity_stats.py",
        )

    def test_npy_allow_pickle_false(self):
        """np.load must be called with allow_pickle=False."""
        import inspect
        source = inspect.getsource(self.mod.load_matrix)
        self.assertIn("allow_pickle=False", source)

    def test_non_finite_matrix_raises(self):
        """Matrix with NaN/Inf must raise ValueError."""
        import numpy as np
        mat = np.array([[1.0, float("nan")], [0.0, 1.0]])
        with self.assertRaises(ValueError):
            self.mod.compute_stats(mat, 1e-8)

    def test_1d_matrix_raises(self):
        """1D array must raise ValueError."""
        import numpy as np
        with self.assertRaises(ValueError):
            self.mod.compute_stats(np.array([1.0, 2.0]), 1e-8)

    def test_negative_symmetry_tol_raises(self):
        """Negative symmetry tolerance must raise ValueError."""
        import numpy as np
        mat = np.eye(2)
        with self.assertRaises(ValueError):
            self.mod.compute_stats(mat, -1.0)


class TestConvergenceDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "convergence_diagnostics",
            "skills/core-numerical/linear-solvers/scripts/convergence_diagnostics.py",
        )

    def test_parse_list_rejects_nonfinite(self):
        """Non-finite values in parsed list must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.parse_list("1.0,inf,0.5")
        with self.assertRaises(ValueError):
            self.mod.parse_list("1.0,nan,0.5")

    def test_parse_list_rejects_oversized(self):
        """Lists exceeding length limit must raise ValueError."""
        huge = ",".join(["1.0"] * (self.mod.MAX_LIST_LENGTH + 1))
        with self.assertRaises(ValueError):
            self.mod.parse_list(huge)

    def test_parse_list_empty_raises(self):
        with self.assertRaises(ValueError):
            self.mod.parse_list("")


class TestResidualNorms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "residual_norms",
            "skills/core-numerical/linear-solvers/scripts/residual_norms.py",
        )

    def test_parse_list_rejects_nonfinite(self):
        """Non-finite values must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.parse_list("1.0,inf")

    def test_parse_list_rejects_oversized(self):
        """Lists exceeding length limit must raise ValueError."""
        huge = ",".join(["1.0"] * (self.mod.MAX_LIST_LENGTH + 1))
        with self.assertRaises(ValueError):
            self.mod.parse_list(huge)


if __name__ == "__main__":
    unittest.main()
