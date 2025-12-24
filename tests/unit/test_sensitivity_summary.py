import unittest

from tests.unit._utils import load_module


class TestSensitivitySummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "sensitivity_summary",
            "skills/simulation-workflow/parameter-optimization/scripts/sensitivity_summary.py",
        )

    def test_ranking_order(self):
        """Test ranking orders by descending sensitivity."""
        result = self.mod.summarize([0.1, 0.5, 0.2], ["a", "b", "c"])
        self.assertEqual(result["ranking"][0][0], "b")
        self.assertEqual(result["ranking"][1][0], "c")
        self.assertEqual(result["ranking"][2][0], "a")

    def test_ranking_values(self):
        """Test ranking preserves sensitivity values."""
        result = self.mod.summarize([0.1, 0.5, 0.2], ["a", "b", "c"])
        self.assertEqual(result["ranking"][0][1], 0.5)
        self.assertEqual(result["ranking"][1][1], 0.2)
        self.assertEqual(result["ranking"][2][1], 0.1)

    def test_single_parameter(self):
        """Test summarize works with single parameter."""
        result = self.mod.summarize([0.8], ["only_param"])
        self.assertEqual(len(result["ranking"]), 1)
        self.assertEqual(result["ranking"][0][0], "only_param")

    def test_equal_sensitivities(self):
        """Test ranking with equal sensitivities."""
        result = self.mod.summarize([0.5, 0.5, 0.5], ["a", "b", "c"])
        self.assertEqual(len(result["ranking"]), 3)
        # All have same value
        for name, score in result["ranking"]:
            self.assertEqual(score, 0.5)

    def test_low_sensitivity_note(self):
        """Test low sensitivity adds note."""
        result = self.mod.summarize([0.05, 0.02, 0.01], ["a", "b", "c"])
        self.assertTrue(len(result["notes"]) > 0)
        self.assertTrue(any("low" in note.lower() for note in result["notes"]))

    def test_high_sensitivity_no_note(self):
        """Test high sensitivity doesn't add low note."""
        result = self.mod.summarize([0.8, 0.5, 0.3], ["a", "b", "c"])
        low_notes = [n for n in result["notes"] if "low" in n.lower()]
        self.assertEqual(len(low_notes), 0)

    def test_parse_list_valid(self):
        """Test parse_list with valid input."""
        result = self.mod.parse_list("0.1, 0.5, 0.2")
        self.assertEqual(result, [0.1, 0.5, 0.2])

    def test_parse_list_no_spaces(self):
        """Test parse_list without spaces."""
        result = self.mod.parse_list("0.1,0.5,0.2")
        self.assertEqual(result, [0.1, 0.5, 0.2])

    def test_parse_list_scientific(self):
        """Test parse_list with scientific notation."""
        result = self.mod.parse_list("1e-3, 5e-2, 2e-1")
        self.assertAlmostEqual(result[0], 0.001, places=6)
        self.assertAlmostEqual(result[1], 0.05, places=6)
        self.assertAlmostEqual(result[2], 0.2, places=6)

    def test_parse_list_empty(self):
        """Test parse_list with empty string raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.parse_list("")
        self.assertIn("comma-separated", str(ctx.exception))

    def test_parse_names_default(self):
        """Test parse_names generates default names."""
        result = self.mod.parse_names("", 3)
        self.assertEqual(result, ["p1", "p2", "p3"])

    def test_parse_names_custom(self):
        """Test parse_names parses custom names."""
        result = self.mod.parse_names("alpha, beta, gamma", 3)
        self.assertEqual(result, ["alpha", "beta", "gamma"])

    def test_parse_names_mismatch(self):
        """Test parse_names with count mismatch raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.parse_names("a,b", 3)
        self.assertIn("count must match", str(ctx.exception))

    def test_negative_sensitivities(self):
        """Test summarize handles negative values (edge case)."""
        result = self.mod.summarize([-0.1, 0.5, -0.2], ["a", "b", "c"])
        self.assertEqual(result["ranking"][0][0], "b")
        self.assertEqual(result["ranking"][2][0], "c")  # -0.2 is lowest


if __name__ == "__main__":
    unittest.main()
