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
        rate, stagnation, action, asymptotic = self.mod.compute_diagnostics(
            [1.0, 0.1, 0.01]
        )
        self.assertLess(rate, 0.2)
        self.assertLess(asymptotic, 0.2)
        self.assertFalse(stagnation)
        self.assertIn("fast", action.lower())

    def test_stagnation(self):
        rate, stagnation, action, asymptotic = self.mod.compute_diagnostics(
            [1.0, 0.98, 0.96]
        )
        self.assertTrue(stagnation)
        self.assertGreater(asymptotic, 0.95)
        self.assertIn("stagnation", action.lower())

    def test_invalid_residuals(self):
        with self.assertRaises(ValueError):
            self.mod.compute_diagnostics([1.0])

    def test_late_onset_stagnation_eval2(self):
        """Regression (F1/F8): a fast early drop then a flat tail must flag
        stagnation. This is the eval-2 residual history; the old whole-history
        mean returned stagnation=False and masked the plateau."""
        residuals = [1.0, 0.1, 0.03, 0.01, 0.008, 0.007, 0.007, 0.007]
        rate, stagnation, action, asymptotic = self.mod.compute_diagnostics(residuals)
        self.assertTrue(stagnation)
        self.assertGreater(asymptotic, 0.95)
        self.assertLess(rate, 0.95)  # whole-history mean is misleadingly low
        self.assertIn("stagnation", action.lower())

    def test_skill_md_worked_example_flags_stagnation(self):
        """Regression (F1): the SKILL.md conversational example ends in a flat
        tail (...0.002, 0.002, 0.002) and must flag stagnation."""
        residuals = [1.0, 0.1, 0.01, 0.005, 0.003, 0.002, 0.002, 0.002]
        _rate, stagnation, _action, asymptotic = self.mod.compute_diagnostics(
            residuals
        )
        self.assertTrue(stagnation)
        self.assertGreater(asymptotic, 0.95)

    def test_good_progress_not_stagnation(self):
        """A steady, non-flat tail must NOT be flagged as stagnation."""
        residuals = [1.0, 0.2, 0.05, 0.01]
        _rate, stagnation, _action, asymptotic = self.mod.compute_diagnostics(
            residuals
        )
        self.assertFalse(stagnation)
        self.assertLess(asymptotic, 0.95)


if __name__ == "__main__":
    unittest.main()
