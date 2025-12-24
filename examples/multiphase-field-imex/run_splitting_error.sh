#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-integration/scripts/splitting_error_estimator.py" \
  --dt 2e-6 \
  --scheme strang \
  --commutator-norm 5e3 \
  --target-error 1e-6 \
  --json
