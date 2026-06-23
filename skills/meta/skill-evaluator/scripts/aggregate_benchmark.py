#!/usr/bin/env python3
"""Aggregate graded runs into a benchmark with the with/without-skill delta.

Reads grading.json files written under an iteration workspace and produces
benchmark.json + benchmark.md with mean/stddev/min/max per configuration and the
delta between the first two configurations (typically with_skill vs.
without_skill). The delta in pass_rate is the headline measure of a skill's value.

Layout consumed (as produced by run_quality_eval.py + a grading pass):
    <iteration_dir>/
      eval-<id>-<slug>/
        with_skill/run-1/grading.json   (+ optional timing.json)
        without_skill/run-1/grading.json

grading.json must contain summary.pass_rate / passed / failed / total (see
references/schemas.md and references/grader.md). Adapted from the open-source
skill-creator reference aggregator; kept dependency-free and agent-agnostic.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def stats(values: list[float]) -> dict:
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    mean = sum(values) / n
    stddev = math.sqrt(sum((x - mean) ** 2 for x in values) / (n - 1)) if n > 1 else 0.0
    return {"mean": round(mean, 4), "stddev": round(stddev, 4),
            "min": round(min(values), 4), "max": round(max(values), 4)}


def load_runs(iteration_dir: Path) -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for eval_dir in sorted(iteration_dir.glob("eval-*")):
        if not eval_dir.is_dir():
            continue
        try:
            eval_id = int(eval_dir.name.split("-")[1])
        except (ValueError, IndexError):
            eval_id = eval_dir.name
        for config_dir in sorted(eval_dir.iterdir()):
            if not config_dir.is_dir() or not list(config_dir.glob("run-*")):
                continue
            config = config_dir.name
            results.setdefault(config, [])
            for run_dir in sorted(config_dir.glob("run-*")):
                gpath = run_dir / "grading.json"
                if not gpath.exists():
                    continue
                try:
                    g = json.loads(gpath.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                summ = g.get("summary", {})
                row = {
                    "eval_id": eval_id,
                    "run_number": int(run_dir.name.split("-")[1]) if "-" in run_dir.name else 1,
                    "pass_rate": summ.get("pass_rate", 0.0),
                    "passed": summ.get("passed", 0),
                    "failed": summ.get("failed", 0),
                    "total": summ.get("total", 0),
                    "expectations": g.get("expectations", []),
                }
                tpath = run_dir / "timing.json"
                if tpath.exists():
                    try:
                        t = json.loads(tpath.read_text(encoding="utf-8"))
                        row["time_seconds"] = t.get("total_duration_seconds", 0.0)
                        row["tokens"] = t.get("total_tokens") or 0
                    except json.JSONDecodeError:
                        pass
                row.setdefault("time_seconds", g.get("timing", {}).get("total_duration_seconds", 0.0))
                row.setdefault("tokens", 0)
                results[config].append(row)
    return results


def aggregate(results: dict[str, list[dict]]) -> dict:
    summary = {}
    configs = list(results.keys())
    for cfg in configs:
        runs = results[cfg]
        summary[cfg] = {
            "pass_rate": stats([r["pass_rate"] for r in runs]),
            "time_seconds": stats([r.get("time_seconds", 0.0) for r in runs]),
            "tokens": stats([r.get("tokens", 0) for r in runs]),
        }
    if len(configs) >= 2:
        a, b = summary[configs[0]], summary[configs[1]]
        summary["delta"] = {
            "pass_rate": f"{a['pass_rate']['mean'] - b['pass_rate']['mean']:+.2f}",
            "time_seconds": f"{a['time_seconds']['mean'] - b['time_seconds']['mean']:+.1f}",
            "tokens": f"{a['tokens']['mean'] - b['tokens']['mean']:+.0f}",
        }
    return summary


def build_benchmark(iteration_dir: Path, skill_name: str, agent: str = "") -> dict:
    results = load_runs(iteration_dir)
    run_summary = aggregate(results)
    runs = []
    for cfg, rows in results.items():
        for r in rows:
            runs.append({
                "eval_id": r["eval_id"], "configuration": cfg, "run_number": r["run_number"],
                "result": {"pass_rate": r["pass_rate"], "passed": r["passed"],
                           "failed": r["failed"], "total": r["total"],
                           "time_seconds": r.get("time_seconds", 0.0), "tokens": r.get("tokens", 0)},
                "expectations": r["expectations"],
            })
    eval_ids = sorted({r["eval_id"] for rows in results.values() for r in rows}, key=str)
    return {
        "metadata": {"skill_name": skill_name or iteration_dir.parent.name, "agent": agent,
                     "evals_run": eval_ids, "iteration_dir": str(iteration_dir)},
        "runs": runs, "run_summary": run_summary, "notes": [],
    }


def to_markdown(b: dict) -> str:
    m, rs = b["metadata"], b["run_summary"]
    configs = [k for k in rs if k != "delta"]
    a = configs[0] if configs else "config_a"
    bb = configs[1] if len(configs) > 1 else "config_b"
    d = rs.get("delta", {})
    la, lb = a.replace("_", " ").title(), bb.replace("_", " ").title()
    out = [f"# Skill Benchmark: {m['skill_name']}", "",
           f"**Agent**: {m.get('agent','')}  ", f"**Evals**: {', '.join(map(str, m['evals_run']))}", "",
           f"| Metric | {la} | {lb} | Delta |", "|---|---|---|---|"]
    pa, pb = rs.get(a, {}).get("pass_rate", {}), rs.get(bb, {}).get("pass_rate", {})
    out.append(f"| Pass rate | {pa.get('mean',0)*100:.0f}% ± {pa.get('stddev',0)*100:.0f}% | "
               f"{pb.get('mean',0)*100:.0f}% ± {pb.get('stddev',0)*100:.0f}% | {d.get('pass_rate','—')} |")
    ta, tb = rs.get(a, {}).get("time_seconds", {}), rs.get(bb, {}).get("time_seconds", {})
    out.append(f"| Time (s) | {ta.get('mean',0):.1f} ± {ta.get('stddev',0):.1f} | "
               f"{tb.get('mean',0):.1f} ± {tb.get('stddev',0):.1f} | {d.get('time_seconds','—')} |")
    if b.get("notes"):
        out += ["", "## Notes", ""] + [f"- {n}" for n in b["notes"]]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Aggregate graded runs into benchmark.json/.md with delta")
    p.add_argument("iteration_dir", type=Path)
    p.add_argument("--skill-name", default="")
    p.add_argument("--agent", default="")
    p.add_argument("--output", "-o", type=Path, default=None)
    p.add_argument("--json", action="store_true", help="Print benchmark JSON to stdout")
    args = p.parse_args(argv)

    if not args.iteration_dir.exists():
        print(f"Not found: {args.iteration_dir}", file=sys.stderr)
        return 2
    benchmark = build_benchmark(args.iteration_dir, args.skill_name, args.agent)
    out_json = args.output or (args.iteration_dir / "benchmark.json")
    out_json.write_text(json.dumps(benchmark, indent=2), encoding="utf-8")
    out_json.with_suffix(".md").write_text(to_markdown(benchmark), encoding="utf-8")
    if args.json:
        print(json.dumps(benchmark, indent=2))
    else:
        rs = benchmark["run_summary"]
        print(f"Wrote {out_json}")
        for cfg in [k for k in rs if k != "delta"]:
            print(f"  {cfg.replace('_',' ').title()}: {rs[cfg]['pass_rate']['mean']*100:.1f}% pass rate")
        if "delta" in rs:
            print(f"  Delta (pass rate): {rs['delta']['pass_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
