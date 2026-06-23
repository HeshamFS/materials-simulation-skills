#!/usr/bin/env python3
"""Trigger (discovery) evaluation: does a skill's *description* cause the agent to
actually consult the skill on the right prompts — and stay out of the way on
tricky near-miss prompts that should NOT trigger it?

The description is the primary triggering mechanism. A scientifically correct
skill that never activates is worthless; one that over-triggers is noise. This
runner exercises the description against a labelled query set through the chosen
coding-agent CLI and reports the trigger rate vs. the expected label.

Query set (JSON list); design ~20, half should-trigger, half tricky negatives:
    [ {"query": "...", "should_trigger": true},
      {"query": "...", "should_trigger": false} ]
If --queries is omitted, the skill's eval prompts are used as should_trigger=true
cases (add negatives via --queries for a real discrimination test).

Detection is heuristic and CLI-agnostic: the skill is installed for the run and
"triggered" means the agent's transcript shows it consulted the skill (its name,
SKILL.md, or one of its script files appears in the captured output). This is a
pragmatic cross-tool signal; for the most precise detection on Claude Code, parse
its stream-json tool-use events. Use --dry-run to print the plan without running.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import agent_adapters as A  # noqa: E402


def _skill_markers(skill_dir: Path) -> list[str]:
    markers = [skill_dir.name, "SKILL.md"]
    scripts = skill_dir / "scripts"
    if scripts.is_dir():
        markers += [p.name for p in scripts.glob("*.py")]
    return [m for m in markers if m]


def _detect_triggered(stdout: str, markers: list[str]) -> bool:
    low = stdout.lower()
    return any(m.lower() in low for m in markers)


def run_query(skill_dir: Path, query: str, cli: str, model: str | None,
              tmp_root: Path, timeout: int, dry_run: bool) -> dict:
    workdir = tmp_root / "workdir"
    workdir.mkdir(parents=True, exist_ok=True)
    sub = A.get(cli)["skills_project_subdir"]
    dest = workdir / sub / skill_dir.name
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_dir, dest, dirs_exist_ok=True)
    argv = A.build_argv(cli, query, workdir=str(workdir.resolve()), model=model, with_skill=True)
    rec: dict[str, Any] = {"command": A.command_string(argv), "argv": argv}
    if dry_run:
        rec["dry_run"] = True
        return rec
    cwd = str(workdir.resolve()) if A.runs_in_cwd(cli) else os.getcwd()
    start = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                              timeout=timeout, check=False)
        rec["exit_code"] = proc.returncode
        rec["duration_ms"] = int((time.monotonic() - start) * 1000)
        rec["triggered"] = _detect_triggered(proc.stdout + proc.stderr, _skill_markers(skill_dir))
    except subprocess.TimeoutExpired:
        rec["error"] = f"timeout {timeout}s"
        rec["triggered"] = False
    except FileNotFoundError:
        rec["error"] = f"binary '{A.get(cli)['binary']}' not found; install: {A.get(cli)['install']}"
        rec["triggered"] = None
    return rec


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Trigger/discovery eval for a skill description via a coding-agent CLI")
    p.add_argument("--skill", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--queries", default=None, help="JSON file: [{query, should_trigger}]")
    p.add_argument("--runs-per-query", type=int, default=3)
    p.add_argument("--threshold", type=float, default=0.5, help="trigger-rate pass threshold")
    p.add_argument("--model", default=None)
    p.add_argument("--workspace", default=None, help="temp root for run dirs (default: system temp)")
    p.add_argument("--timeout", type=int, default=120)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    skill_dir = Path(args.skill).resolve()
    if not (skill_dir / "SKILL.md").exists():
        print(f"Not a skill directory: {skill_dir}", file=sys.stderr)
        return 2
    try:
        cli = A.resolve(args.agent)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.queries:
        queries = json.loads(Path(args.queries).read_text(encoding="utf-8"))
    else:
        ev = json.loads((skill_dir / "evals" / "evals.json").read_text(encoding="utf-8"))
        queries = [{"query": c["prompt"], "should_trigger": True} for c in ev.get("evals", [])]

    import tempfile
    base = Path(args.workspace).resolve() if args.workspace else Path(tempfile.mkdtemp(prefix="trigger-"))
    results = []
    for i, q in enumerate(queries):
        triggers = []
        runs = []
        for r in range(args.runs_per_query):
            rec = run_query(skill_dir, q["query"], cli, args.model,
                            base / f"q{i}" / f"r{r}", args.timeout, args.dry_run)
            runs.append(rec)
            if not args.dry_run and rec.get("triggered") is not None:
                triggers.append(bool(rec.get("triggered")))
        rate = (sum(triggers) / len(triggers)) if triggers else None
        should = q.get("should_trigger", True)
        passed = None
        if rate is not None:
            passed = (rate >= args.threshold) if should else (rate < args.threshold)
        results.append({"query": q["query"], "should_trigger": should,
                        "trigger_rate": rate, "passed": passed, "runs": runs})

    graded = [r for r in results if r["passed"] is not None]
    passed = sum(1 for r in graded if r["passed"])
    out = {
        "skill": skill_dir.name, "agent": cli, "dry_run": args.dry_run,
        "threshold": args.threshold, "runs_per_query": args.runs_per_query,
        "summary": {"queries": len(results), "graded": len(graded),
                    "passed": passed, "failed": len(graded) - passed},
        "results": results,
        "auth_env_required": A.get(cli)["auth_env"],
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        if args.dry_run:
            print(f"DRY RUN: trigger eval {skill_dir.name} via {cli}, "
                  f"{len(queries)} queries x {args.runs_per_query} runs")
            for r in results:
                print(f"  [{'+' if r['should_trigger'] else '-'}] {r['query'][:70]}")
                print(f"      {r['runs'][0]['command']}")
        else:
            for r in graded:
                st = "PASS" if r["passed"] else "FAIL"
                print(f"[{st}] rate={r['trigger_rate']:.2f} expect_trigger={r['should_trigger']}: {r['query'][:60]}")
            print(f"\n{passed}/{len(graded)} trigger cases passed (threshold {args.threshold})")
    return 0 if (args.dry_run or passed == len(graded)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
