import unittest

from tests.unit._utils import load_module


class TestCheckpointPlanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "checkpoint_planner",
            "skills/core-numerical/time-stepping/scripts/checkpoint_planner.py",
        )

    def test_cap_method(self):
        result = self.mod.compute_interval(
            run_time=36000,
            checkpoint_cost=120,
            max_lost_time=1800,
            mtbf=None,
        )
        self.assertEqual(result["method"], "cap")
        self.assertGreater(result["checkpoint_interval"], 0)

    def test_daly_method(self):
        result = self.mod.compute_interval(
            run_time=36000,
            checkpoint_cost=120,
            max_lost_time=3600,
            mtbf=72000,
        )
        self.assertEqual(result["method"], "daly")

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            self.mod.compute_interval(
                run_time=0,
                checkpoint_cost=1,
                max_lost_time=1,
                mtbf=None,
            )

    def test_overhead_fraction_value(self):
        # Regression for F1: documented worked example must report ~6.67% overhead.
        result = self.mod.compute_interval(
            run_time=36000,
            checkpoint_cost=120,
            max_lost_time=1800,
            mtbf=None,
        )
        self.assertEqual(result["checkpoints"], 20)
        self.assertAlmostEqual(result["overhead_fraction"], 0.0666666666, places=8)
        self.assertEqual(result["warnings"], [])

    def test_checkpoint_cost_ge_run_time_rejected(self):
        # Regression for F3: checkpoint-cost must be < run-time (documented + security).
        with self.assertRaises(ValueError) as ctx:
            self.mod.compute_interval(
                run_time=100,
                checkpoint_cost=200,
                max_lost_time=50,
                mtbf=None,
            )
        self.assertIn("checkpoint-cost must be < run-time", str(ctx.exception))

    def test_overhead_warning_emitted(self):
        # F3 defense-in-depth: overhead > 10% surfaces a warning.
        result = self.mod.compute_interval(
            run_time=1000,
            checkpoint_cost=300,
            max_lost_time=300,
            mtbf=None,
        )
        self.assertGreater(result["overhead_fraction"], 0.10)
        self.assertTrue(result["warnings"])

    def test_non_finite_rejected(self):
        with self.assertRaises(ValueError):
            self.mod.compute_interval(
                run_time=float("inf"),
                checkpoint_cost=1,
                max_lost_time=1,
                mtbf=None,
            )


if __name__ == "__main__":
    unittest.main()
