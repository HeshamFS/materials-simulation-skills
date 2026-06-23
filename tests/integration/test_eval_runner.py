"""Tests for the deterministic skill-eval harness (materials_simulation_skills.eval_runner).

Covers the grading engine (path resolution, operators, exit-code handling) and a
live end-to-end run that all seeded ``script_checks`` pass — so the harness is
itself regression-guarded in CI alongside the skills it checks.
"""
import unittest

from materials_simulation_skills.eval_runner import (
    _grade_assertion,
    _resolve_path,
    run_eval_checks,
)
from materials_simulation_skills.skill_utils import find_repo_root


class TestPathResolution(unittest.TestCase):
    def test_nested_dict_and_list(self):
        obj = {"a": {"b": [10, 20, {"c": 3}]}}
        self.assertEqual(_resolve_path(obj, "a.b.0"), 10)
        self.assertEqual(_resolve_path(obj, "a.b.2.c"), 3)

    def test_missing_path_raises(self):
        with self.assertRaises(KeyError):
            _resolve_path({"a": 1}, "a.b")
        with self.assertRaises(KeyError):
            _resolve_path({"a": [1]}, "a.5")


class TestGradeAssertion(unittest.TestCase):
    def setUp(self):
        self.obj = {"metrics": {"cfl": 50.0, "fourier": 1e-4}, "stable": False, "name": "von Neumann"}

    def test_eq_and_ne(self):
        self.assertTrue(_grade_assertion(self.obj, {"path": "stable", "op": "eq", "value": False})[0])
        self.assertFalse(_grade_assertion(self.obj, {"path": "stable", "op": "eq", "value": True})[0])
        self.assertTrue(_grade_assertion(self.obj, {"path": "stable", "op": "ne", "value": True})[0])

    def test_approx(self):
        self.assertTrue(_grade_assertion(self.obj, {"path": "metrics.cfl", "op": "approx", "value": 50.0, "rel_tol": 1e-9})[0])
        self.assertTrue(_grade_assertion(self.obj, {"path": "metrics.fourier", "op": "approx", "value": 1e-4, "rel_tol": 1e-3})[0])
        self.assertFalse(_grade_assertion(self.obj, {"path": "metrics.cfl", "op": "approx", "value": 49.0, "rel_tol": 1e-6})[0])

    def test_numeric_ops(self):
        self.assertTrue(_grade_assertion(self.obj, {"path": "metrics.cfl", "op": "gt", "value": 1.0})[0])
        self.assertTrue(_grade_assertion(self.obj, {"path": "metrics.fourier", "op": "lt", "value": 0.5})[0])

    def test_contains_and_type(self):
        self.assertTrue(_grade_assertion(self.obj, {"path": "name", "op": "contains", "value": "Neumann"})[0])
        self.assertTrue(_grade_assertion(self.obj, {"path": "metrics.cfl", "op": "type", "value": "number"})[0])
        self.assertFalse(_grade_assertion(self.obj, {"path": "stable", "op": "type", "value": "number"})[0])

    def test_exists_and_missing(self):
        self.assertTrue(_grade_assertion(self.obj, {"path": "metrics.cfl", "op": "exists"})[0])
        self.assertFalse(_grade_assertion(self.obj, {"path": "metrics.absent", "op": "exists"})[0])
        # A missing path on a value comparison fails gracefully, not raises.
        ok, evidence = _grade_assertion(self.obj, {"path": "metrics.absent", "op": "eq", "value": 1})
        self.assertFalse(ok)
        self.assertIn("not found", evidence)


class TestEndToEnd(unittest.TestCase):
    def test_all_seeded_checks_pass(self):
        """Every seeded script_check must pass against the live scripts.

        This is the skill-level regression guard: if a script's output drifts
        from its documented/expected behavior, this fails in CI.
        """
        result = run_eval_checks(find_repo_root())
        failures = [
            (s["skill"], c["id"], chk["description"], chk.get("error"))
            for s in result["skills"]
            for c in s["cases"]
            for chk in c["checks"]
            if not chk["passed"]
        ]
        self.assertTrue(result["ok"], msg=f"script_checks failed: {failures}")
        self.assertGreaterEqual(result["summary"]["checks"], 7)
        self.assertEqual(result["summary"]["checks"], result["summary"]["checks_passed"])

    def test_unknown_skill_reports_error(self):
        result = run_eval_checks(find_repo_root(), skill_name="does-not-exist")
        self.assertFalse(result["ok"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
