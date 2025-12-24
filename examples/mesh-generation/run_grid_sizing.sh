#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/mesh-generation/scripts/grid_sizing.py" \
  --length 2.0 \
  --resolution 400 \
  --dims 2 \
  --json
