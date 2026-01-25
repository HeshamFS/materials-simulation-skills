#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "=== Nonlinear Solver Selection Example ==="
echo ""

echo "1. Select solver for a large optimization problem without Jacobian:"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/solver_selector.py" \
  --size 50000 \
  --smooth \
  --memory-limited \
  --json
echo ""

echo "2. Select solver for a small root-finding problem with Jacobian:"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/solver_selector.py" \
  --jacobian-available \
  --size 500 \
  --smooth \
  --high-accuracy \
  --json
echo ""

echo "3. Select solver for bound-constrained optimization:"
python3 "$ROOT_DIR/skills/core-numerical/nonlinear-solvers/scripts/solver_selector.py" \
  --size 1000 \
  --smooth \
  --spd-hessian \
  --constraints bound \
  --json
echo ""

echo "=== Done ==="
