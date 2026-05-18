---
name: parameter-optimization
description: >
  Explore and optimize simulation parameters via design of experiments (DOE),
  sensitivity analysis, and optimizer selection — generate Latin Hypercube,
  quasi-random, or factorial sample plans, rank parameter influence with
  sensitivity scores, recommend Bayesian optimization, CMA-ES, or gradient-
  based methods based on dimension and budget, and fit surrogate models for
  expensive evaluations. Use when calibrating material properties against
  experimental data, planning a parameter sweep, performing uncertainty
  quantification, or choosing an optimization strategy for a simulation
  with a limited evaluation budget, even if the user only says "which
  parameters matter most" or "how do I calibrate my model."
allowed-tools: Read, Write, Grep, Glob
metadata:
  author: HeshamFS
  version: "1.1.0"
  security_tier: medium
  security_reviewed: true
  tested_with:
    - claude-code
    - gemini-cli
    - vs-code-copilot
  eval_cases: 5
  last_reviewed: "2026-03-26"
---

# Parameter Optimization

## Goal

Provide a workflow to design experiments, rank parameter influence, and select optimization strategies for materials simulation calibration.

## Requirements

- Python 3.10+
- No external dependencies (uses Python standard library only)

## Inputs to Gather

Before running any scripts, collect from the user:

| Input | Description | Example |
|-------|-------------|---------|
| Parameter bounds | Min/max for each parameter with units | `kappa: [0.1, 10.0] W/mK` |
| Evaluation budget | Max number of simulations allowed | `50 runs` |
| Noise level | Stochasticity of simulation outputs | `low`, `medium`, `high` |
| Constraints | Feasibility rules or forbidden regions | `kappa + mobility < 5` |

## Decision Guidance

### Choosing a DOE Method

```
Is dimension <= 3 AND full coverage needed?
├── YES → Use factorial
└── NO → Is sensitivity analysis the goal?
    ├── YES → Use quasi-random (preferred; "sobol" is accepted but deprecated)
    └── NO → Use lhs (Latin Hypercube)
```

| Method | Best For | Avoid When |
|--------|----------|------------|
| `lhs` | General exploration, moderate dimensions (3-20) | Need exact grid coverage |
| `sobol` | Sensitivity analysis, uniform coverage | Very high dimensions (>20) |
| `factorial` | Low dimension (<4), need all corners | High dimension (exponential growth) |

### Choosing an Optimizer

```
Is dimension <= 5 AND budget <= 100?
├── YES → Bayesian Optimization
└── NO → Is dimension <= 20?
    ├── YES → CMA-ES
    └── NO → Random Search with screening
```

| Noise Level | Recommendation |
|-------------|----------------|
| Low | Gradient-based if derivatives available, else Bayesian Optimization |
| Medium | Bayesian Optimization with noise model |
| High | Evolutionary algorithms or robust Bayesian Optimization |

## Script Outputs (JSON Fields)

| Script | Output Fields |
|--------|---------------|
| `scripts/doe_generator.py` | `samples`, `method`, `coverage` |
| `scripts/optimizer_selector.py` | `recommended`, `expected_evals`, `notes` |
| `scripts/sensitivity_summary.py` | `ranking`, `notes` |
| `scripts/surrogate_builder.py` | `model_type`, `metrics`, `notes` |

## Workflow

