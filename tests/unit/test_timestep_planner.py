import unittest

from tests.unit._utils import load_module


class TestTimestepPlanner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "timestep_planner",
            "skills/core-numerical/time-stepping/scripts/timestep_planner.py",
        )

    def test_recommended_dt(self):
        result = self.mod.plan_timestep(
            dt_target=1e-3,
            dt_limit=5e-4,
            safety=0.8,
            dt_min=None,
            dt_max=None,
            ramp_steps=0,
            ramp_kind="linear",
            preview_steps=0,
        )
        self.assertAlmostEqual(result["dt_recommended"], 4e-4, places=12)
        self.assertTrue(any("reduced" in note for note in result["notes"]))

    def test_ramp_schedule(self):
        result = self.mod.plan_timestep(
            dt_target=1e-4,
            dt_limit=1e-4,
            safety=1.0,
            dt_min=None,
            dt_max=None,
            ramp_steps=4,
            ramp_kind="linear",
            preview_steps=4,
        )
        self.assertEqual(len(result["ramp_schedule"]), 4)
        self.assertAlmostEqual(result["ramp_schedule"][-1], 1e-4, places=12)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            self.mod.plan_timestep(
                dt_target=-1.0,
                dt_limit=1.0,
                safety=1.0,
                dt_min=None,
                dt_max=None,
                ramp_steps=0,
                ramp_kind="linear",
                preview_steps=0,
            )

    def test_invalid_min_max(self):
        with self.assertRaises(ValueError):
            self.mod.plan_timestep(
                dt_target=1e-3,
                dt_limit=1e-3,
                safety=1.0,
                dt_min=1e-2,
                dt_max=1e-3,
                ramp_steps=0,
                ramp_kind="linear",
                preview_steps=0,
            )


if __name__ == "__main__":
    unittest.main()
