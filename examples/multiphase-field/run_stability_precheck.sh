#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-stability/scripts/cfl_checker.py" \
  --dx 2e-9 \
  --dt 1e-5 \
  --velocity 0.0 \
  --diffusivity 1e-14 \
  --reaction-rate 200 \
  --dimensions 2 \
  --json
