#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/simulation-workflow/simulation-validator/scripts/result_validator.py" \
  --metrics "$ROOT_DIR/examples/simulation-validator/simulation_metrics.json" \
  --bound-min 0 \
  --bound-max 1 \
  --json
