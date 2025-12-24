import unittest

from tests.unit._utils import load_module


class TestTruncationError(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "truncation_error",
            "skills/core-numerical/differentiation-schemes/scripts/truncation_error.py",
        )

    def test_error_scaling(self):
        result = self.mod.estimate_truncation_error(dx=0.1, accuracy=2, scale=3.0)
        self.assertAlmostEqual(result["error_scale"], 0.03, places=6)
        self.assertEqual(result["reduction_if_halved"], 4)

    def test_invalid_dx(self):
        with self.assertRaises(ValueError):
            self.mod.estimate_truncation_error(dx=0.0, accuracy=2, scale=1.0)


if __name__ == "__main__":
    unittest.main()
