#!/bin/bash
# Example: Analyze timing from simulation log

echo "=== Timing Analysis Example ==="
echo ""

# Run timing analyzer
python3 skills/simulation-workflow/performance-profiling/scripts/timing_analyzer.py \
    --log examples/performance-profiling/sample_timing_log.txt \
    --json

echo ""
echo "Analysis complete!"
