import unittest

from tests.unit._utils import load_module


class TestResidualMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "residual_monitor",
            "skills/core-numerical/nonlinear-solvers/scripts/residual_monitor.py",
        )

    def test_normal_convergence(self):
        """Test detection of normal convergence pattern."""
        residuals = [1.0, 0.5, 0.25, 0.125, 0.0625]
        result = self.mod.monitor_residuals(residuals)
        self.assertIn("normal", result["patterns_detected"])
        self.assertFalse(result["converged"])

    def test_converged(self):
        """Test detection of converged solver."""
        residuals = [1.0, 0.1, 0.01, 1e-12]
        result = self.mod.monitor_residuals(residuals, target_tolerance=1e-10)
        self.assertTrue(result["converged"])
        self.assertIn("converged", result["recommendations"][0].lower())

    def test_oscillation_detection(self):
        """Test detection of oscillating residuals."""
        residuals = [1.0, 0.8, 1.2, 0.7, 1.1, 0.6, 1.0, 0.5]
        result = self.mod.monitor_residuals(residuals)
        self.assertIn("oscillating", result["patterns_detected"])
        self.assertTrue(len(result["alerts"]) > 0)

    def test_plateau_detection(self):
        """Test detection of residual plateau."""
        residuals = [1.0, 0.5, 0.3, 0.299, 0.298, 0.297, 0.296]
        result = self.mod.monitor_residuals(residuals, target_tolerance=1e-10)
        self.assertIn("plateau", result["patterns_detected"])

    def test_divergence_detection(self):
        """Test detection of diverging solver."""
        residuals = [1.0, 2.0, 4.0, 8.0]
        result = self.mod.monitor_residuals(residuals)
        self.assertIn("diverging", result["patterns_detected"])
        self.assertTrue(len(result["alerts"]) > 0)

    def test_initial_spike_detection(self):
        """Test detection of initial spike."""
        residuals = [1.0, 3.0, 1.5, 0.8, 0.4]
        result = self.mod.monitor_residuals(residuals)
        self.assertIn("initial_spike", result["patterns_detected"])

    def test_function_eval_efficiency(self):
        """Test efficiency calculation with function evaluations."""
        residuals = [1.0, 0.1, 0.01, 0.001]
        function_evals = [1, 3, 5, 7]
        result = self.mod.monitor_residuals(
            residuals, function_evals=function_evals
        )
        self.assertIn("function_evals", result)
        self.assertEqual(result["function_evals"], 7)
        self.assertIn("efficiency", result)

    def test_step_size_trend_decreasing(self):
        """Test detection of decreasing step sizes."""
        residuals = [1.0, 0.8, 0.6, 0.4, 0.3]
        step_sizes = [1.0, 0.8, 0.4, 0.2, 0.1]
        result = self.mod.monitor_residuals(residuals, step_sizes=step_sizes)
        self.assertEqual(result["step_size_trend"], "decreasing")

    def test_step_size_trend_stable(self):
        """Test detection of stable step sizes."""
        residuals = [1.0, 0.8, 0.6, 0.4, 0.3]
        step_sizes = [1.0, 1.0, 1.0, 1.0, 1.0]
        result = self.mod.monitor_residuals(residuals, step_sizes=step_sizes)
        self.assertEqual(result["step_size_trend"], "stable")

    def test_residual_reduction(self):
        """Test residual reduction calculation."""
        residuals = [1.0, 0.1]
        result = self.mod.monitor_residuals(residuals)
        self.assertAlmostEqual(result["residual_reduction"], 0.1, places=5)

    def test_empty_residuals_raises(self):
        """Test that empty residuals raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.monitor_residuals([])

    def test_negative_residual_raises(self):
        """Test that negative residual raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.monitor_residuals([1.0, -0.5, 0.1])

    def test_invalid_tolerance_raises(self):
        """Test that non-positive tolerance raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.monitor_residuals([1.0, 0.5], target_tolerance=-1e-10)


if __name__ == "__main__":
    unittest.main()
