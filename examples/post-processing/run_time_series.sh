#!/bin/bash
# Example: Analyze time series data from simulation history

cd "$(dirname "$0")/../.." || exit 1

echo "=== Time Series Analysis Example ==="
echo ""

echo "1. Analyze energy evolution:"
python skills/simulation-workflow/post-processing/scripts/time_series_analyzer.py \
    --input examples/post-processing/history.json \
    --quantity energy \
    --json

echo ""
echo "2. Detect steady state in residual:"
python skills/simulation-workflow/post-processing/scripts/time_series_analyzer.py \
    --input examples/post-processing/history.json \
    --quantity residual \
    --detect-steady-state \
    --tolerance 1e-5 \
    --json
