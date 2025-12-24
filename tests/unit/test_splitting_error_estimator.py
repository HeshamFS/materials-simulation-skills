import unittest

from tests.unit._utils import load_module


class TestSplittingErrorEstimator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "splitting_error_estimator",
            "skills/core-numerical/numerical-integration/scripts/splitting_error_estimator.py",
        )

    def test_strang_error(self):
        result = self.mod.estimate_error(dt=1e-3, scheme="strang", commutator_norm=100.0, target_error=0.0)
        self.assertGreater(result["error_estimate"], 0.0)
        self.assertEqual(result["order"], 2)

    def test_target_error(self):
        result = self.mod.estimate_error(dt=1e-2, scheme="lie", commutator_norm=10.0, target_error=1e-6)
        self.assertGreaterEqual(result["substeps"], 1)
        self.assertLessEqual(result["error_estimate"], 1e-6)

    def test_invalid_dt(self):
        with self.assertRaises(ValueError):
            self.mod.estimate_error(dt=0.0, scheme="lie", commutator_norm=1.0, target_error=0.0)


if __name__ == "__main__":
    unittest.main()
