# Design Document: Performance Profiling Skill

## Overview

The Performance Profiling Skill provides four Python scripts that analyze simulation performance from different perspectives:

1. **timing_analyzer.py** - Parses simulation logs to extract and analyze timing information
2. **scaling_analyzer.py** - Analyzes strong and weak scaling from multi-run data
3. **memory_profiler.py** - Estimates memory requirements from simulation parameters
4. **bottleneck_detector.py** - Identifies performance bottlenecks and recommends optimizations

Each script follows the repository's established patterns:
- Python 3.8+ compatible using only standard library
- JSON output for automation
- Cross-platform support (Linux, macOS, Windows)
- Clear command-line interfaces with --help documentation
- Consistent error handling and reporting

The skill integrates into the materials-simulation-skills repository under `skills/simulation-workflow/performance-profiling/`.

## Architecture

### Component Structure

```
skills/simulation-workflow/performance-profiling/
├── SKILL.md                          # Skill documentation with YAML frontmatter
├── scripts/
│   ├── timing_analyzer.py            # Extract and analyze timing data
│   ├── scaling_analyzer.py           # Compute scaling efficiency
│   ├── memory_profiler.py            # Estimate memory requirements
│   └── bottleneck_detector.py        # Detect bottlenecks and recommend fixes
└── references/
    ├── profiling_guide.md            # Profiling concepts and interpretation
    └── optimization_strategies.md    # Common optimization approaches

examples/performance-profiling/
├── README.md                         # Example usage guide
├── sample_timing_log.txt             # Example simulation log with timing
├── sample_scaling_data.json          # Example scaling data
└── sample_simulation_params.json     # Example simulation parameters

tests/unit/
└── test_performance_profiling.py     # Unit tests for all scripts

tests/integration/
└── test_performance_profiling_integration.py  # Integration tests
```

### Data Flow

```
User Input → Script → Parser → Analyzer → JSON Output
                ↓
         Error Handler
```

Each script follows this pattern:
1. Parse command-line arguments
2. Load and validate input data
3. Perform analysis computations
4. Generate structured output (JSON or human-readable)
5. Handle errors gracefully with informative messages

## Components and Interfaces

### 1. Timing Analyzer (timing_analyzer.py)

**Purpose**: Parse simulation logs to extract timing information and identify slow phases.

**Command-Line Interface**:
```bash
python3 timing_analyzer.py --log <path> [--pattern <regex>] [--json]
```

**Parameters**:
- `--log`: Path to simulation log file (required)
- `--pattern`: Custom regex pattern for timing entries (optional, default: common patterns)
- `--json`: Output JSON format (optional)

**Input Format**: Text log file with timing entries like:
```
[2024-01-15 10:23:45] Phase: Mesh Generation, Time: 12.34s
[2024-01-15 10:24:01] Phase: Assembly, Time: 45.67s
```

**Output Structure** (JSON):
```json
{
  "inputs": {
    "log_file": "simulation.log",
    "pattern": "default"
  },
  "timing_data": {
    "phases": [
      {
        "name": "Mesh Generation",
        "total_time": 12.34,
        "count": 1,
        "mean_time": 12.34,
        "min_time": 12.34,
        "max_time": 12.34,
        "percentage": 15.2
      }
    ],
    "total_time": 81.23,
    "slowest_phase": "Assembly"
  }
}
```

**Core Functions**:
- `parse_timing_log(log_path, pattern)` → List of timing entries
- `aggregate_timings(entries)` → Aggregated statistics per phase
- `identify_slowest_phases(aggregated, top_n)` → Top N slowest phases

### 2. Scaling Analyzer (scaling_analyzer.py)

**Purpose**: Analyze strong and weak scaling efficiency from multiple simulation runs.

**Command-Line Interface**:
```bash
python3 scaling_analyzer.py --data <path> --type <strong|weak> [--json]
```

**Parameters**:
- `--data`: Path to JSON file with scaling data (required)
- `--type`: Scaling type: "strong" or "weak" (required)
- `--json`: Output JSON format (optional)

**Input Format** (JSON):
```json
{
  "runs": [
    {"processors": 1, "problem_size": 1000, "time": 100.0},
    {"processors": 2, "problem_size": 1000, "time": 55.0},
    {"processors": 4, "problem_size": 1000, "time": 30.0}
  ]
}
```

**Output Structure** (JSON):
```json
{
  "inputs": {
    "data_file": "scaling.json",
    "scaling_type": "strong"
  },
  "scaling_analysis": {
    "type": "strong",
    "baseline": {"processors": 1, "time": 100.0},
    "results": [
      {
        "processors": 2,
        "time": 55.0,
        "speedup": 1.82,
        "efficiency": 0.91
      }
    ],
    "efficiency_threshold_processors": 8,
    "average_efficiency": 0.78
  }
}
```

