# materials-simulation-skills

Open-source Agent Skills for computational materials science and numerical
simulation workflows.

## What are skills?
Skills are folders of instructions, scripts, and resources that agents can
discover and use. Write once, use everywhere.

Each skill includes:
- `SKILL.md` with YAML frontmatter (name + description) and instructions
- `scripts/` for deterministic workflows
- `references/` for domain details loaded on demand

The agent discovers skills by name/description and loads the `SKILL.md` only
when the skill triggers. Scripts are executed directly for reliability.

## What's included

### Core Numerical Skills (`skills/core-numerical/`)
| Skill | Description |
|-------|-------------|
| `numerical-stability` | CFL analysis, von Neumann stability, stiffness detection |
| `numerical-integration` | Integrator selection, error norms, adaptive stepping |
| `linear-solvers` | Solver selection, preconditioner advice, convergence diagnostics |
| `time-stepping` | Time step planning, output scheduling, checkpointing |
| `differentiation-schemes` | Scheme selection, stencil generation, truncation error |
| `mesh-generation` | Grid sizing, mesh quality metrics |

### Simulation Workflow Skills (`skills/simulation-workflow/`)
| Skill | Description |
|-------|-------------|
| `simulation-validator` | Pre-flight checks, runtime monitoring, post-flight validation |
| `parameter-optimization` | DOE sampling, optimizer selection, sensitivity analysis |
| `simulation-orchestrator` | Parameter sweeps, campaign management, result aggregation |
| `post-processing` | Field extraction, time series analysis, statistics, derived quantities |

### Additional Resources
- Examples for each skill in `examples/`
- Comprehensive unit and integration tests in `tests/`
- CI/CD pipeline for cross-platform testing (Python 3.10-3.12)

## Using the skills
1. Mention the skill by name in your request, or ask a task that matches its
   description.
2. Run the scripts directly for reproducible outputs.
3. Optionally install skills into your agent's global skills directory for
   reuse across projects.

Example:
```text
Use numerical-stability to check a proposed dt for my phase-field run.
```

## Compatibility
This repo follows the Agent Skills standard, originating with [Anthropic](https://anthropic.com),
and is designed to work with Claude Code, Codex-style agents, and any tool that
supports `SKILL.md`-based skills.

## Quick start
Run the full test suite:
```bash
python3 -m unittest discover -s tests
```

Browse and run examples:
```bash
cat examples/README.md
```

## Repository layout
```
skills/              # Skill packages (SKILL.md, scripts, references)
examples/            # Runnable CLI examples
tests/               # Unit + integration tests
```

## Acknowledgements
- Agent Skills standard: https://agentskills.io
- Reference implementation: https://github.com/agentskills/agentskills

