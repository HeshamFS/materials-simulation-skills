import unittest

from tests.unit._utils import load_module


class TestAdaptiveStepController(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "adaptive_step_controller",
            "skills/core-numerical/numerical-integration/scripts/adaptive_step_controller.py",
        )

    def test_accept_step(self):
        result = self.mod.compute_step(
            dt=0.1,
            error_norm=0.5,
            order=4,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=5.0,
            controller="p",
            prev_error=None,
        )
        self.assertTrue(result["accept"])
        self.assertGreater(result["dt_next"], 0.1)

    def test_reject_step(self):
        result = self.mod.compute_step(
            dt=0.1,
            error_norm=2.0,
            order=2,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=5.0,
            controller="p",
            prev_error=None,
        )
        self.assertFalse(result["accept"])
        self.assertLess(result["dt_next"], 0.1)

    def test_zero_error(self):
        result = self.mod.compute_step(
            dt=0.1,
            error_norm=0.0,
            order=2,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=3.0,
            controller="p",
            prev_error=None,
        )
        self.assertEqual(result["factor"], 3.0)

    def test_pi_controller(self):
        result = self.mod.compute_step(
            dt=0.1,
            error_norm=0.8,
            order=3,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=5.0,
            controller="pi",
            prev_error=1.2,
        )
        self.assertEqual(result["controller_used"], "pi")
        self.assertTrue(result["accept"])

    def test_factor_clamp(self):
        result = self.mod.compute_step(
            dt=0.1,
            error_norm=1e-12,
            order=4,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=1.5,
            controller="p",
            prev_error=None,
        )
        self.assertAlmostEqual(result["factor"], 1.5, places=6)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            self.mod.compute_step(
                dt=-0.1,
                error_norm=0.5,
                order=1,
                accept_threshold=1.0,
                safety=0.9,
                min_factor=0.2,
                max_factor=5.0,
                controller="p",
                prev_error=None,
            )


if __name__ == "__main__":
    unittest.main()