**Core Functions**:
- `load_scaling_data(path)` → List of run configurations
- `compute_strong_scaling(runs)` → Strong scaling metrics
- `compute_weak_scaling(runs)` → Weak scaling metrics
- `find_efficiency_threshold(results, threshold)` → Processor count where efficiency drops

### 3. Memory Profiler (memory_profiler.py)

**Purpose**: Estimate memory requirements from simulation parameters.

**Command-Line Interface**:
```bash
python3 memory_profiler.py --params <path> [--available-gb <float>] [--json]
```

**Parameters**:
- `--params`: Path to JSON file with simulation parameters (required)
- `--available-gb`: Available system memory in GB (optional, for warnings)
- `--json`: Output JSON format (optional)

**Input Format** (JSON):
```json
{
  "mesh": {
    "nx": 256,
    "ny": 256,
    "nz": 256
  },
  "fields": {
    "concentration": {"components": 2, "bytes_per_value": 8},
    "temperature": {"components": 1, "bytes_per_value": 8}
  },
  "solver": {
    "type": "iterative",
    "workspace_multiplier": 5
  },
  "processors": 4
}
```

**Output Structure** (JSON):
```json
{
  "inputs": {
    "params_file": "params.json",
    "available_gb": 16.0
  },
  "memory_profile": {
    "mesh_points": 16777216,
    "field_memory_gb": 0.384,
    "solver_workspace_gb": 1.92,
    "total_memory_gb": 2.304,
    "per_process_gb": 0.576,
    "warnings": []
  }
}
```

**Core Functions**:
- `load_parameters(path)` → Parameter dictionary
- `estimate_field_memory(mesh, fields)` → Memory for field variables
- `estimate_solver_memory(mesh, solver_type)` → Memory for solver workspace
- `compute_total_memory(components, processors)` → Total and per-process memory

### 4. Bottleneck Detector (bottleneck_detector.py)

**Purpose**: Identify performance bottlenecks and recommend optimization strategies.

**Command-Line Interface**:
```bash
python3 bottleneck_detector.py --timing <path> [--scaling <path>] [--memory <path>] [--json]
```

**Parameters**:
- `--timing`: Path to timing analysis JSON (required)
- `--scaling`: Path to scaling analysis JSON (optional)
- `--memory`: Path to memory profile JSON (optional)
- `--json`: Output JSON format (optional)

**Input Format**: JSON outputs from other profiling scripts

**Output Structure** (JSON):
```json
{
  "inputs": {
    "timing_file": "timing.json",
    "scaling_file": "scaling.json",
    "memory_file": "memory.json"
  },
  "bottlenecks": [
    {
      "type": "timing",
      "phase": "Linear Solver",
      "severity": "high",
      "metric": "percentage",
      "value": 65.3,
      "threshold": 50.0
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "category": "solver",
      "issue": "Linear solver dominates runtime (65.3%)",
      "strategies": [
        "Use algebraic multigrid preconditioner",
        "Tighten solver tolerance if over-solving",
        "Consider direct solver for small problems"
      ]
    }
  ]
}
```

**Core Functions**:
- `load_analysis_results(timing_path, scaling_path, memory_path)` → Combined analysis data
- `detect_timing_bottlenecks(timing_data, threshold)` → List of timing bottlenecks
- `detect_scaling_bottlenecks(scaling_data, threshold)` → List of scaling issues
- `detect_memory_bottlenecks(memory_data, threshold)` → List of memory issues
- `generate_recommendations(bottlenecks)` → Prioritized optimization strategies

## Data Models

### TimingEntry
```python
{
  "phase": str,           # Name of the computational phase
  "time": float,          # Time in seconds
  "timestamp": str        # Optional timestamp
}
```

### AggregatedTiming
```python
{
  "name": str,            # Phase name
  "total_time": float,    # Sum of all occurrences
  "count": int,           # Number of occurrences
  "mean_time": float,     # Average time
  "min_time": float,      # Minimum time
  "max_time": float,      # Maximum time
  "percentage": float     # Percentage of total runtime
}
```

### ScalingRun
```python
{
  "processors": int,      # Number of processors
  "problem_size": int,    # Problem size (mesh points, DOFs, etc.)
  "time": float          # Wall-clock time in seconds
}
```

### ScalingResult
```python
{
  "processors": int,      # Number of processors
  "time": float,          # Wall-clock time
  "speedup": float,       # Speedup relative to baseline
  "efficiency": float     # Parallel efficiency (0.0 to 1.0)
}
```

### MemoryEstimate
```python
{
  "mesh_points": int,           # Total mesh points
  "field_memory_gb": float,     # Memory for field variables
  "solver_workspace_gb": float, # Memory for solver
  "total_memory_gb": float,     # Total memory required
  "per_process_gb": float,      # Memory per process
  "warnings": List[str]         # Memory-related warnings
}
```

