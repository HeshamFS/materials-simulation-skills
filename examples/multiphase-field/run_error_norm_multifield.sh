#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-integration/scripts/error_norm.py" \
  --error 1.2e-4,8.0e-5,1.5e-4,2.0e-6,5.0e-6 \
  --solution 0.35,0.55,0.10,0.02,0.98 \
  --rtol 1e-4 \
  --atol 1e-7 \
  --norm rms \
  --json
