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
  --ill-conditioned \
  --memory-limited \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/preconditioner_advisor.py" \
  --matrix-type symmetric-indefinite \
  --sparse \
  --ill-conditioned \
  --symmetric \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/scaling_equilibration.py" \
  --matrix "$MATRIX" \
  --symmetric \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/residual_norms.py" \
  --residual 1,0.7,0.55,0.53,0.52 \
  --rhs 1,0,0,0,0 \
  --abs-tol 1e-3 \
  --rel-tol 1e-2 \
  --json

python3 "$ROOT_DIR/skills/core-numerical/linear-solvers/scripts/convergence_diagnostics.py" \
  --residuals 1,0.7,0.55,0.53,0.52 \
  --json
