#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-integration/scripts/integrator_selector.py" \
  --stiff \
  --jacobian-available \
  --implicit-allowed \
  --accuracy high \
  --dimension 2000000 \
  --low-memory \
  --json
