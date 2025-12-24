#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/simulation-workflow/parameter-optimization/scripts/doe_generator.py" \
  --params 3 \
  --budget 20 \
  --method lhs \
  --json
