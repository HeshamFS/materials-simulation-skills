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
  version: "1.2.0"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
  last_evaluated: "2026-06-23"
  eval_cases: 3
  last_reviewed: "2026-06-23"
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

- Use **one-off scripts** for fewer than 5 local exploratory runs (no provenance, no HPC).
- Use **jobflow/atomate2** when the workflow is Python-native and Materials Project style input sets are useful.
- Use **AiiDA** when provenance-critical work is also remote (HPC) or large (>= 50 runs) — i.e. long-lived, database-backed campaigns. For smaller local provenance needs, atomate2 (Materials Project codes, >= 10 runs) or jobflow stores already capture inputs, outputs, code version, and environment, so the mapper recommends those instead of the heavier AiiDA stack.
- Use **pyiron** when interactive atomistic workflows, notebooks, and job management are the primary user surface (ASE/LAMMPS without strict provenance).

The recommendations are emitted in a fixed precedence so the prose and the implemented thresholds agree: an explicit `--preferred` engine overrides everything; otherwise one-off (small local, no provenance/HPC) -> AiiDA (provenance AND remote/large) -> atomate2 (VASP/QE/CP2K/force-field, >= 10 runs) -> pyiron (ASE/LAMMPS, no provenance) -> jobflow (fallback).

## Script Outputs

`scripts/workflow_engine_mapper.py` emits:

- `recommended_engine`
- `dag_pattern`
- `provenance_requirements`
- `restart_strategy`
- `storage_layout`
- `migration_triggers`
- `notes`

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
- `runs` must be a finite positive integer and is capped at 1,000,000; out-of-range or non-finite values exit with code 2.
- Free-text fields are length-bounded: `task` <= 2000 characters, `code` and `preferred` <= 100 characters each; `preferred` must be one of the allowed engine names.
- All invalid input is rejected with a message on stderr and exit code 2 before any recommendation is computed.
- It does not connect to remote services, submit jobs, read files, or deserialize untrusted data.
- The skill uses `Bash` only to run the bundled script.

## References

- See `references/workflow_engines.md` for engine selection heuristics.

## Version History

- 1.2.0: Strengthen evals with deterministic `script_checks` that pin the mapper's exact output (recommended_engine, dag_pattern, provenance_requirements, restart_strategy, migration_triggers) so each case discriminates the skill from a from-memory baseline.
- 1.1.0: Compose branch+sweep DAG patterns instead of overwriting; emit a forward-looking migration trigger for one-off runs; document AiiDA gating/precedence; add input-validation safeguards (bounds, length caps) matching the Security section.
- 1.0.0: Initial workflow engine mapping skill.
