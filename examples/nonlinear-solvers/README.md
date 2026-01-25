# Nonlinear Solvers Examples

This directory contains examples demonstrating the nonlinear-solvers skill for
selecting and configuring Newton, quasi-Newton, and fixed-point methods.

## Files

- `sample_jacobian.txt`: A 3x3 test Jacobian matrix
- `sample_residual_history.json`: Example convergence data
- `run_solver_selection.sh`: Basic solver selection workflow
- `run_convergence_analysis.sh`: Analyze convergence from residual history
- `run_full_workflow.sh`: Complete preflight workflow for a nonlinear solve

## Quick Start

```bash
# Select solver for your problem
bash examples/nonlinear-solvers/run_solver_selection.sh

# Analyze convergence from a residual history
bash examples/nonlinear-solvers/run_convergence_analysis.sh

# Run complete preflight workflow
bash examples/nonlinear-solvers/run_full_workflow.sh
```

## Sample Problem

The examples simulate a Newton solver for a 3-variable nonlinear system.
The Jacobian in `sample_jacobian.txt` represents a moderately conditioned
system typical of phase-field or Navier-Stokes discretizations.

The residual history in `sample_residual_history.json` shows a solver that
initially converges well but then stagnates, demonstrating the diagnostic
capabilities of the skill.

## Workflow Steps

1. **Solver Selection**: Choose Newton, quasi-Newton, or fixed-point based on
   problem characteristics

2. **Globalization Strategy**: Select line search or trust region based on
   Jacobian quality and solver history

3. **Jacobian Analysis**: Check condition number and rank deficiency

4. **Convergence Monitoring**: Track residual patterns and detect issues

5. **Step Quality**: Evaluate Newton steps for trust region management
