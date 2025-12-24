#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-integration/scripts/imex_split_planner.py" \
  --stiff-terms diffusion,gradient,elastic \
  --nonstiff-terms reaction,source \
  --coupling strong \
  --accuracy high \
  --stiffness-ratio 1e5 \
  --conservative \
  --json
