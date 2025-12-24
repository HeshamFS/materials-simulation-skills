#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-stability/scripts/cfl_checker.py" \
  --dx 0.1 \
  --dt 0.01 \
  --velocity 1.0 \
  --diffusivity 0.1 \
  --reaction-rate 0.5 \
  --dimensions 2 \
  --json
