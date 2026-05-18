#!/usr/bin/env python3
"""Plan molecular dynamics trajectory analysis tasks."""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Dict, List


GOAL_MAP = {
    "rdf": ("radial distribution function", ["positions", "cell", "species"]),
    "coordination": ("coordination number", ["positions", "cell", "species", "cutoff rule"]),
    "bond-angle": ("bond-angle distribution", ["positions", "neighbor list", "species"]),
    "diffusion": ("MSD and diffusion coefficient", ["unwrapped positions", "time axis"]),
    "msd": ("MSD and diffusion coefficient", ["unwrapped positions", "time axis"]),
    "vacf": ("velocity autocorrelation", ["velocities", "time axis"]),
    "vdos": ("vibrational density of states", ["velocities", "time axis"]),
    "stress-strain": ("stress-strain curve", ["stress or virial", "strain history"]),
    "equilibration": ("equilibration diagnostics", ["thermo history", "time axis"]),
}


def _split_goals(value: str) -> List[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def plan_md_analysis(
    system: str,
    goals: List[str],
    trajectory_format: str,
    has_velocities: bool,
    has_stress: bool,
    unwrap_needed: bool,
    timestep_fs: float | None,
) -> Dict:
    if not system.strip():
        raise ValueError("system must not be empty")
    if not goals:
        raise ValueError("at least one goal is required")
    if timestep_fs is not None and (not math.isfinite(timestep_fs) or timestep_fs <= 0):
        raise ValueError("timestep_fs must be a positive finite number")

    analyses = []
    required_data = set()
    warnings: List[str] = []
    for goal in goals:
        if goal not in GOAL_MAP:
            warnings.append(f"Unknown goal {goal!r}; add a custom analysis note.")
            analyses.append({"goal": goal, "method": "custom analysis", "status": "needs review"})
            continue
        method, requirements = GOAL_MAP[goal]
        status = "ready"
        if goal in {"vacf", "vdos"} and not has_velocities:
            status = "blocked"
            warnings.append(f"{goal} needs velocities or a defensible finite-difference velocity estimate.")
        if goal == "stress-strain" and not has_stress:
            status = "blocked"
            warnings.append("stress-strain analysis needs stress/virial output and strain history.")
        if goal in {"diffusion", "msd"} and unwrap_needed:
            warnings.append("Diffusion analysis requires unwrapped trajectories before fitting MSD.")
        if goal in {"diffusion", "msd", "vacf", "vdos", "equilibration"} and timestep_fs is None:
            status = "needs time axis"
            warnings.append(f"{goal} needs timestep or saved-frame spacing.")
        required_data.update(requirements)
        analyses.append({"goal": goal, "method": method, "status": status})

    return {
        "analysis_plan": analyses,
        "required_data": sorted(required_data),
        "equilibration_checks": [
            "discard startup transient before property fits",
            "check temperature and pressure plateaus",
            "compare first-half and second-half property estimates",
            "use block averaging for uncertainty",
        ],
        "pbc_handling": {
            "unwrap_needed": unwrap_needed,
            "minimum_action": "unwrap before displacement-based analysis" if unwrap_needed else "confirm wrapping convention",
            "format_note": f"Check image flags or cell metadata for {trajectory_format}",
        },
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--system", required=True)
    parser.add_argument("--goals", required=True, help="Comma-separated goals")
    parser.add_argument("--trajectory-format", default="unknown")
    parser.add_argument("--has-velocities", action="store_true")
    parser.add_argument("--has-stress", action="store_true")
    parser.add_argument("--unwrap-needed", action="store_true")
    parser.add_argument("--timestep-fs", type=float)
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        results = plan_md_analysis(
            system=args.system,
            goals=_split_goals(args.goals),
            trajectory_format=args.trajectory_format,
            has_velocities=args.has_velocities,
            has_stress=args.has_stress,
            unwrap_needed=args.unwrap_needed,
            timestep_fs=args.timestep_fs,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = {
        "inputs": {
            "system": args.system,
            "goals": _split_goals(args.goals),
            "trajectory_format": args.trajectory_format,
            "has_velocities": args.has_velocities,
            "has_stress": args.has_stress,
            "unwrap_needed": args.unwrap_needed,
            "timestep_fs": args.timestep_fs,
        },
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Analysis plan:")
        for item in results["analysis_plan"]:
            print(f"- {item['goal']}: {item['method']} ({item['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
