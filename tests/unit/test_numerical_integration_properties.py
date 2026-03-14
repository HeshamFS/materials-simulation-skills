import unittest

from tests.unit._utils import load_module


class TestNumericalIntegrationProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.error_norm = load_module(
            "error_norm",
            "skills/core-numerical/numerical-integration/scripts/error_norm.py",
        )
        cls.controller = load_module(
            "adaptive_step_controller",
            "skills/core-numerical/numerical-integration/scripts/adaptive_step_controller.py",
        )
        cls.selector = load_module(
            "integrator_selector",
            "skills/core-numerical/numerical-integration/scripts/integrator_selector.py",
        )

    def test_error_norm_scales_linearly(self):
        error = [0.1, 0.2]
        scale = [0.5, 0.5]
        base, _, _, _ = self.error_norm.compute_error_norm(
            error=error,
            solution=None,
            scale=scale,
            rtol=1e-3,
            atol=1e-6,
            norm="rms",
            min_scale=0.0,
        )
        scaled, _, _, _ = self.error_norm.compute_error_norm(
            error=[e * 3.0 for e in error],
            solution=None,
            scale=scale,
            rtol=1e-3,
            atol=1e-6,
            norm="rms",
            min_scale=0.0,
        )
        self.assertAlmostEqual(scaled, base * 3.0, places=6)

    def test_dt_factor_monotonic(self):
        low_error = self.controller.compute_step(
            dt=0.1,
            error_norm=0.1,
            order=3,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=5.0,
            controller="p",
            prev_error=None,
        )
        high_error = self.controller.compute_step(
            dt=0.1,
            error_norm=2.0,
            order=3,
            accept_threshold=1.0,
            safety=0.9,
            min_factor=0.2,
            max_factor=5.0,
            controller="p",
            prev_error=None,
        )
        self.assertGreater(low_error["factor"], high_error["factor"])

    def test_event_detection_note(self):
        result = self.selector.select_integrator(
            stiff=False,
            oscillatory=False,
            event_detection=True,
            jacobian_available=False,
            implicit_allowed=False,
            accuracy="medium",
            dimension=10,
            low_memory=False,
        )
        self.assertTrue(any("dense output" in note for note in result["notes"]))



class TestImexSplitPlannerSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "imex_split_planner",
            "skills/core-numerical/numerical-integration/scripts/imex_split_planner.py",
        )

    def test_parse_terms_rejects_shell_metacharacters(self):
        """Term names with shell metacharacters must be rejected."""
        with self.assertRaises(ValueError):
            self.mod.parse_terms("diffusion;rm -rf /")
        with self.assertRaises(ValueError):
            self.mod.parse_terms("$(whoami)")
        with self.assertRaises(ValueError):
            self.mod.parse_terms("`cat /etc/passwd`")

    def test_parse_terms_rejects_oversized(self):
        """Too many terms must be rejected."""
        huge = ",".join([f"term_{i}" for i in range(self.mod.MAX_TERMS + 1)])
        with self.assertRaises(ValueError):
            self.mod.parse_terms(huge)

    def test_parse_terms_rejects_long_name(self):
        """Excessively long term names must be rejected."""
        with self.assertRaises(ValueError):
            self.mod.parse_terms("a" * 200)

    def test_parse_terms_accepts_valid(self):
        """Valid physics term names must be accepted."""
        result = self.mod.parse_terms("diffusion,reaction,elastic stress")
        self.assertEqual(result, ["diffusion", "reaction", "elastic stress"])

    def test_stiffness_ratio_inf_raises(self):
        with self.assertRaises(ValueError):
            self.mod.plan_imex(["diffusion"], [], "weak", "low", float("inf"), False)

    def test_stiffness_ratio_nan_raises(self):
        with self.assertRaises(ValueError):
            self.mod.plan_imex(["diffusion"], [], "weak", "low", float("nan"), False)


class TestErrorNormSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "error_norm",
            "skills/core-numerical/numerical-integration/scripts/error_norm.py",
        )

    def test_parse_list_rejects_nonfinite(self):
        with self.assertRaises(ValueError):
            self.mod.parse_list("1.0,inf,0.5")

    def test_parse_list_rejects_oversized(self):
        huge = ",".join(["1.0"] * (self.mod.MAX_LIST_LENGTH + 1))
        with self.assertRaises(ValueError):
            self.mod.parse_list(huge)

    def test_rtol_inf_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_error_norm(
                [0.1], None, [1.0], float("inf"), 1e-6, "rms", 0.0
            )

    def test_atol_nan_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_error_norm(
                [0.1], None, [1.0], 1e-3, float("nan"), "rms", 0.0
            )


class TestAdaptiveStepControllerSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "adaptive_step_controller",
            "skills/core-numerical/numerical-integration/scripts/adaptive_step_controller.py",
        )

    def test_dt_inf_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_step(float("inf"), 0.5, 4, 1.0, 0.9, 0.2, 5.0, "p", None)

    def test_order_exceeds_max_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_step(0.01, 0.5, 100, 1.0, 0.9, 0.2, 5.0, "p", None)

    def test_safety_nan_raises(self):
        with self.assertRaises(ValueError):
            self.mod.compute_step(0.01, 0.5, 4, 1.0, float("nan"), 0.2, 5.0, "p", None)


class TestSplittingErrorEstimatorSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "splitting_error_estimator",
            "skills/core-numerical/numerical-integration/scripts/splitting_error_estimator.py",
        )

    def test_dt_inf_raises(self):
        with self.assertRaises(ValueError):
            self.mod.estimate_error(float("inf"), "strang", 50.0, 1e-6)

    def test_commutator_norm_nan_raises(self):
        with self.assertRaises(ValueError):
            self.mod.estimate_error(1e-4, "strang", float("nan"), 1e-6)

    def test_target_error_inf_raises(self):
        with self.assertRaises(ValueError):
            self.mod.estimate_error(1e-4, "strang", 50.0, float("inf"))


class TestIntegratorSelectorSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "integrator_selector",
            "skills/core-numerical/numerical-integration/scripts/integrator_selector.py",
        )

    def test_dimension_exceeds_max_raises(self):
        with self.assertRaises(ValueError):
            self.mod.select_integrator(
                False, False, False, False, False, "medium", 20_000_000_000, False
            )

    def test_negative_dimension_raises(self):
        with self.assertRaises(ValueError):
            self.mod.select_integrator(
                False, False, False, False, False, "medium", -1, False
            )


if __name__ == "__main__":
    unittest.main()
