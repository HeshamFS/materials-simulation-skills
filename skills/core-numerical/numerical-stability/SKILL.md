---
name: numerical-stability
description: >
  Analyze numerical stability for time-dependent PDE simulations — check CFL
  and Fourier criteria, perform von Neumann stability analysis, detect stiffness,
  evaluate matrix conditioning, and recommend explicit vs implicit time-stepping
  schemes. Use when selecting time steps, diagnosing numerical blow-up or solver
  divergence, checking convergence criteria, or evaluating scheme stability for
  advection, diffusion, or reaction problems, even if the user doesn't explicitly
  mention "stability" or "CFL."
allowed-tools: Read, Bash, Write, Grep, Glob
metadata:
  author: HeshamFS
  version: "1.2.1"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
  last_evaluated: "2026-06-24"
  eval_cases: 4
  last_reviewed: "2026-06-23"
---

# Numerical Stability

## Goal

Provide a repeatable checklist and script-driven checks to keep time-dependent simulations stable and defensible.

## Requirements

- Python 3.10+
- NumPy (for matrix_condition.py and von_neumann_analyzer.py)
- See `scripts/requirements.txt` for dependencies

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Grid spacing `dx` | Spatial discretization | `0.01 m` |
| Time step `dt` | Temporal discretization | `1e-4 s` |
| Velocity `v` | Advection speed | `1.0 m/s` |
| Diffusivity `D` | Thermal/mass diffusivity | `1e-5 m²/s` |
| Reaction rate `k` | First-order rate constant | `100 s⁻¹` |
| Dimensions | 1D, 2D, or 3D | `2` |
| Scheme type | Explicit or implicit | `explicit` |

## Decision Guidance

### Choosing Explicit vs Implicit

```
Is the problem stiff (fast + slow dynamics)?
├── YES → Use implicit or IMEX scheme
│         └── Check conditioning with matrix_condition.py
└── NO → Is CFL/Fourier satisfied with reasonable dt?
    ├── YES → Use explicit scheme (cheaper per step)
    └── NO → Consider implicit or reduce dx
```

### Stability Limit Quick Reference

| Physics | Number | Explicit Limit (1D) | Formula |
|---------|--------|---------------------|---------|
| Advection | CFL | C ≤ 1 | `C = v·dt/dx` |
| Diffusion | Fourier | Fo ≤ 0.5 | `Fo = D·dt/dx²` |
| Reaction | Reaction | R ≤ 1 | `R = k·dt` |

**Multi-dimensional correction**: For d dimensions, diffusion limit is `Fo ≤ 1/(2d)`.

## Script Outputs (JSON Fields)

| Script | Key Outputs |
|--------|-------------|
| `scripts/cfl_checker.py` | `metrics.cfl`, `metrics.fourier`, `recommended_dt`, `stable` |
| `scripts/von_neumann_analyzer.py` | `results.max_amplification`, `results.stable` |
| `scripts/matrix_condition.py` | `results.condition_number`, `results.is_symmetric` |
| `scripts/stiffness_detector.py` | `results.stiffness_ratio`, `results.real_part_stiffness_ratio`, `results.imag_dominated`, `results.stiff`, `results.recommendation`, `results.warning` |

## Workflow

1. **Identify dominant physics** (advection vs diffusion vs reaction)
2. **Run CFL checker** with `scripts/cfl_checker.py`
3. **Compare to limits** and adjust `dt` if needed
4. **Check stiffness** with `scripts/stiffness_detector.py` if multiple scales
5. **Analyze custom schemes** with `scripts/von_neumann_analyzer.py`
6. **Check conditioning** with `scripts/matrix_condition.py` for implicit solves
7. **Document** the stability verdict and recommended time step

## Conversational Workflow Example

**User**: My phase-field simulation is blowing up after 100 steps. I'm using explicit Euler with dx=0.01, dt=1e-4, and diffusivity D=1.0.

**Agent workflow**:
1. Check stability criteria:
   ```bash
   python3 scripts/cfl_checker.py --dx 0.01 --dt 1e-4 --diffusivity 1.0 --dimensions 2 --json
   ```
2. Interpret results:
   - Fourier number: `Fo = 1.0 × 1e-4 / (0.01)² = 1.0`
   - 2D limit: `Fo ≤ 0.25`
   - **Violation**: Fo = 1.0 > 0.25, unstable!
