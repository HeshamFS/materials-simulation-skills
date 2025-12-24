#!/bin/bash
# Example: Compute derived quantities from field data

cd "$(dirname "$0")/../.." || exit 1

echo "=== Derived Quantities Example ==="
echo ""

echo "1. Compute volume fraction:"
python skills/simulation-workflow/post-processing/scripts/derived_quantities.py \
    --input examples/post-processing/field_output.json \
    --quantity volume_fraction \
    --field phi \
    --threshold 0.5 \
    --json

echo ""
echo "2. Compute gradient magnitude:"
python skills/simulation-workflow/post-processing/scripts/derived_quantities.py \
    --input examples/post-processing/field_output.json \
    --quantity gradient_magnitude \
    --field phi \
    --json
