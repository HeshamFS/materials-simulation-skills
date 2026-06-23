import math
import subprocess
import sys
import unittest
from pathlib import Path

from tests.unit._utils import load_module

_SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills/core-numerical/numerical-integration/scripts/error_norm.py"
)


class TestErrorNorm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "error_norm",
            "skills/core-numerical/numerical-integration/scripts/error_norm.py",
        )

    def test_rms_norm(self):
        error = [0.1, 0.2]
        solution = [1.0, 2.0]
        error_norm, max_component, scale_min, scale_max = self.mod.compute_error_norm(
            error=error,
            solution=solution,
            scale=None,
            rtol=1e-3,
            atol=1e-6,
            norm="rms",
            min_scale=0.0,
        )
        scale = [1e-6 + 1e-3 * 1.0, 1e-6 + 1e-3 * 2.0]
        expected = math.sqrt(
            ((0.1 / scale[0]) ** 2 + (0.2 / scale[1]) ** 2) / 2.0
        )
        self.assertAlmostEqual(error_norm, expected, places=6)
        self.assertAlmostEqual(max_component, max(0.1 / scale[0], 0.2 / scale[1]), places=6)
        self.assertAlmostEqual(scale_min, min(scale), places=12)
        self.assertAlmostEqual(scale_max, max(scale), places=12)

    def test_inf_norm(self):
        error = [0.1, -0.3]
        scale = [0.1, 0.2]
        error_norm, max_component, _, _ = self.mod.compute_error_norm(
            error=error,
            solution=None,
            scale=scale,
            rtol=1e-3,
            atol=1e-6,
            norm="inf",
            min_scale=0.0,
        )
        self.assertAlmostEqual(error_norm, 1.5, places=6)
        self.assertAlmostEqual(max_component, 1.5, places=6)

    def test_length_mismatch(self):
        with self.assertRaises(ValueError):
            self.mod.compute_error_norm(
                error=[0.1, 0.2],
                solution=[1.0],
                scale=None,
                rtol=1e-3,
                atol=1e-6,
                norm="rms",
                min_scale=0.0,
            )

    def test_negative_tolerance(self):
        with self.assertRaises(ValueError):
            self.mod.compute_error_norm(
                error=[0.1],
                solution=[1.0],
                scale=None,
                rtol=-1e-3,
                atol=1e-6,
                norm="rms",
                min_scale=0.0,
            )

    def test_solution_scale_collapse_raises(self):
        # Regression (F1): rtol=0, atol=0, default min_scale=0 makes every
        # scale entry 0. Must raise a clean ValueError instead of an
        # uncaught ZeroDivisionError.
        with self.assertRaises(ValueError):
            self.mod.compute_error_norm(
                error=[0.01],
                solution=[1.0],
                scale=None,
                rtol=0.0,
                atol=0.0,
                norm="rms",
                min_scale=0.0,
            )

    def test_min_scale(self):
        error = [0.0]
        solution = [0.0]
        _, _, scale_min, scale_max = self.mod.compute_error_norm(
            error=error,
            solution=solution,
            scale=None,
            rtol=0.0,
            atol=0.0,
            norm="rms",
            min_scale=1e-3,
        )
        self.assertAlmostEqual(scale_min, 1e-3, places=12)
        self.assertAlmostEqual(scale_max, 1e-3, places=12)


class TestErrorNormCliMessages(unittest.TestCase):
    """Regression (F3): the exact strings documented in SKILL.md's Error
    Handling table must actually be emitted by the script, and bad input must
    exit 2."""

    def _run(self, *args):
        return subprocess.run(
            [sys.executable, str(_SCRIPT), *args],
            capture_output=True,
            text=True,
        )

    def test_negative_rtol_message(self):
        proc = self._run("--error", "0.01", "--solution", "1.0", "--rtol=-1e-3")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("rtol must be a non-negative finite number", proc.stderr)

    def test_negative_atol_message(self):
        proc = self._run("--error", "0.01", "--solution", "1.0", "--atol=-1e-6")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("atol must be a non-negative finite number", proc.stderr)

    def test_scale_collapse_message(self):
        proc = self._run(
            "--error", "0.01", "--solution", "1.0", "--rtol", "0", "--atol", "0"
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("scale must be positive", proc.stderr)


if __name__ == "__main__":
    unittest.main()
