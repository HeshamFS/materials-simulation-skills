#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-stability/scripts/stiffness_detector.py" \
  --eigs=-1,-1000 \
  --json
