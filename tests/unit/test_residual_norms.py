import unittest

from tests.unit._utils import load_module


class TestResidualNorms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "residual_norms",
            "skills/core-numerical/linear-solvers/scripts/residual_norms.py",
        )

    def test_norms_and_convergence(self):
        residual = [0.1, 0.0, -0.1]
        rhs = [1.0, 0.0, 0.0]
        residual_norms, reference_norms, relative_norms, meta = self.mod.compute_residual_metrics(
            residual=residual,
            rhs=rhs,
            initial=None,
            abs_tol=0.2,
            rel_tol=0.2,
            norm="l2",
            require_both=False,
        )
        self.assertAlmostEqual(residual_norms["l2"], 0.141421356, places=6)
        self.assertIsNotNone(reference_norms)
        self.assertIsNotNone(relative_norms)
        self.assertTrue(meta["converged"])

    def test_require_both(self):
        residual = [0.1, 0.0, -0.1]
        rhs = [1.0, 0.0, 0.0]
        _, _, _, meta = self.mod.compute_residual_metrics(
            residual=residual,
            rhs=rhs,
            initial=None,
            abs_tol=0.05,
            rel_tol=0.2,
            norm="l2",
            require_both=True,
        )
        self.assertFalse(meta["converged"])

    def test_nonfinite_tolerance_rejected(self):
        """Security hardening: non-finite tolerances must raise ValueError."""
        for abs_tol, rel_tol in ((float("inf"), 1e-6), (1e-8, float("nan"))):
            with self.assertRaises(ValueError):
                self.mod.compute_residual_metrics(
                    residual=[1.0],
                    rhs=None,
                    initial=None,
                    abs_tol=abs_tol,
                    rel_tol=rel_tol,
                    norm="l2",
                    require_both=False,
                )

    def test_invalid_norm(self):
        with self.assertRaises(ValueError):
            self.mod.compute_residual_metrics(
                residual=[1.0],
                rhs=None,
                initial=None,
                abs_tol=1e-8,
                rel_tol=1e-6,
                norm="bad",
                require_both=False,
            )


if __name__ == "__main__":
    unittest.main()
