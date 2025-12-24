import unittest

from tests.unit._utils import load_module


class TestResultValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "result_validator",
            "skills/simulation-workflow/simulation-validator/scripts/result_validator.py",
        )

    def test_mass_conserved(self):
        """Test mass conservation check passes."""
        metrics = {"mass_initial": 1.0, "mass_final": 1.0005}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["mass_conserved"])

    def test_mass_not_conserved(self):
        """Test mass conservation check fails."""
        metrics = {"mass_initial": 1.0, "mass_final": 1.1}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertFalse(result["checks"]["mass_conserved"])
        self.assertIn("mass_conserved", result["failed_checks"])

    def test_energy_decreases(self):
        """Test energy decrease check passes."""
        metrics = {"energy_history": [10.0, 9.0, 8.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["energy_decreases"])

    def test_energy_increases(self):
        """Test energy increase check fails."""
        metrics = {"energy_history": [10.0, 11.0, 12.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertFalse(result["checks"]["energy_decreases"])

    def test_bounds_satisfied(self):
        """Test bounds check passes."""
        metrics = {"field_min": 0.0, "field_max": 1.0}
        result = self.mod.validate_metrics(metrics, 0.0, 1.0, 1e-3)
        self.assertTrue(result["checks"]["bounds_satisfied"])

    def test_bounds_violated_min(self):
        """Test bounds check fails on min violation."""
        metrics = {"field_min": -0.1, "field_max": 1.0}
        result = self.mod.validate_metrics(metrics, 0.0, 1.0, 1e-3)
        self.assertFalse(result["checks"]["bounds_satisfied"])

    def test_bounds_violated_max(self):
        """Test bounds check fails on max violation."""
        metrics = {"field_min": 0.0, "field_max": 1.2}
        result = self.mod.validate_metrics(metrics, 0.0, 1.0, 1e-3)
        self.assertFalse(result["checks"]["bounds_satisfied"])

    def test_nan_detected(self):
        """Test NaN detection fails."""
        metrics = {"has_nan": True}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertFalse(result["checks"]["no_nan"])
        self.assertIn("no_nan", result["failed_checks"])

    def test_no_nan(self):
        """Test no NaN passes."""
        metrics = {"has_nan": False}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["no_nan"])

    def test_confidence_score_all_pass(self):
        """Test confidence score when all checks pass."""
        metrics = {
            "mass_initial": 1.0,
            "mass_final": 1.0,
            "energy_history": [10.0, 9.0],
            "field_min": 0.0,
            "field_max": 1.0,
            "has_nan": False,
        }
        result = self.mod.validate_metrics(metrics, 0.0, 1.0, 1e-3)
        self.assertEqual(result["confidence_score"], 1.0)

    def test_confidence_score_partial(self):
        """Test confidence score with partial pass."""
        metrics = {
            "mass_initial": 1.0,
            "mass_final": 1.0,
            "energy_history": [10.0, 11.0],  # Fails
            "field_min": 0.0,
            "field_max": 1.0,
            "has_nan": False,
        }
        result = self.mod.validate_metrics(metrics, 0.0, 1.0, 1e-3)
        self.assertGreater(result["confidence_score"], 0.5)
        self.assertLess(result["confidence_score"], 1.0)

    def test_no_checks_available(self):
        """Test empty metrics gives no_checks."""
        metrics = {}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"].get("no_checks", False))

    def test_mass_tolerance_boundary(self):
        """Test mass at tolerance boundary."""
        metrics = {"mass_initial": 1.0, "mass_final": 1.001}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["mass_conserved"])

    def test_energy_constant(self):
        """Test constant energy passes."""
        metrics = {"energy_history": [10.0, 10.0, 10.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["energy_decreases"])

    def test_only_bound_min(self):
        """Test only bound_min specified."""
        metrics = {"field_min": 0.5, "field_max": 10.0}
        result = self.mod.validate_metrics(metrics, 0.0, None, 1e-3)
        self.assertTrue(result["checks"]["bounds_satisfied"])

    def test_only_bound_max(self):
        """Test only bound_max specified."""
        metrics = {"field_min": -10.0, "field_max": 0.9}
        result = self.mod.validate_metrics(metrics, None, 1.0, 1e-3)
        self.assertTrue(result["checks"]["bounds_satisfied"])

    def test_combined_all_checks(self):
        """Test all checks combined."""
        metrics = {
            "mass_initial": 1.0,
            "mass_final": 1.0005,
            "energy_history": [10.0, 9.0],
            "field_min": 0.0,
            "field_max": 1.0,
            "has_nan": False,
        }
        result = self.mod.validate_metrics(metrics, 0.0, 1.0, 1e-3)
        self.assertTrue(result["checks"]["mass_conserved"])
        self.assertTrue(result["checks"]["energy_decreases"])
        self.assertTrue(result["checks"]["bounds_satisfied"])
        self.assertTrue(result["checks"]["no_nan"])
        self.assertEqual(len(result["failed_checks"]), 0)


if __name__ == "__main__":
    unittest.main()
