#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/simulation-workflow/parameter-optimization/scripts/surrogate_builder.py" \
  --x 0,1,2,3 \
  --y 1,1.5,2.2,3.1 \
  --model rbf \
  --json
