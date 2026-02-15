#!/usr/bin/env bash
set -euo pipefail
SCRIPT="skills/core-numerical/convergence-study/scripts/gci_calculator.py"

echo "=== Grid Convergence Index (3 mesh levels) ==="
python3 "$SCRIPT" --spacings "0.04,0.02,0.01" --values "1.0128,1.0032,1.0008" --json
