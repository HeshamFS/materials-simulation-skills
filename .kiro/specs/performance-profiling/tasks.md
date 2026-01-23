# Implementation Plan: Performance Profiling Skill

## Overview

This implementation plan breaks down the Performance Profiling Skill into discrete coding tasks. The approach follows the repository's established patterns and implements four profiling scripts with comprehensive testing. Each task builds incrementally, with testing integrated throughout to catch errors early.

## Tasks

- [x] 1. Set up project structure and shared utilities
  - Create `skills/simulation-workflow/performance-profiling/` directory structure
  - Create `scripts/`, `references/` subdirectories
  - Implement shared utility functions for JSON output, error handling, and argument parsing
  - Create base test structure in `tests/unit/test_performance_profiling.py`
  - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 7.1_

- [x] 2. Implement timing analyzer script
  - [x] 2.1 Create `scripts/timing_analyzer.py` with command-line interface
    - Implement argument parser with --log, --pattern, --json flags
    - Add --help documentation
    - _Requirements: 1.1, 7.1, 7.2_
  
  - [x] 2.2 Implement log parsing and timing extraction
    - Write `parse_timing_log()` function with regex pattern matching
    - Handle multiple common log formats
    - Implement robust error handling for malformed entries
    - _Requirements: 1.1, 1.4_
  
  - [x] 2.3 Implement timing aggregation logic
    - Write `aggregate_timings()` function to compute sum, mean, min, max per phase
    - Calculate percentage of total time for each phase
    - Identify slowest phases
    - _Requirements: 1.2, 1.3_
  
  - [x] 2.4 Implement JSON output formatting
    - Structure output with inputs and timing_data sections
    - Handle empty log case (no timing data found)
    - _Requirements: 1.5, 1.6, 6.1, 6.2, 6.3_
  
  - [x] 2.5 Write property test for complete timing extraction
    - **Property 1: Complete timing extraction**
    - **Validates: Requirements 1.1**
  
  - [x] 2.6 Write property test for aggregation correctness
    - **Property 3: Aggregation correctness**
    - **Validates: Requirements 1.3**
  
  - [x] 2.7 Write unit tests for timing analyzer
    - Test empty log edge case
    - Test malformed entries handling
    - Test slowest phase identification
    - Test JSON output structure
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 3. Implement scaling analyzer script
  - [x] 3.1 Create `scripts/scaling_analyzer.py` with command-line interface
    - Implement argument parser with --data, --type, --json flags
    - Add --help documentation
    - Validate scaling type (strong or weak)
    - _Requirements: 2.1, 2.2, 7.1, 7.2, 7.3_
  
  - [x] 3.2 Implement scaling data loader and validator
    - Write `load_scaling_data()` function to parse JSON input
    - Validate required fields (processors, problem_size, time)
    - Check for minimum data points (at least 2 runs)
    - _Requirements: 2.6_
  
  - [x] 3.3 Implement strong scaling analysis
    - Write `compute_strong_scaling()` function
    - Calculate speedup and efficiency for each configuration
    - Use smallest processor count as baseline
    - _Requirements: 2.1, 2.3_
  
  - [x] 3.4 Implement weak scaling analysis
    - Write `compute_weak_scaling()` function
    - Calculate efficiency for constant work per processor
    - Use smallest processor count as baseline
    - _Requirements: 2.2, 2.3_
  
  - [x] 3.5 Implement efficiency threshold detection
    - Write `find_efficiency_threshold()` function
    - Identify first processor count where efficiency < 0.70
    - _Requirements: 2.4_
  
  - [x] 3.6 Implement JSON output formatting
    - Structure output with inputs and scaling_analysis sections
    - Include baseline, results, and threshold information
    - _Requirements: 2.5, 6.1, 6.2, 6.3_
  
  - [x] 3.7 Write property test for strong scaling efficiency formula
    - **Property 5: Strong scaling efficiency formula**
    - **Validates: Requirements 2.1**
  
  - [x] 3.8 Write property test for weak scaling efficiency formula
    - **Property 6: Weak scaling efficiency formula**
    - **Validates: Requirements 2.2**
  
  - [x] 3.9 Write property test for baseline selection
    - **Property 7: Baseline selection correctness**
    - **Validates: Requirements 2.3**
  
  - [x] 3.10 Write unit tests for scaling analyzer
    - Test insufficient data points edge case
    - Test efficiency threshold detection
    - Test JSON output structure
    - Test error handling for invalid scaling type
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 4. Checkpoint - Ensure timing and scaling analyzers work correctly
  - Run all tests for timing and scaling analyzers
  - Verify JSON output format consistency
  - Test command-line interfaces manually
  - Ask the user if questions arise

