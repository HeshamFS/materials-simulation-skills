---
name: hpc-runtime-doctor
description: >
  Diagnose HPC runtime and scheduler problems for materials simulations,
  including MPI/OpenMP/GPU layout, modules, CUDA/Kokkos hints, scratch paths,
  walltime, job arrays, restart strategy, scheduler portability, and resource
  mismatch. Use when jobs fail, run slowly, get killed, or behave differently
  on a cluster than on a workstation.
allowed-tools: Read, Bash, Write, Grep, Glob
metadata:
  author: HeshamFS
  version: "1.0.0"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
    - gemini-cli
    - vs-code-copilot
  eval_cases: 3
  last_reviewed: "2026-05-18"
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
| GPUs | GPUs requested | `4` |
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

- `resource_layout`
- `diagnoses`
- `environment_checks`
- `retry_plan`
- `scheduler_notes`

## Workflow

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

## Error Handling

Invalid resource counts stop with exit code 2. Unknown symptoms are preserved as custom items for human review.

## Limitations

This skill does not query a live scheduler. It diagnoses from the submitted layout and symptoms.

## Security

- Inputs are scalar CLI values and booleans only.
- The script does not execute scheduler commands or inspect environment variables.
- The skill uses `Bash` only to run its bundled script.

## References

- See `references/hpc_runtime_patterns.md` for scheduler and runtime diagnosis patterns.

## Version History

- 1.0.0: Initial HPC runtime diagnosis skill.
