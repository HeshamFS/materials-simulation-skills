import unittest

from tests.unit._utils import load_module


class TestCflChecker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "cfl_checker",
            "skills/core-numerical/numerical-stability/scripts/cfl_checker.py",
        )

    def test_explicit_stable(self):
        result = self.mod.compute_cfl(
            dx=0.1,
            dt=0.01,
            velocity=1.0,
            diffusivity=0.1,
            reaction_rate=1.0,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        self.assertTrue(result["stable"])
        self.assertAlmostEqual(result["metrics"]["cfl"], 0.1, places=6)
        self.assertAlmostEqual(result["metrics"]["fourier"], 0.1, places=6)
        self.assertAlmostEqual(result["recommended_dt"], 0.05, places=6)

    def test_explicit_unstable(self):
        result = self.mod.compute_cfl(
            dx=0.1,
            dt=0.1,
            velocity=2.0,
            diffusivity=None,
            reaction_rate=None,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        self.assertFalse(result["stable"])
        self.assertAlmostEqual(result["recommended_dt"], 0.05, places=6)

    def test_reaction_unstable(self):
        result = self.mod.compute_cfl(
            dx=0.1,
            dt=0.2,
            velocity=None,
            diffusivity=None,
            reaction_rate=10.0,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        self.assertFalse(result["stable"])
        self.assertAlmostEqual(result["metrics"]["reaction"], 2.0, places=6)
        self.assertAlmostEqual(result["recommended_dt"], 0.1, places=6)

    def test_no_criteria(self):
        result = self.mod.compute_cfl(
            dx=0.1,
            dt=0.01,
            velocity=None,
            diffusivity=None,
            reaction_rate=None,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        self.assertIsNone(result["stable"])
        self.assertIn("No stability criteria applied", result["notes"][0])

    def test_criteria_applied_advection_only(self):
        result = self.mod.compute_cfl(
            dx=0.2,
            dt=0.1,
            velocity=0.5,
            diffusivity=None,
            reaction_rate=None,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        self.assertIn("advection", result["criteria_applied"])
        self.assertNotIn("diffusion", result["criteria_applied"])

    def test_custom_limits(self):
        result = self.mod.compute_cfl(
            dx=0.1,
            dt=0.1,
            velocity=1.0,
            diffusivity=1.0,
            reaction_rate=None,
            dimensions=1,
            scheme="explicit",
            advection_limit=0.2,
            diffusion_limit=0.1,
            reaction_limit=1.0,
            safety=1.0,
        )
        self.assertAlmostEqual(result["limits"]["advection_limit"], 0.2, places=6)
        self.assertAlmostEqual(result["limits"]["diffusion_limit"], 0.1, places=6)
        self.assertFalse(result["stable"])

    def test_invalid_dimensions(self):
        with self.assertRaises(ValueError):
            self.mod.compute_cfl(
                dx=0.1,
                dt=0.01,
                velocity=1.0,
                diffusivity=0.1,
                reaction_rate=None,
                dimensions=0,
                scheme="explicit",
                advection_limit=None,
                diffusion_limit=None,
                reaction_limit=None,
                safety=1.0,
            )

    def test_invalid_safety(self):
        with self.assertRaises(ValueError):
            self.mod.compute_cfl(
                dx=0.1,
                dt=0.01,
                velocity=1.0,
                diffusivity=0.1,
                reaction_rate=None,
                dimensions=1,
                scheme="explicit",
                advection_limit=None,
                diffusion_limit=None,
                reaction_limit=None,
                safety=0.0,
            )

    def test_diffusion_limit_dimensions(self):
        result = self.mod.compute_cfl(
            dx=0.1,
            dt=0.005,
            velocity=None,
            diffusivity=0.2,
            reaction_rate=None,
            dimensions=2,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        self.assertAlmostEqual(result["limits"]["diffusion_limit"], 0.25, places=6)
        self.assertTrue(result["stable"])

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            self.mod.compute_cfl(
                dx=0.0,
                dt=0.01,
                velocity=1.0,
                diffusivity=0.1,
                reaction_rate=None,
                dimensions=1,
                scheme="explicit",
                advection_limit=None,
                diffusion_limit=None,
                reaction_limit=None,
                safety=1.0,
            )


if __name__ == "__main__":
    unittest.main()
