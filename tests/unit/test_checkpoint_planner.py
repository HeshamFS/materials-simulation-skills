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


if __name__ == "__main__":
    unittest.main()
