#!/bin/bash
# Example: Complete profiling workflow

echo "=== Complete Performance Profiling Workflow ==="
echo ""

# Step 1: Timing analysis
echo "Step 1: Analyzing timing data..."
python3 skills/simulation-workflow/performance-profiling/scripts/timing_analyzer.py \
    --log examples/performance-profiling/sample_timing_log.txt \
    --json > timing_results.json

# Step 2: Scaling analysis
echo "Step 2: Analyzing scaling behavior..."
python3 skills/simulation-workflow/performance-profiling/scripts/scaling_analyzer.py \
    --data examples/performance-profiling/sample_scaling_data.json \
    --type strong \
    --json > scaling_results.json

# Step 3: Memory profiling
echo "Step 3: Profiling memory usage..."
python3 skills/simulation-workflow/performance-profiling/scripts/memory_profiler.py \
    --params examples/performance-profiling/sample_simulation_params.json \
    --available-gb 16.0 \
    --json > memory_results.json

# Step 4: Bottleneck detection
echo "Step 4: Detecting bottlenecks and generating recommendations..."
python3 skills/simulation-workflow/performance-profiling/scripts/bottleneck_detector.py \
    --timing timing_results.json \
    --scaling scaling_results.json \
    --memory memory_results.json \
    --json

# Cleanup
rm -f timing_results.json scaling_results.json memory_results.json

echo ""
echo "Complete workflow finished!"
