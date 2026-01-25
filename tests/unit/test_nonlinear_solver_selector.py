import unittest

from tests.unit._utils import load_module


class TestNonlinearSolverSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "solver_selector",
            "skills/core-numerical/nonlinear-solvers/scripts/solver_selector.py",
        )

    def test_newton_full_small_with_jacobian(self):
        """Test that full Newton is recommended for small problems with available Jacobian."""
        result = self.mod.select_solver(
            jacobian_available=True,
            jacobian_expensive=False,
            problem_size=500,
            spd_hessian=False,
            smooth_objective=True,
            constraint_type="none",
            memory_limited=False,
            high_accuracy=False,
        )
        self.assertIn("Newton (full)", result["recommended"])

    def test_newton_krylov_large_with_jacobian(self):
        """Test that Newton-Krylov is recommended for large problems."""
        result = self.mod.select_solver(
            jacobian_available=True,
            jacobian_expensive=False,
            problem_size=50000,
            spd_hessian=False,
            smooth_objective=True,
            constraint_type="none",
            memory_limited=False,
            high_accuracy=False,
        )
        self.assertIn("Newton-Krylov (GMRES)", result["recommended"])

    def test_lbfgs_no_jacobian_memory_limited(self):
        """Test that L-BFGS is recommended when no Jacobian and memory limited."""
        result = self.mod.select_solver(
            jacobian_available=False,
            jacobian_expensive=False,
            problem_size=10000,
            spd_hessian=False,
            smooth_objective=True,
            constraint_type="none",
            memory_limited=True,
            high_accuracy=False,
        )
        self.assertIn("L-BFGS", result["recommended"])

    def test_bfgs_no_jacobian_smooth(self):
        """Test that BFGS is recommended for smooth problems without Jacobian."""
        result = self.mod.select_solver(
            jacobian_available=False,
            jacobian_expensive=False,
            problem_size=100,
            spd_hessian=False,
            smooth_objective=True,
            constraint_type="none",
            memory_limited=False,
            high_accuracy=False,
        )
        self.assertIn("BFGS", result["recommended"])

    def test_anderson_non_smooth(self):
        """Test that Anderson acceleration is recommended for non-smooth problems."""
        result = self.mod.select_solver(
            jacobian_available=False,
            jacobian_expensive=False,
            problem_size=1000,
            spd_hessian=False,
            smooth_objective=False,
            constraint_type="none",
            memory_limited=False,
            high_accuracy=False,
        )
        self.assertIn("Anderson Acceleration", result["recommended"])

    def test_lbfgsb_bound_constrained(self):
        """Test that L-BFGS-B is recommended for bound constrained with SPD Hessian."""
        result = self.mod.select_solver(
            jacobian_available=False,
            jacobian_expensive=False,
            problem_size=1000,
            spd_hessian=True,
            smooth_objective=True,
            constraint_type="bound",
            memory_limited=False,
            high_accuracy=False,
        )
        self.assertIn("L-BFGS-B", result["recommended"])

    def test_sqp_equality_constrained(self):
        """Test that SQP is recommended for equality constrained problems."""
        result = self.mod.select_solver(
            jacobian_available=True,
            jacobian_expensive=False,
            problem_size=100,
            spd_hessian=False,
            smooth_objective=True,
            constraint_type="equality",
            memory_limited=False,
            high_accuracy=False,
        )
        self.assertIn("SQP", result["recommended"])

    def test_sqp_inequality_constrained(self):
        """Test that SQP is recommended for inequality constrained problems."""
        result = self.mod.select_solver(
            jacobian_available=True,
            jacobian_expensive=False,
            problem_size=100,
            spd_hessian=False,
            smooth_objective=True,
            constraint_type="inequality",
            memory_limited=False,
            high_accuracy=False,
        )
        self.assertIn("SQP (Sequential Quadratic Programming)", result["recommended"])

    def test_high_accuracy_newton(self):
        """Test that full Newton is recommended when high accuracy is needed."""
        result = self.mod.select_solver(
            jacobian_available=True,
            jacobian_expensive=False,
            problem_size=500,
            spd_hessian=False,
            smooth_objective=True,
            constraint_type="none",
            memory_limited=False,
            high_accuracy=True,
        )
        self.assertIn("Newton (full)", result["recommended"])
        self.assertTrue(any("quadratic" in note.lower() for note in result["notes"]))

    def test_invalid_size(self):
        """Test that invalid problem size raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.select_solver(
                jacobian_available=False,
                jacobian_expensive=False,
                problem_size=0,
                spd_hessian=False,
                smooth_objective=True,
                constraint_type="none",
                memory_limited=False,
                high_accuracy=False,
            )

    def test_invalid_constraint_type(self):
        """Test that invalid constraint type raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.select_solver(
                jacobian_available=False,
                jacobian_expensive=False,
                problem_size=100,
                spd_hessian=False,
                smooth_objective=True,
                constraint_type="invalid",
                memory_limited=False,
                high_accuracy=False,
            )


if __name__ == "__main__":
    unittest.main()
