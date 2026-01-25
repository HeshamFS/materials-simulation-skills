#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== Convergence Analysis Example ==="
echo ""

echo "1. Analyze a well-converged solver (quadratic convergence):"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/convergence_analyzer.py" \
  --residuals "1,0.1,0.01,0.0001,1e-8,1e-16" \
  --tolerance 1e-10 \
  --json
echo ""

echo "2. Analyze stagnating solver (from sample data):"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/convergence_analyzer.py" \
  --residuals "1.0,0.32,0.11,0.045,0.021,0.012,0.0095,0.0087,0.0082,0.0079,0.0077,0.0076" \
  --tolerance 1e-10 \
  --json
echo ""

echo "3. Monitor residual patterns for the stagnating case:"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/residual_monitor.py" \
  --residuals "1.0,0.32,0.11,0.045,0.021,0.012,0.0095,0.0087,0.0082,0.0079,0.0077,0.0076" \
  --step-sizes "1.0,1.0,1.0,0.8,0.5,0.3,0.2,0.15,0.1,0.08,0.06,0.05" \
  --target-tolerance 1e-10 \
  --json
echo ""

echo "=== Done ==="
