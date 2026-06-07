# Materials Simulation Skills

[![CI](https://github.com/HeshamFS/materials-simulation-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/HeshamFS/materials-simulation-skills/actions/workflows/ci.yml)
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
  - [Verification & Validation Skills](#verification--validation-skills-skillsverification-validation)
  - [Data Management Skills](#data-management-skills-skillsdata-management)
  - [Robustness Skills](#robustness-skills-skillsrobustness)
  - [Ontology Skills](#ontology-skills-skillsontology)
- [How Skills Work](#how-skills-work)
- [Security](#security)
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

**23 skills** | **73 scripts** | **956 tests** | **96 eval cases** | **366 assertions** | Cross-platform CI on Python 3.10-3.12

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
| `workflow-engine-mapper` | Map simulations onto jobflow, atomate2, AiiDA, pyiron, or simpler scripts with DAG and provenance guidance |
| `md-analysis-planner` | Plan MD post-processing for RDF, MSD/diffusion, VACF/VDOS, coordination, stress-strain, and equilibration checks |

### HPC Deployment Skills (`skills/hpc-deployment/`)

Deployment and job submission tooling for running simulations on HPC systems.

| Skill | What it does |
|-------|-------------|
| `slurm-job-script-generator` | Generate `sbatch` scripts, sanity-check resource requests, and standardize `#SBATCH` directives |
| `hpc-runtime-doctor` | Diagnose module, MPI/OpenMP/GPU, scheduler, scratch, restart, walltime, and resource mismatch issues |

### Verification & Validation Skills (`skills/verification-validation/`)

Code verification, benchmark selection, and validation reporting.

| Skill | What it does |
|-------|-------------|
| `benchmark-and-mms-planner` | Plan manufactured solutions, canonical benchmarks, refinement protocols, uncertainty propagation, and pass/fail reports |

### Data Management Skills (`skills/data-management/`)

Reproducibility and FAIR packaging for simulation campaigns.

| Skill | What it does |
|-------|-------------|
| `fair-simulation-packager` | Create metadata manifests with units, engine versions, hashes, structure identifiers, provenance, and repository-friendly fields |

### Robustness Skills (`skills/robustness/`)

Failure diagnosis and retry planning across simulation engines.

| Skill | What it does |
|-------|-------------|
| `simulation-failure-triage` | Build retry ladders for nonconvergence, NaN/Inf, exploding energies, unstable timesteps, pressure blow-up, bad potentials, and incomplete runs |

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
        stability_criteria.md
        common_pitfalls.md
        scheme_catalog.md
    evals/                # Evaluation suite per agentskills.io spec
        evals.json        # Test cases with prompts, assertions, expected outputs
    CHANGELOG.md          # Version history
```

1. **Discovery** -- The agent sees each skill's name and description at startup (~100 tokens per skill)
2. **Activation** -- When a task matches, the agent loads the full `SKILL.md` with decision guidance, workflows, and CLI examples
3. **Execution** -- Scripts run as subprocesses with `--json` output for structured, parseable results

All scripts are standalone CLI tools with `--help`, a pure-function core for testing, and consistent error handling (exit code 2 for bad input, 1 for runtime errors).

---

## Security

All skills are hardened against the [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/), with dedicated validation and edge-case tests. Key safeguards:

- **Tool access is explicit** -- Skills that only inspect or write files avoid `Bash`; script-bearing skills declare `Bash` and keep executable behavior inside reviewed Python CLIs
- **Input validation at every boundary** -- Numeric parameters are bounds-checked and validated as finite; string inputs (parameter names, field names, term names) are validated against regex allowlists
- **Safe file loading** -- All JSON/CSV/NPY loaders enforce file size limits (100-500 MB) and structure validation (dict root required); `np.load()` uses `allow_pickle=False`
- **No `eval()`/`exec()`** -- Region condition parsing uses strict regex matching, never dynamic code execution
- **Prompt injection resistance** -- String values extracted from external files are truncated and stripped of control characters before surfacing to the agent; phase names from logs are sanitized
- **Command construction safety** -- `shlex.quote()` escapes paths interpolated into shell commands; command templates are validated against a shell-operator denylist
- **ReDoS prevention** -- User-supplied regex patterns are length-capped and checked for catastrophic backtracking constructs

Each skill documents its specific safeguards in a **Security** section within its `SKILL.md`, with standardized subsections for Input Validation, File Access, Tool Restrictions, and Safety Measures.

### Security Risk Tiers

Every skill is classified by its tool access surface:

| Tier | Criteria | Skills |
|------|----------|-------|
| **HIGH** | Has `Bash` (can execute scripts) | 15 skills — numerical-stability, time-stepping, convergence-study, differentiation-schemes, nonlinear-solvers, ontology-explorer, ontology-validator, simulation-validator, slurm-job-script-generator, benchmark-and-mms-planner, workflow-engine-mapper, fair-simulation-packager, md-analysis-planner, hpc-runtime-doctor, simulation-failure-triage |
| **MEDIUM** | Has `Write` but no `Bash` | 7 skills — linear-solvers, mesh-generation, numerical-integration, parameter-optimization, performance-profiling, post-processing, simulation-orchestrator |
| **LOW** | Read/Grep/Glob only | 1 skill — ontology-mapper |

---

## Quality & Evaluation

Every skill includes an evaluation suite (`evals/evals.json`) following the [agentskills.io evaluation spec](https://agentskills.io/skill-creation/evaluating-skills). Each suite contains 4-5 test cases with realistic prompts, expected outputs, and verifiable assertions.

**Current metrics:** 96 eval test cases | 366 assertions | All 23 skills evaluated

The CI pipeline validates:
- SKILL.md frontmatter (name, description < 1024 chars, metadata block)
- Eval suite completeness (every skill has evals.json with ≥ 3 test cases)
- Security section presence (all skills must have `## Security`)
- Changelog existence (all skills must have CHANGELOG.md)

---

## Quick Start

### Install

```bash
git clone https://github.com/HeshamFS/materials-simulation-skills.git
cd materials-simulation-skills
pip install -e ".[dev]"
```

### Use the helper CLI

```bash
mss list --json
mss validate --json
mss run numerical-stability cfl_checker -- --dx 0.01 --dt 0.001 --velocity 2.0 --json
mss install --agent codex --scope project --skill numerical-stability
```

### Run the test suite

```bash
python -m pytest tests/ -v --tb=short          # All 956 tests
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
    simulation-workflow/     # 7 skills: validation, optimization, orchestration, workflow mapping, ...
    hpc-deployment/          # 2 skills: SLURM generation and runtime diagnosis
    verification-validation/ # 1 skill: MMS and benchmark planning
    data-management/         # 1 skill: FAIR simulation packaging
    robustness/              # 1 skill: simulation failure triage
    ontology/                # 3 skills: ontology exploration, mapping, validation
    <each-skill>/
        SKILL.md             # Instructions + YAML frontmatter (with metadata block)
        scripts/             # Python CLI tools with --json output
        references/          # Domain knowledge documents
        evals/evals.json     # Evaluation suite (prompts, assertions)
        CHANGELOG.md         # Version history
tests/
    unit/                    # Pure-function tests via load_module()
    integration/             # Subprocess + JSON schema validation
    fixtures/                # Sample data files for CI smoke tests
materials_simulation_skills/
    cli.py                   # Installable mss helper CLI
tools/
    validate_skills.py       # Repo quality validation
    update_metrics.py        # README metric computation
.github/
    workflows/ci.yml         # Cross-platform CI + quality validation
    ISSUE_TEMPLATE/          # Bug reports, skill proposals
    PULL_REQUEST_TEMPLATE.md # PR checklist
```

---

## Contributing

We welcome contributions of all kinds -- new skills, bug fixes, documentation, and tests. The project is designed to grow from 23 skills across 7 active categories into a broader collection spanning materials physics, simulation patterns, HPC deployment, and more.

See **[CONTRIBUTING.md](CONTRIBUTING.md)** for:
- Step-by-step guide to creating a new skill
- Script and test templates
- Skill taxonomy and open categories for community contributions
- PR guidelines and checklists

---

## Star History

<a href="https://www.star-history.com/?repos=HeshamFS%2Fmaterials-simulation-skills&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=HeshamFS/materials-simulation-skills&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=HeshamFS/materials-simulation-skills&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=HeshamFS/materials-simulation-skills&type=date&legend=top-left" />
 </picture>
</a>

## License

[Apache 2.0](LICENSE)

## Acknowledgements

- [Agent Skills standard](https://agentskills.io) -- Open specification for portable agent capabilities
- [Anthropic](https://anthropic.com) -- Original developer of the Agent Skills format
- [agentskills/agentskills](https://github.com/agentskills/agentskills) -- Reference implementation and validation library
