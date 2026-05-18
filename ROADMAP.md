# Roadmap

This roadmap prioritizes validated, portable Agent Skills over a large all-in-one simulation container.

## Near Term

- Keep repository metadata, README metrics, CI, and skill validation reproducible.
- Add the `mss` helper CLI for listing, validating, running, and installing skills.
- Expand into six high-need LLM simulation support areas:
  - verification and validation benchmarks
  - workflow engine mapping
  - FAIR simulation packaging
  - molecular dynamics analysis planning
  - HPC runtime diagnosis
  - cross-code simulation failure triage

## Medium Term

- Add code-interface skills for LAMMPS and DFT input review.
- Add materials-physics skills for structure preparation, interatomic potential selection, and MLIP readiness.
- Add more engine-specific failure signatures while keeping the core scripts dependency-light.

## Contribution Principles

- Start small: one well-tested script is better than a broad but fragile skill.
- Preserve progressive disclosure: put detailed domain tables in `references/`, not the main `SKILL.md`.
- Add eval cases with concrete prompts and assertions for every skill.
