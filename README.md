# Materials Simulation Skills

[![CI](https://github.com/HeshamFS/materials-simulation-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/HeshamFS/materials-simulation-skills/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-standard-orange.svg)](https://agentskills.io)
[![Python 3.10-3.12](https://img.shields.io/badge/Python-3.10--3.12-blue.svg)](https://www.python.org/)
[![Skills](https://img.shields.io/badge/skills-24-blue.svg)](skills_index.json)
[![Deterministic eval coverage](https://img.shields.io/badge/deterministic_eval_coverage-100%25-brightgreen.svg)](docs/EVALUATION_METHODOLOGY.md)

**Give your AI coding agent real expertise in numerical methods, simulation best practices, and computational materials science — so it stops guessing.**

> **New to Agent Skills?** A "skill" is a portable folder of instructions + small scripts that an AI coding agent **discovers automatically and loads only when relevant**. They follow the open [Agent Skills standard](https://agentskills.io) and work across **20+ tools** — Claude Code, Codex, Cursor, Antigravity, GitHub Copilot, and more. Nothing to wire up: drop them in and your agent gets smarter at the task.

---

## What it solves

Simulation engineers repeat the same guidance to AI agents constantly: *"Check the CFL number before running," "Use Richardson extrapolation for grid convergence," "Exit code 2 means bad input."* General-purpose agents lack the domain knowledge to run reliable numerical simulations without heavy hand-holding — so they pick wrong time steps, miss convergence checks, and misread solver failures.

This project packages that domain knowledge into **skills** the agent finds and runs on its own:

```text
You: Check if dt=0.001 is stable for my advection problem with v=2.0 m/s and dx=0.01.

Agent: I'll use the numerical-stability skill to check this.
       [runs cfl_checker.py --dx 0.01 --dt 0.001 --velocity 2.0 --json]

       CFL number = 0.2 (limit: 1.0) -- stable.
       Recommended max dt = 0.005 with safety factor 1.0.
```

No prompt engineering, no copy-pasting formulas. **24 skills** span numerical methods, simulation workflows, HPC deployment, verification & validation, FAIR data, robustness, and materials ontologies.

### Validated, not just curated

Most agent-skill collections are unverified prompt text. These are **measured**:

- **Tested scripts** — every skill ships Python CLIs with a pure-function core (1283 tests, Python 3.10–3.12).
- **100% deterministic eval coverage** — every eval case runs the script and asserts its exact output, so docs can't silently drift from code. Enforced in CI.
- **Measured uplift** — skills are evaluated *with vs. without* the skill across coding-agent CLIs; value is the pass-rate **delta**, not a claim.
- **Cited science + an enforced [protocol](docs/PROTOCOL.md)** — rules reference authoritative standards (ASME V&V20, the SchedMD `sbatch` spec, CMSO IRIs).

How and why: **[evaluation methodology](docs/EVALUATION_METHODOLOGY.md)** · **[harness](docs/EVAL_HARNESS.md)**.

---

## Install

The repo follows the open standard, so the ecosystem installers work out of the box:

```bash
npx skills add HeshamFS/materials-simulation-skills          # any agent → ~/.agents/skills/
gh skill install HeshamFS/materials-simulation-skills --pin v1.0.0   # version-pinned
```

Or install a curated **bundle** into a specific agent with the bundled `mss` CLI:

```bash
mss bundles                                                  # list bundles
mss install --agent claude --bundle verification-and-validation
```

Claude Code users can also `/plugin marketplace add HeshamFS/materials-simulation-skills`.
Full per-agent guide → **[docs/INSTALL.md](docs/INSTALL.md)**.

---

## Use it

Once installed, just describe your task — the agent picks the right skill, runs the
script, and interprets the result (as in the example above). You can also name a
skill explicitly:

```text
Use convergence-study to check if my mesh is in the asymptotic range:
h = 0.4, 0.2, 0.1 gave stress = 98.5, 99.6, 99.9 MPa.
```

Browse the full catalog in **[docs/SKILLS.md](docs/SKILLS.md)** (or the machine-readable
[`skills_index.json`](skills_index.json)).

**Try it locally / develop:**

```bash
git clone https://github.com/HeshamFS/materials-simulation-skills.git
cd materials-simulation-skills && pip install -e ".[dev]"

mss list                                              # list skills
mss run numerical-stability cfl_checker -- --dx 0.01 --dt 0.001 --velocity 2.0 --json
mss eval                                              # run the deterministic eval gate
python -m pytest tests/                               # full test suite
```

---

## What's inside

**24 skills** across 8 categories (one-line summary; full tables in [docs/SKILLS.md](docs/SKILLS.md)):

| Category | Skills | Focus |
|---|---|---|
| Core Numerical | 8 | stability, time-stepping, meshing, convergence, integration, differentiation, linear/nonlinear solvers |
| Simulation Workflow | 7 | validation, DOE/optimization, orchestration, post-processing, profiling, workflow mapping, MD analysis |
| HPC Deployment | 2 | SLURM script generation, runtime diagnosis |
| Verification & Validation | 1 | manufactured solutions, benchmarks, pass/fail reports |
| Data Management | 1 | FAIR reproducibility packaging |
| Robustness | 1 | cross-code failure triage & retry ladders |
| Ontology | 3 | CMSO/ASMO exploration, mapping, validation |
| Meta | 1 | `skill-evaluator` — evaluate any skill across any agent CLI |

Quality is gated in CI: spec-valid frontmatter, deterministic `script_checks`, the
standardized Security section, and a fresh index — see **[docs/PROTOCOL.md](docs/PROTOCOL.md)**
and **[docs/SECURITY.md](docs/SECURITY.md)**.

---

## Contributing

This is an open project and contributions are very welcome — **a new skill, a fix, docs, or just an idea**.

- **Have an idea or a skill to propose?** Open an [issue](https://github.com/HeshamFS/materials-simulation-skills/issues) (there are templates for bug reports and skill proposals) — early ideas are great even without code.
- **Want to build a skill?** **[CONTRIBUTING.md](CONTRIBUTING.md)** has a step-by-step guide, script/test templates, the skill taxonomy, and open categories. The bar that keeps this project trustworthy: a skill ships a **tested script + an eval case with a deterministic `script_check`**, and passes `mss validate` + `mss eval`.
- **Where it's headed:** the **[ROADMAP.md](ROADMAP.md)** — growing toward materials-physics and code-interface skills (LAMMPS, DFT) and a richer skill protocol.

---

## Documentation

| Doc | What's in it |
|---|---|
| [docs/SKILLS.md](docs/SKILLS.md) | Full skill catalog, how skills work, repo layout |
| [docs/INSTALL.md](docs/INSTALL.md) | Install for every supported agent |
| [docs/EVALUATION_METHODOLOGY.md](docs/EVALUATION_METHODOLOGY.md) | How skills are evaluated, with results |
| [docs/EVAL_HARNESS.md](docs/EVAL_HARNESS.md) | The three-layer evaluation harness |
| [docs/PROTOCOL.md](docs/PROTOCOL.md) | The Materials Simulation Skill Protocol |
| [docs/SECURITY.md](docs/SECURITY.md) | Safeguards and security tiers |
| [CONTRIBUTING.md](CONTRIBUTING.md) · [ROADMAP.md](ROADMAP.md) | Contributing guide · direction |

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

- [Agent Skills standard](https://agentskills.io) — open specification for portable agent capabilities
- [Anthropic](https://anthropic.com) — original developer of the Agent Skills format
- [agentskills/agentskills](https://github.com/agentskills/agentskills) — reference implementation and validation library
