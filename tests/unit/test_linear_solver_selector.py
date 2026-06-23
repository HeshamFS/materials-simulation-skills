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

    def test_symmetric_indefinite_small_dense(self):
        """Small dense symmetric-indefinite -> direct LDL^T (Bunch-Kaufman)."""
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
        self.assertIn("LDL^T (Bunch-Kaufman)", result["recommended"])
        self.assertIn("MINRES", result["alternatives"])

    def test_symmetric_indefinite_large_sparse(self):
        """Large sparse symmetric-indefinite -> iterative MINRES."""
        result = self.mod.select_solver(
            symmetric=True,
            positive_definite=False,
            sparse=True,
            size=500_000,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=False,
        )
        self.assertIn("MINRES", result["recommended"])

    def test_dense_spd_infeasible_routes_to_cg(self):
        """Regression (F3): a dense SPD matrix too large to factor in memory
        must route to CG with a dense-storage note, not recommend Cholesky."""
        result = self.mod.select_solver(
            symmetric=True,
            positive_definite=True,
            sparse=False,
            size=199_999,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=False,
        )
        self.assertIn("CG", result["recommended"])
        self.assertNotIn("Cholesky", result["recommended"])
        self.assertTrue(any("GB" in note for note in result["notes"]))

    def test_small_dense_spd_uses_cholesky(self):
        """Small dense SPD still recommends a direct Cholesky factorization."""
        result = self.mod.select_solver(
            symmetric=True,
            positive_definite=True,
            sparse=False,
            size=1000,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=False,
        )
        self.assertIn("Cholesky", result["recommended"])

    def test_small_dense_nonsymmetric_uses_lu(self):
        """Small dense nonsymmetric -> direct LU with partial pivoting."""
        result = self.mod.select_solver(
            symmetric=False,
            positive_definite=False,
            sparse=False,
            size=800,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=False,
        )
        self.assertIn("LU (partial pivoting)", result["recommended"])

    def test_saddle_point(self):
        """Regression (F6): saddle-point structure routes to Schur/Uzawa with a
        block-preconditioner warning."""
        result = self.mod.select_solver(
            symmetric=False,
            positive_definite=False,
            sparse=True,
            size=50_000,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=False,
            saddle_point=True,
        )
        self.assertTrue(any("Schur" in r for r in result["recommended"]))
        self.assertTrue(any("block" in note.lower() for note in result["notes"]))

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
