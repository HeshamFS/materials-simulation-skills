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


if __name__ == "__main__":
    unittest.main()
