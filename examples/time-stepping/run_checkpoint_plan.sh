#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/time-stepping/scripts/checkpoint_planner.py" \
  --run-time 72000 \
  --checkpoint-cost 180 \
  --max-lost-time 3600 \
  --mtbf 144000 \
  --json
