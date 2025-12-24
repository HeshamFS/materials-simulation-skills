import unittest

from tests.unit._utils import load_module


class TestIntegratorSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "integrator_selector",
            "skills/core-numerical/numerical-integration/scripts/integrator_selector.py",
        )

    def test_stiff_implicit(self):
        result = self.mod.select_integrator(
            stiff=True,
            oscillatory=False,
            event_detection=False,
            jacobian_available=True,
            implicit_allowed=True,
            accuracy="medium",
            dimension=10,
            low_memory=False,
        )
        self.assertIn("BDF", result["recommended"])
        self.assertIn("Radau IIA", result["recommended"])

    def test_nonstiff_default(self):
        result = self.mod.select_integrator(
            stiff=False,
            oscillatory=False,
            event_detection=False,
            jacobian_available=False,
            implicit_allowed=False,
            accuracy="medium",
            dimension=10,
            low_memory=False,
        )
        self.assertIn("RK45", result["recommended"])

    def test_oscillatory(self):
        result = self.mod.select_integrator(
            stiff=False,
            oscillatory=True,
            event_detection=False,
            jacobian_available=False,
            implicit_allowed=False,
            accuracy="medium",
            dimension=10,
            low_memory=False,
        )
        self.assertIn("Symplectic Verlet", result["recommended"])

    def test_invalid_dimension(self):
        with self.assertRaises(ValueError):
            self.mod.select_integrator(
                stiff=False,
                oscillatory=False,
                event_detection=False,
                jacobian_available=False,
                implicit_allowed=False,
                accuracy="medium",
                dimension=0,
                low_memory=False,
            )

    def test_invalid_accuracy(self):
        with self.assertRaises(ValueError):
            self.mod.select_integrator(
                stiff=False,
                oscillatory=False,
                event_detection=False,
                jacobian_available=False,
                implicit_allowed=False,
                accuracy="bad",
                dimension=10,
                low_memory=False,
            )


if __name__ == "__main__":
    unittest.main()
