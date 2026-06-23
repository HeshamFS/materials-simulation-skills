import unittest
import warnings

from tests.unit._utils import load_module


class TestDoeGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "doe_generator",
            "skills/simulation-workflow/parameter-optimization/scripts/doe_generator.py",
        )

    def test_lhs_samples(self):
        """Test LHS method generates correct sample count."""
        result = self.mod.generate_doe(2, 5, "lhs", 0)
        self.assertEqual(result["coverage"]["count"], 5)
        self.assertEqual(result["coverage"]["dimension"], 2)
        self.assertEqual(result["method"], "lhs")

    def test_lhs_dimensions(self):
        """Test LHS samples have correct dimensionality."""
        result = self.mod.generate_doe(4, 10, "lhs", 42)
        samples = result["samples"]
        self.assertEqual(len(samples), 10)
        for sample in samples:
            self.assertEqual(len(sample), 4)
            # All values should be in [0, 1]
            for val in sample:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.0)

    def test_lhs_reproducibility(self):
        """Test LHS with same seed produces same samples."""
        result1 = self.mod.generate_doe(3, 8, "lhs", 123)
        result2 = self.mod.generate_doe(3, 8, "lhs", 123)
        self.assertEqual(result1["samples"], result2["samples"])

    def test_lhs_different_seeds(self):
        """Test LHS with different seeds produces different samples."""
        result1 = self.mod.generate_doe(3, 8, "lhs", 1)
        result2 = self.mod.generate_doe(3, 8, "lhs", 2)
        self.assertNotEqual(result1["samples"], result2["samples"])

    def test_quasi_random_samples(self):
        """Test quasi-random method generates correct sample count."""
        result = self.mod.generate_doe(2, 10, "quasi-random", 0)
        self.assertEqual(result["coverage"]["count"], 10)
        self.assertEqual(result["method"], "quasi-random")

    def test_sobol_backward_compat(self):
        """Test sobol method works (backward compatibility)."""
        result = self.mod.generate_doe(2, 10, "sobol", 0)
        self.assertEqual(result["coverage"]["count"], 10)
        self.assertEqual(result["method"], "sobol")

    def test_factorial_samples(self):
        """Test factorial method generates grid samples."""
        result = self.mod.generate_doe(2, 9, "factorial", 0)
        # Factorial should create 3^2 = 9 samples for 2D with 3 levels
        self.assertEqual(result["method"], "factorial")
        self.assertGreater(len(result["samples"]), 0)

    def test_factorial_corner_coverage(self):
        """Test factorial includes corner points."""
        result = self.mod.generate_doe(2, 4, "factorial", 0)
        samples = result["samples"]
        # Should include [0,0] and [1,1] corners
        has_origin = any(s[0] == 0.0 and s[1] == 0.0 for s in samples)
        has_corner = any(s[0] == 1.0 and s[1] == 1.0 for s in samples)
        self.assertTrue(has_origin)
        self.assertTrue(has_corner)

    def test_factorial_levels_explicit(self):
        """Regression (F6): --levels yields exactly levels**dim samples."""
        result = self.mod.generate_doe(2, None, "factorial", 0, levels=4)
        self.assertEqual(result["coverage"]["count"], 16)
        self.assertEqual(result["coverage"]["levels"], 4)
        # No spurious budget-mismatch note when levels are explicit.
        self.assertNotIn("note", result)

    def test_factorial_levels_three_dims(self):
        """Regression (F6): levels**dim = 3**3 = 27 samples."""
        result = self.mod.generate_doe(3, None, "factorial", 0, levels=3)
        self.assertEqual(result["coverage"]["count"], 27)
        self.assertEqual(result["coverage"]["levels"], 3)

    def test_factorial_budget_perfect_power_no_note(self):
        """Regression (F6): a perfect-power budget is honored silently."""
        result = self.mod.generate_doe(2, 16, "factorial", 0)
        self.assertEqual(result["coverage"]["count"], 16)
        self.assertEqual(result["coverage"]["levels"], 4)
        self.assertNotIn("note", result)

    def test_factorial_budget_non_power_warns(self):
        """Regression (F6): a non-perfect-power budget produces a note and the
        realized count differs from the requested budget (no longer silent)."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = self.mod.generate_doe(2, 20, "factorial", 0)
        self.assertEqual(result["coverage"]["count"], 16)
        self.assertEqual(result["requested_budget"], 20)
        self.assertIn("note", result)
        self.assertIn("realized", result["note"])
        self.assertTrue(any("realized" in str(w.message) for w in caught))

    def test_factorial_levels_too_small(self):
        """Regression (F6): levels < 2 is rejected."""
        with self.assertRaises(ValueError):
            self.mod.generate_doe(2, None, "factorial", 0, levels=1)

    def test_factorial_levels_exceeds_max(self):
        """Regression (F6): an oversized factorial design is rejected."""
        with self.assertRaises(ValueError):
            self.mod.generate_doe(10, None, "factorial", 0, levels=1000)

    def test_factorial_no_budget_no_levels_errors(self):
        """Regression (F6): factorial without budget or levels is rejected."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.generate_doe(2, None, "factorial", 0)
        self.assertIn("budget must be positive", str(ctx.exception))

    def test_invalid_method(self):
        """Test invalid method raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.generate_doe(2, 5, "bad", 0)
        self.assertIn("method must be one of", str(ctx.exception))

    def test_invalid_dim_zero(self):
        """Test zero dimension raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.generate_doe(0, 5, "lhs", 0)
        self.assertIn("params must be positive", str(ctx.exception))

    def test_invalid_dim_negative(self):
        """Test negative dimension raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.generate_doe(-1, 5, "lhs", 0)

    def test_invalid_budget_zero(self):
        """Test zero budget raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.generate_doe(2, 0, "lhs", 0)
        self.assertIn("budget must be positive", str(ctx.exception))

    def test_invalid_budget_negative(self):
        """Test negative budget raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.generate_doe(2, -5, "lhs", 0)

    def test_high_dimension(self):
        """Test DOE works with high dimensions."""
        result = self.mod.generate_doe(20, 50, "lhs", 0)
        self.assertEqual(result["coverage"]["dimension"], 20)
        self.assertEqual(len(result["samples"]), 50)


if __name__ == "__main__":
    unittest.main()
