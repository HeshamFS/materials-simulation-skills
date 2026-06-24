---
name: nonlinear-solvers
description: >
  Select and configure nonlinear solvers for root-finding f(x)=0, optimization
  min F(x), and least-squares problems — choose among Newton, Newton-Krylov,
  quasi-Newton (BFGS, L-BFGS), Broyden, Anderson acceleration, and
  Levenberg-Marquardt methods, configure line search or trust-region
  globalization, diagnose convergence rate (quadratic, linear, stagnated),
  and assess Jacobian quality and conditioning. Use when a Newton solver
  converges slowly or diverges, choosing between line search and trust region,
  debugging nonlinear iteration failures in FEM or phase-field codes, or
  selecting a solver for large-scale unconstrained optimization, even if
  the user only says "my Newton iterations aren't converging."
allowed-tools: Read, Bash, Write, Grep, Glob
metadata:
  author: HeshamFS
  version: "1.2.1"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
  last_evaluated: "2026-06-24"
  eval_cases: 5
  last_reviewed: "2026-06-23"
---

# Nonlinear Solvers

## Goal

Provide a universal workflow to select a nonlinear solver, configure globalization strategies, and diagnose convergence for root-finding, optimization, and least-squares problems.

## Requirements

- Python 3.10+
- NumPy (for Jacobian diagnostics)
- SciPy (optional, for advanced analysis)

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Problem type | Root-finding, optimization, least-squares | `root-finding` |
| Problem size | Number of unknowns | `n = 10000` |
| Jacobian availability | Analytic, finite-diff, unavailable | `analytic` |
| Jacobian cost | Cheap or expensive to compute | `expensive` |
| Constraints | None, bounds, equality, inequality | `none` |
| Smoothness | Is objective/residual smooth? | `yes` |
| Residual history | Sequence of residual norms | `1,0.1,0.01,...` |

## Decision Guidance

### Solver Selection Flowchart

```
Is Jacobian available and cheap?
├── YES → Problem size?
│   ├── Small (n < 1000) → Newton (full)
│   └── Large (n ≥ 1000) → Newton-Krylov
└── NO → Is objective smooth?
    ├── YES → Memory limited?
    │   ├── YES → L-BFGS or Broyden
    │   └── NO → BFGS
    └── NO → Anderson acceleration or Picard
```

### Quick Reference

| Problem Type | First Choice | Alternative | Globalization |
|--------------|--------------|-------------|---------------|
| Small root-finding | Newton | Broyden | Line search |
| Large root-finding | Newton-Krylov | Anderson | Trust region |
| Optimization | L-BFGS | BFGS | Wolfe line search |
| Least-squares | Levenberg-Marquardt | Gauss-Newton | Trust region |
| Bound constrained | L-BFGS-B | Trust-region reflective | Projected |

## Script Outputs (JSON Fields)

| Script | Key Outputs |
|--------|-------------|
| `scripts/solver_selector.py` | `recommended`, `alternatives`, `notes` |
| `scripts/convergence_analyzer.py` | `converged`, `convergence_type`, `estimated_rate`, `diagnosis` |
| `scripts/jacobian_diagnostics.py` | `condition_number`, `jacobian_quality`, `rank_deficient` |
| `scripts/globalization_advisor.py` | `strategy`, `line_search_type`, `trust_region_type`, `parameters` |
| `scripts/residual_monitor.py` | `patterns_detected`, `alerts`, `recommendations` |
| `scripts/step_quality.py` | `ratio`, `step_quality`, `accept_step`, `trust_radius_action` |

## Workflow

1. **Characterize problem** - Identify type, size, Jacobian availability
2. **Select solver** - Run `scripts/solver_selector.py`
3. **Choose globalization** - Run `scripts/globalization_advisor.py`
4. **Analyze Jacobian** - If available, run `scripts/jacobian_diagnostics.py`
5. **Monitor residuals** - During solve, use `scripts/residual_monitor.py`
6. **Analyze convergence** - Run `scripts/convergence_analyzer.py`
7. **Evaluate steps** - For trust region, use `scripts/step_quality.py`

