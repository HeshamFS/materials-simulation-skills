import unittest

import numpy as np

from tests.unit._utils import load_module


class TestProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfl = load_module(
            "cfl_checker",
            "skills/core-numerical/numerical-stability/scripts/cfl_checker.py",
        )
        cls.vn = load_module(
            "von_neumann_analyzer",
            "skills/core-numerical/numerical-stability/scripts/von_neumann_analyzer.py",
        )
        cls.cond = load_module(
            "matrix_condition",
            "skills/core-numerical/numerical-stability/scripts/matrix_condition.py",
        )
        cls.stiff = load_module(
            "stiffness_detector",
            "skills/core-numerical/numerical-stability/scripts/stiffness_detector.py",
        )

    def test_cfl_metrics_scale_with_dt(self):
        result1 = self.cfl.compute_cfl(
            dx=0.2,
            dt=0.01,
            velocity=1.5,
            diffusivity=0.4,
            reaction_rate=2.0,
            dimensions=2,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        result2 = self.cfl.compute_cfl(
            dx=0.2,
            dt=0.02,
            velocity=1.5,
            diffusivity=0.4,
            reaction_rate=2.0,
            dimensions=2,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        self.assertAlmostEqual(
            result2["metrics"]["cfl"] / result1["metrics"]["cfl"], 2.0, places=6
        )
        self.assertAlmostEqual(
            result2["metrics"]["fourier"] / result1["metrics"]["fourier"], 2.0, places=6
        )
        self.assertAlmostEqual(
            result2["metrics"]["reaction"] / result1["metrics"]["reaction"], 2.0, places=6
        )

    def test_cfl_recommended_dt_is_safe(self):
        result = self.cfl.compute_cfl(
            dx=0.1,
            dt=1.0,
            velocity=2.0,
            diffusivity=0.5,
            reaction_rate=1.0,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        recommended = result["recommended_dt"]
        self.assertIsNotNone(recommended)
        check = self.cfl.compute_cfl(
            dx=0.1,
            dt=recommended * 0.9,
            velocity=2.0,
            diffusivity=0.5,
            reaction_rate=1.0,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        self.assertTrue(check["stable"])

    def test_cfl_safety_factor_scales(self):
        base = self.cfl.compute_cfl(
            dx=0.1,
            dt=1.0,
            velocity=2.0,
            diffusivity=0.5,
            reaction_rate=1.0,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=1.0,
        )
        scaled = self.cfl.compute_cfl(
            dx=0.1,
            dt=1.0,
            velocity=2.0,
            diffusivity=0.5,
            reaction_rate=1.0,
            dimensions=1,
            scheme="explicit",
            advection_limit=None,
            diffusion_limit=None,
            reaction_limit=None,
            safety=0.5,
        )
        self.assertAlmostEqual(
            scaled["recommended_dt"], base["recommended_dt"] * 0.5, places=6
        )

    def test_cfl_stable_implies_below_limits(self):
        rng = np.random.default_rng(2)
        for _ in range(5):
            dx = rng.uniform(0.05, 0.2)
            dt = rng.uniform(0.001, 0.01)
            velocity = rng.uniform(0.1, 1.0)
            diffusivity = rng.uniform(0.01, 0.2)
            result = self.cfl.compute_cfl(
                dx=dx,
                dt=dt,
                velocity=velocity,
                diffusivity=diffusivity,
                reaction_rate=None,
                dimensions=1,
                scheme="explicit",
                advection_limit=None,
                diffusion_limit=None,
                reaction_limit=None,
                safety=1.0,
            )
            if result["stable"]:
                self.assertLessEqual(
                    result["metrics"]["cfl"], result["limits"]["advection_limit"] + 1e-12
                )
                self.assertLessEqual(
                    result["metrics"]["fourier"],
                    result["limits"]["diffusion_limit"] + 1e-12,
                )
    def test_von_neumann_nonnegative_coeffs_sum_one(self):
        rng = np.random.default_rng(0)
        for _ in range(5):
            coeffs = rng.random(4)
            coeffs = coeffs / coeffs.sum()
            result = self.vn.compute_amplification(
                coeffs=coeffs,
                dx=1.0,
                nk=128,
                offset=None,
                kmin=None,
                kmax=None,
            )
            self.assertTrue(result["results"]["stable"])

    def test_von_neumann_scaling_property(self):
        rng = np.random.default_rng(3)
        coeffs = rng.normal(0.0, 1.0, size=5)
        base = self.vn.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=256,
            offset=None,
            kmin=None,
            kmax=None,
        )
        factor = 2.5
        scaled = self.vn.compute_amplification(
            coeffs=coeffs * factor,
            dx=1.0,
            nk=256,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertAlmostEqual(
            scaled["results"]["max_amplification"],
            base["results"]["max_amplification"] * factor,
            places=6,
        )

    def test_von_neumann_sampling_resolution(self):
        coeffs = np.array([0.1, -0.2, 1.3, -0.2, 0.1], dtype=float)
        coarse = self.vn.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=64,
            offset=None,
            kmin=None,
            kmax=None,
        )
        fine = self.vn.compute_amplification(
            coeffs=coeffs,
            dx=1.0,
            nk=512,
            offset=None,
            kmin=None,
            kmax=None,
        )
        self.assertGreaterEqual(
            fine["results"]["max_amplification"],
            coarse["results"]["max_amplification"] - 1e-8,
        )

    def test_stiffness_ratio_invariant_to_scaling(self):
        eigs = np.array([-1.0, -10.0, -100.0])
        result1 = self.stiff.compute_stiffness(eigs, threshold=1e3)
        result2 = self.stiff.compute_stiffness(eigs * 5.0, threshold=1e3)
        self.assertAlmostEqual(
            result1["stiffness_ratio"], result2["stiffness_ratio"], places=6
        )

    def test_diagonal_condition_number(self):
        rng = np.random.default_rng(1)
        diag = rng.uniform(1.0, 10.0, size=5)
        matrix = np.diag(diag)
        result = self.cond.compute_condition(
            matrix=matrix,
            norm=2.0,
            symmetry_tol=1e-8,
            skip_eigs=False,
        )
        expected = diag.max() / diag.min()
        self.assertAlmostEqual(result["condition_number"], expected, places=6)
        self.assertTrue(result["is_symmetric"])

    def test_condition_invariant_to_scaling(self):
        matrix = np.array([[2.0, 0.0], [0.0, 5.0]])
        base = self.cond.compute_condition(
            matrix=matrix,
            norm=2.0,
            symmetry_tol=1e-8,
            skip_eigs=True,
        )
        scaled = self.cond.compute_condition(
            matrix=matrix * 3.0,
            norm=2.0,
            symmetry_tol=1e-8,
            skip_eigs=True,
        )
        self.assertAlmostEqual(
            base["condition_number"], scaled["condition_number"], places=6
        )


if __name__ == "__main__":
    unittest.main()
