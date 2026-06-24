# Security & safeguards

How the skills are hardened. (For reporting a vulnerability, see the repository's
[SECURITY.md](../SECURITY.md) disclosure policy.)

All skills are hardened against the
[OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/),
with dedicated validation and edge-case tests. Key safeguards:

- **Tool access is explicit** — skills that only inspect or write files avoid `Bash`; script-bearing skills declare `Bash` and keep executable behavior inside reviewed Python CLIs.
- **Input validation at every boundary** — numeric parameters are bounds-checked and validated as finite; string inputs (parameter/field/term names) are validated against regex allowlists.
- **Safe file loading** — JSON/CSV/NPY loaders enforce file-size limits (100–500 MB) and structure validation (dict root required); `np.load()` uses `allow_pickle=False`.
- **No `eval()`/`exec()`** — region-condition parsing uses strict regex matching, never dynamic code execution.
- **Prompt-injection resistance** — string values extracted from external files are truncated and stripped of control characters before surfacing to the agent; log-derived phase names are sanitized.
- **Command-construction safety** — `shlex.quote()` escapes paths interpolated into shell commands; command templates are validated against a shell-operator denylist.
- **ReDoS prevention** — user-supplied regex patterns are length-capped and checked for catastrophic backtracking.

Each skill documents its specific safeguards in a `## Security` section within its
`SKILL.md`, with standardized subsections for **Input Validation**, **File Access**,
**Tool Restrictions**, and **Safety Measures** — enforced by `mss validate` (see
[PROTOCOL.md](PROTOCOL.md)).

## Security risk tiers

Every skill is classified by its tool-access surface:

| Tier | Criteria | Skills |
|------|----------|--------|
| **HIGH** | Has `Bash` (can execute scripts) | 16 — numerical-stability, time-stepping, convergence-study, differentiation-schemes, nonlinear-solvers, ontology-explorer, ontology-validator, simulation-validator, slurm-job-script-generator, benchmark-and-mms-planner, workflow-engine-mapper, fair-simulation-packager, md-analysis-planner, hpc-runtime-doctor, simulation-failure-triage, skill-evaluator |
| **MEDIUM** | Has `Write` but no `Bash` | 7 — linear-solvers, mesh-generation, numerical-integration, parameter-optimization, performance-profiling, post-processing, simulation-orchestrator |
| **LOW** | Read/Grep/Glob only | 1 — ontology-mapper |

Per-skill tiers are also in the machine-readable [`skills_index.json`](../skills_index.json).
