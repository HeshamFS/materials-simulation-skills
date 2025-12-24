#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/time-stepping/scripts/output_schedule.py" \
  --t-start 0 \
  --t-end 0.5 \
  --interval 0.01 \
  --json
