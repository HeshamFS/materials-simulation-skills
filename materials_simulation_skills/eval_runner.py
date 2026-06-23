"""Deterministic evaluation runner for Materials Simulation Skills.

This is the *mechanical* grading layer described by the Agent Skills evaluation
spec (https://agentskills.io/skill-creation/evaluating-skills): "For assertions
that can be checked by code ... use a verification script -- scripts are more
reliable than LLM judgment for mechanical checks and reusable across iterations."

It executes the optional ``script_checks`` block that a skill's
``evals/evals.json`` may attach to each eval case, runs the named script with the
given arguments, and grades the parsed ``--json`` output against a list of
assertions. This catches the largest class of skill defects found in the audit
(documentation/number drift between SKILL.md and the scripts) and guards against
regression, without needing an LLM or network access -- so it runs in CI.

The companion LLM-judge layer (running each eval prompt with vs. without the
skill and grading the natural-language ``assertions``) is intentionally NOT here;
it requires an agent runtime and is opt-in. See ROADMAP.md.

``script_checks`` schema (all keys optional except ``cmd`` and ``assert``)::

    "script_checks": [
      {
        "description": "human-readable label",
        "cmd": ["scripts/cfl_checker.py", "--dx", "0.01", ..., "--json"],
        "expect_exit": 0,
        "assert": [
          {"path": "metrics.fourier", "op": "approx", "value": 1e-4, "rel_tol": 1e-6},
          {"path": "stable", "op": "eq", "value": true}
        ]
      }
    ]

``cmd[0]`` is resolved relative to the skill directory (keeping evals portable).
``path`` is a dotted path into the JSON output; list indices are integers.
Supported ``op`` values: eq, ne, approx, gt, ge, lt, le, contains, in, type,
exists, truthy, falsy.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

from .skill_utils import find_repo_root, iter_skill_dirs


class CheckError(Exception):
    """Raised for a malformed script_checks definition."""


def _resolve_path(obj: Any, dotted: str) -> Any:
    """Walk a dotted path into nested dicts/lists. Raises KeyError if absent."""
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
    """Evaluate one assertion against the parsed JSON. Returns (passed, evidence)."""
    if "path" not in spec:
        raise CheckError(f"assertion missing 'path': {spec!r}")
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

    if op not in ("type",) and "value" not in spec:
        raise CheckError(f"assertion op '{op}' requires 'value': {spec!r}")
    expected = spec.get("value")

    try:
        if op == "eq":
            ok = actual == expected
        elif op == "ne":
            ok = actual != expected
        elif op == "approx":
            ok = math.isclose(
                float(actual), float(expected),
                rel_tol=float(spec.get("rel_tol", 1e-6)),
                abs_tol=float(spec.get("abs_tol", 0.0)),
            )
        elif op in _NUMERIC_OPS:
            a, e = float(actual), float(expected)
            ok = {"gt": a > e, "ge": a >= e, "lt": a < e, "le": a <= e}[op]
        elif op == "contains":
            ok = expected in actual  # substring or membership
        elif op == "in":
            ok = actual in expected
        elif op == "type":
            type_map = {
                "number": (int, float), "int": int, "float": float,
                "str": str, "bool": bool, "list": list, "dict": dict,
                "null": type(None),
            }
            want = type_map.get(str(expected))
            if want is None:
                raise CheckError(f"unknown type {expected!r}")
            # bool is a subclass of int; treat distinctly
            if expected == "number":
                ok = isinstance(actual, (int, float)) and not isinstance(actual, bool)
            else:
                ok = isinstance(actual, want)
        else:
            raise CheckError(f"unknown op {op!r}")
    except (TypeError, ValueError) as exc:
        return False, f"{path}={actual!r} could not be compared ({op} {expected!r}): {exc}"

    return ok, f"{path}={actual!r} {op} {expected!r}"


def _run_one_check(skill_dir: Path, check: dict) -> dict:
    """Run a single script_check and grade its assertions."""
    cmd = check.get("cmd")
    if not cmd or not isinstance(cmd, list):
        raise CheckError(f"script_check missing list 'cmd': {check!r}")
    asserts = check.get("assert", [])
    if not isinstance(asserts, list):
        raise CheckError(f"script_check 'assert' must be a list: {check!r}")

    script = (skill_dir / cmd[0]).resolve()
    expect_exit = int(check.get("expect_exit", 0))
    record: dict[str, Any] = {
        "description": check.get("description", " ".join(str(c) for c in cmd)),
        "cmd": cmd,
        "passed": False,
        "exit_code": None,
        "assertions": [],
        "error": None,
    }

    if not script.exists():
        record["error"] = f"script not found: {cmd[0]}"
        return record

    proc = subprocess.run(
        [sys.executable, str(script), *[str(a) for a in cmd[1:]]],
        cwd=skill_dir, capture_output=True, text=True, check=False,
    )
    record["exit_code"] = proc.returncode
    exit_ok = proc.returncode == expect_exit
    if not exit_ok:
        record["error"] = (
            f"exit {proc.returncode} != expected {expect_exit}; "
            f"stderr: {proc.stderr.strip()[:300]}"
        )

    parsed = None
    if proc.stdout.strip():
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            record["error"] = (record["error"] or "") + f" | invalid JSON: {exc}"

    all_ok = exit_ok and (parsed is not None or not asserts)
    for spec in asserts:
        if parsed is None:
            record["assertions"].append({"assert": spec, "passed": False, "evidence": "no JSON output to grade"})
            all_ok = False
            continue
        ok, evidence = _grade_assertion(parsed, spec)
        record["assertions"].append({"assert": spec, "passed": ok, "evidence": evidence})
        all_ok = all_ok and ok

    record["passed"] = all_ok
    return record


def run_eval_checks(root: Path | None = None, skill_name: str | None = None) -> dict:
    """Run all ``script_checks`` across skills (or one skill).

    Returns a structured result with per-skill, per-case grading and an overall
    summary. ``ok`` is False if any check failed (CI gate).
    """
    root = find_repo_root(root)
    skills_out: list[dict] = []
    totals = {
        "skills_with_checks": 0,
        "cases_with_checks": 0,
        "cases_without_checks": 0,
        "checks": 0,
        "checks_passed": 0,
        "assertions": 0,
        "assertions_passed": 0,
    }
    any_fail = False
    selected = False

    for skill_dir in iter_skill_dirs(root):
        if skill_name and skill_dir.name != skill_name:
            continue
        selected = True
        eval_path = skill_dir / "evals" / "evals.json"
        if not eval_path.exists():
            continue
        data = json.loads(eval_path.read_text(encoding="utf-8"))
        cases = data.get("evals", [])
        case_records: list[dict] = []
        skill_has_checks = False
        for case in cases:
            checks = case.get("script_checks") or []
            if not checks:
                totals["cases_without_checks"] += 1
                continue
            skill_has_checks = True
            totals["cases_with_checks"] += 1
            check_records = []
            for check in checks:
                rec = _run_one_check(skill_dir, check)
                check_records.append(rec)
                totals["checks"] += 1
                totals["checks_passed"] += int(rec["passed"])
                totals["assertions"] += len(rec["assertions"])
                totals["assertions_passed"] += sum(a["passed"] for a in rec["assertions"])
                if not rec["passed"]:
                    any_fail = True
            case_records.append({"id": case.get("id"), "checks": check_records})
        if skill_has_checks:
            totals["skills_with_checks"] += 1
            skills_out.append({"skill": skill_dir.name, "cases": case_records})

    if skill_name and not selected:
        return {"ok": False, "error": f"Unknown skill: {skill_name}", "summary": totals, "skills": []}

    return {"ok": not any_fail, "summary": totals, "skills": skills_out}
