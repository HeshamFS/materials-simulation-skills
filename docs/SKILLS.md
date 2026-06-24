# Skill catalog

The full list of skills. For a machine-readable version (with versions, security
tiers, eval coverage, and bundles) see [`skills_index.json`](../skills_index.json),
or run `mss list` / `mss index`.

**24 skills** across 8 categories.

## Core Numerical (`skills/core-numerical/`)

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

## Simulation Workflow (`skills/simulation-workflow/`)

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

## HPC Deployment (`skills/hpc-deployment/`)

Deployment and job submission tooling for running simulations on HPC systems.

| Skill | What it does |
|-------|-------------|
| `slurm-job-script-generator` | Generate `sbatch` scripts, sanity-check resource requests, and standardize `#SBATCH` directives |
| `hpc-runtime-doctor` | Diagnose module, MPI/OpenMP/GPU, scheduler, scratch, restart, walltime, and resource mismatch issues |

## Verification & Validation (`skills/verification-validation/`)

| Skill | What it does |
|-------|-------------|
| `benchmark-and-mms-planner` | Plan manufactured solutions, canonical benchmarks, refinement protocols, uncertainty propagation, and pass/fail reports |

## Data Management (`skills/data-management/`)

| Skill | What it does |
|-------|-------------|
| `fair-simulation-packager` | Create metadata manifests with units, engine versions, hashes, structure identifiers, provenance, and repository-friendly fields |

## Robustness (`skills/robustness/`)

| Skill | What it does |
|-------|-------------|
| `simulation-failure-triage` | Build retry ladders for nonconvergence, NaN/Inf, exploding energies, unstable timesteps, pressure blow-up, bad potentials, and incomplete runs |

## Ontology (`skills/ontology/`)

Materials science ontology understanding, mapping, and validation.

| Skill | What it does |
|-------|-------------|
| `ontology-explorer` | Parse OWL/XML ontologies, browse class hierarchies, look up properties, search concepts (CMSO, ASMO, OCDO ecosystem) |
| `ontology-mapper` | Map natural-language materials terms and crystal parameters to ontology classes and properties (CMSO, ASMO) |
| `ontology-validator` | Validate annotations against ontology constraints, check completeness, verify relationship domain/range |

## Meta (`skills/meta/`)

Tooling skills that operate on skills themselves.

| Skill | What it does |
|-------|-------------|
| `skill-evaluator` | Rigorously evaluate any Agent Skill end-to-end across **any** coding-agent CLI (Claude Code, Codex, Antigravity, Cursor, Copilot, Amp, opencode, Grok): deterministic `script_checks`, trigger/discovery testing, and with-skill-vs-baseline quality benchmarking with the pass-rate delta |

---

## How skills work

Skills follow the open [Agent Skills standard](https://agentskills.io/specification).
Each skill is a folder with three tiers of content, loaded progressively to keep
context efficient:

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
        evals.json        # Test cases with prompts, assertions, expected outputs, script_checks
    CHANGELOG.md          # Version history
```

1. **Discovery** — the agent sees each skill's name and description at startup (~100 tokens per skill).
2. **Activation** — when a task matches, the agent loads the full `SKILL.md` with decision guidance, workflows, and CLI examples.
3. **Execution** — scripts run as subprocesses with `--json` output for structured, parseable results.

All scripts are standalone CLI tools with `--help`, a pure-function core for
testing, and consistent error handling (exit code 2 for bad input, 1 for runtime
errors). See [PROTOCOL.md](PROTOCOL.md) for the full conventions.

---

## Repository layout

```
skills/
    core-numerical/          # 8 skills: stability, solvers, meshing, convergence, ...
    simulation-workflow/     # 7 skills: validation, optimization, orchestration, ...
    hpc-deployment/          # 2 skills: SLURM generation and runtime diagnosis
    verification-validation/ # 1 skill: MMS and benchmark planning
    data-management/         # 1 skill: FAIR simulation packaging
    robustness/              # 1 skill: simulation failure triage
    ontology/                # 3 skills: ontology exploration, mapping, validation
    meta/                    # 1 skill: skill-evaluator (agent-agnostic eval harness)
    <each-skill>/
        SKILL.md  scripts/  references/  evals/evals.json  CHANGELOG.md
tests/
    unit/                    # Pure-function tests via load_module()
    integration/             # Subprocess + JSON schema + protocol/index conformance
    fixtures/                # Sample data files for CI smoke tests
materials_simulation_skills/ # The `mss` helper CLI (list/validate/eval/index/install)
tools/                       # validate_skills.py, run_skill_evals.py, build_index.py, update_metrics.py
docs/                        # PROTOCOL, EVAL_HARNESS, EVALUATION_METHODOLOGY, INSTALL, SECURITY, SKILLS
.github/workflows/ci.yml     # Cross-platform CI + quality/eval/index gates
skills_index.json            # Machine-readable catalog (generated)
.claude-plugin/marketplace.json  # Claude Code plugin marketplace (generated)
```
