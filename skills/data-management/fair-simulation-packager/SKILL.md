---
name: fair-simulation-packager
description: >
  Create FAIR-minded reproducibility bundles for materials simulations by
  collecting input/output file inventories, hashes, units, engine versions,
  structure identifiers, provenance, and NOMAD/OPTIMADE/Materials Project
  friendly metadata. Use before publishing, sharing, archiving, or handing
  simulation results to another agent.
allowed-tools: Read, Bash, Write, Grep, Glob
metadata:
  author: HeshamFS
  version: "1.0.0"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
    - gemini-cli
    - vs-code-copilot
  eval_cases: 3
  last_reviewed: "2026-05-18"
---

# FAIR Simulation Packager

## Goal

Build a minimal reproducibility manifest for materials simulation results so another person or agent can understand what was run, with which inputs, and how outputs should be interpreted.

## Requirements

- Python 3.10+
- No external dependencies
- Works on Linux, macOS, and Windows

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Project name | Human-readable bundle name | `al-cu-diffusion-study` |
| Engine | Simulation code | `LAMMPS`, `VASP`, `MOOSE` |
| Input files | Files needed to rerun | `in.lammps,data.lmp` |
| Output files | Files needed to verify results | `log.lammps,traj.dump` |
| Structure ID | Database or local identifier | `mp-149` |
| Units | Field/unit mapping | `energy=eV,length=angstrom` |

## Decision Guidance

- Always include input files, output files, code version, and units.
- Include hashes for every file that exists locally.
- Include structure identifiers when using Materials Project, NOMAD, OPTIMADE, CIF, POSCAR, or internal database records.
- Record missing files as warnings instead of silently dropping them.

## Script Outputs

`scripts/fair_packager.py` emits:

- `manifest`
- `file_inventory`
- `missing_files`
- `fair_checks`
- `recommended_next_steps`

## Workflow

```bash
python3 skills/data-management/fair-simulation-packager/scripts/fair_packager.py \
  --project-name al-cu-diffusion \
  --engine LAMMPS \
  --inputs in.lammps,data.lmp \
  --outputs log.lammps,traj.dump \
  --units energy=eV,length=angstrom,time=ps \
  --structure-id local:alcu-cell-001 \
  --json
```

Use `--out manifest.json` only when the user wants a manifest file written.

## Error Handling

Missing files are reported in `missing_files`; invalid unit fields or unsafe paths stop with exit code 2.

## Limitations

This skill creates a metadata manifest. It does not upload to NOMAD, Materials Project, or an OPTIMADE provider.

## Security

- File paths are read only for metadata and SHA-256 hashing.
- The script rejects control characters and oversized files above 500 MB.
- Optional manifest writing is restricted to the requested output path.
- The skill uses `Bash` only to run the bundled script.

## References

- See `references/fair_manifest.md` for recommended manifest fields.

## Version History

- 1.0.0: Initial FAIR simulation packaging skill.
