# Examples

This directory contains runnable examples demonstrating the materials simulation skills. Each example shows real-world usage patterns for numerical methods, validation workflows, and parameter optimization in materials science simulations.

## Quick Start

Run any example from the repository root:

```bash
# Example: Check CFL stability for a phase-field simulation
bash examples/numerical-stability/run_cfl.sh

# Example: Validate simulation configuration before running
bash examples/simulation-validator/run_preflight.sh
```

## Directory Structure

| Directory | Description |
|-----------|-------------|
| `numerical-stability/` | CFL, von Neumann, matrix conditioning, stiffness detection |
| `numerical-integration/` | Error norms, adaptive stepping, integrator selection |
| `linear-solvers/` | Solver selection, preconditioning, convergence diagnostics |
| `time-stepping/` | Time step planning, output scheduling, checkpointing |
| `differentiation-schemes/` | Scheme selection, stencil generation, truncation error |
| `mesh-generation/` | Grid sizing, mesh quality metrics |
| `multiphase-field/` | Complex multi-physics scenario combining multiple skills |
| `multiphase-field-imex/` | IMEX splitting for stiff/non-stiff coupling |
| `simulation-validator/` | Pre-flight, runtime, post-flight validation |
| `parameter-optimization/` | DOE sampling, optimizer selection, sensitivity analysis |
| `simulation-orchestrator/` | Parameter sweeps, campaign management, result aggregation |
| `post-processing/` | Field extraction, time series analysis, statistics, derived quantities |

---

## Core Numerical Examples

### numerical-stability/

Demonstrates stability analysis tools for explicit time-stepping schemes.

```bash
# Check CFL, Fourier, and reaction stability numbers
bash examples/numerical-stability/run_cfl.sh

# Analyze amplification factor via von Neumann analysis
bash examples/numerical-stability/run_von_neumann.sh

# Check matrix conditioning for linear solves
bash examples/numerical-stability/run_matrix_condition.sh

# Detect stiffness from eigenvalue spectrum
bash examples/numerical-stability/run_stiffness.sh
```

**Use cases:**
- Pre-simulation stability validation
- Time step selection
- Detecting need for implicit methods

### numerical-integration/

Demonstrates time integration method selection and error control.

```bash
# Compute scaled error norms for adaptive stepping
bash examples/numerical-integration/run_error_norm.sh

# Configure adaptive step size controller
bash examples/numerical-integration/run_adaptive_step.sh

# Select integrator based on problem characteristics
bash examples/numerical-integration/run_selector.sh
```

**Use cases:**
- Choosing RK45 vs BDF vs IMEX
- Configuring adaptive tolerances
- Error estimation

### linear-solvers/

Demonstrates linear solver and preconditioner selection.

```bash
# Full solver selection with matrix analysis
bash examples/linear-solvers/run_full_preflight.sh

# Analyze converged solver behavior
bash examples/linear-solvers/run_full_preflight_converged.sh
```

**Use cases:**
- Selecting CG vs GMRES vs BiCGSTAB
- Choosing ILU vs AMG preconditioners
- Diagnosing convergence issues

### time-stepping/

Demonstrates time step management and output scheduling.

```bash
# Plan time step ramping (cold start to steady state)
bash examples/time-stepping/run_timestep_plan.sh

# Schedule output times (uniform, logarithmic, event-based)
bash examples/time-stepping/run_output_schedule.sh

# Optimize checkpoint intervals (Daly's formula)
bash examples/time-stepping/run_checkpoint_plan.sh
```

**Use cases:**
- Ramping dt from small initial values
- Balancing output frequency vs disk usage
- Minimizing time lost to failures

### differentiation-schemes/

Demonstrates finite difference scheme selection and analysis.

```bash
# Select scheme based on physics type
bash examples/differentiation-schemes/run_scheme_selector.sh

# Generate stencil coefficients
bash examples/differentiation-schemes/run_stencil_generator.sh

# Estimate truncation error
bash examples/differentiation-schemes/run_truncation_error.sh
```

**Use cases:**
- Choosing central vs upwind vs WENO
- Custom stencil generation
- Error analysis

### mesh-generation/

Demonstrates grid sizing and quality assessment.

```bash
# Compute grid spacing from feature sizes
bash examples/mesh-generation/run_grid_sizing.sh

# Evaluate mesh quality metrics
bash examples/mesh-generation/run_mesh_quality.sh
```

**Use cases:**
- Resolution planning for interfaces
- Mesh quality validation

---

## Complex Scenario Examples

### multiphase-field/

