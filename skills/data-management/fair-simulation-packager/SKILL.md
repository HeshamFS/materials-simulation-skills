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
  version: "1.2.0"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
  last_evaluated: "2026-06-23"
  eval_cases: 3
  last_reviewed: "2026-06-23"
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

`scripts/fair_packager.py --json` prints an envelope with two top-level keys:

- `inputs`: the parsed CLI arguments echoed back (note: `inputs.inputs` is the raw
  comma-separated string passed via `--inputs`, not the per-file records).
- `results`: contains a single key `manifest`.

`results.manifest` contains these fields:

- `project_name`, `engine`, `engine_version`, `structure_id`, `units`
- `file_inventory` with `inputs` and `outputs`, each a list of per-file records
  (`path`, `exists`, and when the file exists, `size_bytes` and `sha256`)
- `missing_files`: paths that do not exist on disk
- `provenance` (`working_directory`, `manifest_schema`)
- `fair_checks`: `has_inputs`, `has_outputs`, `has_units`, `has_engine_version`, and
  `has_hashes_for_existing_files` (`true`/`false`, or `null` when no files exist so the
  check is not applicable)
- `recommended_next_steps`

Parse fields at `results.manifest.<field>`. When `--out PATH` is given, only the bare
`manifest` object (not the `inputs`/`results` envelope) is written to `PATH`.

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

Missing files are reported in `missing_files` (exit code 0). Invalid input stops with
exit code 2: malformed unit entries, fields containing control characters, fields longer
than 4096 characters, more than 1000 input or output entries, or a file larger than
500 MB. Note that ordinary file paths — including absolute paths and paths containing
`..` — are accepted and inventoried; the tool reads file contents only to compute
metadata and SHA-256 hashes.

## Limitations

This skill creates a metadata manifest. It does not upload to NOMAD, Materials Project, or an OPTIMADE provider.

## Security

- File paths are read only for metadata and SHA-256 hashing.
- The script rejects control characters in fields, fields longer than 4096 characters,
  lists of more than 1000 entries, and files larger than 500 MB (exit code 2).
- Unit keys and values must match the allowlist `[A-Za-z0-9_.:/@+-]+`.
- The manifest is written only to the single path passed via `--out`; no other files are
  created. The path is user-controlled, so if `--out` points outside the working
  directory (via `..` or an absolute path) the file is written there as requested — the
  tool does not sandbox the output location.
- The skill uses `Bash` only to run the bundled script.

## References

- See `references/fair_manifest.md` for recommended manifest fields.

## Version History

- 1.2.0: Made eval cases discriminating by pinning the script's exact `--json`
  output (per-file `sha256`/`size_bytes`, `units`, `structure_id`, `engine_version`,
  `missing_files`, and the tri-state `has_hashes_for_existing_files`) against
  committed `evals/files/` fixtures.
- 1.1.0: Documented the real `--json` envelope shape; made
  `has_hashes_for_existing_files` tri-state (`null` when no files exist); added entry-count
  (1000) and field-length (4096) caps; corrected the Error Handling and Security wording
  to describe actual path behavior.
- 1.0.0: Initial FAIR simulation packaging skill.
