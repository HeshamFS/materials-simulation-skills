"""Property-based tests for core-numerical skills.

Uses Hypothesis to verify mathematical invariants of CFL checker,
von Neumann analyzer, and mesh quality functions.
"""

import math
import unittest

import numpy as np

try:
    from hypothesis import given, strategies as st, settings, assume
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    def given(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    settings = lambda **kwargs: lambda func: func
    st = None
    def assume(x):
        pass

from tests.unit._utils import load_module


@unittest.skipIf(not HYPOTHESIS_AVAILABLE, "Hypothesis not installed")
class TestCflCheckerProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "cfl_checker",
            "skills/core-numerical/numerical-stability/scripts/cfl_checker.py",
        )

    @given(
        velocity=st.floats(min_value=0.01, max_value=1e6, allow_nan=False, allow_infinity=False),
        dt=st.floats(min_value=1e-12, max_value=1.0, allow_nan=False, allow_infinity=False),
        dx=st.floats(min_value=1e-12, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_cfl_formula_correctness(self, velocity, dt, dx):
        """CFL number must equal v*dt/dx."""
        result = self.mod.compute_cfl(
            dx=dx, dt=dt, velocity=velocity,
            diffusivity=None, reaction_rate=None, dimensions=1,
            scheme="explicit", advection_limit=None, diffusion_limit=None,
            reaction_limit=None, safety=1.0,
        )
        expected_cfl = velocity * dt / dx
        self.assertAlmostEqual(result["metrics"]["cfl"], expected_cfl, places=6)

    @given(
        diffusivity=st.floats(min_value=0.01, max_value=1e4, allow_nan=False, allow_infinity=False),
        dt=st.floats(min_value=1e-12, max_value=1.0, allow_nan=False, allow_infinity=False),
        dx=st.floats(min_value=1e-6, max_value=1.0, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_fourier_limit_decreases_with_dimensions(self, diffusivity, dt, dx):
        """Fourier stability limit should decrease with more dimensions."""
        r1 = self.mod.compute_cfl(
            dx=dx, dt=dt, velocity=None, diffusivity=diffusivity,
            reaction_rate=None, dimensions=1, scheme="explicit",
            advection_limit=None, diffusion_limit=None, reaction_limit=None, safety=1.0,
        )
        r2 = self.mod.compute_cfl(
            dx=dx, dt=dt, velocity=None, diffusivity=diffusivity,
            reaction_rate=None, dimensions=2, scheme="explicit",
            advection_limit=None, diffusion_limit=None, reaction_limit=None, safety=1.0,
        )
        self.assertGreater(
            r1["limits"]["diffusion_limit"],
            r2["limits"]["diffusion_limit"],
        )


@unittest.skipIf(not HYPOTHESIS_AVAILABLE, "Hypothesis not installed")
class TestVonNeumannProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "von_neumann_analyzer",
            "skills/core-numerical/numerical-stability/scripts/von_neumann_analyzer.py",
        )

    @given(
        coeffs=st.lists(
            st.floats(min_value=-2.0, max_value=2.0, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=7,
        ),
    )
    @settings(max_examples=100, deadline=None)
    def test_amplification_always_non_negative(self, coeffs):
        """Max amplification factor must be non-negative."""
        arr = np.array(coeffs, dtype=float)
        result = self.mod.compute_amplification(
            coeffs=arr, dx=1.0, nk=64, offset=None, kmin=None, kmax=None,
        )
        self.assertGreaterEqual(result["results"]["max_amplification"], 0.0)

    @given(
        r=st.floats(min_value=0.01, max_value=0.49, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None)
    def test_ftcs_diffusion_with_r_leq_half_stable(self, r):
        """FTCS diffusion scheme with r <= 0.5 must be stable."""
        coeffs = np.array([r, 1.0 - 2.0 * r, r], dtype=float)
        result = self.mod.compute_amplification(
            coeffs=coeffs, dx=1.0, nk=512, offset=None, kmin=None, kmax=None,
        )
        self.assertTrue(result["results"]["stable"])


@unittest.skipIf(not HYPOTHESIS_AVAILABLE, "Hypothesis not installed")
class TestMeshQualityProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "mesh_quality",
            "skills/core-numerical/mesh-generation/scripts/mesh_quality.py",
        )

    @given(
        dx=st.floats(min_value=1e-6, max_value=1e6, allow_nan=False, allow_infinity=False),
        dy=st.floats(min_value=1e-6, max_value=1e6, allow_nan=False, allow_infinity=False),
        dz=st.floats(min_value=1e-6, max_value=1e6, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=100, deadline=None)
    def test_aspect_ratio_at_least_one(self, dx, dy, dz):
        """Aspect ratio is always >= 1."""
        result = self.mod.compute_quality(dx, dy, dz)
        self.assertGreaterEqual(result["aspect_ratio"], 1.0 - 1e-12)

    @given(
        s=st.floats(min_value=1e-6, max_value=1e6, allow_nan=False, allow_infinity=False),
    )
    @settings(max_examples=50, deadline=None)
    def test_uniform_spacing_gives_unit_aspect_ratio(self, s):
        """Uniform spacing must give aspect_ratio=1 and skewness=0."""
        result = self.mod.compute_quality(s, s, s)
        self.assertAlmostEqual(result["aspect_ratio"], 1.0, places=10)
        self.assertAlmostEqual(result["skewness"], 0.0, places=10)


if __name__ == "__main__":
    unittest.main()
