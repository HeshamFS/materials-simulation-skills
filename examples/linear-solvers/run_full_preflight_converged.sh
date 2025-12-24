#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MATRIX="$ROOT_DIR/examples/linear-solvers/coupled_block_matrix.txt"

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/sparsity_stats.py" \
  --matrix "$MATRIX" \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/solver_selector.py" \
  --symmetric \
  --sparse \
  --size 200000 \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/preconditioner_advisor.py" \
  --matrix-type symmetric-indefinite \
  --sparse \
  --symmetric \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/scaling_equilibration.py" \
  --matrix "$MATRIX" \
  --symmetric \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/residual_norms.py" \
  --residual 8e-6,1.5e-6,3e-7,8e-8,1e-8 \
  --rhs 1,0,0,0,0 \
  --abs-tol 1e-6 \
  --rel-tol 1e-5 \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/convergence_diagnostics.py" \
  --residuals 8e-6,1.5e-6,3e-7,8e-8,1e-8 \
  --json
