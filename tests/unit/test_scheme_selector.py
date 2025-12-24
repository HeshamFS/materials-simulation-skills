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


if __name__ == "__main__":
    unittest.main()
