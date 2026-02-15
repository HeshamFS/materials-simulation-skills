#!/usr/bin/env bash
set -euo pipefail
SCRIPT="skills/core-numerical/convergence-study/scripts/richardson_extrapolation.py"

echo "=== Richardson Extrapolation ==="
python3 "$SCRIPT" --spacings "0.02,0.01" --values "1.0032,1.0008" --order 2.0 --json
