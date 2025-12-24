#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/simulation-workflow/simulation-validator/scripts/failure_diagnoser.py" \
  --log "$ROOT_DIR/examples/simulation-validator/simulation.log" \
  --json
