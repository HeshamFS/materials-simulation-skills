#!/usr/bin/env python3
"""Output-quality evaluation: run each eval prompt WITH the skill and as a
no-skill BASELINE, through whichever coding-agent CLI the user selected, and lay
the runs out in the spec's workspace structure for grading + benchmarking.

This implements the agent-agnostic version of the canonical loop
(https://agentskills.io/skill-creation/evaluating-skills): the value of a skill
is the *delta* between its with-skill and without-skill pass rates. Each run
starts from a clean working directory so the agent follows only the SKILL.md.

Pipeline per eval case and per configuration (with_skill, without_skill):
  1. Build an isolated working dir; for with_skill, install the skill into the
     CLI's project skills directory (e.g. .claude/skills/<name>); copy eval files.
  2. Build the headless command via the per-CLI adapter (agent_adapters.py).
  3. Run it (unless --dry-run), capturing stdout -> response, wall-clock timing,
     and any files the agent wrote to outputs/.
  4. Write <workspace>/iteration-N/eval-<id>/<config>/{outputs/, response.txt,
     timing.json, run.json}.

Then grade each run against its assertions (see references/grader.md) into
grading.json, and aggregate with aggregate_benchmark.py.

Use --dry-run to print the exact plan and commands without executing anything —
handy for verifying adapter wiring before spending tokens.
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


def _slug(text: str, n: int = 40) -> str:
    keep = [c if (c.isalnum() or c in "-_") else "-" for c in text.lower()]
    s = "".join(keep).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s[:n] or "eval"


def _wrapper_prompt(eval_prompt: str, outputs_dir: Path, files: list[str], save_hint: str) -> str:
    """Wrap the user's eval prompt with the standard execution envelope."""
    lines = [
        "Execute this task and save any deliverables to the outputs directory.",
        "",
        f"Task: {eval_prompt}",
        f"Input files: {', '.join(files) if files else 'none'}",
        f"Save all outputs (files you create) to: {outputs_dir}",
        f"Outputs to save: {save_hint or 'any files or analysis the task calls for'}",
        "",
        "Also write a short user_notes.md in that outputs directory listing any uncertainties, things that need review, or workarounds you used.",
    ]
    return "\n".join(lines)


def prepare_run_dir(
    skill_dir: Path, run_dir: Path, cli: str, with_skill: bool, files: list[str], eval_src_dir: Path,
) -> Path:
    """Create an isolated working dir; install the skill if with_skill. Returns workdir."""
    workdir = run_dir / "workdir"
    outputs = run_dir / "outputs"
    workdir.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    if with_skill:
        sub = A.get(cli)["skills_project_subdir"]
        dest = workdir / sub / skill_dir.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(skill_dir, dest, dirs_exist_ok=True)
    # Copy eval input files into the workdir (preserve relative names)
    for rel in files:
        src = (eval_src_dir / rel)
        if src.exists():
            tgt = workdir / Path(rel).name
            shutil.copy2(src, tgt)
    return workdir


