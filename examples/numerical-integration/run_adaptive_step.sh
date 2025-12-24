#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-integration/scripts/adaptive_step_controller.py" \
  --dt 0.01 \
  --error-norm 0.8 \
  --order 4 \
  --controller pi \
  --prev-error 1.1 \
  --json
