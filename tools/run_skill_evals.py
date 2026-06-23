#!/usr/bin/env python3
"""Run deterministic ``script_checks`` from skill eval suites (CI gate).

This is the mechanical grading layer of the skill-evaluation harness. It runs
every ``script_checks`` block defined in skills' ``evals/evals.json`` and grades
the JSON output, failing (exit 1) if any check fails. The complementary
LLM-judge layer (with-skill vs. without-skill on the natural-language
assertions) is opt-in and lives outside CI; see ROADMAP.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials_simulation_skills.eval_runner import run_eval_checks  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", help="Run checks for one skill by name")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    result = run_eval_checks(ROOT, skill_name=args.skill)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["ok"] else 1

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        return 1

    for skill in result["skills"]:
        for case in skill["cases"]:
            for check in case["checks"]:
                status = "PASS" if check["passed"] else "FAIL"
                print(f"[{status}] {skill['skill']} (eval {case['id']}): {check['description']}")
                if not check["passed"]:
                    if check.get("error"):
                        print(f"         {check['error']}", file=sys.stderr)
                    for a in check["assertions"]:
                        if not a["passed"]:
                            print(f"         x {a['evidence']}", file=sys.stderr)

    s = result["summary"]
    print(
        f"\n{s['checks_passed']}/{s['checks']} script-checks passed "
        f"({s['assertions_passed']}/{s['assertions']} assertions) across "
        f"{s['skills_with_checks']} skills; "
        f"{s['cases_without_checks']} eval cases have no script_checks (LLM-judge only)."
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