1. **Generate DOE** with `scripts/doe_generator.py`
2. **Run simulations** at DOE sample points (user's responsibility)
3. **Summarize sensitivity** with `scripts/sensitivity_summary.py`
4. **Choose optimizer** using `scripts/optimizer_selector.py`
5. **(Optional)** Fit surrogate with `scripts/surrogate_builder.py`

## CLI Examples

```bash
# Generate 20 LHS samples for 3 parameters
python3 scripts/doe_generator.py --params 3 --budget 20 --method lhs --json

# Rank parameters by sensitivity scores
python3 scripts/sensitivity_summary.py --scores 0.2,0.5,0.3 --names kappa,mobility,W --json

# Get optimizer recommendation for 3D problem with 50 eval budget
python3 scripts/optimizer_selector.py --dim 3 --budget 50 --noise low --json

# Build surrogate model from simulation data
python3 scripts/surrogate_builder.py --x 0,1,2 --y 10,12,15 --model rbf --json
```

## Conversational Workflow Example

**User**: I need to calibrate thermal conductivity and diffusivity for my FEM simulation. I can run about 30 simulations.

**Agent workflow**:
1. Identify 2 parameters → `--params 2`
2. Budget is 30 → `--budget 30`
3. Use LHS for general exploration:
   ```bash
   python3 scripts/doe_generator.py --params 2 --budget 30 --method lhs --json
   ```
4. After user runs simulations and provides outputs, summarize sensitivity:
   ```bash
   python3 scripts/sensitivity_summary.py --scores 0.7,0.3 --names conductivity,diffusivity --json
   ```
5. Recommend optimizer:
   ```bash
   python3 scripts/optimizer_selector.py --dim 2 --budget 30 --noise low --json
   ```

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `params must be positive` | Zero or negative dimension | Ask user for valid parameter count |
| `budget must be positive` | Zero or negative budget | Ask user for realistic simulation budget |
| `method must be lhs, sobol, or factorial` | Invalid method | Use decision guidance to pick valid method |
| `scores must be comma-separated` | Malformed input | Reformat as `0.1,0.2,0.3` |

## Security

### Input Validation
- `sensitivity_summary.py` validates `--names` against `[a-zA-Z_][a-zA-Z0-9_ .-]*` with a 200-char limit, preventing shell metacharacter injection via crafted parameter names
- All numeric list inputs are validated as finite numbers (`NaN`/`Inf` rejected)
- Comma-separated value lists are capped (10,000 for scores, 100,000 for surrogate data) to prevent resource exhaustion
- `doe_generator.py` caps dimension at 1,000 and budget at 1,000,000; `optimizer_selector.py` caps dimension at 100,000 and budget at 10,000,000
- `--method` is validated against a fixed allowlist (`lhs`, `sobol`, `factorial`)
- `--noise` is validated against a fixed allowlist (`low`, `medium`, `high`)
- `--model` (surrogate type) is validated against a fixed allowlist (`rbf`, `linear`, `polynomial`)

### File Access
- Scripts read no external files; all inputs are provided via CLI arguments
- Scripts write only to stdout (JSON output); no files are created unless the agent explicitly uses the Write tool

### Tool Restrictions
- **Read**: Used to inspect script source, references, and user data files
- **Write**: Used to save DOE sample plans, sensitivity rankings, or optimizer recommendations; writes are scoped to the user's working directory
- **Grep/Glob**: Used to locate relevant files and search references
- The skill's `allowed-tools` excludes `Bash` to prevent the agent from executing arbitrary commands when processing user-provided parameter names and constraints

### Safety Measures
- No `eval()`, `exec()`, or dynamic code generation
- All subprocess calls use explicit argument lists (no `shell=True`)
- Reduced tool surface (no Bash) limits the agent to read/write operations only
- Parameter names are sanitized before use, preventing injection via crafted identifiers

## Limitations

- **Not for real-time optimization**: Scripts provide recommendations, not live optimization loops
- **Surrogate is a placeholder**: `surrogate_builder.py` computes basic metrics; replace with actual model for production
- **No automatic simulation execution**: User must run simulations externally and provide results

## References

- `references/doe_methods.md` - Detailed DOE method comparison
- `references/optimizer_selection.md` - Optimizer algorithm details
- `references/sensitivity_guidelines.md` - Sensitivity analysis interpretation
- `references/surrogate_guidelines.md` - Surrogate model selection

## Version History

- **v1.1.0** (2024-12-24): Enhanced documentation, decision guidance, conversational examples
- **v1.0.0**: Initial release with core scripts
