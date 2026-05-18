---
name: benchmark-and-mms-planner
description: >
  Plan verification and validation campaigns for simulation codes using
  manufactured solutions, canonical benchmark problems, grid/time refinement,
  uncertainty propagation, and pass/fail acceptance criteria. Use when an
  agent needs to prove a solver, model, or result is trustworthy rather than
  only plausible.
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

# Benchmark And MMS Planner

## Goal

Design a verification and validation plan before trusting simulation results. The skill helps agents choose manufactured solutions, benchmark cases, refinement protocols, uncertainty checks, and pass/fail criteria.

## Requirements

- Python 3.10+
- No external dependencies
- Works on Linux, macOS, and Windows

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| PDE or model class | Governing family | `diffusion`, `elasticity`, `phase-field` |
| Quantity of interest | Metric to validate | `interface velocity`, `L2 temperature error` |
| Dimension | 1, 2, or 3 | `2` |
| Expected order | Formal discretization order | `2` |
| Reference availability | Analytic, benchmark, or none | `analytic` |
| Risk level | Cost or consequence of wrong result | `high` |

## Decision Guidance

- Use **MMS** when code correctness is uncertain and an analytic solution can be injected.
- Use **canonical benchmarks** when physical model validation matters more than code verification.
- Use **grid/time refinement** whenever the result is used for a claim, design decision, or comparison.
- Use **uncertainty propagation** when inputs are calibrated, noisy, or experimentally measured.

## Script Outputs

`scripts/benchmark_mms_planner.py` emits `inputs` and `results` with:

- `verification_strategy`
- `mms_plan`
- `benchmark_cases`
- `refinement_protocol`
- `acceptance_criteria`
- `warnings`

## Workflow

1. Collect the governing model, quantity of interest, and risk level.
2. Run `benchmark_mms_planner.py --json`.
3. Treat warnings as blockers for high-risk claims.
4. Convert the returned protocol into tests, simulation runs, or review checklist items.

```bash
python3 skills/verification-validation/benchmark-and-mms-planner/scripts/benchmark_mms_planner.py \
  --model diffusion \
  --quantity "L2 error in temperature" \
  --dimension 2 \
  --expected-order 2 \
  --reference analytic \
  --risk high \
  --json
```

## Error Handling

- If the dimension or expected order is invalid, stop and correct the model description.
- If no reference exists, use conservation and convergence checks but do not call the result validated.

## Limitations

This skill plans verification work; it does not run the solver or prove that a physical model is appropriate for an experiment.

## Security

- Inputs are scalar strings and finite numeric values only.
- The script does not execute external solvers.
- File writes are not performed.
- The skill uses `Bash` only to run its bundled script.

## References

- See `references/vv_patterns.md` for MMS, benchmark, and uncertainty planning notes.

## Version History

- 1.0.0: Initial benchmark and MMS planning skill.
