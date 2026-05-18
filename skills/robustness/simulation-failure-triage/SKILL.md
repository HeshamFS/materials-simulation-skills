---
name: simulation-failure-triage
description: >
  Triage cross-code simulation failures and propose safe retry ladders for
  nonconvergence, NaN/Inf, exploding energies, unstable timesteps, pressure
  blow-up, missing potentials, bad pseudopotentials, corrupted output, and
  incomplete runs. Use when an agent sees a failed or suspicious materials
  simulation and needs a defensible first response.
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

- Log files are read with a 10 MB size cap.
- Log text is truncated and never executed.
- The script does not run external solvers.
- The skill uses `Bash` only to run its bundled script.

## References

- See `references/failure_patterns.md` for common failure signatures and retry ladders.

## Version History

- 1.0.0: Initial cross-code simulation failure triage skill.