- [x] 5. Implement memory profiler script
  - [x] 5.1 Create `scripts/memory_profiler.py` with command-line interface
    - Implement argument parser with --params, --available-gb, --json flags
    - Add --help documentation
    - _Requirements: 3.1, 7.1, 7.2_
  
  - [x] 5.2 Implement parameter loader and validator
    - Write `load_parameters()` function to parse JSON input
    - Validate required fields (mesh, fields)
    - Report missing parameters with specific names
    - _Requirements: 3.6_
  
  - [x] 5.3 Implement field memory estimation
    - Write `estimate_field_memory()` function
    - Calculate memory based on mesh size, field components, and bytes per value
    - _Requirements: 3.1, 3.2_
  
  - [x] 5.4 Implement solver workspace estimation
    - Write `estimate_solver_memory()` function
    - Apply workspace multiplier based on solver type
    - _Requirements: 3.1, 3.2_
  
  - [x] 5.5 Implement total memory calculation
    - Write `compute_total_memory()` function
    - Sum all memory components
    - Calculate per-process memory (total / processors)
    - Generate warnings if memory exceeds available
    - _Requirements: 3.2, 3.3, 3.4_
  
  - [x] 5.6 Implement JSON output formatting
    - Structure output with inputs and memory_profile sections
    - Include all memory components and warnings
    - _Requirements: 3.5, 6.1, 6.2, 6.3_
  
  - [x] 5.7 Write property test for memory estimation completeness
    - **Property 9: Memory estimation completeness**
    - **Validates: Requirements 3.2**
  
  - [x] 5.8 Write property test for per-process memory calculation
    - **Property 10: Per-process memory calculation**
    - **Validates: Requirements 3.3**
  
  - [x] 5.9 Write property test for memory warning generation
    - **Property 11: Memory warning generation**
    - **Validates: Requirements 3.4**
  
  - [x] 5.10 Write unit tests for memory profiler
    - Test missing parameters error reporting
    - Test memory warning generation
    - Test JSON output structure
    - Test various mesh sizes and field configurations
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 6. Implement bottleneck detector script
  - [x] 6.1 Create `scripts/bottleneck_detector.py` with command-line interface
    - Implement argument parser with --timing, --scaling, --memory, --json flags
    - Add --help documentation
    - Make scaling and memory inputs optional
    - _Requirements: 4.1, 7.1, 7.2_
  
  - [x] 6.2 Implement analysis results loader
    - Write `load_analysis_results()` function
    - Load and parse JSON from timing, scaling, and memory analyzers
    - Handle missing optional inputs gracefully
    - _Requirements: 4.1_
  
  - [x] 6.3 Implement timing bottleneck detection
    - Write `detect_timing_bottlenecks()` function
    - Flag phases consuming >50% of total time as high severity
    - Calculate severity based on percentage thresholds
    - _Requirements: 4.1_
  
  - [x] 6.4 Implement scaling bottleneck detection
    - Write `detect_scaling_bottlenecks()` function
    - Flag efficiency <70% as bottleneck
    - _Requirements: 4.2_
  
  - [x] 6.5 Implement memory bottleneck detection
    - Write `detect_memory_bottlenecks()` function
    - Flag memory usage >80% of available as bottleneck
    - _Requirements: 4.3_
  
  - [x] 6.6 Implement recommendation generation
    - Write `generate_recommendations()` function
    - Map bottleneck types to optimization strategies
    - Assign priority levels (high, medium, low)
    - Include solver-specific recommendations for solver bottlenecks
    - Handle case where no bottlenecks are detected
    - _Requirements: 4.2, 4.3, 4.4, 4.6_
  
  - [x] 6.7 Implement JSON output formatting
    - Structure output with inputs, bottlenecks, and recommendations sections
    - Include priority levels in recommendations
    - _Requirements: 4.5, 6.1, 6.2, 6.3_
  
  - [x] 6.8 Write property test for dominant phase bottleneck detection
    - **Property 13: Dominant phase bottleneck detection**
    - **Validates: Requirements 4.1**
  
  - [x] 6.9 Write property test for poor scaling recommendations
    - **Property 14: Poor scaling recommendations**
    - **Validates: Requirements 4.2**
  
  - [x] 6.10 Write property test for solver bottleneck recommendations
    - **Property 16: Solver bottleneck recommendations**
    - **Validates: Requirements 4.4**
  
  - [x] 6.11 Write unit tests for bottleneck detector
    - Test no bottlenecks edge case
    - Test recommendation priority assignment
    - Test JSON output structure
    - Test handling of missing optional inputs
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 7. Checkpoint - Ensure all four scripts work correctly
  - Run all unit tests and property tests
  - Verify JSON output consistency across all scripts
  - Test error handling for all scripts
  - Ask the user if questions arise

