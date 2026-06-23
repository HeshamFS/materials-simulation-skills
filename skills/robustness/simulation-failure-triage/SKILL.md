---
name: simulation-failure-triage
description: >
  First-response triage for cross-code (LAMMPS/VASP/QE/MOOSE) simulation
  failures: classifies the failure signature (nonconvergence, NaN/Inf,
  exploding energy, unstable timestep, pressure blow-up, missing
  potentials/pseudopotentials, memory exhaustion, process crash/segfault,
  corrupted output, incomplete runs) and proposes a SAFE one-change-at-a-time
  RETRY LADDER with explicit STOP CONDITIONS, prioritizing evidence
  preservation. Use as the immediate first response to a failed or suspicious
  run. For deep per-stage validation, conservation/physical-bounds checks, and
  "can I trust these results" analysis, defer to the simulation-validator skill.
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

# Simulation Failure Triage

## Goal

Classify common simulation failure signatures and return immediate actions, retry ladders, and stop conditions.

## Requirements

- Python 3.10+
- No external dependencies
- Works on Linux, macOS, and Windows

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Code | Simulation code | `LAMMPS`, `VASP`, `MOOSE`, `QE` |
| Stage | Setup, runtime, postprocess | `runtime` |
| Symptoms | Failure signs | `nan,pressure-blowup` |
| Log text or file | Error evidence | `Lost atoms`, `ZBRENT` |
| Recent change | Last modified setting | `larger timestep` |

## Decision Guidance

- First preserve evidence: logs, inputs, executable version, and scheduler output.
- Separate setup errors from numerical instability and physical model issues.
- Retry with a single controlled change.
- Stop retrying when the result becomes scientifically meaningless or a required model input is missing.

## Script Outputs

`scripts/failure_triage.py` emits:

- `likely_causes`
- `immediate_actions`
- `retry_ladder`
- `stop_conditions`
- `evidence`

## Workflow

```bash
python3 skills/robustness/simulation-failure-triage/scripts/failure_triage.py \
  --code LAMMPS \
  --stage runtime \
  --symptoms nan,pressure-blowup \
  --recent-change "increased timestep" \
  --json
```

## Error Handling

Invalid stages or oversized log files stop with exit code 2. Unknown symptoms are retained as custom evidence.

## Limitations

This skill gives first-response triage. It does not guarantee that a failed simulation can be repaired.

## Security

- Log files are read with a 10 MB size cap; oversized files exit with code 2.
- Log text is truncated to 10 MB and never executed.
- Symptoms are capped at 50 entries and 100 characters each; `code` is capped at 100 characters. Invalid input exits with code 2.
- The script does not run external solvers.
- The skill uses `Bash` only to run its bundled script.

## References

- See `references/failure_patterns.md` for common failure signatures and retry ladders.

## Version History

- 1.1.1: Strengthen evals to be discriminating — each case now pins the exact `failure_triage.py` JSON output via `script_checks` (specific `category`/`first_action` strings, log-hint symptom inference, fixed retry-ladder/stop-condition text, recent-change immediate action), so the suite measures the skill's actual output rather than generic triage knowledge.
- 1.1.0: Add dedicated `out-of-memory` and `crash` (segfault) classifications; segfaults and OOM are no longer mislabeled as I/O or interrupted-execution. Preserve original-case log excerpt. Add input-validation caps (symptoms, code length). Sharpen description to defer deep validation to simulation-validator. Fix `missing-potential` eval token.
- 1.0.0: Initial cross-code simulation failure triage skill.
