import unittest

from tests.unit._utils import load_module


class TestImexSplitPlanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "imex_split_planner",
            "skills/core-numerical/numerical-integration/scripts/imex_split_planner.py",
        )

    def test_strong_coupling(self):
        result = self.mod.plan_imex(
            stiff_terms=["diffusion", "elastic"],
            nonstiff_terms=["reaction"],
            coupling="strong",
            accuracy="high",
            stiffness_ratio=1e5,
            conservative=True,
        )
        self.assertEqual(result["splitting_strategy"], "imex-coupled")
        self.assertIn("IMEX-ARK", result["recommended_integrator"])

    def test_nonstiff_only(self):
        result = self.mod.plan_imex(
            stiff_terms=[],
            nonstiff_terms=["advection"],
            coupling="weak",
            accuracy="medium",
            stiffness_ratio=10.0,
            conservative=False,
        )
        self.assertIn("RK45", result["recommended_integrator"])

    def test_invalid_coupling(self):
        with self.assertRaises(ValueError):
            self.mod.plan_imex(
                stiff_terms=["diffusion"],
                nonstiff_terms=["reaction"],
                coupling="bad",
                accuracy="medium",
                stiffness_ratio=1e3,
                conservative=False,
            )


if __name__ == "__main__":
    unittest.main()
