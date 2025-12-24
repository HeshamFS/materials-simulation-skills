import unittest

from tests.unit._utils import load_module


class TestNumericalIntegrationProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.error_norm = load_module(
            "error_norm",
            "skills/core-numerical/numerical-integration/scripts/error_norm.py",
        )
        cls.controller = load_module(
            "adaptive_step_controller",
            "skills/core-numerical/numerical-integration/scripts/adaptive_step_controller.py",
        )
        cls.selector = load_module(
            "integrator_selector",
            "skills/core-numerical/numerical-integration/scripts/integrator_selector.py",
        )

    def test_error_norm_scales_linearly(self):
        error = [0.1, 0.2]
        scale = [0.5, 0.5]
        base, _, _, _ = self.error_norm.compute_error_norm(
            error=error,
            solution=None,
            scale=scale,
            rtol=1e-3,
            atol=1e-6,
            norm="rms",
            min_scale=0.0,
        )
        scaled, _, _, _ = self.error_norm.compute_error_norm(
            error=[e * 3.0 for e in error],
            solution=None,
            scale=scale,
            rtol=1e-3,
            atol=1e-6,
            norm="rms",
            min_scale=0.0,
        )
        self.assertAlmostEqual(scaled, base * 3.0, places=6)

    def test_dt_factor_monotonic(self):
        low_error = self.controller.compute_step(
            dt=0.1,
            error_norm=0.1,
            order=3,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=5.0,
            controller="p",
            prev_error=None,
        )
        high_error = self.controller.compute_step(
            dt=0.1,
            error_norm=2.0,
            order=3,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=5.0,
            controller="p",
            prev_error=None,
        )
        self.assertGreater(low_error["factor"], high_error["factor"])

    def test_event_detection_note(self):
        result = self.selector.select_integrator(
            stiff=False,
            oscillatory=False,
            event_detection=True,
            jacobian_available=False,
            implicit_allowed=False,
            accuracy="medium",
            dimension=10,
            low_memory=False,
        )
        self.assertTrue(any("dense output" in note for note in result["notes"]))


if __name__ == "__main__":
    unittest.main()
