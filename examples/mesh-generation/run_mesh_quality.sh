#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/mesh-generation/scripts/mesh_quality.py" \
  --dx 1.0 \
  --dy 0.5 \
  --dz 0.5 \
  --json
