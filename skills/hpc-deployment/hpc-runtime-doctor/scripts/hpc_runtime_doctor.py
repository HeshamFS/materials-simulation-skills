#!/usr/bin/env python3
"""Diagnose common HPC runtime and scheduler issues."""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Dict, List


SYMPTOM_RULES = {
    "oom": ("memory", "Increase memory, reduce ranks per node, or reduce per-rank memory footprint."),
    "killed": ("scheduler", "Check walltime, memory limits, preemption policy, and stdout/stderr."),
    "timeout": ("walltime", "Add checkpoint/restart and request walltime based on measured throughput."),
    "slow-gpu": ("gpu", "Confirm GPU build, device binding, CPU/GPU balance, and accelerator package."),
    "mpi-hang": ("mpi", "Check MPI implementation mismatch, fabric settings, and collective imbalance."),
    "filesystem": ("io", "Move heavy I/O to scratch and reduce metadata-heavy small-file writes."),
    "module": ("environment", "Capture module list and verify compiler/MPI/CUDA ABI compatibility."),
    "restart-missing": ("restart", "Write restart files before walltime and copy them out of scratch."),
}


def _positive_int(value: int, name: str) -> int:
    if not math.isfinite(float(value)) or value < 0:
        raise ValueError(f"{name} must be a non-negative finite integer")
    return value


def _split_symptoms(value: str) -> List[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def diagnose_hpc(
    scheduler: str,
    nodes: int,
    tasks: int,
    cpus_per_task: int,
    gpus: int,
    symptoms: List[str],
    uses_mpi: bool,
    uses_openmp: bool,
    uses_gpu: bool,
    walltime: str | None,
    scratch: bool,
) -> Dict:
    for name, value in {
        "nodes": nodes,
        "tasks": tasks,
        "cpus_per_task": cpus_per_task,
        "gpus": gpus,
    }.items():
        _positive_int(value, name)
    if nodes == 0:
        raise ValueError("nodes must be at least 1")
    if tasks == 0:
        raise ValueError("tasks must be at least 1")
    if cpus_per_task == 0:
        raise ValueError("cpus_per_task must be at least 1")

    tasks_per_node = tasks / nodes
    total_cpus = tasks * cpus_per_task
    diagnoses = []
    for symptom in symptoms:
        if symptom in SYMPTOM_RULES:
            category, action = SYMPTOM_RULES[symptom]
            diagnoses.append({"symptom": symptom, "category": category, "recommended_action": action})
        else:
            diagnoses.append(
                {
                    "symptom": symptom,
                    "category": "custom",
                    "recommended_action": "Collect scheduler stderr, stdout, module list, and command line.",
                }
            )

    warnings: List[str] = []
    if uses_openmp and cpus_per_task == 1:
        warnings.append("OpenMP requested but cpus_per_task is 1.")
    if uses_gpu and gpus == 0:
        warnings.append("GPU execution requested but no GPUs are allocated.")
    if uses_mpi and tasks < nodes:
        warnings.append("MPI task count is lower than node count; check scheduler layout.")
    if gpus and tasks_per_node > max(gpus, 1) * 16:
        warnings.append("Many MPI ranks per GPU may reduce GPU efficiency.")
    if not scratch and ("filesystem" in symptoms or tasks >= 64):
        warnings.append("Large parallel jobs should use node-local or parallel scratch for heavy I/O.")

    return {
        "resource_layout": {
            "scheduler": scheduler,
            "nodes": nodes,
            "tasks": tasks,
            "tasks_per_node": tasks_per_node,
            "cpus_per_task": cpus_per_task,
            "total_cpus": total_cpus,
            "gpus": gpus,
            "walltime": walltime,
        },
        "diagnoses": diagnoses,
        "environment_checks": [
            "record module list and loaded compiler/MPI stack",
            "record executable path and version",
            "verify MPI launcher matches the loaded MPI",
            "verify CUDA/Kokkos/OpenMP build flags when using accelerators",
            "capture scheduler stdout and stderr",
        ],
        "retry_plan": [
            "rerun the smallest reproducing case",
            "enable frequent restart/checkpoint files",
            "change one resource variable at a time",
            "save scheduler script and environment snapshot with results",
        ],
        "scheduler_notes": [
            "SLURM: compare --ntasks, --ntasks-per-node, and --cpus-per-task",
            "PBS/LSF: translate resources carefully; names differ across sites",
            "GPU queues often require account, partition, constraint, or gres flags",
        ],
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scheduler", default="slurm")
    parser.add_argument("--nodes", type=int, default=1)
    parser.add_argument("--tasks", type=int, default=1)
    parser.add_argument("--cpus-per-task", type=int, default=1)
    parser.add_argument("--gpus", type=int, default=0)
    parser.add_argument("--symptoms", default="")
    parser.add_argument("--uses-mpi", action="store_true")
    parser.add_argument("--uses-openmp", action="store_true")
    parser.add_argument("--uses-gpu", action="store_true")
    parser.add_argument("--walltime")
    parser.add_argument("--scratch", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        results = diagnose_hpc(
            scheduler=args.scheduler,
            nodes=args.nodes,
            tasks=args.tasks,
            cpus_per_task=args.cpus_per_task,
            gpus=args.gpus,
            symptoms=_split_symptoms(args.symptoms),
            uses_mpi=args.uses_mpi,
            uses_openmp=args.uses_openmp,
            uses_gpu=args.uses_gpu,
            walltime=args.walltime,
            scratch=args.scratch,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = {"inputs": vars(args), "results": results}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for item in results["diagnoses"]:
            print(f"{item['symptom']}: {item['recommended_action']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
