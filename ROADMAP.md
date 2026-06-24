# Roadmap

Where this project is headed. The aim is to grow from a collection of helper
skills into a **Materials Simulation Skill Protocol** — a small, opinionated
standard layered on the open [Agent Skills spec](https://agentskills.io/specification)
that makes computational-materials and numerical-simulation skills **portable,
composable, and scientifically trustworthy** across any compatible agent.

The guiding bet: *validated, portable skills beat one monolithic simulation
container.*

> This file is the general direction. Day-to-day bug fixes, doc corrections, and
> small improvements are ordinary contribution work — see
> [CONTRIBUTING.md](CONTRIBUTING.md) — not roadmap items.

---

## Guiding principles

- **Start small, prove it.** One well-tested script beats a broad, fragile skill.
- **Progressive disclosure.** Detail lives in `references/`, not `SKILL.md`
  (keep `SKILL.md` under ~500 lines).
- **Every claim is checkable.** Numeric examples and documented output fields are
  guarded by deterministic `script_checks`; rules cite an authoritative standard.
- **Honesty over polish.** A Security section documents only what the code does;
  a limitation is stated, not hidden.
- **Composability first.** Skills reference and build on each other rather than
  duplicate logic.

---

## The protocol (conventions on top of the Agent Skills spec)

These conventions are what turn a collection into a coherent standard. They are
codified in **[docs/PROTOCOL.md](docs/PROTOCOL.md)** with a conformance checklist;
the frontmatter, naming, Security-subsection, and eval-coverage rules are enforced
in CI by `mss validate` and `mss eval`. The direction is to enforce more of the
checklist automatically (e.g. the script I/O envelope and `compatibility`).

1. **Script I/O envelope.** Every CLI emits `--json` as
   `{ "inputs": {...}, "results": {...}, "notes": [ ... ] }`, with exit `2` on
   bad input, `1` on runtime error, `0` on success.
2. **Units & provenance.** Numeric results carry units; outputs that feed FAIR
   packaging expose engine/version/standard references.
3. **Cited science.** Each skill names the standard or reference behind its rules
   (e.g., ASME V&V20, SchedMD, CMSO IRIs) so an agent can defend an answer.
4. **Declared compatibility.** Use the spec's `compatibility` frontmatter field
   for environment needs (Python version, NumPy/SciPy, network) instead of prose.
5. **Spec-conformant metadata.** Keep `metadata` spec-aligned and run
   `skills-ref validate` for conformance alongside the repo's own validator.
6. **Security tiers that match reality.** A skill either declares the `Bash` it
   needs to run its scripts, or it ships logic the agent applies without
   execution — never both stories at once. Standard `## Security` subsections.
7. **Composition contract.** A skill may declare sibling skills it builds on
   (a lightweight `metadata.depends_on`), enabling a dependency graph and bundles.

---

## Direction

### Evaluation as a first-class gate

The [three-layer evaluation harness](docs/EVAL_HARNESS.md) exists: a deterministic
`script_checks` CI gate plus the agent-agnostic `skill-evaluator` skill (trigger
eval + with/without quality benchmarking across Claude Code, Codex, Antigravity,
Cursor, Copilot, Amp, opencode, Grok). The direction now is depth, not foundation:

- Grow deterministic `script_checks` toward every eval case with a computable
  answer, so doc↔code drift can never regress silently.
- Wire the LLM-judge (Layer 3) into CI as an **opt-in** gate — when a CLI and key
  are available, gate skill changes on "with-skill beats baseline."
- Precise per-CLI trigger detection (parse tool-use events) beyond the current
  cross-tool heuristic; per-skill dashboards tracking pass-rate and token/latency
  deltas across iterations so regressions and bloat are visible.
- Cross-skill integration scenarios: graded end-to-end "campaigns" exercising
  several skills together (stability → mesh → solver → convergence → validate →
  package).

### Breadth — new skill areas

Each new skill starts from one well-tested script.

- **Materials physics**: structure preparation (supercells, defects, surfaces,
  grain boundaries), interatomic-potential / **MLIP readiness** selection,
  CALPHAD/thermodynamic sanity, elasticity and symmetry checks.
- **Code-interface review**: LAMMPS input review, DFT input review (VASP/QE —
  k-points, cutoffs, smearing, convergence), phase-field setup review.
- **Deeper HPC & V&V**: more scheduler portability (PBS/LSF), profiling-to-action
  loops, richer manufactured-solution libraries and benchmark catalogs.
- **Data / FAIR**: tighter NOMAD / OPTIMADE / Materials Project round-tripping.

### Interoperability & distribution

- **Skill registry / index.** A generated, machine-readable index (name,
  description, category, compatibility, dependencies, cited standards) so agents
  and humans can discover and compose skills.
- **Skill bundles.** Named sets (e.g., `phase-field-starter`, `dft-campaign`)
  installable as a coherent group via `mss install`.
- **Versioning & governance.** Semver per skill, enforced CHANGELOG discipline,
  and a protocol-conformance badge for skills that pass the checklist.
- **Publishing.** Package conformant skills for the agentskills ecosystem so they
  install cleanly into Claude Code, Codex, Antigravity (`agy`, the CLI that
  replaced Gemini CLI on 2026-06-18), Cursor, Copilot, Amp, opencode, and Grok.

---

## Contribution principles

- Start small: one well-tested script beats a broad but fragile skill.
- Preserve progressive disclosure: detailed tables go in `references/`.
- Every numeric claim in a `SKILL.md` gets a `script_check`; every rule cites a
  standard.
- Add eval cases with concrete prompts and assertions for every skill, and a
  deterministic `script_check` whenever the answer is computable.
