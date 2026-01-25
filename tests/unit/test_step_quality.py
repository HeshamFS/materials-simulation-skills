import unittest

from tests.unit._utils import load_module


class TestStepQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "step_quality",
            "skills/core-numerical/nonlinear-solvers/scripts/step_quality.py",
        )

    def test_excellent_step(self):
        """Test detection of excellent step quality."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.9,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["step_quality"], "excellent")
        self.assertTrue(result["accept_step"])
        self.assertAlmostEqual(result["ratio"], 0.9, places=5)

    def test_good_step(self):
        """Test detection of good step quality."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.5,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["step_quality"], "good")
        self.assertTrue(result["accept_step"])

    def test_marginal_step(self):
        """Test detection of marginal step quality."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.15,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["step_quality"], "marginal")
        self.assertTrue(result["accept_step"])

    def test_poor_step(self):
        """Test detection of poor step quality."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.05,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["step_quality"], "poor")
        self.assertFalse(result["accept_step"])

    def test_very_poor_step(self):
        """Test detection of very poor (negative) step quality."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=-0.5,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["step_quality"], "very_poor")
        self.assertFalse(result["accept_step"])

    def test_trust_radius_expand(self):
        """Test trust radius expansion when step at boundary."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.9,
            step_norm=0.95,  # Near trust radius
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["trust_radius_action"], "expand")
        self.assertGreater(result["suggested_trust_radius"], 1.0)

    def test_trust_radius_shrink(self):
        """Test trust radius shrink for marginal step."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.15,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["trust_radius_action"], "shrink")
        self.assertLess(result["suggested_trust_radius"], 1.0)

    def test_trust_radius_shrink_aggressive(self):
        """Test aggressive trust radius shrink for poor step."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.05,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["trust_radius_action"], "shrink_aggressive")
        self.assertLess(result["suggested_trust_radius"], 0.5)

    def test_trust_radius_maintain(self):
        """Test trust radius maintenance for good step not at boundary."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.5,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=1.0,
        )
        self.assertEqual(result["trust_radius_action"], "maintain")
        self.assertAlmostEqual(result["suggested_trust_radius"], 1.0, places=5)

    def test_no_trust_radius(self):
        """Test evaluation without trust radius (line search mode)."""
        result = self.mod.evaluate_step(
            predicted_reduction=1.0,
            actual_reduction=0.9,
            step_norm=0.5,
            gradient_norm=1.0,
            trust_radius=None,
        )
        self.assertIsNone(result["trust_radius_action"])
        self.assertIsNone(result["suggested_trust_radius"])
        self.assertTrue(result["accept_step"])

    def test_near_zero_predicted(self):
        """Test handling of near-zero predicted reduction."""
        result = self.mod.evaluate_step(
            predicted_reduction=1e-40,
            actual_reduction=1e-40,
            step_norm=0.5,
            gradient_norm=1e-12,
            trust_radius=1.0,
        )
        # Should handle gracefully
        self.assertIn("notes", result)

    def test_invalid_predicted_reduction_raises(self):
        """Test that negative predicted reduction raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.evaluate_step(
                predicted_reduction=-1.0,
                actual_reduction=0.5,
                step_norm=0.5,
                gradient_norm=1.0,
            )

    def test_invalid_step_norm_raises(self):
        """Test that negative step norm raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.evaluate_step(
                predicted_reduction=1.0,
                actual_reduction=0.5,
                step_norm=-0.5,
                gradient_norm=1.0,
            )

    def test_invalid_trust_radius_raises(self):
        """Test that non-positive trust radius raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.evaluate_step(
                predicted_reduction=1.0,
                actual_reduction=0.5,
                step_norm=0.5,
                gradient_norm=1.0,
                trust_radius=0.0,
            )


if __name__ == "__main__":
    unittest.main()
