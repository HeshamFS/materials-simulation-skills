---
name: workflow-engine-mapper
description: >
  Map computational materials tasks onto workflow engines such as atomate2,
  jobflow, AiiDA, pyiron, or a simple one-off script. Use when deciding how to
  structure a reproducible campaign, DAG, restart strategy, provenance record,
  storage layout, or migration path from ad hoc scripts to managed workflows.
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

# Workflow Engine Mapper

## Goal

Choose the smallest workflow structure that preserves reproducibility, restartability, and provenance for a materials simulation task.

## Requirements

- Python 3.10+
- No external dependencies
- Works on Linux, macOS, and Windows

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Task | Workflow purpose | `VASP relax-static-DOS for 200 structures` |
| Code | Main simulation engine | `vasp`, `qe`, `lammps`, `ase` |
| Runs | Approximate number of calculations | `200` |
| Provenance | Whether audit trail matters | `true` |
| Restart | Whether jobs may resume after failure | `true` |
| HPC | Whether remote scheduler is required | `true` |

## Decision Guidance

- Use **one-off scripts** for fewer than 5 local exploratory runs.
- Use **jobflow/atomate2** when the workflow is Python-native and Materials Project style input sets are useful.
- Use **AiiDA** when provenance, database-backed records, and remote execution are central.
- Use **pyiron** when interactive atomistic workflows, notebooks, and job management are the primary user surface.

## Script Outputs

`scripts/workflow_engine_mapper.py` emits:

- `recommended_engine`
- `dag_pattern`
- `provenance_requirements`
- `restart_strategy`
- `storage_layout`
- `migration_triggers`

## Workflow

```bash
python3 skills/simulation-workflow/workflow-engine-mapper/scripts/workflow_engine_mapper.py \
  --task "relax static dos for 200 oxides" \
  --code vasp \
  --runs 200 \
  --needs-provenance \
  --needs-restart \
  --hpc \
  --json
```

Use the output to scaffold the workflow before writing engine-specific code.

## Error Handling

If the task has too few details, choose the conservative pattern and ask for engine, run count, and restart needs before implementation.

## Limitations

The skill does not replace the official APIs of atomate2, jobflow, AiiDA, or pyiron; it selects and explains the workflow shape.

## Security

- The script accepts only scalar CLI inputs and booleans.
- It does not connect to remote services or submit jobs.
- The skill uses `Bash` only to run the bundled script.

## References

- See `references/workflow_engines.md` for engine selection heuristics.

## Version History

- 1.0.0: Initial workflow engine mapping skill.