def run_one(
    skill_dir: Path, eval_case: dict, cli: str, config: str, run_dir: Path,
    model: str | None, eval_src_dir: Path, timeout: int, dry_run: bool,
) -> dict:
    with_skill = config == "with_skill"
    files = eval_case.get("files", []) or []
    outputs_dir = run_dir / "outputs"
    workdir = prepare_run_dir(skill_dir, run_dir, cli, with_skill, files, eval_src_dir)
    prompt = _wrapper_prompt(
        eval_case["prompt"], outputs_dir.resolve(), files,
        eval_case.get("expected_output", ""),
    )
    argv = A.build_argv(cli, prompt, workdir=str(workdir.resolve()), model=model, with_skill=with_skill)
    runs_in_cwd = A.runs_in_cwd(cli)
    cmd_str = A.command_string(argv)

    record: dict[str, Any] = {
        "eval_id": eval_case.get("id"),
        "configuration": config,
        "cli": A.resolve(cli),
        "with_skill": with_skill,
        "command": cmd_str,
        "argv": argv,
        "runs_in_cwd": runs_in_cwd,
        "workdir": str(workdir.resolve()),
        "outputs_dir": str(outputs_dir.resolve()),
    }
    if dry_run:
        record["dry_run"] = True
        (run_dir / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        return record

    cwd = str(workdir.resolve()) if runs_in_cwd else os.getcwd()
    start = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                              timeout=timeout, check=False)
        duration_ms = int((time.monotonic() - start) * 1000)
        (run_dir / "response.txt").write_text(proc.stdout, encoding="utf-8")
        if proc.stderr:
            (run_dir / "stderr.txt").write_text(proc.stderr, encoding="utf-8")
        record["exit_code"] = proc.returncode
        record["duration_ms"] = duration_ms
        timing = {"duration_ms": duration_ms, "total_duration_seconds": round(duration_ms / 1000, 1),
                  "total_tokens": _extract_tokens(proc.stdout, cli)}
        (run_dir / "timing.json").write_text(json.dumps(timing, indent=2), encoding="utf-8")
    except subprocess.TimeoutExpired:
        record["exit_code"] = None
        record["error"] = f"timed out after {timeout}s"
    except FileNotFoundError:
        record["exit_code"] = None
        record["error"] = (f"CLI binary '{A.get(cli)['binary']}' not found on PATH. "
                           f"Install: {A.get(cli)['install']}")
    (run_dir / "run.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def _extract_tokens(stdout: str, cli: str) -> int | None:
    """Best-effort token extraction from a CLI's JSON result envelope (Claude-style)."""
    try:
        kind = A.get(cli)["invocation"]["result_kind"]
    except KeyError:
        return None
    if not kind.startswith("json:"):
        return None
    try:
        doc = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return None
    usage = doc.get("usage") if isinstance(doc, dict) else None
    if isinstance(usage, dict):
        total = 0
        for k in ("input_tokens", "output_tokens", "total_tokens"):
            v = usage.get(k)
            if isinstance(v, (int, float)):
                total += int(v)
        return total or None
    return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Run with-skill vs baseline quality eval via a coding-agent CLI")
    p.add_argument("--skill", required=True, help="Path to the skill directory")
    p.add_argument("--agent", required=True, help="Coding-agent CLI id/alias (see agent_adapters.py list)")
    p.add_argument("--workspace", required=True, help="Workspace root for results")
    p.add_argument("--iteration", type=int, default=1)
    p.add_argument("--model", default=None)
    p.add_argument("--only", type=int, default=None, help="Run a single eval id")
    p.add_argument("--baseline", choices=["without_skill", "none"], default="without_skill",
                   help="'without_skill' runs a no-skill baseline; 'none' runs only with_skill")
    p.add_argument("--timeout", type=int, default=600)
    p.add_argument("--dry-run", action="store_true", help="Print the plan/commands; execute nothing")
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

    evals_path = skill_dir / "evals" / "evals.json"
    cases = json.loads(evals_path.read_text(encoding="utf-8")).get("evals", [])
    if args.only is not None:
        cases = [c for c in cases if c.get("id") == args.only]
    configs = ["with_skill"] + ([] if args.baseline == "none" else ["without_skill"])

    iter_dir = Path(args.workspace).resolve() / f"iteration-{args.iteration}"
    plan = []
    for case in cases:
        ename = f"eval-{case.get('id')}-{_slug(case.get('expected_output', case['prompt']))}"
        for cfg in configs:
            run_dir = iter_dir / ename / cfg / "run-1"
            run_dir.mkdir(parents=True, exist_ok=True)
            rec = run_one(skill_dir, case, cli, cfg, run_dir, args.model,
                          eval_src_dir=skill_dir, timeout=args.timeout, dry_run=args.dry_run)
            plan.append(rec)

    auth = A.get(cli)["auth_env"]
    summary = {
        "skill": skill_dir.name, "agent": cli, "iteration": args.iteration,
        "configs": configs, "evals": [c.get("id") for c in cases],
        "runs": len(plan), "dry_run": args.dry_run,
        "workspace": str(iter_dir),
        "auth_env_required": auth,
        "next_steps": [
            "Grade each run against its assertions per references/grader.md -> grading.json",
            f"Aggregate: python aggregate_benchmark.py {iter_dir} --skill-name {skill_dir.name} --json",
        ],
    }
    if args.json:
        print(json.dumps({"summary": summary, "runs": plan}, indent=2))
    else:
        print(f"{'DRY RUN: ' if args.dry_run else ''}{skill_dir.name} via {cli} "
              f"-> {len(plan)} runs in {iter_dir}")
        if args.dry_run:
            for r in plan:
                print(f"  [eval {r['eval_id']} / {r['configuration']}] {r['command']}")
        print(f"  auth: set one of {auth}")
        for s in summary["next_steps"]:
            print(f"  next: {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
