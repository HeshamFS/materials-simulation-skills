# Materials Simulation Skills

[![CI](https://github.com/heshamfs/materials-simulation-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/heshamfs/materials-simulation-skills/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-standard-orange.svg)](https://agentskills.io)
[![Python 3.10-3.12](https://img.shields.io/badge/Python-3.10--3.12-blue.svg)](https://www.python.org/)

**Open-source [Agent Skills](https://agentskills.io) for computational materials science and numerical simulation workflows.**

Give your AI coding agent domain expertise in numerical methods, simulation best practices, and scientific computing -- without re-explaining the same concepts every session. Skills are portable across Claude Code, Codex, Gemini CLI, Cursor, VS Code Copilot, and [20+ other compatible tools](https://agentskills.io).

---

## Table of Contents

- [The Problem](#the-problem)
- [The Solution](#the-solution)
- [What's Inside](#whats-inside)
  - [Core Numerical Skills](#core-numerical-skills-skillscore-numerical)
  - [Simulation Workflow Skills](#simulation-workflow-skills-skillssimulation-workflow)
  - [HPC Deployment Skills](#hpc-deployment-skills-skillshpc-deployment)
  - [Ontology Skills](#ontology-skills-skillsontology)
- [How Skills Work](#how-skills-work)
- [Quick Start](#quick-start)
- [Adding Skills to Your Agent](#adding-skills-to-your-agent)
  - [Claude Code](#claude-code)
  - [Gemini CLI](#gemini-cli)
  - [OpenAI Codex](#openai-codex)
  - [VS Code / GitHub Copilot](#vs-code--github-copilot)
  - [Cursor](#cursor)
  - [Other Agents](#other-agents)
- [Repository Layout](#repository-layout)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## The Problem

Simulation engineers repeat the same guidance to AI agents constantly: *"Check the CFL number before running," "Use Richardson extrapolation for grid convergence," "Exit code 2 means bad input."* General-purpose agents lack the domain knowledge to run reliable numerical simulations without heavy hand-holding.

## The Solution

This project packages that domain knowledge into **skills** -- structured folders of instructions, scripts, and references that agents discover automatically and load on demand. Each skill teaches an agent a specific simulation competency, backed by validated Python scripts that produce reproducible results.

```text
You: Check if dt=0.001 is stable for my advection problem with v=2.0 m/s and dx=0.01.

Agent: I'll use the numerical-stability skill to check this.
       [runs cfl_checker.py --dx 0.01 --dt 0.001 --velocity 2.0 --json]

       CFL number = 0.2 (limit: 1.0) -- stable.
       Recommended max dt = 0.005 with safety factor 1.0.
```

No prompt engineering. No copy-pasting formulas. The agent finds the right skill, runs the script, and interprets the results.

---

## What's Inside

**17 skills** | **67 scripts** | **857 tests** | Cross-platform CI on Python 3.10-3.12

### Core Numerical Skills (`skills/core-numerical/`)

Foundational numerical methods and analysis tools.

| Skill | What it does |
|-------|-------------|
| `numerical-stability` | CFL/Fourier analysis, von Neumann stability, stiffness detection, matrix conditioning |
| `time-stepping` | Time integrator selection, adaptive step-size control, output scheduling |
| `mesh-generation` | Mesh quality metrics (aspect ratio, skewness, orthogonality), refinement guidance |
| `convergence-study` | Grid/time convergence analysis, Richardson extrapolation, GCI calculation |
| `numerical-integration` | Quadrature rule selection, error estimation, adaptive stepping |
| `differentiation-schemes` | Finite difference stencil generation, truncation error analysis, scheme comparison |
| `linear-solvers` | Iterative/direct solver selection, preconditioner advice, convergence diagnostics |
| `nonlinear-solvers` | Newton/quasi-Newton/fixed-point selection, globalization strategies, convergence diagnostics |

### Simulation Workflow Skills (`skills/simulation-workflow/`)

End-to-end simulation management and automation.

| Skill | What it does |
|-------|-------------|
| `simulation-validator` | Pre-flight checks, runtime log monitoring, post-flight validation |
| `parameter-optimization` | DOE sampling (LHS, factorial), optimizer selection, sensitivity analysis |
| `simulation-orchestrator` | Parameter sweeps, batch campaign management, result aggregation |
| `post-processing` | Field extraction, time series analysis, derived quantity computation |
| `performance-profiling` | Timing analysis, scaling studies, memory profiling, bottleneck detection |

### HPC Deployment Skills (`skills/hpc-deployment/`)

Deployment and job submission tooling for running simulations on HPC systems.

| Skill | What it does |
|-------|-------------|
| `slurm-job-script-generator` | Generate `sbatch` scripts, sanity-check resource requests, and standardize `#SBATCH` directives |

### Ontology Skills (`skills/ontology/`)

Materials science ontology understanding, mapping, and validation.

| Skill | What it does |
|-------|-------------|
| `ontology-explorer` | Parse OWL/XML ontologies, browse class hierarchies, look up properties, search concepts (CMSO, ASMO, OCDO ecosystem) |
| `ontology-mapper` | Map natural-language materials terms and crystal parameters to ontology classes and properties (CMSO, ASMO) |
| `ontology-validator` | Validate annotations against ontology constraints, check completeness, verify relationship domain/range |

---

## How Skills Work

Skills follow the open [Agent Skills standard](https://agentskills.io/specification). Each skill is a folder with three tiers of content, loaded progressively to keep context efficient:

```
skills/core-numerical/numerical-stability/
    SKILL.md              # Instructions + YAML metadata (loaded when skill triggers)
    scripts/              # Python CLI tools (executed for reproducible results)
        cfl_checker.py
        von_neumann_analyzer.py
        matrix_condition.py
        stiffness_detector.py
    references/           # Deep domain knowledge (loaded only when needed)
        stability_reference.md
```

1. **Discovery** -- The agent sees each skill's name and description at startup (~100 tokens per skill)
2. **Activation** -- When a task matches, the agent loads the full `SKILL.md` with decision guidance, workflows, and CLI examples
3. **Execution** -- Scripts run as subprocesses with `--json` output for structured, parseable results

All scripts are standalone CLI tools with `--help`, a pure-function core for testing, and consistent error handling (exit code 2 for bad input, 1 for runtime errors).

---

## Quick Start

### Install

```bash
git clone https://github.com/heshamfs/materials-simulation-skills.git
cd materials-simulation-skills
pip install -r requirements-dev.txt
```

### Run the test suite

```bash
python -m pytest tests/ -v --tb=short          # All 857 tests
python -m pytest tests/unit -v --tb=short       # Unit tests only
python -m pytest tests/integration -v           # Integration tests only
```

---

## Adding Skills to Your Agent

These skills follow the open [Agent Skills standard](https://agentskills.io) and work across 20+ AI coding tools. Choose your agent below.

### Claude Code

Copy individual skills (or the whole `skills/` tree) into your personal or project skills directory:

```bash
# Personal (available across all projects)
cp -r skills/core-numerical/numerical-stability ~/.claude/skills/numerical-stability

# Project-level (committed to version control)
cp -r skills/core-numerical/numerical-stability .claude/skills/numerical-stability
```

Or clone the whole repo and point Claude Code at it with `--add-dir`:

```bash
claude --add-dir /path/to/materials-simulation-skills/skills
```

Verify with: `What skills are available?` or type `/` to see skills in the autocomplete menu.

See the [Claude Code skills docs](https://code.claude.com/docs/en/skills) for more details.

### Gemini CLI

Install directly from the repo, or copy skills into your Gemini skills directory:

```bash
# User-scoped (available across all workspaces)
cp -r skills/core-numerical/numerical-stability ~/.gemini/skills/numerical-stability

# Workspace-scoped (project-specific)
cp -r skills/core-numerical/numerical-stability .gemini/skills/numerical-stability
```

Verify with: `gemini skills list`

See the [Gemini CLI skills docs](https://geminicli.com/docs/cli/skills/) for more details.

### OpenAI Codex

Copy skills into one of the Codex skills directories:

```bash
# User-scoped
cp -r skills/core-numerical/numerical-stability ~/.agents/skills/numerical-stability

# Repository-scoped
cp -r skills/core-numerical/numerical-stability .agents/skills/numerical-stability
```

Restart Codex after adding skills. Use `/skills` or `$` to invoke skills by name.

See the [Codex skills docs](https://developers.openai.com/codex/skills) for more details.

### VS Code / GitHub Copilot

Copy skills into your workspace or personal skills directory:

```bash
# Workspace (committed to version control)
cp -r skills/core-numerical/numerical-stability .github/skills/numerical-stability

# Personal (across all workspaces)
cp -r skills/core-numerical/numerical-stability ~/.copilot/skills/numerical-stability
```

Type `/skills` in the chat input to see and invoke available skills.

See the [VS Code skills docs](https://code.visualstudio.com/docs/copilot/customization/agent-skills) for more details.

### Cursor

Copy skills into a `skills/` directory at your project root:

```bash
cp -r skills/core-numerical/numerical-stability skills/numerical-stability
```

Cursor's MCP server auto-discovers skills from the `skills/` directory.

### Other Agents

Any agent that supports the [Agent Skills standard](https://agentskills.io) can use these skills. The general pattern:

1. Copy the skill directory (containing `SKILL.md`, `scripts/`, `references/`) into your agent's skills folder
2. The agent discovers the skill by its `name` and `description` in the YAML frontmatter
3. Mention the skill by name or ask a task that matches its description

```text
Use numerical-stability to check a proposed dt for my phase-field run.
```

The agent loads the skill's instructions, runs the appropriate scripts, and interprets the results.

---

## Repository Layout

```
skills/
    core-numerical/          # 8 skills: stability, solvers, meshing, convergence, ...
    simulation-workflow/     # 5 skills: validation, optimization, orchestration, ...
    hpc-deployment/          # 1 skill: SLURM job script generation
    ontology/                # 3 skills: ontology exploration, mapping, validation
tests/
    unit/                    # Pure-function tests via load_module()
    integration/             # Subprocess + JSON schema validation
    fixtures/                # Sample data files for CI smoke tests
.github/
    workflows/ci.yml         # Cross-platform CI (Ubuntu, Windows, macOS)
    ISSUE_TEMPLATE/          # Bug reports, skill proposals
    PULL_REQUEST_TEMPLATE.md # PR checklist
```

---

## Contributing

We welcome contributions of all kinds -- new skills, bug fixes, documentation, and tests. The project is designed to grow from 17 skills across 4 categories into a broader collection spanning materials physics, verification & validation, HPC deployment, and more.

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for:
- Step-by-step guide to creating a new skill
- Script and test templates
- Skill taxonomy and open categories for community contributions
- PR guidelines and checklists

---

## License

[Apache 2.0](LICENSE)

## Acknowledgements

- [Agent Skills standard](https://agentskills.io) -- Open specification for portable agent capabilities
- [Anthropic](https://anthropic.com) -- Original developer of the Agent Skills format
- [agentskills/agentskills](https://github.com/agentskills/agentskills) -- Reference implementation and validation library
