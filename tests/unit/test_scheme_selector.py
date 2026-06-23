import unittest

from tests.unit._utils import load_module


class TestSchemeSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "scheme_selector",
            "skills/core-numerical/differentiation-schemes/scripts/scheme_selector.py",
        )

    def test_smooth_periodic(self):
        result = self.mod.select_scheme(
            smooth=True,
            periodic=True,
            discontinuous=False,
            order=1,
            accuracy=4,
            boundary=False,
        )
        self.assertIn("Spectral", result["recommended"][0])

    def test_discontinuous(self):
        result = self.mod.select_scheme(
            smooth=False,
            periodic=False,
            discontinuous=True,
            order=1,
            accuracy=2,
            boundary=True,
        )
        self.assertTrue(any("Finite Volume" in s for s in result["recommended"]))
        self.assertTrue(any("boundar" in n.lower() for n in result["notes"]))

    def test_invalid_flags(self):
        with self.assertRaises(ValueError):
            self.mod.select_scheme(
                smooth=True,
                periodic=False,
                discontinuous=True,
                order=1,
                accuracy=2,
                boundary=False,
            )

    def test_smooth_non_periodic_recommends_central(self):
        # F6: smooth, non-periodic should recommend Central FD (consistent with
        # the central stencil the workflow generates), not Spectral.
        result = self.mod.select_scheme(
            smooth=True,
            periodic=False,
            discontinuous=False,
            order=2,
            accuracy=4,
            boundary=False,
        )
        self.assertEqual(result["recommended"], ["Central FD"])

    def test_smooth_advection_lists_higher_order_upwind(self):
        # F5: smooth-advection output is self-supporting (higher-order upwind
        # alternative + pointer to truncation_error.py).
        result = self.mod.select_scheme(
            smooth=True,
            periodic=False,
            discontinuous=False,
            order=1,
            accuracy=2,
            boundary=False,
        )
        self.assertTrue(
            any("upwind" in a.lower() for a in result["alternatives"])
        )
        self.assertTrue(
            any("truncation_error.py" in n for n in result["notes"])
        )


if __name__ == "__main__":
    unittest.main()
