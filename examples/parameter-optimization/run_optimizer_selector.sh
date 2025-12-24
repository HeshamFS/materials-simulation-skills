#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/simulation-workflow/parameter-optimization/scripts/optimizer_selector.py" \
  --dim 3 \
  --budget 50 \
  --noise low \
  --json
