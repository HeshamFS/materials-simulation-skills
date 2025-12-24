import unittest

from tests.unit._utils import load_module


class TestConvergenceDiagnostics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "convergence_diagnostics",
            "skills/core-numerical/linear-solvers/scripts/convergence_diagnostics.py",
        )

    def test_fast_convergence(self):
        rate, stagnation, action = self.mod.compute_diagnostics([1.0, 0.1, 0.01])
        self.assertLess(rate, 0.2)
        self.assertFalse(stagnation)
        self.assertIn("fast", action.lower())

    def test_stagnation(self):
        rate, stagnation, action = self.mod.compute_diagnostics([1.0, 0.98, 0.96])
        self.assertTrue(stagnation)
        self.assertIn("stagnation", action.lower())

    def test_invalid_residuals(self):
        with self.assertRaises(ValueError):
            self.mod.compute_diagnostics([1.0])


if __name__ == "__main__":
    unittest.main()
