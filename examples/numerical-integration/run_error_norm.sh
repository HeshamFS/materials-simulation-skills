#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-integration/scripts/error_norm.py" \
  --error 0.01,0.02,0.005 \
  --solution 1.0,2.0,0.5 \
  --rtol 1e-3 \
  --atol 1e-6 \
  --json
