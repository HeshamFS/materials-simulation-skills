#!/bin/bash
# Example: Compute statistics on field data

cd "$(dirname "$0")/../.." || exit 1

echo "=== Statistical Analysis Example ==="
echo ""

echo "1. Basic statistics for phi field:"
python skills/simulation-workflow/post-processing/scripts/statistical_analyzer.py \
    --input examples/post-processing/field_output.json \
    --field phi \
    --json

echo ""
echo "2. Statistics with histogram:"
python skills/simulation-workflow/post-processing/scripts/statistical_analyzer.py \
    --input examples/post-processing/field_output.json \
    --field phi \
    --histogram \
    --bins 10 \
    --json
