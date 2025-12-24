#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-stability/scripts/von_neumann_analyzer.py" \
  --coeffs 0.2,0.6,0.2 \
  --dx 1.0 \
  --nk 128 \
  --json
