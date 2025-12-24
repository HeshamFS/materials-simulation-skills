#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/differentiation-schemes/scripts/truncation_error.py" \
  --dx 0.01 \
  --accuracy 4 \
  --scale 2.0 \
  --json
