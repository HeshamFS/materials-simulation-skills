import unittest

from tests.unit._utils import load_module


class TestGlobalizationAdvisor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "globalization_advisor",
            "skills/core-numerical/nonlinear-solvers/scripts/globalization_advisor.py",
        )

    def test_line_search_for_good_jacobian(self):
        """Test that line search is recommended for good Jacobian quality."""
        result = self.mod.advise_globalization(
            problem_type="root-finding",
            jacobian_quality="good",
            previous_failures=0,
            oscillating_residual=False,
            step_rejection_rate=0.0,
        )
        self.assertEqual(result["strategy"], "line-search")
        self.assertIsNotNone(result["line_search_type"])
        self.assertIsNone(result["trust_region_type"])

    def test_trust_region_for_ill_conditioned(self):
        """Test that trust region is recommended for ill-conditioned Jacobian."""
        result = self.mod.advise_globalization(
            problem_type="root-finding",
            jacobian_quality="ill-conditioned",
            previous_failures=0,
            oscillating_residual=False,
            step_rejection_rate=0.0,
        )
        self.assertEqual(result["strategy"], "trust-region")
        self.assertIsNotNone(result["trust_region_type"])

    def test_trust_region_for_near_singular(self):
        """Test that trust region with LM is recommended for near-singular."""
        result = self.mod.advise_globalization(
            problem_type="root-finding",
            jacobian_quality="near-singular",
            previous_failures=0,
            oscillating_residual=False,
            step_rejection_rate=0.0,
        )
        self.assertEqual(result["strategy"], "trust-region")
        self.assertEqual(result["trust_region_type"], "Levenberg-Marquardt")

    def test_trust_region_for_least_squares(self):
        """Test that trust region is recommended for least-squares."""
        result = self.mod.advise_globalization(
            problem_type="least-squares",
            jacobian_quality="good",
            previous_failures=0,
            oscillating_residual=False,
            step_rejection_rate=0.0,
        )
        self.assertEqual(result["strategy"], "trust-region")

    def test_trust_region_after_failures(self):
        """Test that trust region is recommended after multiple failures."""
        result = self.mod.advise_globalization(
            problem_type="root-finding",
            jacobian_quality="good",
            previous_failures=3,
            oscillating_residual=False,
            step_rejection_rate=0.0,
        )
        self.assertEqual(result["strategy"], "trust-region")

    def test_trust_region_for_oscillating(self):
        """Test that trust region is recommended for oscillating residuals."""
        result = self.mod.advise_globalization(
            problem_type="root-finding",
            jacobian_quality="good",
            previous_failures=0,
            oscillating_residual=True,
            step_rejection_rate=0.0,
        )
        self.assertEqual(result["strategy"], "trust-region")

    def test_trust_region_for_high_rejection(self):
        """Test that trust region is recommended for high step rejection rate."""
        result = self.mod.advise_globalization(
            problem_type="root-finding",
            jacobian_quality="good",
            previous_failures=0,
            oscillating_residual=False,
            step_rejection_rate=0.5,
        )
        self.assertEqual(result["strategy"], "trust-region")

    def test_wolfe_for_optimization(self):
        """Test that Wolfe line search is recommended for optimization."""
        result = self.mod.advise_globalization(
            problem_type="optimization",
            jacobian_quality="good",
            previous_failures=0,
            oscillating_residual=False,
            step_rejection_rate=0.0,
        )
        self.assertEqual(result["strategy"], "line-search")
        self.assertEqual(result["line_search_type"], "Wolfe")

    def test_armijo_for_root_finding(self):
        """Test that Armijo is recommended for root-finding."""
        result = self.mod.advise_globalization(
            problem_type="root-finding",
            jacobian_quality="good",
            previous_failures=0,
            oscillating_residual=False,
            step_rejection_rate=0.0,
        )
        self.assertEqual(result["line_search_type"], "Armijo")

    def test_parameters_present(self):
        """Test that parameters are included in output."""
        result = self.mod.advise_globalization(
            problem_type="root-finding",
            jacobian_quality="good",
            previous_failures=0,
            oscillating_residual=False,
            step_rejection_rate=0.0,
        )
        self.assertIn("parameters", result)
        self.assertIsInstance(result["parameters"], dict)

    def test_invalid_problem_type_raises(self):
        """Test that invalid problem type raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.advise_globalization(
                problem_type="invalid",
                jacobian_quality="good",
                previous_failures=0,
                oscillating_residual=False,
                step_rejection_rate=0.0,
            )

    def test_invalid_jacobian_quality_raises(self):
        """Test that invalid jacobian quality raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.advise_globalization(
                problem_type="root-finding",
                jacobian_quality="invalid",
                previous_failures=0,
                oscillating_residual=False,
                step_rejection_rate=0.0,
            )

    def test_invalid_step_rejection_rate_raises(self):
        """Test that out-of-range step rejection rate raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.advise_globalization(
                problem_type="root-finding",
                jacobian_quality="good",
                previous_failures=0,
                oscillating_residual=False,
                step_rejection_rate=1.5,
            )


if __name__ == "__main__":
    unittest.main()