### Bottleneck
```python
{
  "type": str,            # "timing", "scaling", or "memory"
  "phase": str,           # Affected phase or component
  "severity": str,        # "high", "medium", or "low"
  "metric": str,          # Metric name
  "value": float,         # Measured value
  "threshold": float      # Threshold that was exceeded
}
```

### Recommendation
```python
{
  "priority": str,        # "high", "medium", or "low"
  "category": str,        # "solver", "mesh", "io", "communication", etc.
  "issue": str,           # Description of the issue
  "strategies": List[str] # List of optimization strategies
}
```


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Timing Analysis Properties

**Property 1: Complete timing extraction**
*For any* valid simulation log file containing timing entries, parsing should extract all timing information without loss.
**Validates: Requirements 1.1**

**Property 2: Slowest phase identification correctness**
*For any* set of aggregated timing data, the identified slowest phases should be those with the highest total time values.
**Validates: Requirements 1.2**

**Property 3: Aggregation correctness**
*For any* set of timing entries for the same phase, the aggregated sum should equal the sum of all individual times, the mean should equal sum/count, the min should be the minimum value, and the max should be the maximum value.
**Validates: Requirements 1.3**

**Property 4: Robustness to malformed data**
*For any* log file containing both valid and malformed timing entries, the system should process all valid entries and report warnings for malformed entries without crashing.
**Validates: Requirements 1.4**

### Scaling Analysis Properties

**Property 5: Strong scaling efficiency formula**
*For any* set of strong scaling runs with fixed problem size, the computed efficiency for N processors should equal (T_baseline / (N * T_N)) where T_baseline is the time for the smallest processor count and T_N is the time for N processors.
**Validates: Requirements 2.1**

**Property 6: Weak scaling efficiency formula**
*For any* set of weak scaling runs with constant problem size per processor, the computed efficiency for N processors should equal (T_baseline / T_N) where T_baseline is the time for the smallest processor count.
**Validates: Requirements 2.2**

**Property 7: Baseline selection correctness**
*For any* set of scaling runs, the baseline should be the run with the smallest processor count.
**Validates: Requirements 2.3**

**Property 8: Efficiency threshold detection**
*For any* scaling data with varying efficiency values, if a processor count exists where efficiency first drops below 0.70, that processor count should be correctly identified.
**Validates: Requirements 2.4**

### Memory Profiling Properties

**Property 9: Memory estimation completeness**
*For any* simulation parameters, the total memory estimate should include contributions from mesh size, field variables, and solver workspace.
**Validates: Requirements 3.2**

**Property 10: Per-process memory calculation**
*For any* memory estimate with N processors, the per-process memory should equal total_memory / N.
**Validates: Requirements 3.3**

**Property 11: Memory warning generation**
*For any* memory estimate where total_memory > available_memory, a warning should be present in the output.
**Validates: Requirements 3.4**

**Property 12: Missing parameter reporting**
*For any* incomplete parameter set, the error message should identify all missing required parameters.
**Validates: Requirements 3.6**

### Bottleneck Detection Properties

**Property 13: Dominant phase bottleneck detection**
*For any* timing data where a phase consumes more than 50% of total time, that phase should be flagged as a bottleneck with high severity.
**Validates: Requirements 4.1**

**Property 14: Poor scaling recommendations**
*For any* scaling data where efficiency is below 0.70, recommendations should include investigating communication overhead or load imbalance.
**Validates: Requirements 4.2**

**Property 15: High memory recommendations**
*For any* memory profile where usage exceeds 80% of available memory, recommendations should include memory reduction strategies.
**Validates: Requirements 4.3**

**Property 16: Solver bottleneck recommendations**
*For any* timing data where a solver-related phase is dominant (>50%), recommendations should include solver-specific optimizations (preconditioner tuning, tolerance adjustment).
**Validates: Requirements 4.4**

### Cross-Platform Properties

**Property 17: Path separator handling**
*For any* file path provided as input, the system should correctly handle both forward slashes and backslashes regardless of the platform.
**Validates: Requirements 5.5**

### JSON Output Properties

**Property 18: JSON validity and structure**
*For any* script execution with the --json flag, the output should be valid parseable JSON containing both an "inputs" section and a "results" or "report" section.
**Validates: Requirements 6.1, 6.2, 6.3, 6.5**

**Property 19: JSON error formatting**
*For any* error condition when the --json flag is set, error information should be output in valid JSON format.
**Validates: Requirements 6.4**

### Command-Line Interface Properties

**Property 20: Missing parameter error messages**
*For any* script invocation missing required parameters, an error message should be displayed indicating which specific parameters are needed.
**Validates: Requirements 7.2**

**Property 21: Invalid parameter error messages**
*For any* script invocation with invalid parameter values, an error message should be displayed with information about valid ranges or formats.
**Validates: Requirements 7.3**

