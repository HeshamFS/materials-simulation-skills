import unittest

import numpy as np

from tests.unit._utils import load_module


class TestVonNeumannAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "von_neumann_analyzer",
            "skills/core-numerical/numerical-stability/scripts/von_neumann_analyzer.py",
        )

    def test_stable_average(self):
        coeffs = np.array([0.2, 0.6, 0.2], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=128,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertTrue(result["results"]["stable"])
        self.assertLessEqual(result["results"]["max_amplification"], 1.0 + 1e-6)

    def test_unstable_two_point(self):
        coeffs = np.array([1.2, -0.2], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=128,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertFalse(result["results"]["stable"])
        self.assertGreater(result["results"]["max_amplification"], 1.0)

    def test_invalid_inputs(self):
        coeffs = np.array([0.5, 0.5], dtype=float)
        with self.assertRaises(ValueError):
            self.mod.compute_amplification(
                coeffs=coeffs,
                dx=0.0,
                nk=128,
                offset=None,
                kmin=None,
                kmax=None,
            )

    def test_invalid_offset(self):
        coeffs = np.array([0.5, 0.5, 0.0], dtype=float)
        with self.assertRaises(ValueError):
            self.mod.compute_amplification(
                coeffs=coeffs,
                dx=1.0,
                nk=64,
                offset=5,
                kmin=None,
                kmax=None,
            )

    def test_kmin_kmax_error(self):
        coeffs = np.array([0.2, 0.6, 0.2], dtype=float)
        with self.assertRaises(ValueError):
            self.mod.compute_amplification(
                coeffs=coeffs,
                dx=1.0,
                nk=64,
                offset=None,
                kmin=1.0,
                kmax=0.0,
            )

    def test_even_length_warning(self):
        coeffs = np.array([0.5, 0.5], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=64,
            offset=1,
            kmin=None,
            kmax=None,
        )
        self.assertIsNotNone(result["results"]["warning"])

    def test_constant_amplification_unstable(self):
        coeffs = np.array([0.0, 2.0, 0.0], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=64,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertFalse(result["results"]["stable"])
        self.assertAlmostEqual(result["results"]["max_amplification"], 2.0, places=6)

    def test_ftcs_advection_unstable(self):
        cfl = 0.5
        coeffs = np.array([-0.5 * cfl, 1.0, 0.5 * cfl], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=512,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertFalse(result["results"]["stable"])

    def test_ftcs_diffusion_stable(self):
        r = 0.4
        coeffs = np.array([r, 1.0 - 2.0 * r, r], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=512,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertTrue(result["results"]["stable"])

    def test_ftcs_diffusion_unstable(self):
        r = 0.6
        coeffs = np.array([r, 1.0 - 2.0 * r, r], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=512,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertFalse(result["results"]["stable"])

    def test_nan_coefficients_raise(self):
        """NaN in coefficients must raise ValueError."""
        coeffs = np.array([0.2, float("nan"), 0.2], dtype=float)
        with self.assertRaises(ValueError):
            self.mod.compute_amplification(
                coeffs=coeffs, dx=1.0, nk=64, offset=None, kmin=None, kmax=None,
            )

    def test_inf_coefficients_raise(self):
        """Inf in coefficients must raise ValueError."""
        coeffs = np.array([0.2, float("inf"), 0.2], dtype=float)
        with self.assertRaises(ValueError):
            self.mod.compute_amplification(
                coeffs=coeffs, dx=1.0, nk=64, offset=None, kmin=None, kmax=None,
            )

    def test_lax_friedrichs_advection_stable(self):
        cfl = 0.8
        coeffs = np.array([0.5 * (1.0 + cfl), 0.0, 0.5 * (1.0 - cfl)], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=512,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertTrue(result["results"]["stable"])


if __name__ == "__main__":
    unittest.main()
