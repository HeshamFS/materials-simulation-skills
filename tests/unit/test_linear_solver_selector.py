import unittest

from tests.unit._utils import load_module


class TestLinearSolverSelector(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "solver_selector",
            "skills/core-numerical/linear-solvers/scripts/solver_selector.py",
        )

    def test_spd_sparse_large(self):
        result = self.mod.select_solver(
            symmetric=True,
            positive_definite=True,
            sparse=True,
            size=1_000_000,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=True,
        )
        self.assertIn("CG", result["recommended"])
        self.assertTrue(any("IC/AMG" in note for note in result["notes"]))

    def test_symmetric_indefinite(self):
        result = self.mod.select_solver(
            symmetric=True,
            positive_definite=False,
            sparse=False,
            size=1000,
            nearly_symmetric=False,
            ill_conditioned=False,
            complex_valued=False,
            memory_limited=False,
        )
        self.assertIn("MINRES", result["recommended"])

    def test_nonsymmetric(self):
        result = self.mod.select_solver(
            symmetric=False,
            positive_definite=False,
            sparse=True,
            size=10000,
            nearly_symmetric=False,
            ill_conditioned=True,
            complex_valued=False,
            memory_limited=False,
        )
        self.assertIn("GMRES (restarted)", result["recommended"])
        self.assertTrue(any("preconditioning" in note for note in result["notes"]))

    def test_invalid_size(self):
        with self.assertRaises(ValueError):
            self.mod.select_solver(
                symmetric=False,
                positive_definite=False,
                sparse=False,
                size=0,
                nearly_symmetric=False,
                ill_conditioned=False,
                complex_valued=False,
                memory_limited=False,
            )


if __name__ == "__main__":
    unittest.main()
