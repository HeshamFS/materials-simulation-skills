# Post-Processing Examples

This directory contains examples demonstrating the post-processing skill.

## Files

- `field_output.json` - Example 2D field data (phase-field and concentration)
- `history.json` - Example time series data (energy, residual, mass)
- `reference_profile.json` - Reference data for comparison
- `run_field_extractor.sh` - Field extraction examples
- `run_time_series.sh` - Time series analysis examples
- `run_statistics.sh` - Statistical analysis examples
- `run_derived_quantities.sh` - Derived quantities examples

## Quick Start

```bash
# Extract field data
bash examples/post-processing/run_field_extractor.sh

# Analyze time series
bash examples/post-processing/run_time_series.sh

# Compute statistics
bash examples/post-processing/run_statistics.sh

# Compute derived quantities
bash examples/post-processing/run_derived_quantities.sh
```

## Individual Script Examples

### Field Extractor

```bash
# List available fields
python skills/simulation-workflow/post-processing/scripts/field_extractor.py \
    --input examples/post-processing/field_output.json \
    --list --json

# Extract specific field
python skills/simulation-workflow/post-processing/scripts/field_extractor.py \
    --input examples/post-processing/field_output.json \
    --field phi --json
```

### Time Series Analyzer

```bash
# Analyze energy convergence
python skills/simulation-workflow/post-processing/scripts/time_series_analyzer.py \
    --input examples/post-processing/history.json \
    --quantity energy --json

# Detect steady state
python skills/simulation-workflow/post-processing/scripts/time_series_analyzer.py \
    --input examples/post-processing/history.json \
    --quantity residual \
    --detect-steady-state \
    --tolerance 1e-5 --json
```

### Statistical Analyzer

```bash
# Basic statistics
python skills/simulation-workflow/post-processing/scripts/statistical_analyzer.py \
    --input examples/post-processing/field_output.json \
    --field phi --json

# With histogram
python skills/simulation-workflow/post-processing/scripts/statistical_analyzer.py \
    --input examples/post-processing/field_output.json \
    --field phi --histogram --bins 20 --json
```

### Derived Quantities

```bash
# Volume fraction
python skills/simulation-workflow/post-processing/scripts/derived_quantities.py \
    --input examples/post-processing/field_output.json \
    --quantity volume_fraction \
    --field phi --threshold 0.5 --json

# Gradient magnitude
python skills/simulation-workflow/post-processing/scripts/derived_quantities.py \
    --input examples/post-processing/field_output.json \
    --quantity gradient_magnitude \
    --field phi --json

# Total mass
python skills/simulation-workflow/post-processing/scripts/derived_quantities.py \
    --input examples/post-processing/field_output.json \
    --quantity mass \
    --field phi --json
```

### Comparison Tool

```bash
# Compare simulation to reference
python skills/simulation-workflow/post-processing/scripts/comparison_tool.py \
    --simulation examples/post-processing/field_output.json \
    --reference examples/post-processing/reference_profile.json \
    --metric l2_error --json
```

## Use Cases

- **Field Extraction**: Extract specific fields from multi-field output files
- **Time Series Analysis**: Monitor convergence, detect steady state
- **Statistical Analysis**: Compute distributions, detect bimodal phases
- **Derived Quantities**: Calculate volume fractions, interface areas, gradients
- **Comparison**: Validate results against reference/experimental data
