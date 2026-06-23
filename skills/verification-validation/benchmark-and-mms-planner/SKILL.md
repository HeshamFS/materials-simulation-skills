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
  version: "1.1.1"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
  last_evaluated: "2026-06-23"
  eval_cases: 3
  last_reviewed: "2026-06-23"
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
- `effective_model` — the resolved model family actually used; unknown families fall back to `general`.
- `mms_plan`
- `benchmark_cases`
- `refinement_protocol` (`dimension`, `levels`, `spacing_ratio`, `expected_order`, `accept_observed_order_min`, `include_time_refinement`)
- `uncertainty_plan` (`propagate_inputs`, `report_error_bars`, `separate_discretization_and_model_error`) — propagation/error-bar guidance driven by risk level and reference type.
- `acceptance_criteria`
- `warnings`

The `accept_observed_order_min` is an **engineering screening heuristic**, not a certified bound: it is the formal `expected_order` reduced by a fractional tolerance (10% for high risk, 20% otherwise) and floored at first-order convergence (`1.0`). The relative band keeps strictness consistent across formal orders. See `references/vv_patterns.md`.

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
- String inputs (`model`, `quantity`) are capped at 256 characters; oversized inputs are rejected with exit code 2.
- `dimension` must be 1, 2, or 3; `expected_order` must be a positive, finite number; `risk` and `reference` must be drawn from their fixed allowlists. Invalid input exits with code 2.
- The script does not execute external solvers, import pickled data, or read input files.
- File writes are not performed.
- The skill uses `Bash` only to run its bundled script.

## References

- See `references/vv_patterns.md` for MMS, benchmark, and uncertainty planning notes.

## Version History

- 1.1.1: Make the eval suite discriminating by adding deterministic `script_checks`
  that pin the planner's specific output (resolved `verification_strategy`, the
  relative `accept_observed_order_min` band, refinement `levels`,
  `include_time_refinement`, `uncertainty_plan` flags, model-specific benchmark
  cases, and the exact warning strings) for each of the three cases.
- 1.1.0: Resolve unknown model families to `general` once so benchmark selection and the
  time-refinement decision agree (transient unlisted PDEs no longer skip time refinement);
  echo the resolved family as `effective_model`. Replace the fixed absolute observed-order
  offset with a relative tolerance floored at first order. Document `uncertainty_plan`,
  `effective_model`, and the acceptance heuristic. Add 256-character caps on string inputs.
- 1.0.0: Initial benchmark and MMS planning skill.
