import unittest

from tests.unit._utils import load_module


class TestRuntimeMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "runtime_monitor",
            "skills/simulation-workflow/simulation-validator/scripts/runtime_monitor.py",
        )

    def test_residual_growth_alert(self):
        """Test residual growth triggers alert."""
        result = self.mod.monitor(
            residuals=[1.0, 20.0],
            dts=[1e-3, 1e-3],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        self.assertTrue(result["alerts"])
        self.assertTrue(any("Residual" in a for a in result["alerts"]))

    def test_dt_drop_alert(self):
        """Test dt reduction triggers alert."""
        result = self.mod.monitor(
            residuals=[1.0, 0.5],
            dts=[1e-3, 1e-5],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        self.assertTrue(result["alerts"])
        self.assertTrue(any("Time step" in a for a in result["alerts"]))

    def test_no_alerts_stable(self):
        """Test no alerts for stable simulation."""
        result = self.mod.monitor(
            residuals=[1.0, 0.5, 0.25],
            dts=[1e-3, 9e-4, 8e-4],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        self.assertFalse(result["alerts"])

    def test_residual_stats(self):
        """Test residual statistics are computed."""
        result = self.mod.monitor(
            residuals=[1.0, 0.5, 0.1],
            dts=[],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        stats = result["residual_stats"]
        self.assertEqual(stats["min"], 0.1)
        self.assertEqual(stats["max"], 1.0)
        self.assertEqual(stats["last"], 0.1)

    def test_dt_stats(self):
        """Test dt statistics are computed."""
        result = self.mod.monitor(
            residuals=[],
            dts=[1e-3, 1e-4, 1e-5],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        stats = result["dt_stats"]
        self.assertEqual(stats["min"], 1e-5)
        self.assertEqual(stats["max"], 1e-3)
        self.assertEqual(stats["last"], 1e-5)

    def test_empty_residuals(self):
        """Test empty residuals produces None stats."""
        result = self.mod.monitor(
            residuals=[],
            dts=[1e-3],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        self.assertIsNone(result["residual_stats"]["min"])
        self.assertIsNone(result["residual_stats"]["max"])
        self.assertIsNone(result["residual_stats"]["last"])

    def test_empty_dts(self):
        """Test empty dts produces None stats."""
        result = self.mod.monitor(
            residuals=[1.0],
            dts=[],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        self.assertIsNone(result["dt_stats"]["min"])
        self.assertIsNone(result["dt_stats"]["max"])
        self.assertIsNone(result["dt_stats"]["last"])

    def test_both_alerts(self):
        """Test both residual and dt alerts can trigger."""
        result = self.mod.monitor(
            residuals=[1.0, 100.0],
            dts=[1e-3, 1e-6],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        self.assertEqual(len(result["alerts"]), 2)

    def test_threshold_boundary_residual(self):
        """Test residual at exact threshold."""
        result = self.mod.monitor(
            residuals=[1.0, 10.0],
            dts=[],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        # Exactly at threshold should NOT trigger (> not >=)
        self.assertFalse(result["alerts"])

    def test_threshold_boundary_dt(self):
        """Test dt at exact threshold."""
        result = self.mod.monitor(
            residuals=[],
            dts=[1e-3, 2e-5],  # ratio = 50
            residual_growth=10.0,
            dt_drop=50.0,
        )
        # Exactly at threshold should NOT trigger (> not >=)
        self.assertFalse(result["alerts"])

    def test_single_residual(self):
        """Test single residual value (no comparison)."""
        result = self.mod.monitor(
            residuals=[1.0],
            dts=[],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        self.assertFalse(result["alerts"])
        self.assertEqual(result["residual_stats"]["last"], 1.0)

    def test_single_dt(self):
        """Test single dt value (no drop possible)."""
        result = self.mod.monitor(
            residuals=[],
            dts=[1e-3],
            residual_growth=10.0,
            dt_drop=50.0,
        )
        self.assertFalse(result["alerts"])

    def test_parse_log_residual_pattern(self):
        """Test parse_log extracts residual values."""
        log = "residual = 1.5e-3\nresidual = 1.0e-4"
        residuals, dts = self.mod.parse_log(
            log,
            residual_pattern=r"residual[^0-9eE+\-]*([0-9][0-9eE+\.-]*)",
            dt_pattern=r"dt[^0-9eE+\-]*([0-9][0-9eE+\.-]*)",
        )
        self.assertEqual(len(residuals), 2)
        self.assertAlmostEqual(residuals[0], 1.5e-3, places=10)

    def test_parse_log_dt_pattern(self):
        """Test parse_log extracts dt values."""
        log = "dt = 0.001\ndt = 0.0005"
        residuals, dts = self.mod.parse_log(
            log,
            residual_pattern=r"residual[^0-9eE+\-]*([0-9][0-9eE+\.-]*)",
            dt_pattern=r"dt[^0-9eE+\-]*([0-9][0-9eE+\.-]*)",
        )
        self.assertEqual(len(dts), 2)
        self.assertAlmostEqual(dts[0], 0.001, places=10)

    def test_compute_stats_values(self):
        """Test compute_stats helper function."""
        stats = self.mod.compute_stats([5.0, 2.0, 8.0, 3.0])
        self.assertEqual(stats["min"], 2.0)
        self.assertEqual(stats["max"], 8.0)
        self.assertEqual(stats["last"], 3.0)

    # --- F4: dt pattern regression ---
    def test_dt_pattern_parses_adaptive_reduction(self):
        """Regression (F4): 'dt reduced from 1e-3 to 5e-4' captures the 'to' value."""
        _, dts = self.mod.parse_log(
            "dt reduced from 1e-3 to 5e-4",
            residual_pattern=r"residual[^0-9eE+\-]*([0-9][0-9eE+\.-]*)",
            dt_pattern=self.mod.DEFAULT_DT_PATTERN,
        )
        self.assertEqual(dts, [5e-4])

    def test_dt_pattern_ignores_width(self):
        """Regression (F4): 'width 0.5 mm' must NOT be captured as dt."""
        _, dts = self.mod.parse_log(
            "width 0.5 mm",
            residual_pattern=r"residual[^0-9eE+\-]*([0-9][0-9eE+\.-]*)",
            dt_pattern=self.mod.DEFAULT_DT_PATTERN,
        )
        self.assertEqual(dts, [])

    def test_dt_pattern_canonical_lines(self):
        """Regression (F4): canonical log_patterns.md dt lines all parse."""
        log = (
            "[INFO] dt reduced from 1e-3 to 5e-4\n"
            "[WARN] dt approaching minimum: 1.2e-10\n"
            "DT=2.0\n"
            "dt = 1e-5\n"
        )
        _, dts = self.mod.parse_log(
            log,
            residual_pattern=r"residual[^0-9eE+\-]*([0-9][0-9eE+\.-]*)",
            dt_pattern=self.mod.DEFAULT_DT_PATTERN,
        )
        self.assertEqual(dts, [5e-4, 1.2e-10, 2.0, 1e-5])
        result = self.mod.monitor(
            residuals=[], dts=dts, residual_growth=10.0, dt_drop=100.0
        )
        # peak 2.0 -> 1.2e-10 is a collapse > 100x
        self.assertTrue(any("Time step" in a for a in result["alerts"]))

    # --- F5: direction-aware dt collapse ---
    def test_dt_ramp_up_no_alert(self):
        """Regression (F5): a healthy dt ramp-up does NOT trigger a collapse alert."""
        result = self.mod.monitor(
            residuals=[], dts=[1e-6, 1e-5, 1e-4, 1e-2],
            residual_growth=10.0, dt_drop=100.0,
        )
        self.assertFalse(any("Time step" in a for a in result["alerts"]))

    def test_dt_collapse_alerts(self):
        """Regression (F5): an actual collapse from peak triggers an alert."""
        result = self.mod.monitor(
            residuals=[], dts=[1e-2, 1e-4, 1e-6],
            residual_growth=10.0, dt_drop=100.0,
        )
        self.assertTrue(any("Time step" in a for a in result["alerts"]))

    def test_dt_collapse_after_ramp(self):
        """Regression (F5): ramp then collapse below running max alerts."""
        result = self.mod.monitor(
            residuals=[], dts=[1e-4, 1e-2, 1e-6],
            residual_growth=10.0, dt_drop=100.0,
        )
        self.assertTrue(any("Time step" in a for a in result["alerts"]))

    # --- F1: NaN/Inf detection in the runtime monitor ---
    def test_scan_nan_inf_detects(self):
        """Regression (F1): runtime monitor scans for NaN/Inf/overflow."""
        self.assertTrue(self.mod.scan_nan_inf("[ERROR] Field contains NaN at step 1523"))
        self.assertTrue(self.mod.scan_nan_inf("Solution overflow at t=0.02"))

    def test_scan_nan_inf_ignores_domain_words(self):
        """Regression (F1/F3): domain words do not trigger NaN/Inf detection."""
        self.assertFalse(self.mod.scan_nan_inf("nanometer scale resolved"))
        self.assertFalse(self.mod.scan_nan_inf("information logged; infrastructure ok"))

    def test_monitor_emits_nan_alert(self):
        """Regression (F1): has_nan_inf flag surfaces an alert."""
        result = self.mod.monitor(
            residuals=[1.0], dts=[1e-3],
            residual_growth=10.0, dt_drop=100.0, has_nan_inf=True,
        )
        self.assertTrue(any("NaN" in a for a in result["alerts"]))

    # --- F6: threshold validators ---
    def test_positive_finite_float_rejects_bad(self):
        """Regression (F6): non-finite/non-positive thresholds are rejected."""
        import argparse
        for bad in ["-5", "0", "nan", "inf", "abc"]:
            with self.assertRaises(argparse.ArgumentTypeError):
                self.mod.positive_finite_float(bad)
        self.assertEqual(self.mod.positive_finite_float("10.0"), 10.0)


if __name__ == "__main__":
    unittest.main()
