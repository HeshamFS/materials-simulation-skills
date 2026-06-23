import subprocess
import sys
import unittest
from pathlib import Path

from tests.unit._utils import load_module

_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills/core-numerical/numerical-integration/scripts/adaptive_step_controller.py"
)


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

    def test_pi_controller_matches_standard_formula(self):
        # Regression (F4): PI factor must follow the standard
        # err^(-alpha) * err_prev^(beta) form with alpha=0.7/(p+1),
        # beta=0.4/(p+1) (Hairer & Wanner / error_control.md), NOT
        # err_prev^(-0.3/(p+1)).
        order = 4
        err = 0.8
        prev = 0.5
        safety = 0.9
        result = self.mod.compute_step(
            dt=1.0,
            error_norm=err,
            order=order,
            accept_threshold=1.0,
            safety=safety,
            min_factor=0.2,
            max_factor=5.0,
            controller="pi",
            prev_error=prev,
        )
        exp = 1.0 / (order + 1.0)
        alpha = 0.7 * exp
        beta = 0.4 * exp
        expected = safety * (err ** (-alpha)) * (prev ** beta)
        self.assertAlmostEqual(result["factor"], expected, places=12)

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


class TestControllerAllowlist(unittest.TestCase):
    """Regression (F2/F3): the CLI controller allowlist is {p, pi}; invalid
    choices must be rejected by argparse with exit code 2 and the documented
    message."""

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(_SCRIPT), *args],
            capture_output=True,
            text=True,
        )

    def test_invalid_controller_rejected(self):
        proc = self._run(
            "--dt", "1e-3", "--error-norm", "0.8", "--order", "4", "--controller", "i"
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("argument --controller: invalid choice", proc.stderr)
        # argparse changed its choice formatting in 3.12 (quoted "'p', 'pi'" ->
        # unquoted "p, pi"); strip quotes so the check holds on 3.10-3.12.
        self.assertIn("p, pi", proc.stderr.replace("'", ""))

    def test_error_norm_message(self):
        proc = self._run("--dt", "1e-3", "--error-norm", "-0.5", "--order", "4")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("error_norm must be finite and non-negative", proc.stderr)


if __name__ == "__main__":
    unittest.main()