- [x] 8. Create SKILL.md documentation
  - [x] 8.1 Write SKILL.md with YAML frontmatter
    - Include name, description, allowed-tools in frontmatter
    - Follow repository conventions from other skills
    - _Requirements: 8.1_
  
  - [x] 8.2 Add Goal, Requirements, and Inputs sections
    - Document Python version and dependencies
    - List inputs needed for each script
    - _Requirements: 8.1_
  
  - [x] 8.3 Add Decision Guidance section
    - Create decision tree for when to use each script
    - Include guidance on choosing thresholds
    - _Requirements: 8.2_
  
  - [x] 8.4 Add Script Outputs and Usage Examples sections
    - Document JSON output fields for each script
    - Include example command-line invocations
    - _Requirements: 8.3_
  
  - [x] 8.5 Add Interpretation Guidance and Error Handling sections
    - Explain how to interpret profiling results
    - Document common error patterns and resolutions
    - _Requirements: 8.2_

- [x] 9. Create reference documentation
  - [x] 9.1 Write `references/profiling_guide.md`
    - Explain profiling concepts (timing, scaling, memory)
    - Describe strong vs weak scaling
    - Provide interpretation guidance for results
    - _Requirements: 8.4_
  
  - [x] 9.2 Write `references/optimization_strategies.md`
    - Document common optimization approaches
    - Map bottleneck types to strategies
    - Include examples for materials science simulations
    - _Requirements: 8.4_

- [x] 10. Create example files and integration tests
  - [x] 10.1 Create example directory structure
    - Create `examples/performance-profiling/` directory
    - Write `examples/performance-profiling/README.md`
    - _Requirements: 8.5_
  
  - [x] 10.2 Create example input files
    - Create `sample_timing_log.txt` with realistic timing data
    - Create `sample_scaling_data.json` with strong and weak scaling examples
    - Create `sample_simulation_params.json` with mesh and field parameters
    - _Requirements: 8.5_
  
  - [x] 10.3 Create example workflow script
    - Write shell script demonstrating complete profiling workflow
    - Show how to chain scripts together
    - Include expected outputs
    - _Requirements: 8.3_
  
  - [x] 10.4 Write integration tests
    - Create `tests/integration/test_performance_profiling_integration.py`
    - Test each script's CLI with example inputs
    - Verify JSON output can be parsed and chained
    - Test cross-platform path handling
    - _Requirements: 5.1, 5.2, 5.3, 5.5, 6.1, 6.4_

- [x] 11. Final checkpoint and validation
  - Run complete test suite (unit + integration + property tests)
  - Verify all scripts work on sample data
  - Check documentation completeness
  - Verify cross-platform compatibility (if possible)
  - Ask the user if questions arise

## Notes

- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end workflows and CLI interfaces
