# Requirements Document: Performance Profiling Skill

## Introduction

The Performance Profiling Skill provides computational materials scientists with tools to identify performance bottlenecks, analyze scaling behavior, estimate memory requirements, and receive optimization recommendations for their simulations. This skill enables users to understand where computational resources are being spent and how to improve simulation efficiency.

## Glossary

- **System**: The Performance Profiling Skill implementation
- **User**: A computational materials scientist running simulations
- **Simulation_Log**: A text file containing timestamped output from a simulation run
- **Timing_Data**: Extracted information about how long different simulation phases took
- **Scaling_Data**: Performance measurements from multiple simulation runs with varying problem sizes or processor counts
- **Strong_Scaling**: Performance analysis where problem size is fixed and processor count varies
- **Weak_Scaling**: Performance analysis where problem size per processor is fixed and processor count varies
- **Memory_Profile**: Estimated or measured memory usage for a simulation
- **Bottleneck**: A computational phase or operation that limits overall performance
- **Optimization_Strategy**: A recommended approach to improve simulation performance

## Requirements

### Requirement 1: Timing Analysis

**User Story:** As a user, I want to extract timing information from simulation logs, so that I can identify which phases of my simulation consume the most time.

#### Acceptance Criteria

1. WHEN a valid simulation log file is provided, THE System SHALL parse the log and extract all timing information
2. WHEN timing data is extracted, THE System SHALL identify the slowest computational phases
3. WHEN multiple timing entries exist for the same phase, THE System SHALL aggregate them (sum, mean, min, max)
4. WHEN timing data is incomplete or malformed, THE System SHALL report warnings and continue processing valid entries
5. THE System SHALL output timing analysis results in JSON format
6. WHEN no timing information is found, THE System SHALL return an empty timing report with appropriate status

### Requirement 2: Scaling Analysis

**User Story:** As a user, I want to analyze scaling behavior from multiple simulation runs, so that I can understand how my simulation performs with different problem sizes and processor counts.

#### Acceptance Criteria

1. WHEN scaling data from multiple runs is provided, THE System SHALL compute strong scaling efficiency
2. WHEN scaling data from multiple runs is provided, THE System SHALL compute weak scaling efficiency
3. WHEN computing scaling efficiency, THE System SHALL use the smallest configuration as the baseline
4. WHEN scaling data is provided, THE System SHALL identify the processor count where efficiency drops below 70%
5. THE System SHALL output scaling analysis results in JSON format
6. WHEN insufficient data points are provided (fewer than 2), THE System SHALL report an error

### Requirement 3: Memory Profiling

**User Story:** As a user, I want to estimate memory requirements from simulation parameters, so that I can plan resource allocation and avoid out-of-memory failures.

#### Acceptance Criteria

1. WHEN simulation parameters are provided, THE System SHALL estimate memory usage for the main data structures
2. WHEN estimating memory, THE System SHALL account for mesh size, field variables, and solver workspace
3. WHEN memory estimates are computed, THE System SHALL provide both per-process and total memory requirements
4. WHEN memory estimates exceed available system memory, THE System SHALL issue a warning
5. THE System SHALL output memory profile results in JSON format
6. WHEN required parameters are missing, THE System SHALL report which parameters are needed

### Requirement 4: Bottleneck Detection and Optimization Recommendations

**User Story:** As a user, I want to receive actionable optimization recommendations based on profiling analysis, so that I can improve my simulation performance.

#### Acceptance Criteria

1. WHEN timing analysis identifies a dominant phase (>50% of total time), THE System SHALL flag it as a bottleneck
2. WHEN scaling efficiency is poor (<70%), THE System SHALL recommend investigating communication overhead or load imbalance
3. WHEN memory usage is high (>80% of available), THE System SHALL recommend memory reduction strategies
4. WHEN solver iterations dominate runtime, THE System SHALL recommend preconditioner tuning or tolerance adjustment
5. THE System SHALL output recommendations in JSON format with priority levels (high, medium, low)
6. WHEN no bottlenecks are detected, THE System SHALL report that performance appears balanced

### Requirement 5: Cross-Platform Compatibility

**User Story:** As a user, I want the profiling tools to work on any platform, so that I can use them regardless of my operating system.

#### Acceptance Criteria

1. THE System SHALL run on Linux operating systems
2. THE System SHALL run on macOS operating systems
3. THE System SHALL run on Windows operating systems
4. THE System SHALL use only Python standard library or widely available packages
5. THE System SHALL handle platform-specific path separators correctly

### Requirement 6: JSON Output Format

**User Story:** As a developer integrating this skill, I want all scripts to output structured JSON, so that I can automate workflows and parse results programmatically.

#### Acceptance Criteria

1. WHEN the --json flag is provided, THE System SHALL output valid JSON to stdout
2. WHEN outputting JSON, THE System SHALL include an "inputs" section documenting what parameters were used
3. WHEN outputting JSON, THE System SHALL include a "results" or "report" section with analysis findings
4. WHEN errors occur, THE System SHALL output error information in JSON format if --json flag is set
5. THE System SHALL ensure all JSON output is properly formatted and parseable

### Requirement 7: Command-Line Interface

**User Story:** As a user, I want clear command-line interfaces for all profiling scripts, so that I can easily run analyses with appropriate parameters.

#### Acceptance Criteria

1. WHEN a script is invoked with --help, THE System SHALL display usage information and parameter descriptions
2. WHEN required parameters are missing, THE System SHALL display an error message indicating which parameters are needed
3. WHEN invalid parameter values are provided, THE System SHALL display an error message with valid ranges or formats
4. THE System SHALL use consistent parameter naming across all scripts
5. THE System SHALL provide sensible default values for optional parameters

### Requirement 8: Documentation and Examples

**User Story:** As a user learning to use this skill, I want comprehensive documentation and examples, so that I can quickly understand how to apply it to my simulations.

#### Acceptance Criteria

1. THE System SHALL provide a SKILL.md file with YAML frontmatter following repository conventions
2. WHEN a user reads SKILL.md, THE System SHALL provide decision guidance for when to use each script
3. THE System SHALL include example command-line invocations for common use cases
4. THE System SHALL provide reference documentation explaining profiling concepts and interpretation
5. THE System SHALL include example input files and expected outputs in the examples/ directory