A realistic multi-phase-field simulation scenario combining stability checks, matrix analysis, and integration selection.

```bash
# Full pre-flight check for coupled phase-field simulation
bash examples/multiphase-field/run_full_preflight.sh

# Individual component checks
bash examples/multiphase-field/run_stability_precheck.sh
bash examples/multiphase-field/run_stability_adjusted.sh
bash examples/multiphase-field/run_integration_selector.sh
bash examples/multiphase-field/run_error_norm_multifield.sh
bash examples/multiphase-field/run_adaptive_step_reject.sh
bash examples/multiphase-field/run_matrix_condition_coupled.sh
```

**Scenario:**
- Multiple order parameters (phi_alpha, phi_beta, phi_gamma)
- Coupled Allen-Cahn + Cahn-Hilliard dynamics
- Anisotropic diffusion coefficients
- Multi-grid preconditioning

### multiphase-field-imex/

Demonstrates IMEX (Implicit-Explicit) splitting for stiff/non-stiff coupling.

```bash
# Plan IMEX splitting strategy
bash examples/multiphase-field-imex/run_imex_split.sh

# Estimate splitting error
bash examples/multiphase-field-imex/run_splitting_error.sh
```

**Use cases:**
- Stiff chemistry + non-stiff advection
- Implicit diffusion + explicit reaction
- Phase-field with fast interface kinetics

---

## Simulation Workflow Examples

### simulation-validator/

Demonstrates the three-stage validation protocol (pre-flight, runtime, post-flight).

```bash
# Stage 1: Pre-flight validation before simulation starts
bash examples/simulation-validator/run_preflight.sh

# Stage 2: Runtime monitoring during simulation
bash examples/simulation-validator/run_runtime_monitor.sh

# Stage 3: Post-flight result validation
bash examples/simulation-validator/run_result_validator.sh

# Diagnose failures from logs
bash examples/simulation-validator/run_failure_diagnoser.sh
```

**Data files:**
- `simulation_config.json` - Example simulation configuration
- `simulation_metrics.json` - Example runtime metrics
- `simulation.log` - Example log file with issues

**Use cases:**
- Preventing simulation failures
- Monitoring convergence
- Validating conservation laws
- Root cause analysis

### parameter-optimization/

Demonstrates design of experiments and optimizer selection.

```bash
# Generate DOE samples (LHS, Sobol, Factorial)
bash examples/parameter-optimization/run_doe.sh

# Select optimization algorithm
bash examples/parameter-optimization/run_optimizer_selector.sh

# Analyze parameter sensitivity
bash examples/parameter-optimization/run_sensitivity.sh

# Setup surrogate model
bash examples/parameter-optimization/run_surrogate.sh
```

**Use cases:**
- Parameter sweeps
- Calibration studies
- Sensitivity analysis
- Uncertainty quantification

### simulation-orchestrator/

Demonstrates multi-simulation campaign management.

```bash
# Generate parameter sweep configurations
bash examples/simulation-orchestrator/run_sweep.sh
```

**Data files:**
- `base_config.json` - Example base simulation configuration

**Use cases:**
- Parameter sweep generation
- Campaign initialization and tracking
- Result aggregation from multiple runs
- Batch simulation management

### post-processing/

Demonstrates post-processing of simulation output data.

```bash
# Extract field data
bash examples/post-processing/run_field_extractor.sh

# Analyze time series (convergence, steady state)
bash examples/post-processing/run_time_series.sh

# Compute statistics
bash examples/post-processing/run_statistics.sh

# Calculate derived quantities
bash examples/post-processing/run_derived_quantities.sh
```

**Data files:**
- `field_output.json` - Example 2D field data
- `history.json` - Example time series data
- `reference_profile.json` - Reference data for comparison

**Use cases:**
- Field extraction from multi-field output
- Convergence monitoring and steady state detection
- Statistical analysis of field distributions
- Computing volume fractions, gradients, interface areas
- Comparison with reference/experimental data

---

## Running All Examples

To verify all examples work correctly:

```bash
# From repository root
for script in examples/*/run_*.sh; do
    echo "Running: $script"
    bash "$script" || echo "FAILED: $script"
done
```

## Adding New Examples

1. Create a new directory under `examples/`
2. Add shell scripts named `run_*.sh`
3. Include a `README.md` explaining the scenario
4. Add any required data files (JSON, TXT, LOG)
5. Update this README with the new example

## Requirements

- Python 3.10+
- NumPy (for numerical stability scripts)
- No other dependencies for core functionality

Install dependencies:

```bash
pip install -r requirements.txt
```
