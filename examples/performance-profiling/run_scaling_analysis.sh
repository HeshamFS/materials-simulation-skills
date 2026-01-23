#!/bin/bash
# Example: Analyze strong scaling

echo "=== Strong Scaling Analysis Example ==="
echo ""

# Run scaling analyzer
python3 skills/simulation-workflow/performance-profiling/scripts/scaling_analyzer.py \
    --data examples/performance-profiling/sample_scaling_data.json \
    --type strong \
    --json

echo ""
echo "Analysis complete!"
