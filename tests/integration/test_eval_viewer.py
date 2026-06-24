"""Test the skill-evaluator HTML eval viewer (eval-viewer/generate_review.py)."""
import unittest

from tests.unit._utils import load_module

VIEWER = load_module(
    "generate_review",
    "skills/meta/skill-evaluator/eval-viewer/generate_review.py",
)

BENCHMARK = {
    "metadata": {"skill_name": "numerical-stability", "agent": "claude-code", "evals_run": [1]},
    "runs": [
        {"eval_id": 1, "configuration": "with_skill",
         "result": {"pass_rate": 1.0, "passed": 2, "total": 2},
         "expectations": [{"text": "Fo computed correctly", "passed": True, "evidence": "metrics.fourier=1e-4"}]},
        {"eval_id": 1, "configuration": "without_skill",
         "result": {"pass_rate": 0.5, "passed": 1, "total": 2},
         "expectations": [{"text": "Fo computed correctly", "passed": False, "evidence": "no script run"}]},
    ],
    "run_summary": {
        "with_skill": {"pass_rate": {"mean": 1.0, "stddev": 0.0}, "time_seconds": {"mean": 42, "stddev": 3}, "tokens": {"mean": 3800, "stddev": 0}},
        "without_skill": {"pass_rate": {"mean": 0.5, "stddev": 0.0}, "time_seconds": {"mean": 30, "stddev": 2}, "tokens": {"mean": 2100, "stddev": 0}},
        "delta": {"pass_rate": "+0.50", "time_seconds": "+12.0", "tokens": "+1700"},
    },
    "notes": ["baseline could not run the script"],
}


class TestEvalViewer(unittest.TestCase):
    def setUp(self):
        self.html = VIEWER.render(BENCHMARK)

    def test_is_standalone_html(self):
        self.assertTrue(self.html.lstrip().startswith("<!doctype html>"))
        self.assertIn("</html>", self.html)
        # Self-contained: no external script/stylesheet fetches.
        self.assertNotIn("<script src", self.html)
        self.assertNotIn("<link", self.html)

    def test_shows_skill_delta_and_evidence(self):
        self.assertIn("numerical-stability", self.html)
        self.assertIn("+0.50", self.html)              # the headline delta
        self.assertIn("With Skill", self.html)
        self.assertIn("Without Skill", self.html)
        self.assertIn("metrics.fourier=1e-4", self.html)  # per-assertion evidence
        self.assertIn("baseline could not run the script", self.html)  # notes

    def test_escapes_content(self):
        evil = dict(BENCHMARK)
        evil["metadata"] = {**BENCHMARK["metadata"], "skill_name": "<script>alert(1)</script>"}
        out = VIEWER.render(evil)
        self.assertNotIn("<script>alert(1)</script>", out)
        self.assertIn("&lt;script&gt;", out)


if __name__ == "__main__":
    unittest.main()
