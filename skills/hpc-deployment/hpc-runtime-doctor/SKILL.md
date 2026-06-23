---
name: hpc-runtime-doctor
description: >
  Diagnose HPC runtime and scheduler problems for materials simulations,
  including MPI/OpenMP/GPU layout, modules, CUDA/Kokkos hints, scratch paths,
  walltime, job arrays, restart strategy, scheduler portability, and resource
  mismatch. Use when an ALREADY-SUBMITTED job failed, ran slowly, got killed, or
  behaved differently on a cluster than on a workstation. To author or vet a NEW
  submission script before running, use slurm-job-script-generator instead.
allowed-tools: Read, Bash, Write, Grep, Glob
metadata:
  author: HeshamFS
  version: "1.1.1"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
  last_evaluated: "2026-06-23"
  eval_cases: 3
  last_reviewed: "2026-06-23"
---

# HPC Runtime Doctor

## Goal

Turn cluster symptoms into a resource-layout diagnosis, environment checklist, and safe retry plan.

## Requirements

- Python 3.10+
- No external dependencies
- Works on Linux, macOS, and Windows

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Scheduler | SLURM, PBS, LSF, local | `slurm` |
| Nodes/tasks/threads | Runtime layout | `2 nodes, 128 tasks, 2 threads` |
| GPUs | Total (whole-job) GPUs via `--gpus`, or per node via `--gpus-per-node` | `--gpus 4` or `--gpus-per-node 1` |
| Symptoms | Observed failure | `oom,killed,slow-gpu` |
| MPI/OpenMP/GPU use | Parallel modes | `mpi+openmp+gpu` |
| Walltime | Requested time | `12:00:00` |
| Scratch | Whether scratch is used | `true` |

## Decision Guidance

- Check resource layout before changing physics settings.
- Confirm module/compiler/MPI/CUDA consistency before debugging solver behavior.
- Treat missing restart files and scratch cleanup as workflow failures, not physics failures.
- For GPU jobs, confirm the executable was built with the requested accelerator backend.

## Script Outputs

`scripts/hpc_runtime_doctor.py` emits:

- `resource_layout` (includes `tasks_per_node`, `total_cpus`, total `gpus`, and `gpus_per_node`)
- `diagnoses`
- `environment_checks`
- `retry_plan`
- `scheduler_notes`
- `warnings` (layout flags such as ranks-per-GPU oversubscription, OpenMP/thread mismatch, and uneven task placement)

In default (non-JSON) mode the script also prints the resource-layout summary, any
`warnings`, environment checks, and retry plan, so the most actionable items are never hidden.

## Workflow

`--gpus` is the **total** (whole-job) GPU count. Use `--gpus-per-node` (SLURM
`--gres=gpu:N` semantics) when you know the per-node allocation; total GPUs are then
`gpus_per_node * nodes` and it overrides `--gpus`.

```bash
python3 skills/hpc-deployment/hpc-runtime-doctor/scripts/hpc_runtime_doctor.py \
  --scheduler slurm \
  --nodes 2 \
  --tasks 128 \
  --cpus-per-task 2 \
  --gpus 4 \
  --symptoms oom,slow-gpu \
  --uses-mpi \
  --uses-openmp \
  --uses-gpu \
  --json
```

The example above shares 128 ranks across 4 GPUs (32 ranks/GPU), so the
`warnings` list surfaces `Many MPI ranks per GPU (32.0 ranks/GPU) may reduce GPU
efficiency.` The ranks-per-GPU check uses total ranks over total GPUs, so it fires
correctly on multi-node jobs (the threshold is 16 ranks/GPU).

## Error Handling

Invalid resource counts stop with exit code 2. Unknown symptoms are preserved as custom items for human review.

## Limitations

This skill does not query a live scheduler. It diagnoses from the submitted layout and symptoms.

## Security

- Inputs are scalar CLI values and booleans only.
- Resource counts (`--nodes`, `--tasks`, `--cpus-per-task`, `--gpus`, `--gpus-per-node`)
  are validated as non-negative finite integers and capped at 1,000,000; out-of-range or
  non-integer values exit with code 2.
- The symptoms string is capped at 64 entries of at most 64 characters each; `--walltime`
  is capped at 32 characters. Oversized input exits with code 2.
- The script does not execute scheduler commands or inspect environment variables.
- The skill uses `Bash` only to run its bundled script.

## References

- See `references/hpc_runtime_patterns.md` for scheduler and runtime diagnosis patterns.

## Version History

- 1.1.1: Discriminating evals -- each case now pins the script's specific output
  (exact ranks-per-GPU warning, diagnosis categories, resource-layout fields) via
  deterministic `script_checks`.
- 1.1.0: Unit-consistent ranks-per-GPU warning (total ranks / total GPUs), new
  `--gpus-per-node` argument, integer `tasks_per_node` with an uneven-placement warning,
  full human-readable (non-JSON) output, and input caps for resource counts, symptoms,
  and walltime.
- 1.0.0: Initial HPC runtime diagnosis skill.
