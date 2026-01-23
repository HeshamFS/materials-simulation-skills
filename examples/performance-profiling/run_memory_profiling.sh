#!/bin/bash
# Example: Estimate memory requirements

echo "=== Memory Profiling Example ==="
echo ""

# Run memory profiler
python3 skills/simulation-workflow/performance-profiling/scripts/memory_profiler.py \
    --params examples/performance-profiling/sample_simulation_params.json \
    --available-gb 16.0 \
    --json

echo ""
echo "Analysis complete!"
