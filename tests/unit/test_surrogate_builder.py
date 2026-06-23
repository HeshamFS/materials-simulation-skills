import unittest

from tests.unit._utils import load_module


class TestSurrogateBuilder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "surrogate_builder",
            "skills/simulation-workflow/parameter-optimization/scripts/surrogate_builder.py",
        )

    def test_surrogate_rbf(self):
        """Test surrogate with rbf model."""
        result = self.mod.build_surrogate([0.0, 1.0], [1.0, 2.0], "rbf")
        self.assertIn("metrics", result)
        self.assertEqual(result["model_type"], "rbf")

    def test_surrogate_poly(self):
        """Test surrogate with poly model."""
        result = self.mod.build_surrogate([0.0, 1.0, 2.0], [1.0, 4.0, 9.0], "poly")
        self.assertIn("metrics", result)
        self.assertEqual(result["model_type"], "poly")

    def test_metrics_keys(self):
        """Regression (F1/F7): metrics expose honest, separately named fields."""
        result = self.mod.build_surrogate([0.0, 1.0, 2.0], [1.0, 2.0, 3.0], "poly")
        metrics = result["metrics"]
        self.assertIn("mse", metrics)
        self.assertIn("cv_error", metrics)
        self.assertIn("output_variance", metrics)

    def test_output_variance_is_data_variance(self):
        """output_variance equals Var(y) and is reported separately from mse."""
        # y = [1, 2, 3], mean = 2, variance = (1+0+1)/3 = 0.666...
        result = self.mod.build_surrogate([0.0, 1.0, 2.0], [1.0, 2.0, 3.0], "rbf")
        expected_var = (1.0 + 0.0 + 1.0) / 3
        self.assertAlmostEqual(result["metrics"]["output_variance"], expected_var, places=6)

    def test_mse_is_real_residual_not_variance(self):
        """Regression (F1): mse is a fit residual, not Var(y).

        For a linear y = 2x, a degree-2 least-squares poly fits exactly, so the
        residual mse must be ~0 while the data variance is large and nonzero.
        The old placeholder reported Var(y) as 'mse'; this test would catch that.
        """
        x = [0.0, 1.0, 2.0, 3.0, 4.0]
        y = [2.0 * xi for xi in x]
        result = self.mod.build_surrogate(x, y, "poly")
        metrics = result["metrics"]
        self.assertLess(metrics["mse"], 1e-9)
        self.assertGreater(metrics["output_variance"], 1.0)

    def test_mse_responds_to_model_choice(self):
        """Regression (F1): rbf and poly produce different mse for the same data
        (the old implementation ignored model type and x entirely)."""
        x = [0.1, 0.3, 0.5, 0.7, 0.9]
        y = [2.1, 3.5, 4.2, 3.8, 2.6]
        rbf = self.mod.build_surrogate(x, y, "rbf")["metrics"]["mse"]
        poly = self.mod.build_surrogate(x, y, "poly")["metrics"]["mse"]
        # rbf interpolates exactly (mse ~ 0); poly leaves a real residual.
        self.assertLess(rbf, 1e-6)
        self.assertGreater(poly, rbf)

    def test_mse_responds_to_x(self):
        """Regression (F1): the poly fit residual depends on the x layout; the old
        Var(y)-as-mse implementation ignored x entirely and returned the same
        number regardless of x. Here we change the *shape* of the x spacing (not a
        pure affine rescale, which a degree-2 fit is invariant to)."""
        y = [0.0, 1.0, 8.0, 27.0, 64.0]  # cubic, poorly fit by degree 2
        x1 = [0.0, 1.0, 2.0, 3.0, 4.0]  # uniform spacing
        x2 = [0.0, 0.5, 2.0, 4.5, 8.0]  # quadratically stretched spacing
        mse1 = self.mod.build_surrogate(x1, y, "poly")["metrics"]["mse"]
        mse2 = self.mod.build_surrogate(x2, y, "poly")["metrics"]["mse"]
        self.assertNotAlmostEqual(mse1, mse2, places=6)

    def test_rbf_interpolates_exactly(self):
        """RBF in-sample mse is near zero by construction."""
        x = [0.0, 1.0, 2.0, 3.0]
        y = [1.0, 4.0, 9.0, 16.0]
        result = self.mod.build_surrogate(x, y, "rbf")
        self.assertLess(result["metrics"]["mse"], 1e-6)

    def test_production_guidance_note(self):
        """Test the lightweight/production-guidance note is present."""
        result = self.mod.build_surrogate([0.0, 1.0], [1.0, 2.0], "rbf")
        self.assertTrue(
            any("production" in note.lower() for note in result["notes"])
        )

    def test_invalid_lengths(self):
        """Test mismatched x and y lengths raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.build_surrogate([0.0], [1.0, 2.0], "rbf")
        self.assertIn("same length", str(ctx.exception))

    def test_invalid_model(self):
        """Test invalid model type raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.build_surrogate([0.0, 1.0], [1.0, 2.0], "gp")
        self.assertIn("model must be", str(ctx.exception))

    def test_too_few_samples(self):
        """Test fewer than 2 samples raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.build_surrogate([0.0], [1.0], "rbf")
        self.assertIn("at least 2", str(ctx.exception))

    def test_empty_lists(self):
        """Test empty lists raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.build_surrogate([], [], "rbf")

    def test_many_samples(self):
        """Test surrogate works with many samples."""
        x = [float(i) for i in range(100)]
        y = [i * 2.0 for i in x]
        result = self.mod.build_surrogate(x, y, "poly")
        self.assertIn("metrics", result)
        # Linear data fit by a degree-2 polynomial leaves no residual.
        self.assertGreaterEqual(result["metrics"]["mse"], 0.0)
        self.assertLess(result["metrics"]["mse"], 1e-6)

    def test_parse_list_valid(self):
        """Test parse_list with valid input."""
        result = self.mod.parse_list("1.0, 2.0, 3.0")
        self.assertEqual(result, [1.0, 2.0, 3.0])

    def test_parse_list_integers(self):
        """Test parse_list with integer input."""
        result = self.mod.parse_list("1, 2, 3")
        self.assertEqual(result, [1.0, 2.0, 3.0])

    def test_parse_list_empty(self):
        """Test parse_list with empty string raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.parse_list("")
        self.assertIn("comma-separated", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
