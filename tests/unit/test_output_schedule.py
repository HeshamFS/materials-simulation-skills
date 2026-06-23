import unittest

from tests.unit._utils import load_module


class TestOutputSchedule(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "output_schedule",
            "skills/core-numerical/time-stepping/scripts/output_schedule.py",
        )

    def test_schedule(self):
        result = self.mod.schedule_outputs(0.0, 1.0, 0.25, 100)
        self.assertEqual(result["count"], 5)
        self.assertAlmostEqual(result["output_times"][-1], 1.0, places=12)

    def test_invalid_interval(self):
        with self.assertRaises(ValueError):
            self.mod.schedule_outputs(0.0, 1.0, 0.0, 10)

    def test_no_float_drift_endpoint_inclusive(self):
        # Regression for F6: index-based generation removes accumulated drift and
        # snaps the final point exactly to t_end. Endpoint-inclusive count.
        result = self.mod.schedule_outputs(0.0, 10.0, 0.1, 10000)
        self.assertEqual(result["count"], 101)
        self.assertEqual(result["output_times"][0], 0.0)
        self.assertEqual(result["output_times"][-1], 10.0)

    def test_eval3_frame_count(self):
        # Regression for F5: t=0..5 at 0.05 spacing => 101 frames (100 intervals).
        result = self.mod.schedule_outputs(0.0, 5.0, 0.05, 10000)
        self.assertEqual(result["count"], 101)
        self.assertEqual(result["output_times"][-1], 5.0)

    def test_max_outputs_cap(self):
        result = self.mod.schedule_outputs(0.0, 100.0, 0.001, 50)
        self.assertEqual(result["count"], 50)


if __name__ == "__main__":
    unittest.main()
