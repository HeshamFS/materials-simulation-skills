import unittest

from tests.unit._utils import load_module


class TestNonlinearConvergenceAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "convergence_analyzer",
            "skills/core-numerical/nonlinear-solvers/scripts/convergence_analyzer.py",
        )

    def test_converged_quadratic(self):
        """Test detection of quadratic convergence."""
        # Simulate quadratic convergence: residual squares each iteration
        residuals = [1.0, 0.1, 0.01, 0.0001, 1e-8, 1e-16]
        result = self.mod.analyze_convergence(residuals, tolerance=1e-10)
        self.assertTrue(result["converged"])
        self.assertEqual(result["iterations"], 6)

    def test_linear_convergence(self):
        """Test detection of linear convergence."""
        # Linear convergence with rate ~0.5
        residuals = [1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125]
        result = self.mod.analyze_convergence(residuals, tolerance=1e-10)
        self.assertFalse(result["converged"])
        self.assertEqual(result["convergence_type"], "linear")
        self.assertIsNotNone(result["estimated_rate"])
        self.assertAlmostEqual(result["estimated_rate"], 0.5, places=2)

    def test_stagnation_detection(self):
        """Test detection of stagnation."""
        # Last 3 residuals must have < 1% relative change to trigger stagnation
        residuals = [1.0, 0.5, 0.3, 0.1, 0.1, 0.1]
        result = self.mod.analyze_convergence(residuals, tolerance=1e-10)
        self.assertEqual(result["convergence_type"], "stagnated")
        self.assertFalse(result["converged"])

    def test_divergence_detection(self):
        """Test detection of divergence."""
        residuals = [1.0, 2.0, 5.0, 15.0]
        result = self.mod.analyze_convergence(residuals, tolerance=1e-10)
        self.assertEqual(result["convergence_type"], "diverged")
        self.assertFalse(result["converged"])
        self.assertIn("diverging", result["diagnosis"].lower())

    def test_single_residual(self):
        """Test handling of single residual."""
        residuals = [0.001]
        result = self.mod.analyze_convergence(residuals, tolerance=1e-10)
        self.assertEqual(result["convergence_type"], "unknown")
        self.assertEqual(result["iterations"], 1)

    def test_converged_at_tolerance(self):
        """Test that convergence is detected when tolerance is met."""
        residuals = [1.0, 0.1, 0.01, 1e-11]
        result = self.mod.analyze_convergence(residuals, tolerance=1e-10)
        self.assertTrue(result["converged"])
        self.assertEqual(result["final_residual"], 1e-11)

    def test_sublinear_detection(self):
        """Test detection of sublinear convergence."""
        # Very slow convergence: rate > 0.9
        residuals = [1.0, 0.95, 0.91, 0.87, 0.84, 0.81, 0.78, 0.76]
        result = self.mod.analyze_convergence(residuals, tolerance=1e-10)
        self.assertEqual(result["convergence_type"], "sublinear")

    def test_empty_residuals_raises(self):
        """Test that empty residuals raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.analyze_convergence([], tolerance=1e-10)

    def test_negative_residual_raises(self):
        """Test that negative residual raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.analyze_convergence([1.0, -0.5, 0.1], tolerance=1e-10)

    def test_invalid_tolerance_raises(self):
        """Test that non-positive tolerance raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.analyze_convergence([1.0, 0.5], tolerance=0)
        with self.assertRaises(ValueError):
            self.mod.analyze_convergence([1.0, 0.5], tolerance=-1e-10)


if __name__ == "__main__":
    unittest.main()
