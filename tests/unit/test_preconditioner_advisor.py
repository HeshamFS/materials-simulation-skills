import unittest

from tests.unit._utils import load_module


class TestPreconditionerAdvisor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "preconditioner_advisor",
            "skills/core-numerical/linear-solvers/scripts/preconditioner_advisor.py",
        )

    def test_spd(self):
        result = self.mod.advise_preconditioner(
            matrix_type="spd",
            sparse=True,
            ill_conditioned=False,
            saddle_point=False,
            symmetric=True,
        )
        self.assertIn("Incomplete Cholesky (IC)", result["suggested"])

    def test_saddle_point(self):
        result = self.mod.advise_preconditioner(
            matrix_type="nonsymmetric",
            sparse=True,
            ill_conditioned=False,
            saddle_point=True,
            symmetric=False,
        )
        self.assertTrue(any("Schur" in s for s in result["suggested"]))

    def test_invalid_type(self):
        with self.assertRaises(ValueError):
            self.mod.advise_preconditioner(
                matrix_type="bad",
                sparse=True,
                ill_conditioned=False,
                saddle_point=False,
                symmetric=False,
            )


if __name__ == "__main__":
    unittest.main()
