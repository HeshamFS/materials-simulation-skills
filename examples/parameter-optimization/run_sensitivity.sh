#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/simulation-workflow/parameter-optimization/scripts/sensitivity_summary.py" \
  --scores 0.2,0.5,0.3 \
  --names kappa,mobility,W \
  --json
