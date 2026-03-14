import unittest

from tests.unit._utils import load_module


class TestOptimizerSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "optimizer_selector",
            "skills/simulation-workflow/parameter-optimization/scripts/optimizer_selector.py",
        )

    def test_low_dim_low_budget_bayesian(self):
        """Test low dimension + low budget recommends Bayesian."""
        result = self.mod.select_optimizer(3, 40, "low", False)
        self.assertIn("Bayesian", result["recommended"][0])

    def test_low_dim_high_budget_bayesian(self):
        """Test low dimension + high budget still works."""
        result = self.mod.select_optimizer(4, 80, "low", False)
        self.assertIn("Bayesian", result["recommended"][0])

    def test_medium_dim_cmaes(self):
        """Test medium dimension recommends CMA-ES."""
        result = self.mod.select_optimizer(10, 200, "low", False)
        self.assertIn("CMA-ES", result["recommended"][0])

    def test_high_dim_random(self):
        """Test high dimension recommends Random Search."""
        result = self.mod.select_optimizer(30, 200, "medium", False)
        self.assertIn("Random", result["recommended"][0])

    def test_boundary_dim_5(self):
        """Test boundary at dim=5."""
        result = self.mod.select_optimizer(5, 100, "low", False)
        self.assertIn("Bayesian", result["recommended"][0])

    def test_boundary_dim_6(self):
        """Test boundary at dim=6 (should be CMA-ES)."""
        result = self.mod.select_optimizer(6, 100, "low", False)
        self.assertIn("CMA-ES", result["recommended"][0])

    def test_boundary_dim_20(self):
        """Test boundary at dim=20."""
        result = self.mod.select_optimizer(20, 300, "low", False)
        self.assertIn("CMA-ES", result["recommended"][0])

    def test_boundary_dim_21(self):
        """Test boundary at dim=21 (should be Random)."""
        result = self.mod.select_optimizer(21, 300, "low", False)
        self.assertIn("Random", result["recommended"][0])

    def test_high_noise_note(self):
        """Test high noise adds appropriate note."""
        result = self.mod.select_optimizer(3, 40, "high", False)
        self.assertTrue(any("noise" in note.lower() for note in result["notes"]))

    def test_medium_noise_no_note(self):
        """Test medium noise doesn't add noise note."""
        result = self.mod.select_optimizer(3, 40, "medium", False)
        noise_notes = [n for n in result["notes"] if "noise" in n.lower()]
        self.assertEqual(len(noise_notes), 0)

    def test_constraints_note(self):
        """Test constraints adds appropriate note."""
        result = self.mod.select_optimizer(3, 40, "low", True)
        self.assertTrue(any("constrain" in note.lower() for note in result["notes"]))

    def test_no_constraints_no_note(self):
        """Test no constraints doesn't add constraint note."""
        result = self.mod.select_optimizer(3, 40, "low", False)
        constraint_notes = [n for n in result["notes"] if "constrain" in n.lower()]
        self.assertEqual(len(constraint_notes), 0)

    def test_expected_evals_small_budget(self):
        """Test expected_evals respects budget."""
        result = self.mod.select_optimizer(3, 10, "low", False)
        self.assertLessEqual(result["expected_evals"], 10)

    def test_expected_evals_large_budget(self):
        """Test expected_evals has reasonable upper bound."""
        result = self.mod.select_optimizer(5, 1000, "low", False)
        self.assertLessEqual(result["expected_evals"], 1000)

    def test_invalid_dim_zero(self):
        """Test zero dimension raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.select_optimizer(0, 40, "low", False)
        self.assertIn("dim must be positive", str(ctx.exception))

    def test_invalid_dim_negative(self):
        """Test negative dimension raises ValueError."""
        with self.assertRaises(ValueError):
            self.mod.select_optimizer(-1, 40, "low", False)

    def test_invalid_budget_zero(self):
        """Test zero budget raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.select_optimizer(3, 0, "low", False)
        self.assertIn("budget must be positive", str(ctx.exception))

    def test_invalid_noise(self):
        """Test invalid noise level raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.select_optimizer(3, 40, "very_high", False)
        self.assertIn("noise must be", str(ctx.exception))



class TestSensitivitySummarySecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "sensitivity_summary",
            "skills/simulation-workflow/parameter-optimization/scripts/sensitivity_summary.py",
        )

    def test_name_rejects_shell_metacharacters(self):
        with self.assertRaises(ValueError):
            self.mod.parse_names("kappa;rm -rf /,mobility", 2)
        with self.assertRaises(ValueError):
            self.mod.parse_names("$(whoami),test", 2)

    def test_name_accepts_valid(self):
        result = self.mod.parse_names("kappa,mobility,W_interface", 3)
        self.assertEqual(result, ["kappa", "mobility", "W_interface"])

    def test_scores_reject_nonfinite(self):
        with self.assertRaises(ValueError):
            self.mod.parse_list("0.5,inf,0.3")

    def test_scores_reject_oversized(self):
        huge = ",".join(["0.1"] * (self.mod.MAX_LIST_LENGTH + 1))
        with self.assertRaises(ValueError):
            self.mod.parse_list(huge)


class TestDoeGeneratorSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "doe_generator",
            "skills/simulation-workflow/parameter-optimization/scripts/doe_generator.py",
        )

    def test_dim_exceeds_max(self):
        with self.assertRaises(ValueError):
            self.mod.generate_doe(2000, 10, "lhs", 0)

    def test_budget_exceeds_max(self):
        with self.assertRaises(ValueError):
            self.mod.generate_doe(3, 2_000_000, "lhs", 0)


class TestOptimizerSelectorBounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "optimizer_selector",
            "skills/simulation-workflow/parameter-optimization/scripts/optimizer_selector.py",
        )

    def test_dim_exceeds_max(self):
        with self.assertRaises(ValueError):
            self.mod.select_optimizer(200_000, 100, "low", False)

    def test_budget_exceeds_max(self):
        with self.assertRaises(ValueError):
            self.mod.select_optimizer(3, 20_000_000, "low", False)


class TestSurrogateBuilderSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "surrogate_builder",
            "skills/simulation-workflow/parameter-optimization/scripts/surrogate_builder.py",
        )

    def test_rejects_nonfinite(self):
        with self.assertRaises(ValueError):
            self.mod.parse_list("1.0,nan,3.0")

    def test_rejects_oversized(self):
        huge = ",".join(["1.0"] * (self.mod.MAX_LIST_LENGTH + 1))
        with self.assertRaises(ValueError):
            self.mod.parse_list(huge)


if __name__ == "__main__":
    unittest.main()
