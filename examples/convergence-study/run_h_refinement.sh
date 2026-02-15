#!/usr/bin/env bash
set -euo pipefail
SCRIPT="skills/core-numerical/convergence-study/scripts/h_refinement.py"

echo "=== Spatial Convergence Study (4 levels) ==="
python3 "$SCRIPT" --spacings "0.4,0.2,0.1,0.05" --values "1.160,1.040,1.010,1.0025" --expected-order 2.0 --json
