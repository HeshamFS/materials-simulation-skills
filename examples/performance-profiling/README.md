# Performance Profiling Examples

This directory contains runnable examples demonstrating the Performance Profiling Skill.

## Quick Start

Run any example from the repository root:

```bash
# Analyze timing from simulation log
bash examples/performance-profiling/run_timing_analysis.sh

# Analyze strong scaling
bash examples/performance-profiling/run_scaling_analysis.sh

# Estimate memory requirements
bash examples/performance-profiling/run_memory_profiling.sh

# Complete profiling workflow
bash examples/performance-profiling/run_complete_workflow.sh
```

## Example Files

| File | Description |
|------|-------------|
| `sample_timing_log.txt` | Example simulation log with timing entries |
| `sample_scaling_data.json` | Example strong scaling data (5 runs, 1-16 processors) |
| `sample_simulation_params.json` | Example simulation parameters for memory estimation |

## Example Workflows

### 1. Timing Analysis

Extract and analyze timing information from simulation logs:

```bash
python3 skills/simulation-workflow/performance-profiling/scripts/timing_analyzer.py \
    --log examples/performance-profiling/sample_timing_log.txt \
    --json
```

**Output**: Identifies that "Linear Solver" consumes ~75% of runtime.

### 2. Scaling Analysis

Analyze strong scaling efficiency:

```bash
python3 skills/simulation-workflow/performance-profiling/scripts/scaling_analyzer.py \
    --data examples/performance-profiling/sample_scaling_data.json \
    --type strong \
    --json
```

**Output**: Shows efficiency drops below 0.70 at 16 processors.

### 3. Memory Profiling

Estimate memory requirements:

```bash
python3 skills/simulation-workflow/performance-profiling/scripts/memory_profiler.py \
    --params examples/performance-profiling/sample_simulation_params.json \
    --available-gb 16.0 \
    --json
```

**Output**: Estimates ~0.77 GB total memory (field + solver workspace).

### 4. Bottleneck Detection

Identify bottlenecks and get recommendations:

```bash
# First, generate analysis results
python3 skills/simulation-workflow/performance-profiling/scripts/timing_analyzer.py \
    --log examples/performance-profiling/sample_timing_log.txt \
    --json > timing.json

# Then detect bottlenecks
python3 skills/simulation-workflow/performance-profiling/scripts/bottleneck_detector.py \
    --timing timing.json \
    --json
```

**Output**: Recommends using AMG preconditioner, tightening solver tolerance, etc.

## Expected Results

### Timing Analysis
- Total time: ~196s
- Slowest phase: Linear Solver (149.68s, 76.4%)
- Second slowest: Assembly (20.32s, 10.4%)

### Scaling Analysis
- Baseline: 1 processor, 200s
- Speedup at 16 processors: 9.09x
- Efficiency at 16 processors: 0.568 (below 0.70 threshold)

### Memory Profile
- Mesh points: 16,777,216
- Field memory: 0.384 GB
- Solver workspace: 0.640 GB
- Total: 1.024 GB
- Per-process (4 procs): 0.256 GB

### Bottleneck Detection
- **High severity**: Linear Solver dominates (76.4%)
- **Recommendations**: Use AMG preconditioner, tighten tolerance, profile assembly vs solve

## Customization

### Custom Timing Patterns

If your log format differs, provide a custom regex pattern:

```bash
python3 skills/simulation-workflow/performance-profiling/scripts/timing_analyzer.py \
    --log my_log.txt \
    --pattern 'Step\s+(\w+)\s+completed\s+in\s+([\d.]+)\s*seconds' \
    --json
```

### Weak Scaling Analysis

Change `--type` to `weak` for weak scaling:

```bash
python3 skills/simulation-workflow/performance-profiling/scripts/scaling_analyzer.py \
    --data weak_scaling_data.json \
    --type weak \
    --json
```

## Integration with Other Skills

Performance profiling complements other skills:

- **numerical-stability**: Use timing data to identify if stability checks are needed
- **linear-solvers**: Use solver timing to guide preconditioner selection
- **simulation-validator**: Combine with runtime monitoring for comprehensive analysis

## Troubleshooting

**No timing data found**: Check that your log format matches the default patterns or provide a custom pattern.

**Insufficient scaling data**: Ensure at least 2 runs are provided in the scaling data file.

**Missing parameters**: Memory profiler requires `mesh` and `fields` in the parameters file.
