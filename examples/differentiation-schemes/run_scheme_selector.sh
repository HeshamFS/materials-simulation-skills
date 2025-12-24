#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
python3 "$ROOT_DIR/skills/core-numerical/differentiation-schemes/scripts/scheme_selector.py" \
  --smooth \
  --periodic \
  --order 1 \
  --accuracy 4 \
  --json
