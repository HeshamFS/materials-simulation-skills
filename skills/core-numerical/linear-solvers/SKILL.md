---
name: linear-solvers
description: >
  Select and configure linear solvers for Ax=b systems arising in numerical
  simulations — choose between direct (LU, Cholesky) and iterative (CG, GMRES,
  BiCGSTAB, MINRES) methods, analyze sparsity patterns and matrix conditioning,
  recommend preconditioners (AMG, ILU, IC), apply row/column scaling, and
  diagnose convergence stagnation from residual histories. Use when setting up
  a linear solve for FEM/FVM assembly, debugging slow or stalled Krylov
  iterations, choosing a preconditioner for SPD or nonsymmetric systems, or
  investigating ill-conditioning, even if the user only says "my solver is
  slow" or "GMRES won't converge."
allowed-tools: Read, Write, Grep, Glob
metadata:
  author: HeshamFS
  version: "1.1.0"
  security_tier: medium
  security_reviewed: true
  tested_with:
    - claude-code
    - gemini-cli
    - vs-code-copilot
  eval_cases: 4
  last_reviewed: "2026-03-26"
---

# Linear Solvers

## Goal

Provide a universal workflow to select a solver, assess conditioning, and diagnose convergence for linear systems arising in numerical simulations.

## Requirements

- Python 3.10+
- NumPy, SciPy (for matrix operations)
- See individual scripts for dependencies

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Matrix size | Dimension of system | `n = 1000000` |
| Sparsity | Fraction of nonzeros | `0.01%` |
| Symmetry | Is A = Aᵀ? | `yes` |
| Definiteness | Is A positive definite? | `yes (SPD)` |
| Conditioning | Estimated condition number | `10⁶` |

## Decision Guidance

### Solver Selection Flowchart

```
Is matrix small (n < 5000) and dense?
├── YES → Use direct solver (LU, Cholesky)
└── NO → Is matrix symmetric?
    ├── YES → Is it positive definite?
    │   ├── YES → Use CG with AMG/IC preconditioner
    │   └── NO → Use MINRES
    └── NO → Is it nearly symmetric?
        ├── YES → Use BiCGSTAB
        └── NO → Use GMRES with ILU/AMG
```

### Quick Reference

| Matrix Type | Solver | Preconditioner |
|-------------|--------|----------------|
| SPD, sparse | CG | AMG, IC |
| Symmetric indefinite | MINRES | ILU |
| Nonsymmetric | GMRES, BiCGSTAB | ILU, AMG |
| Dense | LU, Cholesky | None |
| Saddle point | Schur complement, Uzawa | Block preconditioner |

## Script Outputs (JSON Fields)

| Script | Key Outputs |
|--------|-------------|
| `scripts/solver_selector.py` | `recommended`, `alternatives`, `notes` |
| `scripts/convergence_diagnostics.py` | `rate`, `stagnation`, `recommended_action` |
| `scripts/sparsity_stats.py` | `nnz`, `density`, `bandwidth`, `symmetry` |
| `scripts/preconditioner_advisor.py` | `suggested`, `notes` |
| `scripts/scaling_equilibration.py` | `row_scale`, `col_scale`, `notes` |
| `scripts/residual_norms.py` | `residual_norms`, `relative_norms`, `converged` |

## Workflow

1. **Characterize matrix** - symmetry, definiteness, sparsity
2. **Analyze sparsity** - Run `scripts/sparsity_stats.py`
3. **Select solver** - Run `scripts/solver_selector.py`
4. **Choose preconditioner** - Run `scripts/preconditioner_advisor.py`
5. **Apply scaling** - If ill-conditioned, use `scripts/scaling_equilibration.py`
6. **Monitor convergence** - Use `scripts/convergence_diagnostics.py`
7. **Diagnose issues** - Check residual history with `scripts/residual_norms.py`

## Conversational Workflow Example

**User**: My GMRES solver is stagnating after 50 iterations. The residual drops to 1e-3 then stops improving.

**Agent workflow**:
1. Diagnose convergence:
   ```bash
   python3 scripts/convergence_diagnostics.py --residuals 1,0.1,0.01,0.005,0.003,0.002,0.002,0.002 --json
   ```
2. Check for preconditioning advice:
   ```bash
   python3 scripts/preconditioner_advisor.py --matrix-type nonsymmetric --sparse --stagnation --json
   ```