## Conversational Workflow Example

**User**: My Newton solver for a phase-field simulation is converging very slowly. After 50 iterations, the residual only dropped from 1 to 0.1.

**Agent workflow**:
1. Analyze convergence:
   ```bash
   python3 scripts/convergence_analyzer.py --residuals 1,0.8,0.6,0.5,0.4,0.3,0.2,0.15,0.12,0.1 --json
   ```
2. Check globalization strategy:
   ```bash
   python3 scripts/globalization_advisor.py --problem-type root-finding --jacobian-quality ill-conditioned --previous-failures 0 --json
   ```
3. Recommend: Switch to trust region with Levenberg-Marquardt regularization, or use Newton-Krylov with better preconditioning.

## Pre-Solve Checklist

- [ ] Confirm problem type (root-finding, optimization, least-squares)
- [ ] Assess Jacobian availability and cost
- [ ] Check initial guess quality
- [ ] Set appropriate tolerances
- [ ] Choose globalization strategy
- [ ] Prepare to monitor convergence

## CLI Examples

```bash
# Select solver for large unconstrained optimization
python3 scripts/solver_selector.py --size 50000 --smooth --memory-limited --json

# Select solver for a small nonlinear least-squares (data-fitting) problem
python3 scripts/solver_selector.py --problem-type least-squares --size 6 --jacobian-available --smooth --json

# Analyze convergence from residual history
python3 scripts/convergence_analyzer.py --residuals 1,0.1,0.01,0.001,0.0001 --tolerance 1e-6 --json

# Diagnose Jacobian quality
python3 scripts/jacobian_diagnostics.py --matrix jacobian.txt --json

# Get globalization recommendation
python3 scripts/globalization_advisor.py --problem-type optimization --jacobian-quality good --json

# Globalization for a distant initial guess (favors trust region)
python3 scripts/globalization_advisor.py --problem-type root-finding --jacobian-quality good --far-from-solution --json

# Monitor residual patterns
python3 scripts/residual_monitor.py --residuals 1,0.8,0.9,0.7,0.75,0.6 --target-tolerance 1e-8 --json

# Evaluate step quality for trust region
python3 scripts/step_quality.py --predicted-reduction 0.5 --actual-reduction 0.4 --step-norm 0.8 --gradient-norm 1.0 --trust-radius 1.0 --json
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `problem_size must be positive` | Invalid size | Check problem dimension |
| `problem_size (...) exceeds maximum (...)` | Size above 10 billion cap | Re-check the unit/value |
| `constraint_type must be one of...` | Unknown constraint | Use: none, bound, equality, inequality |
| `problem_type must be one of...` | Unknown problem type | Use: root-finding, optimization, least-squares |
| `residuals must be non-negative` | Invalid residual data | Check residual computation |
| `residuals must be finite` | NaN/Inf in residual data | Sanitize residual history |
| `residual list length (...) exceeds limit (...)` | More than 100,000 entries | Downsample the history |
| `Matrix file not found` | Invalid path | Verify Jacobian file exists |
| `Matrix file exceeds size limit ...` | Matrix file too large | Use a smaller / sparser matrix |

## Interpretation Guidance

### Convergence Type

| Type | Meaning | Action |
|------|---------|--------|
| quadratic | Optimal Newton (order p ≈ 2) | Continue, near solution |
| superlinear | Ratios shrinking toward 0 (1 < p < 2); quasi-Newton working | Monitor for stagnation |
| linear | Constant contraction ratio (p ≈ 1); a small constant ratio is fast-linear, not superlinear | May improve with preconditioner |
| sublinear | Too slow (ratio → 1) | Change method or formulation |
| stagnated | No progress | Check Jacobian, preconditioner |
| diverged | Increasing residual | Add globalization, check Jacobian |

### Jacobian Quality

| Quality | Condition Number | Action |
|---------|------------------|--------|
| good | < 10⁶ | Standard Newton works |
| moderately-conditioned | 10⁶ - 10¹⁰ | Consider scaling |
| ill-conditioned | > 10¹⁰ | Use regularization |
| near-singular | ∞ | Reformulate or use LM |

### Step Quality (Trust Region)

| Ratio ρ | Quality | Trust Radius |
|---------|---------|--------------|
| ρ < 0 | very_poor | Shrink aggressively |
| ρ < 0.25 | marginal | Shrink |
| 0.25 ≤ ρ < 0.75 | good | Maintain |
| ρ ≥ 0.75 | excellent | Expand if at boundary |

## Security

### Input Validation
- `--size` (problem size) is validated as a positive integer, bounded at 10 billion
- `--residuals` are validated as finite non-negative numbers, capped at 100,000 entries
- `--tolerance` and `--target-tolerance` are validated as finite positive numbers
- `--problem-type` and `--constraint-type` are validated against fixed allowlists
- `--jacobian-quality` is validated against a fixed allowlist (`good`, `ill-conditioned`, etc.)
- Step quality parameters (`predicted-reduction`, `actual-reduction`, `step-norm`, `gradient-norm`, `trust-radius`) are validated as finite numbers

### File Access
- `jacobian_diagnostics.py` reads a single matrix file specified by `--matrix`; no directory traversal beyond the given path
- Matrix files are size-limited and loaded with `allow_pickle=False` to prevent code execution
- All other scripts read no external files; inputs are provided via CLI arguments
- Scripts write only to stdout (JSON output)

### Tool Restrictions
- **Read**: Used to inspect script source, references, and user configuration files
- **Bash**: Used to execute the six Python analysis scripts (`solver_selector.py`, `convergence_analyzer.py`, `jacobian_diagnostics.py`, `globalization_advisor.py`, `residual_monitor.py`, `step_quality.py`) with explicit argument lists
- **Write**: Used to save analysis results or solver recommendations; writes are scoped to the user's working directory
- **Grep/Glob**: Used to locate relevant files and search references

### Safety Measures
- No `eval()`, `exec()`, or dynamic code generation
- All subprocess calls use explicit argument lists (no `shell=True`)
- Matrix dimension limits prevent memory exhaustion when loading Jacobian files
- Residual history analysis operates on bounded-length numeric arrays only

## Limitations

- **No global convergence guarantee**: All methods may fail for pathological problems
- **Jacobian accuracy**: Finite-difference Jacobian may be inaccurate near discontinuities
- **Large dense problems**: May require specialized solvers not covered here
- **Constrained optimization**: Complex constraints need SQP or interior point methods

## References

- `references/solver_decision_tree.md` - Problem-based solver selection
- `references/method_catalog.md` - Method details and parameters
- `references/convergence_diagnostics.md` - Diagnosing convergence issues
- `references/globalization_strategies.md` - Line search and trust region

## Version History

- **v1.2.0** (2026-06-23): Added `--problem-type` to `solver_selector.py` with a nonlinear least-squares path (Levenberg-Marquardt / Gauss-Newton); reordered solver selection so problem size dominates high-accuracy and routes large/expensive-Jacobian problems to Newton-Krylov; added `--far-from-solution` to `globalization_advisor.py` and surfaced Levenberg-Marquardt as the trust-region type for least-squares; corrected convergence classification so constant-ratio sequences are linear (not superlinear); RFC-8259-safe JSON (no `-Infinity`); input-validation hardening
- **v1.1.0** (2026-03-26): Optimized agent-discovery description, evaluation suite, security review docs, standardized metadata block, CHANGELOG
- **v1.0.0**: Initial release with 6 analysis scripts
