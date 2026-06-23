import unittest

import numpy as np

from tests.unit._utils import load_module


class TestStiffnessDetector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "stiffness_detector",
            "skills/core-numerical/numerical-stability/scripts/stiffness_detector.py",
        )

    def test_stiff_system(self):
        eigs = np.array([-1.0, -1000.0])
        result = self.mod.compute_stiffness(eigs, threshold=1e3)
        self.assertTrue(result["stiff"])
        self.assertEqual(result["recommendation"], "implicit (BDF/Radau)")

    def test_non_stiff_system(self):
        eigs = np.array([-1.0, -10.0])
        result = self.mod.compute_stiffness(eigs, threshold=1e3)
        self.assertFalse(result["stiff"])
        self.assertEqual(result["recommendation"], "explicit (RK/Adams)")

    def test_invalid_threshold(self):
        eigs = np.array([-1.0, -10.0])
        with self.assertRaises(ValueError):
            self.mod.compute_stiffness(eigs, threshold=0.0)

    def test_complex_eigs(self):
        eigs = np.array([-1.0 + 2.0j, -1000.0 + 0.5j])
        result = self.mod.compute_stiffness(eigs, threshold=1e2)
        self.assertTrue(result["stiff"])

    def test_zero_eigs(self):
        eigs = np.array([0.0, 0.0])
        result = self.mod.compute_stiffness(eigs, threshold=1e3)
        self.assertTrue(result["stiff"])
        self.assertEqual(result["nonzero_count"], 0)

    def test_non_finite_eigs(self):
        eigs = np.array([1.0, float("nan")])
        with self.assertRaises(ValueError):
            self.mod.compute_stiffness(eigs, threshold=1e3)

    def test_imaginary_dominated_not_stiff(self):
        """Regression (F5): purely imaginary spectrum (wave/Hamiltonian) must
        NOT be classified as stiff despite a large magnitude ratio."""
        eigs = np.array([-1000j, -1j])
        result = self.mod.compute_stiffness(eigs, threshold=1e2)
        self.assertAlmostEqual(result["stiffness_ratio"], 1000.0, places=6)
        self.assertTrue(result["imag_dominated"])
        self.assertFalse(result["stiff"])
        self.assertEqual(result["recommendation"], "explicit (RK/Adams)")
        self.assertIsNotNone(result["warning"])
        self.assertIsNone(result["real_part_stiffness_ratio"])

    def test_real_part_stiffness_reported(self):
        """Decaying-mode scale separation drives the stiff verdict via the
        real-part ratio, which is reported alongside the magnitude ratio."""
        eigs = np.array([-1.0, -1000.0])
        result = self.mod.compute_stiffness(eigs, threshold=1e3)
        self.assertTrue(result["stiff"])
        self.assertFalse(result["imag_dominated"])
        self.assertAlmostEqual(result["real_part_stiffness_ratio"], 1000.0, places=6)

    def test_eigs_cap_enforced(self):
        """Security: --eigs list above MAX_EIGS entries must raise."""
        raw = ",".join(["1"] * (self.mod.MAX_EIGS + 1))
        with self.assertRaises(ValueError):
            self.mod.parse_eigs(raw)

    def test_oscillatory_with_small_decay_not_stiff(self):
        """Lightly-damped oscillators (Re tiny vs Im) are flagged imag-dominated
        and recommended an explicit/symplectic scheme, not BDF/Radau."""
        eigs = np.array([-0.01 + 500j, -0.01 - 500j])
        result = self.mod.compute_stiffness(eigs, threshold=1e2)
        self.assertTrue(result["imag_dominated"])
        self.assertFalse(result["stiff"])


if __name__ == "__main__":
    unittest.main()
