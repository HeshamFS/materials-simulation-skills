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


if __name__ == "__main__":
    unittest.main()
