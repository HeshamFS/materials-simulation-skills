#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
JACOBIAN="$ROOT_DIR/examples/nonlinear-solvers/sample_jacobian.txt"

echo "=== Full Nonlinear Solver Preflight Workflow ==="
echo ""

echo "Step 1: Select solver for medium-sized root-finding with expensive Jacobian"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/solver_selector.py" \
  --jacobian-available \
  --jacobian-expensive \
  --size 5000 \
  --smooth \
  --json
echo ""

echo "Step 2: Diagnose Jacobian quality"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/jacobian_diagnostics.py" \
  --matrix "$JACOBIAN" \
  --json
echo ""

echo "Step 3: Get globalization strategy recommendation"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/globalization_advisor.py" \
  --problem-type root-finding \
  --jacobian-quality good \
  --previous-failures 0 \
  --json
echo ""

echo "Step 4: Analyze convergence from a sample residual history"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/convergence_analyzer.py" \
  --residuals "1.0,0.32,0.11,0.045,0.021,0.012,0.0095,0.0087,0.0082" \
  --tolerance 1e-10 \
  --json
echo ""

echo "Step 5: Monitor residual patterns"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/residual_monitor.py" \
  --residuals "1.0,0.32,0.11,0.045,0.021,0.012,0.0095,0.0087,0.0082" \
  --target-tolerance 1e-10 \
  --json
echo ""

echo "Step 6: Evaluate a Newton step for trust region management"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/step_quality.py" \
  --predicted-reduction 0.5 \
  --actual-reduction 0.4 \
  --step-norm 0.8 \
  --gradient-norm 1.0 \
  --trust-radius 1.0 \
  --json
echo ""

echo "=== Workflow Complete ==="
echo ""
echo "Summary:"
echo "  - Solver: Modified Newton or Broyden (expensive Jacobian)"
echo "  - Jacobian: Well-conditioned (sample matrix)"
echo "  - Globalization: Line search recommended"
echo "  - Convergence: Shows stagnation pattern"
echo "  - Recommendation: Switch to trust region or improve preconditioner"
