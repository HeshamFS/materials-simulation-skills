#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/numerical-stability/scripts/matrix_condition.py" \
  --matrix "$ROOT_DIR/examples/numerical-stability/matrix_example.txt" \
  --json
