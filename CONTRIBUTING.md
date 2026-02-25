# Contributing to Materials Simulation Skills

Thanks for your interest in contributing! This project provides open-source **Agent Skills** for computational materials science and numerical simulation workflows. Each skill is a structured folder (SKILL.md + scripts + references) that AI agents discover by name and load on demand.

Our goal is to grow from the current 17 skills across 4 categories to approximately **38 skills across 8 categories**, covering everything from core numerical methods to materials physics, HPC deployment, and robustness techniques. Every contribution -- whether a new skill, a bug fix, improved documentation, or better tests -- helps the community build more reliable simulation workflows.

All contributors are expected to follow the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/).

---

## Ways to Contribute

| Contribution | Description | Difficulty |
|-------------|-------------|------------|
| Report a bug | File an issue using the [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) | Beginner |
| Fix a bug | Reproduce the issue, add a test, submit a fix | Beginner |
| Improve documentation | Fix typos, clarify SKILL.md sections, expand references | Beginner |
| Add tests | Increase coverage with unit, integration, or property tests | Intermediate |
| Propose a skill | Open a [skill proposal](.github/ISSUE_TEMPLATE/skill_proposal.md) issue | Intermediate |
| Implement a planned skill | Pick a skill from the [taxonomy](#skill-taxonomy--roadmap) and implement it | Advanced |
| Improve infrastructure | CI workflows, test utilities, cross-platform fixes | Advanced |

---

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/heshamfs/materials-simulation-skills.git
cd materials-simulation-skills
```

### 2. Set Up Your Environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows
pip install -r requirements-dev.txt
```

### 3. Run Tests

```bash
python -m pytest tests/ -v --tb=short       # All tests
python -m pytest tests/unit -v --tb=short    # Unit tests only
python -m pytest tests/integration -v        # Integration tests only
```

### 4. Create a Branch

Use one of these naming conventions:

| Branch prefix | Use for |
|--------------|---------|
| `skill/name` | New skill (e.g. `skill/elasticity-mechanics`) |
| `fix/desc` | Bug fix (e.g. `fix/cfl-nan-handling`) |
| `docs/desc` | Documentation changes |
| `test/desc` | Test additions or improvements |
| `infra/desc` | CI, build, or tooling changes |

---

## Creating a New Skill

### Step 1: Directory Layout

Create the following structure under the appropriate category:

```
skills/{category}/{skill-name}/
    SKILL.md
    scripts/
        your_script.py
    references/
        domain_guide.md
```

The available categories are listed in the [Skill Taxonomy](#skill-taxonomy--roadmap) section.

**Naming rules** (per the [Agent Skills specification](https://agentskills.io/specification)):
- Lowercase letters, numbers, and hyphens only (e.g. `mesh-generation`, `cfl-checker`)
- Max 64 characters, no consecutive hyphens (`--`), cannot start or end with a hyphen
- The `name` field in SKILL.md frontmatter **must match** the directory name
- Must not contain reserved words (`anthropic`, `claude`)

### Step 2: Write SKILL.md

Every SKILL.md starts with YAML frontmatter and contains specific sections. Use this template:

```markdown
---
name: your-skill-name
description: >
  Describes what this skill does and when to use it. Write in third person.
  Include specific keywords that help agents identify relevant tasks.
  Example: "Compute CFL and Fourier numbers for explicit time-stepping schemes.
  Use when selecting time steps, diagnosing numerical blow-up, or checking
  stability criteria for advection-diffusion problems."
allowed-tools: Read, Bash, Write, Grep, Glob
# Optional fields:
# license: Apache-2.0
# compatibility: Requires numpy; designed for Claude Code or similar agents
# metadata:
#   author: your-name
#   version: "1.0"
---

# Your Skill Name

## Goal

What problem does this skill solve? One or two sentences.

## Requirements

- Python 3.8+
- NumPy
- List any other dependencies

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| `param_name` | What it represents | `1.0` |

## Decision Guidance

Help the agent choose between approaches. Use decision trees:

\```
Is condition A true?
+-- YES -> Approach 1
+-- NO  -> Approach 2
\```

## Script Outputs

| Script | Output Key | Description |
|--------|-----------|-------------|
| `your_script.py` | `results.metric` | What it means |

## Workflow

1. Gather inputs from the user
2. Run script with appropriate parameters
3. Interpret results and advise

## CLI Examples

\```bash
python skills/{category}/{skill-name}/scripts/your_script.py \
  --param 1.0 --json
\```

## Conversational Workflow Example

> **User**: I need help with [problem].
>
> **Agent**: I will use the your-skill-name skill. Let me gather some inputs...

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `ValueError: param must be positive` | Negative input | Use a positive value |

## Limitations

- Known limitation 1
- Known limitation 2

## References

- Author, "Title," Journal, Year. DOI: ...
- Relevant textbook or standard

## Version History

- v1 (YYYY-MM-DD): Initial implementation
```

**Notes:**
- The `description` in the frontmatter is critical -- agents use it to decide whether to load the skill. Always write in **third person** and describe both *what* the skill does and *when* to use it
- Keep SKILL.md body **under 500 lines**. The Agent Skills standard uses progressive disclosure: only `name` and `description` are loaded at startup (~100 tokens); the full SKILL.md body is loaded on activation; `references/` and `scripts/` are loaded only when needed
- Keep reference files **one level deep** from SKILL.md -- avoid chains where one reference points to another reference
- The `allowed-tools` field controls which tools the agent can use when the skill is active
- Always use **forward slashes** in file paths (`references/guide.md`), even on Windows

### Step 3: New Skill Checklist

Before submitting your PR, verify every item:

- [ ] Skill directory is under the correct category
- [ ] Directory name matches the `name` field in SKILL.md frontmatter
- [ ] Name follows conventions (lowercase, hyphens, max 64 chars, no reserved words)
- [ ] `SKILL.md` has YAML frontmatter with `name`, `description`, and `allowed-tools`
- [ ] Description is third-person and says both *what* the skill does and *when* to use it
- [ ] `SKILL.md` body is under 500 lines (detailed content goes in `references/`)
- [ ] `SKILL.md` contains all 12 sections (Goal through Version History)
- [ ] At least one script in `scripts/`
- [ ] Scripts use `argparse` with `--help` documentation
- [ ] Scripts support `--json` flag for structured output
- [ ] Scripts have a pure-function core (importable for testing)
- [ ] Scripts reject NaN/Inf inputs with `ValueError`
- [ ] Scripts use exit code 2 for validation errors, exit code 1 for runtime errors
- [ ] Unit tests in `tests/unit/test_{script_name}.py`
- [ ] Integration tests in `tests/integration/`
- [ ] Reference docs placed in `references/` directory
- [ ] Skill added to the top-level `README.md`
- [ ] All file paths use forward slashes (even on Windows)
- [ ] Reference files are one level deep from SKILL.md (no nested chains)
- [ ] All tests pass: `python -m pytest tests/ -v --tb=short`
- [ ] Scripts compile: `python -m py_compile scripts/your_script.py`
- [ ] (Optional) Validate with: `skills-ref validate ./skills/{category}/{skill-name}`

---

## Script Conventions

All scripts are standalone CLI tools. Follow this annotated template:

```python
#!/usr/bin/env python3
"""Short description of what this script computes."""

import argparse
import json
import math
import sys
from typing import Dict, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Describe the script purpose.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--param", type=float, required=True, help="Description")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def compute(param: float) -> Dict[str, object]:
    """Pure function: all logic here, no I/O. This is what tests import."""
    # Validate inputs
    if not math.isfinite(param):
        raise ValueError("param must be finite (no NaN or Inf)")
    if param <= 0:
        raise ValueError("param must be positive")

    # Compute results
    result_value = param * 2  # Replace with real logic

    return {
        "metric": result_value,
        "notes": [],
    }


def main() -> None:
    args = parse_args()
    try:
        result = compute(param=args.param)
    except ValueError as exc:
        if args.json:
            json.dump({"error": str(exc)}, sys.stdout)
            print()
        else:
            print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.json:
        output = {
            "inputs": {"param": args.param},
            "results": result,
        }
        json.dump(output, sys.stdout, indent=2)
        print()
    else:
        print(f"Metric: {result['metric']}")


if __name__ == "__main__":
    main()
```

### Key Rules

- **NumPy only**: Scripts should only require `numpy`. Use `scipy` or `scikit-learn` only when truly necessary and document it
- **Exit codes**: Use `sys.exit(2)` for validation errors (bad input), `sys.exit(1)` for unexpected runtime errors
- **NaN/Inf rejection**: Always check `math.isfinite()` on numeric inputs before computation
- **JSON envelope**: When `--json` is active, output follows `{"inputs": {...}, "results": {...}}`; errors emit `{"error": "message"}`
- **Pure-function core**: The `compute()` function must be importable and testable without CLI parsing
- **No interactive input**: Scripts must work in non-interactive (subprocess) mode

---

## Testing Requirements

Tests live in `tests/` with this structure:

```
tests/
    unit/
        _utils.py           # load_module() helper
        test_your_script.py
    integration/
        _schema.py          # assert_schema() helper
        test_cli_your_skill.py
    fixtures/               # Sample data files for CI smoke tests
```

### Unit Tests

Unit tests import the pure-function core directly using `load_module()`:

```python
import unittest

from tests.unit._utils import load_module


class TestYourScript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "your_script",
            "skills/{category}/{skill-name}/scripts/your_script.py",
        )

    def test_basic_case(self):
        result = self.mod.compute(param=1.0)
        self.assertAlmostEqual(result["metric"], 2.0, places=6)

    def test_validation_error(self):
        with self.assertRaises(ValueError):
            self.mod.compute(param=-1.0)

    def test_nan_rejection(self):
        with self.assertRaises(ValueError):
            self.mod.compute(param=float("nan"))

    def test_inf_rejection(self):
        with self.assertRaises(ValueError):
            self.mod.compute(param=float("inf"))
```

### Integration Tests

Integration tests run scripts as subprocesses and validate JSON output:

```python
import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.integration._schema import assert_schema

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "{category}" / "{skill-name}" / "scripts"


class TestCliYourSkill(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_json_output(self):
        result = self.run_cmd([
            str(SCRIPTS / "your_script.py"),
            "--param", "1.0",
            "--json",
        ])
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        assert_schema(data, {
            "inputs": {"param": float},
            "results": {"metric": (int, float)},
        })

    def test_validation_error_exit_code(self):
        result = self.run_cmd([
            str(SCRIPTS / "your_script.py"),
            "--param", "-1.0",
            "--json",
        ])
        self.assertEqual(result.returncode, 2)
        data = json.loads(result.stdout)
        self.assertIn("error", data)
```

### Property Tests (Optional but Encouraged)

Use `hypothesis` for property-based testing:

```python
import unittest

from hypothesis import given, settings
from hypothesis import strategies as st

from tests.unit._utils import load_module


class TestYourScriptProperties(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "your_script",
            "skills/{category}/{skill-name}/scripts/your_script.py",
        )

    @given(param=st.floats(min_value=0.001, max_value=1e6))
    @settings(max_examples=200)
    def test_output_always_positive(self, param):
        result = self.mod.compute(param=param)
        self.assertGreater(result["metric"], 0)
```

### Running Tests

```bash
# All tests
python -m pytest tests/ -v --tb=short

# Single test file
python -m pytest tests/unit/test_your_script.py -v

# Single test method
python -m pytest tests/unit/test_your_script.py::TestYourScript::test_basic_case -v

# With coverage (if installed)
python -m pytest tests/ --cov=skills --cov-report=term-missing
```

---

## Pull Request Guidelines

### Before Submitting

1. **One skill per PR** -- keep PRs focused and reviewable
2. **Link related issues** -- reference the skill proposal or bug report
3. **All CI checks must pass** -- the PR template includes a checklist
4. **Self-review your diff** -- read through your own changes before requesting review

### What Reviewers Check

- **SKILL.md completeness**: All 12 sections present with useful content
- **Script patterns**: argparse, `--json`, pure-function core, error handling
- **Test coverage**: Unit tests for core logic, integration tests for CLI, edge cases for invalid input
- **Cross-platform compatibility**: No OS-specific paths, commands, or assumptions
- **Documentation**: References in `references/`, README updated

### Review Process

1. A maintainer will review within a few days
2. Address feedback by pushing new commits (do not force-push during review)
3. Once approved, a maintainer will merge the PR

---

## Skill Taxonomy & Roadmap

The project is organized into categories. The first four categories are established with 17 skills; the remaining five are open directions where the community can propose and build new skills over time.

### Overview

| Category | Status | Description |
|----------|--------|-------------|
| core-numerical | 8 skills | Foundational numerical methods and analysis tools |
| simulation-workflow | 5 skills | End-to-end simulation management and automation |
| materials-physics | Open | Material behavior, constitutive models, physical properties |
| verification-validation | Open | Code verification, benchmarking, uncertainty quantification |
| data-management | Open | Data formats, visualization, checkpointing |
| hpc-deployment | 1 skill | Parallel computing, job scheduling, build systems |
| ontology | 3 skills | Materials science ontology exploration, mapping, and validation |
| simulation-patterns | Open | Multi-physics coupling, transient strategies, inverse methods |
| robustness | Open | Handling discontinuities, numerical artifacts, difficult physics |

### core-numerical/ (8 skills)

| Skill | Description |
|-------|-------------|
| numerical-stability | CFL/Fourier checks, von Neumann analysis, stiffness detection |
| time-stepping | Time integrator selection and adaptive step-size control |
| mesh-generation | Mesh quality metrics and refinement guidance |
| convergence-study | Grid/time convergence, Richardson extrapolation, GCI |
| numerical-integration | Quadrature rule selection and error estimation |
| differentiation-schemes | Finite difference stencil selection and truncation error |
| linear-solvers | Iterative/direct solver selection and preconditioning |
| nonlinear-solvers | Newton, quasi-Newton, and fixed-point method configuration |

### simulation-workflow/ (5 skills)

| Skill | Description |
|-------|-------------|
| simulation-validator | Log parsing and simulation health checks |
| parameter-optimization | DOE generation and parameter sensitivity analysis |
| simulation-orchestrator | Parameter sweeps and batch job management |
| post-processing | Field extraction and derived quantity computation |
| performance-profiling | Timing analysis, memory profiling, scaling studies |

### hpc-deployment/ (1 skill)

| Skill | Description |
|-------|-------------|
| slurm-job-script-generator | Generate `sbatch` scripts, sanity-check resource requests, and standardize `#SBATCH` directives |

Contributions welcome: expand this category with scheduler portability (PBS/LSF), MPI decomposition guidance, job arrays, build toolchains, and cluster-friendly profiling workflows.

### ontology/ (3 skills)

| Skill | Description |
|-------|-------------|
| ontology-explorer | Parse OWL/XML ontologies, browse class hierarchies, look up properties, search for concepts |
| ontology-mapper | Map natural-language materials terms and crystal parameters to ontology classes |
| ontology-validator | Validate annotations against ontology constraints, check completeness, verify relationships |

Currently supports CMSO (Computational Material Sample Ontology) from the OCDO ecosystem. Contributions welcome: add support for ASMO (simulation methods), CDCO/PODO/PLDO/LDO (crystallographic defects), SPARQL query capabilities, and JSON-LD/Turtle format support.

### materials-physics/ (open for contributions)

Skills related to the physics of materials -- constitutive models, thermodynamic properties, phase behavior, crystallography, chemical kinetics, and microstructure characterization. Example areas include stress-strain analysis, equation of state selection, phase-field modeling, and grain morphology. The community will shape which specific skills emerge first based on demand and contributor interest.

### verification-validation/ (open for contributions)

Skills for verifying simulation codes and validating results against known solutions. This covers manufactured solutions for code verification, standard benchmark problems, uncertainty propagation methods, and sensitivity analysis techniques. If you work in V&V, your domain expertise is especially valuable here.

### data-management/ (open for contributions)

Skills for handling simulation data throughout its lifecycle -- reading and writing common formats (HDF5, VTK, CSV), planning effective visualizations, converting between formats, and managing checkpoint/restart workflows. Contributions that help bridge the gap between simulation output and analysis are welcome.

### simulation-patterns/ (open for contributions)

Skills for common simulation design patterns that cut across specific physics -- multi-physics coupling strategies, transient startup and ramp procedures, data assimilation, and inverse problem formulations. These tend to be more advanced and benefit from real-world experience.

### robustness/ (open for contributions)

Skills for handling numerically challenging scenarios -- shock capturing and limiters, numerical diffusion diagnosis, contact mechanics, and other situations where standard methods struggle. Contributions from practitioners who have dealt with these difficulties firsthand are particularly welcome.

### Contributing a New Skill

1. **Open an issue first** -- use the [skill proposal template](.github/ISSUE_TEMPLATE/skill_proposal.md) to describe the skill and discuss the approach before writing code
2. **Check for in-progress work** -- look at open issues and PRs to avoid duplicating effort
3. **Start small** -- a well-implemented single-script skill is more valuable than an ambitious but incomplete one
4. **Any category is welcome** -- contributions to open categories are encouraged, but improvements to existing categories are equally valued

---

## Getting Help

- **Questions about a skill**: Open a [GitHub Issue](https://github.com/heshamfs/materials-simulation-skills/issues) with the question label
- **Implementation questions**: Tag your issue with `help wanted`
- **General discussion**: Use [GitHub Discussions](https://github.com/heshamfs/materials-simulation-skills/discussions) for open-ended topics

### Label Conventions

| Label | Meaning |
|-------|---------|
| `bug` | Something is broken |
| `enhancement` | Improvement to an existing skill |
| `skill-proposal` | Proposal for a new skill |
| `help wanted` | Open for community contribution |
| `good first issue` | Suitable for newcomers |
| `documentation` | Documentation improvements |
| `P1` / `P2` / `P3` | Priority level |
