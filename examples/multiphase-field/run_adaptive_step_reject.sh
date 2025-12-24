#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-integration/scripts/adaptive_step_controller.py" \
  --dt 2.5e-6 \
  --error-norm 1.6 \
  --order 2 \
  --controller pi \
  --prev-error 1.1 \
  --json