3. Recommend fix:
   - Reduce dt to `2.5e-5` (the tool's `recommended_dt`, giving Fo = 0.25)
   - Or increase dx, or switch to implicit

## Pre-Simulation Stability Checklist

- [ ] Identify dominant physics and nondimensional groups
- [ ] Compute CFL/Fourier/Reaction numbers with `cfl_checker.py`
- [ ] If explicit and limit violated, reduce `dt` or change scheme
- [ ] If stiffness ratio > 1000, select implicit/stiff integrator
- [ ] For custom schemes, verify amplification factor ≤ 1
- [ ] Document stability reasoning with inputs and outputs

## CLI Examples

```bash
# Check CFL/Fourier for 2D diffusion-advection
python3 scripts/cfl_checker.py --dx 0.1 --dt 0.01 --velocity 1.0 --diffusivity 0.1 --dimensions 2 --json

# Von Neumann analysis for custom 3-point stencil
python3 scripts/von_neumann_analyzer.py --coeffs 0.2,0.6,0.2 --dx 1.0 --nk 128 --json

# Detect stiffness from eigenvalue estimates
python3 scripts/stiffness_detector.py --eigs=-1,-1000 --json

# Check matrix conditioning for implicit system
python3 scripts/matrix_condition.py --matrix A.npy --norm 2 --json
```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `dx and dt must be positive` | Zero or negative values | Provide valid positive numbers |
| `No stability criteria applied` | Missing velocity/diffusivity | Provide at least one physics parameter |
| `Matrix not found: <path>` | Invalid path | Check matrix file exists |
| `Could not compute eigenvalues` | Singular or ill-formed matrix | Check matrix validity |

## Interpretation Guidance

| Scenario | Meaning | Action |
|----------|---------|--------|
| `stable: true` | All checked criteria satisfied | Proceed with simulation |
| `stable: false` | At least one limit violated | Reduce dt or change scheme |
| `stable: null` | No criteria could be applied | Provide more physics inputs |
| Stiffness ratio > 1000 | Problem is stiff | Use implicit integrator |
| Condition number > 10⁸ | Poorly-conditioned (`status: poorly-conditioned`) | Preconditioning likely needed |
| Condition number > 10¹⁰ | Ill-conditioned (`status: ill-conditioned`) | Use scaling/preconditioning |

> Conditioning thresholds assume IEEE double precision: solving loses roughly `log10(κ)` significant digits, and a matrix becomes numerically singular near `κ ≈ 1/eps ≈ 4.5e15`. The `> 10⁸` / `> 10¹⁰` cutoffs (matching `matrix_condition.py` `status`) leave ample margin; well-conditioned-for-double FEM matrices (κ up to ~10⁶–10⁷) report `status: ok`.

## Security

### Input Validation
- `dx`, `dt`, and `safety` are validated as finite positive numbers before any computation; `velocity`, `diffusivity`, and `reaction_rate`, when supplied, are validated as finite
- `--dimensions` is restricted to `{1, 2, 3}` (cfl_checker.py raises and exits 2 otherwise)
- Comma-separated eigenvalue lists (`--eigs`) are capped at 10,000 entries and validated as finite numbers
- Stencil coefficient lists (`--coeffs`) are capped at 10,000 entries and validated as finite floats

### File Access
- `matrix_condition.py` reads a single matrix file (`.npy` or text) specified by `--matrix`; no directory traversal beyond the given path
- Matrix/Jacobian files are rejected if they exceed 500 MB before parsing (matrix_condition.py, stiffness_detector.py)
- `np.load()` is called with `allow_pickle=False` to prevent arbitrary code execution via crafted `.npy` files (matrix_condition.py, stiffness_detector.py)
- Scripts write only to stdout (JSON output); no files are created unless the agent explicitly uses the Write tool

### Tool Restrictions
- **Read**: Used to inspect script source, references, and user configuration files
- **Bash**: Used to execute the four Python analysis scripts (`cfl_checker.py`, `von_neumann_analyzer.py`, `matrix_condition.py`, `stiffness_detector.py`) with explicit argument lists
- **Write**: Used to save analysis results or generated reports; writes are scoped to the user's working directory
- **Grep/Glob**: Used to locate relevant files and search references

### Safety Measures
- No `eval()`, `exec()`, or dynamic code generation
- All subprocess calls use explicit argument lists (no `shell=True`)
- Matrix dimension limit (100,000 per side) in matrix_condition.py prevents memory exhaustion
- JSON output mode (`--json`) produces structured, parseable results without shell-interpretable content

## Limitations

- **Explicit schemes only** for CFL/Fourier checks (implicit is unconditionally stable)
- **Von Neumann analysis** assumes linear, constant-coefficient, periodic BCs
- **Stiffness detection** requires eigenvalue estimates from user. The `stiff` verdict is based on scale separation among genuinely decaying modes (`Re(λ) < 0`); the magnitude ratio is still reported as `stiffness_ratio`. Imaginary-axis-dominated spectra (oscillatory/advection/Hamiltonian) are flagged via `imag_dominated` and a `warning`, and are NOT classified as stiff — for those, prefer symplectic/leapfrog or an A-stable scheme sized by the CFL limit, not BDF/Radau.

## References

- `references/stability_criteria.md` - Decision thresholds and formulas
- `references/common_pitfalls.md` - Frequent failure modes and fixes
- `references/scheme_catalog.md` - Stability properties of common schemes

## Version History

- **v1.2.0** (2026-06-23): Corrected the phase-field worked example (genuinely unstable Fo=1.0 with D=1.0); fixed eval case 1 Fourier value; reconciled conditioning thresholds and error-message docs with the scripts; real-part-based stiffness classification with imaginary-dominated detection; enforced documented input/file-size/dimension safeguards
- **v1.1.0** (2024-12-24): Enhanced documentation, decision guidance, examples
- **v1.0.0**: Initial release with 4 stability analysis scripts