3. Recommend: Increase restart parameter, try ILU(k) with higher k, or switch to AMG.

## Pre-Solve Checklist

- [ ] Confirm matrix symmetry/definiteness
- [ ] Decide direct vs iterative based on size and sparsity
- [ ] Set residual tolerance relative to physics scale
- [ ] Choose preconditioner appropriate to matrix structure
- [ ] Apply scaling/equilibration if needed
- [ ] Track convergence and adjust if stagnation occurs

## CLI Examples

```bash
# Analyze sparsity pattern
python3 scripts/sparsity_stats.py --matrix A.npy --json

# Select solver for SPD sparse system
python3 scripts/solver_selector.py --symmetric --positive-definite --sparse --size 1000000 --json

# Get preconditioner recommendation
python3 scripts/preconditioner_advisor.py --matrix-type spd --sparse --json

# Diagnose convergence from residual history
python3 scripts/convergence_diagnostics.py --residuals 1,0.2,0.05,0.01 --json

# Apply scaling
python3 scripts/scaling_equilibration.py --matrix A.npy --symmetric --json

# Compute residual norms
python3 scripts/residual_norms.py --residual 1,0.1,0.01 --rhs 1,0,0 --json
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `Matrix file not found` | Invalid path | Check file exists |
| `Matrix must be square` | Non-square input | Verify matrix dimensions |
| `Residuals must be positive` | Invalid residual data | Check input format |

## Interpretation Guidance

### Convergence Rate

| Rate | Meaning | Action |
|------|---------|--------|
| < 0.1 | Excellent | Current setup optimal |
| 0.1 - 0.5 | Good | Acceptable for most problems |
| 0.5 - 0.9 | Slow | Consider better preconditioner |
| > 0.9 | Stagnation | Change solver or preconditioner |

### Stagnation Diagnosis

| Pattern | Likely Cause | Fix |
|---------|--------------|-----|
| Flat residual | Poor preconditioner | Improve preconditioner |
| Oscillating | Near-singular or indefinite | Check matrix, try different solver |
| Very slow decay | Ill-conditioned | Apply scaling, use AMG |

## Security

### Input Validation
- All numeric inputs (residuals, tolerances, matrix entries) are validated as finite numbers
- Comma-separated residual/vector inputs are capped at 100,000 entries
- The `solver_selector.py` `--size` parameter is bounded at 10 billion
- `--matrix-type` is validated against a fixed allowlist (`spd`, `symmetric`, `nonsymmetric`)
- Boolean flags (`--symmetric`, `--positive-definite`, `--sparse`, `--stagnation`) are type-safe argparse flags

### File Access
- `sparsity_stats.py` and `scaling_equilibration.py` read a single matrix file (`.npy` format) specified by `--matrix`
- `np.load()` is called with `allow_pickle=False` to prevent arbitrary code execution via crafted `.npy` files
- Matrix files are rejected if they exceed 500 MB before any parsing occurs
- Matrix dimension limits (100,000 per dimension) prevent memory exhaustion
- All other scripts read no external files; inputs are provided via CLI arguments

### Tool Restrictions
- **Read**: Used to inspect script source, references, and matrix files
- **Write**: Used to save analysis results or solver recommendations; writes are scoped to the user's working directory
- **Grep/Glob**: Used to locate relevant files and search references
- The skill's `allowed-tools` excludes `Bash` to prevent the agent from executing arbitrary commands when processing untrusted matrix files or numeric inputs

### Safety Measures
- No `eval()`, `exec()`, or dynamic code generation
- All subprocess calls use explicit argument lists (no `shell=True`)
- Reduced tool surface (no Bash) limits the agent to read/write operations only
- JSON output mode produces structured, parseable results without shell-interpretable content

## Limitations

- **Large dense matrices**: Direct solvers may run out of memory
- **Highly indefinite**: Standard preconditioners may fail
- **Saddle-point**: Requires specialized block preconditioners

## References

- `references/solver_decision_tree.md` - Selection logic
- `references/preconditioner_catalog.md` - Preconditioner options
- `references/convergence_patterns.md` - Diagnosing failures
- `references/scaling_guidelines.md` - Equilibration guidance

## Version History

- **v1.1.0** (2024-12-24): Enhanced documentation, decision guidance, examples
- **v1.0.0**: Initial release with 6 solver analysis scripts
