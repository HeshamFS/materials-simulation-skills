#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/simulation-workflow/simulation-validator/scripts/preflight_checker.py" \
  --config "$ROOT_DIR/examples/simulation-validator/simulation_config.json" \
  --required dx,dt \
  --ranges dt:1e-6:1e-2,dx:1e-8:1e-4 \
  --json
