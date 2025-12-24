#!/bin/bash
# Generate a parameter sweep for dt and kappa

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

python3 "$REPO_ROOT/skills/simulation-workflow/simulation-orchestrator/scripts/sweep_generator.py" \
    --base-config "$SCRIPT_DIR/base_config.json" \
    --params "dt:0.001:0.01:3,kappa:0.1:1.0:2" \
    --method linspace \
    --output-dir "$SCRIPT_DIR/sweep_output" \
    --force \
    --json
