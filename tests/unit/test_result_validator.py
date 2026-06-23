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

    def test_energy_net_decrease(self):
        """Non-variational net-decrease check passes when end <= start."""
        metrics = {"energy_history": [10.0, 9.0, 8.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["energy_net_decrease"])

    def test_energy_net_increases(self):
        """Non-variational net-increase fails."""
        metrics = {"energy_history": [10.0, 11.0, 12.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertFalse(result["checks"]["energy_net_decrease"])

    def test_energy_spike_passes_net_decrease(self):
        """Regression (F8): net-decrease check does NOT catch mid-run spikes.

        Documented limitation: variational runs need --variational.
        """
        metrics = {"energy_history": [10.0, 2.0, 50.0, 9.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["energy_net_decrease"])

    def test_energy_monotone_spike_fails_variational(self):
        """Regression (F8): a mid-run spike fails the variational monotone check."""
        metrics = {"energy_history": [10.0, 2.0, 50.0, 9.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3, variational=True)
        self.assertIn("energy_monotone", result["checks"])
        self.assertFalse(result["checks"]["energy_monotone"])
        self.assertIn("energy_monotone", result["failed_checks"])

    def test_energy_monotone_passes_variational(self):
        """A strictly non-increasing history passes the variational check."""
        metrics = {"energy_history": [10.0, 9.0, 8.0, 7.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3, variational=True)
        self.assertTrue(result["checks"]["energy_monotone"])

    def test_energy_monotone_relative_tolerance(self):
        """Regression (F8): round-off-sized bumps tolerated via relative tol."""
        metrics = {"energy_history": [10.0, 9.0, 9.00000005, 8.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3, variational=True)
        self.assertTrue(result["checks"]["energy_monotone"])

    def test_energy_variational_flag_in_metrics(self):
        """Metrics-level energy_variational:true opts into the strict check."""
        metrics = {"energy_history": [10.0, 2.0, 50.0, 9.0], "energy_variational": True}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertFalse(result["checks"]["energy_monotone"])

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
        """Regression (F9): empty metrics gives no green light."""
        metrics = {}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"].get("no_checks", False))
        # Must NOT report full confidence for an empty/unchecked file.
        self.assertIsNone(result["confidence_score"])
        self.assertEqual(result.get("status"), "INSUFFICIENT_DATA")
        self.assertTrue(result["failed_checks"])

    def test_unrecognized_metrics_no_green_light(self):
        """Regression (F9): a file with no recognized keys is INSUFFICIENT_DATA."""
        metrics = {"foo": 1, "bar": 2}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertIsNone(result["confidence_score"])
        self.assertEqual(result.get("status"), "INSUFFICIENT_DATA")

    def test_bounds_requested_but_field_absent(self):
        """Regression (F9): a requested bound with no field value is NOT a vacuous pass."""
        metrics = {"foo": 1, "bar": 2}
        result = self.mod.validate_metrics(metrics, 0.0, 1.0, 1e-3)
        self.assertNotIn("bounds_satisfied", result["checks"])
        self.assertIn("bounds_unverifiable", result["failed_checks"])
        self.assertNotEqual(result["confidence_score"], 1.0)
        self.assertEqual(result.get("status"), "FAIL")

    def test_mass_tolerance_boundary(self):
        """Test mass at tolerance boundary."""
        metrics = {"mass_initial": 1.0, "mass_final": 1.001}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["mass_conserved"])

    def test_energy_constant(self):
        """Test constant energy passes (net-decrease and variational)."""
        metrics = {"energy_history": [10.0, 10.0, 10.0]}
        result = self.mod.validate_metrics(metrics, None, None, 1e-3)
        self.assertTrue(result["checks"]["energy_net_decrease"])
        result_v = self.mod.validate_metrics(metrics, None, None, 1e-3, variational=True)
        self.assertTrue(result_v["checks"]["energy_monotone"])

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
        self.assertTrue(result["checks"]["energy_net_decrease"])
        self.assertTrue(result["checks"]["bounds_satisfied"])
        self.assertTrue(result["checks"]["no_nan"])
        self.assertEqual(len(result["failed_checks"]), 0)
        self.assertEqual(result["confidence_score"], 1.0)


if __name__ == "__main__":
    unittest.main()
