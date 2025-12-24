#!/bin/bash
# Example: Extract field data from simulation output

cd "$(dirname "$0")/../.." || exit 1

echo "=== Field Extraction Example ==="
echo ""

echo "1. List available fields in output file:"
python skills/simulation-workflow/post-processing/scripts/field_extractor.py \
    --input examples/post-processing/field_output.json \
    --list \
    --json

echo ""
echo "2. Extract phi field with statistics:"
python skills/simulation-workflow/post-processing/scripts/field_extractor.py \
    --input examples/post-processing/field_output.json \
    --field phi \
    --json
