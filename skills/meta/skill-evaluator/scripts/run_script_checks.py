#!/usr/bin/env python3
"""Deterministic (no-LLM) grading layer of the skill-evaluation harness.

Runs the optional ``script_checks`` block attached to a skill's eval cases and
grades the script's ``--json`` output against machine-checkable assertions. This
is the mechanical half the Agent Skills evaluation spec recommends:
"For assertions that can be checked by code ... use a verification script."

It catches the largest skill-defect class — drift between what a SKILL.md
documents and what its scripts emit — and runs anywhere, with no agent CLI, no
API key, and no network, so it belongs in CI.

This script is intentionally self-contained (standard library only) so the
skill-evaluator skill is portable across agents.

``script_checks`` schema (per eval case in evals/evals.json)::

    "script_checks": [
      {
        "description": "label",
        "cmd": ["scripts/cfl_checker.py", "--dx", "0.01", ..., "--json"],
        "expect_exit": 0,
        "assert": [
          {"path": "metrics.fourier", "op": "approx", "value": 1e-4, "rel_tol": 1e-3},
          {"path": "stable", "op": "eq", "value": true}
        ]
      }
    ]

``cmd[0]`` is resolved relative to the skill directory. ``path`` is a dotted path
into the JSON output (list indices are integers). Operators: eq, ne, approx, gt,
ge, lt, le, contains, in, type, exists, truthy, falsy.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


def _resolve_path(obj: Any, dotted: str) -> Any:
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError) as exc:
                raise KeyError(dotted) from exc
        elif isinstance(cur, dict):
            if part not in cur:
                raise KeyError(dotted)
            cur = cur[part]
        else:
            raise KeyError(dotted)
    return cur


_NUMERIC_OPS = {"gt", "ge", "lt", "le"}


def _grade_assertion(parsed: Any, spec: dict) -> tuple[bool, str]:
    path = spec["path"]
    op = spec.get("op", "eq")
    if op == "exists":
        try:
            _resolve_path(parsed, path)
            return True, f"{path} exists"
        except KeyError:
            return False, f"{path} is absent"
    try:
        actual = _resolve_path(parsed, path)
    except KeyError:
        return False, f"{path} not found in output"
    if op in ("truthy", "falsy"):
        ok = bool(actual) if op == "truthy" else not bool(actual)
        return ok, f"{path}={actual!r} is {'truthy' if bool(actual) else 'falsy'}"
    expected = spec.get("value")
    try:
        if op == "eq":
            ok = actual == expected
        elif op == "ne":
            ok = actual != expected
        elif op == "approx":
            ok = math.isclose(float(actual), float(expected),
                              rel_tol=float(spec.get("rel_tol", 1e-6)),
                              abs_tol=float(spec.get("abs_tol", 0.0)))
        elif op in _NUMERIC_OPS:
            a, e = float(actual), float(expected)
            ok = {"gt": a > e, "ge": a >= e, "lt": a < e, "le": a <= e}[op]
        elif op == "contains":
            ok = expected in actual
        elif op == "in":
            ok = actual in expected
        elif op == "type":
            if expected == "number":
                ok = isinstance(actual, (int, float)) and not isinstance(actual, bool)
            else:
                tmap = {"int": int, "float": float, "str": str, "bool": bool,
                        "list": list, "dict": dict, "null": type(None)}
                want = tmap.get(str(expected))
                if want is None:
                    return False, f"unknown type {expected!r}"
                ok = isinstance(actual, want)
        else:
            return False, f"unknown op {op!r}"
    except (TypeError, ValueError) as exc:
        return False, f"{path}={actual!r} not comparable ({op} {expected!r}): {exc}"
    return ok, f"{path}={actual!r} {op} {expected!r}"


def _run_check(skill_dir: Path, check: dict) -> dict:
    cmd = check.get("cmd")
    asserts = check.get("assert", [])
    rec: dict[str, Any] = {
        "description": check.get("description", " ".join(map(str, cmd or []))),
        "cmd": cmd, "passed": False, "exit_code": None, "assertions": [], "error": None,
    }
    if not cmd or not isinstance(cmd, list):
        rec["error"] = "script_check missing list 'cmd'"
        return rec
    script = (skill_dir / cmd[0]).resolve()
    if not script.exists():
        rec["error"] = f"script not found: {cmd[0]}"
        return rec
    proc = subprocess.run([sys.executable, str(script), *[str(a) for a in cmd[1:]]],
                          cwd=skill_dir, capture_output=True, text=True, check=False)
    rec["exit_code"] = proc.returncode
    exit_ok = proc.returncode == int(check.get("expect_exit", 0))
    if not exit_ok:
        rec["error"] = f"exit {proc.returncode} != {check.get('expect_exit', 0)}; stderr: {proc.stderr.strip()[:300]}"
    parsed = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            rec["error"] = (rec["error"] or "") + f" | invalid JSON: {exc}"
    all_ok = exit_ok and (parsed is not None or not asserts)
    for spec in asserts:
        if parsed is None:
            rec["assertions"].append({"assert": spec, "passed": False, "evidence": "no JSON output"})
            all_ok = False
            continue
        ok, ev = _grade_assertion(parsed, spec)
        rec["assertions"].append({"assert": spec, "passed": ok, "evidence": ev})
        all_ok = all_ok and ok
    rec["passed"] = all_ok
    return rec


def run_skill(skill_dir: Path) -> dict:
    """Run all script_checks for one skill directory."""
    eval_path = skill_dir / "evals" / "evals.json"
    cases_out, n_checks, n_pass, n_assert, n_assert_pass, n_nocheck = [], 0, 0, 0, 0, 0
    any_fail = False
    if not eval_path.exists():
        return {"ok": True, "skill": skill_dir.name, "error": "no evals/evals.json", "cases": [], "summary": {}}
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    for case in data.get("evals", []):
        checks = case.get("script_checks") or []
        if not checks:
            n_nocheck += 1
            continue
        recs = []
        for chk in checks:
            r = _run_check(skill_dir, chk)
            recs.append(r)
            n_checks += 1
            n_pass += int(r["passed"])
            n_assert += len(r["assertions"])
            n_assert_pass += sum(a["passed"] for a in r["assertions"])
            any_fail = any_fail or not r["passed"]
        cases_out.append({"id": case.get("id"), "checks": recs})
    return {
        "ok": not any_fail,
        "skill": skill_dir.name,
        "cases": cases_out,
        "summary": {
            "checks": n_checks, "checks_passed": n_pass,
            "assertions": n_assert, "assertions_passed": n_assert_pass,
            "cases_without_checks": n_nocheck,
        },
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run deterministic script_checks for a skill")
    p.add_argument("--skill", required=True, help="Path to the skill directory (containing evals/evals.json)")
    p.add_argument("--json", action="store_true", help="Emit JSON")
    args = p.parse_args(argv)

    skill_dir = Path(args.skill).resolve()
    if not (skill_dir / "SKILL.md").exists():
        print(f"Not a skill directory (no SKILL.md): {skill_dir}", file=sys.stderr)
        return 2
    result = run_skill(skill_dir)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1
    for case in result["cases"]:
        for chk in case["checks"]:
            status = "PASS" if chk["passed"] else "FAIL"
            print(f"[{status}] eval {case['id']}: {chk['description']}")
            if not chk["passed"]:
                if chk.get("error"):
                    print(f"        {chk['error']}", file=sys.stderr)
                for a in chk["assertions"]:
                    if not a["passed"]:
                        print(f"        x {a['evidence']}", file=sys.stderr)
    s = result.get("summary", {})
    if s:
        print(f"\n{s['checks_passed']}/{s['checks']} checks passed "
              f"({s['assertions_passed']}/{s['assertions']} assertions); "
              f"{s['cases_without_checks']} cases have no script_checks (LLM-judge only).")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