## Error Handling

### Error Categories

1. **Input Errors**
   - File not found
   - Invalid file format
   - Missing required parameters
   - Invalid parameter values

2. **Parsing Errors**
   - Malformed log entries
   - Invalid JSON structure
   - Unexpected data types

3. **Computation Errors**
   - Division by zero (e.g., zero baseline time)
   - Insufficient data points
   - Negative or invalid values

### Error Handling Strategy

All scripts follow this error handling pattern:

```python
try:
    # Load and validate inputs
    # Perform analysis
    # Generate output
except ValueError as e:
    # Handle validation errors
    if args.json:
        print(json.dumps({"error": str(e)}))
    else:
        print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
except FileNotFoundError as e:
    # Handle missing files
    if args.json:
        print(json.dumps({"error": f"File not found: {e}"}))
    else:
        print(f"Error: File not found: {e}", file=sys.stderr)
    sys.exit(2)
except Exception as e:
    # Handle unexpected errors
    if args.json:
        print(json.dumps({"error": f"Unexpected error: {e}"}))
    else:
        print(f"Unexpected error: {e}", file=sys.stderr)
    sys.exit(3)
```

### Graceful Degradation

- **Partial data**: Process what's available, report warnings
- **Missing optional inputs**: Use defaults, document in output
- **Malformed entries**: Skip and continue, report count of skipped entries

## Testing Strategy

### Dual Testing Approach

The Performance Profiling Skill requires both unit tests and property-based tests for comprehensive validation:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all inputs

Together, these approaches provide comprehensive coverage where unit tests catch concrete bugs and property tests verify general correctness.

### Property-Based Testing

We will use the **Hypothesis** library for Python property-based testing. Each correctness property listed above will be implemented as a property-based test.

**Configuration**:
- Minimum 100 iterations per property test (due to randomization)
- Each test tagged with: `# Feature: performance-profiling, Property N: [property text]`
- Each correctness property implemented by a SINGLE property-based test

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st

@given(
    timing_entries=st.lists(
        st.tuples(
            st.text(min_size=1),  # phase name
            st.floats(min_value=0.001, max_value=1000.0)  # time
        ),
        min_size=1
    )
)
def test_aggregation_correctness(timing_entries):
    """Feature: performance-profiling, Property 3: Aggregation correctness"""
    # Group by phase and aggregate
    aggregated = aggregate_timings(timing_entries)
    
    # Verify sum, mean, min, max are correct
    for phase, stats in aggregated.items():
        phase_times = [t for p, t in timing_entries if p == phase]
        assert stats['sum'] == sum(phase_times)
        assert stats['mean'] == sum(phase_times) / len(phase_times)
        assert stats['min'] == min(phase_times)
        assert stats['max'] == max(phase_times)
```

### Unit Testing

Unit tests focus on:
- **Specific examples**: Known input/output pairs
- **Edge cases**: Empty logs, single data point, extreme values
- **Error conditions**: Missing files, invalid formats, malformed data
- **Integration points**: Script command-line interfaces, JSON output format

**Example Unit Test**:
```python
def test_empty_log_returns_empty_report():
    """Test that an empty log file returns an empty timing report."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("")
        log_path = f.name
    
    result = parse_timing_log(log_path)
    assert result['timing_data']['phases'] == []
    assert result['timing_data']['total_time'] == 0.0
```

### Test Organization

```
tests/unit/test_performance_profiling.py
├── TestTimingAnalyzer
│   ├── test_parse_timing_log_*
│   ├── test_aggregate_timings_*
│   └── test_identify_slowest_phases_*
├── TestScalingAnalyzer
│   ├── test_compute_strong_scaling_*
│   ├── test_compute_weak_scaling_*
│   └── test_find_efficiency_threshold_*
├── TestMemoryProfiler
│   ├── test_estimate_field_memory_*
│   ├── test_estimate_solver_memory_*
│   └── test_compute_total_memory_*
└── TestBottleneckDetector
    ├── test_detect_timing_bottlenecks_*
    ├── test_detect_scaling_bottlenecks_*
    └── test_generate_recommendations_*

tests/integration/test_performance_profiling_integration.py
├── test_timing_analyzer_cli
├── test_scaling_analyzer_cli
├── test_memory_profiler_cli
└── test_bottleneck_detector_cli
```

### Testing Edge Cases

The following edge cases are explicitly handled and tested:

1. **Empty or no timing data** (Requirements 1.6)
2. **Insufficient scaling data points** (Requirements 2.6)
3. **No bottlenecks detected** (Requirements 4.6)
4. **Missing required parameters**
5. **Malformed log entries**
6. **Zero or negative values**
7. **Single data point scenarios**

These edge cases are tested through unit tests rather than property-based tests, as they represent specific boundary conditions.
