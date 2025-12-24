import math
import unittest

from tests.unit._utils import load_module


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


if __name__ == "__main__":
    unittest.main()
