#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/time-stepping/scripts/timestep_planner.py" \
  --dt-target 2e-4 \
  --dt-limit 1e-4 \
  --safety 0.75 \
  --ramp-steps 8 \
  --ramp-kind geometric \
  --preview-steps 8 \
  --json
