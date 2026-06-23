---
name: md-analysis-planner
description: >
  Plan molecular dynamics post-processing for materials simulations, including
  RDF, MSD and diffusion, VACF/VDOS, coordination numbers, bond-angle
  distributions, stress-strain curves, equilibration detection, PBC unwrapping,
  and trajectory format choices. Use before writing MD analysis scripts or
  trusting trajectory-derived results.
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

# MD Analysis Planner

## Goal

Choose the right MD trajectory analyses and prerequisites before writing post-processing code.

## Requirements

- Python 3.10+
- No external dependencies
- Works on Linux, macOS, and Windows

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| System | Material or molecular system | `oxide glass`, `liquid water` |
| Goals | Analysis goals | `rdf,diffusion,coordination` |
| Trajectory format | Dump, DCD, XYZ, H5MD, etc. | `LAMMPS dump` |
| Velocities | Whether velocities are stored | `true` |
| Stress | Whether stress/virial is stored | `true` |
| Unwrap needed | Whether atoms cross PBC | `true` |
| Timestep | fs per saved frame | `10` |

## Decision Guidance

- Use **RDF and coordination** for local structure.
- Use **MSD** for diffusion, but unwrap trajectories and verify diffusive regime.
- Use **VACF/VDOS** only when velocities or reliable finite-difference velocities exist.
- Use **stress-strain** only if stress/virial and deformation history are available.
- Always perform equilibration checks before fitting transport or thermodynamic properties.

## Script Outputs

`scripts/md_analysis_planner.py` emits these fields (JSON under `results`):

| Field | Description |
|-------|-------------|
| `analysis_plan` | One entry per goal: `goal`, `method`, and `status` |
| `required_data` | Sorted, de-duplicated data needed across all goals |
| `equilibration_checks` | Standard pre-fit equilibration checklist |
| `pbc_handling` | `unwrap_needed`, `minimum_action`, `format_note` |
| `warnings` | Safety-critical caveats and blockers |

### Status values

`status` is one of, from most to least severe: `blocked` > `needs time axis` >
`needs review` > `ready`. A more-severe status is never demoted by a less-severe
one. For example, a VACF/VDOS goal with no stored velocities reports `blocked`
even when the timestep is also missing (both warnings are still emitted).

### Default (non-JSON) output

Without `--json` the script prints the plan lines, a `Required data:` list, a
one-line `PBC:` note, and a `Warnings:` section (also mirrored to stderr) so the
safety-critical caveats are visible even when stdout is piped.

## Workflow

```bash
python3 skills/simulation-workflow/md-analysis-planner/scripts/md_analysis_planner.py \
  --system "oxide glass" \
  --goals rdf,coordination,bond-angle \
  --trajectory-format dump \
  --unwrap-needed \
  --timestep-fs 10 \
  --json
```

## Error Handling

If velocities, stress, or timestep information is missing, downgrade dependent
analyses and report warnings. The script exits with code `2` and a message on
stderr for invalid input (empty system, no goals, non-positive or non-finite
timestep, or inputs exceeding the size caps below).

## Limitations

This skill plans analysis and prerequisites; it does not parse large trajectories directly.

## Security

- Inputs are scalar CLI values and booleans only.
- The script does not read trajectory files or execute external analysis programs.
- The skill uses `Bash` only to run the bundled script.
- Input is validated and bounded before use; invalid input exits with code `2`:
  - `system` must be non-empty and at most 256 characters.
  - At most 64 goals; each goal at most 256 characters.
  - `trajectory_format` at most 256 characters.
  - `timestep_fs`, if given, must be a positive, finite number.

## References

- See `references/md_analysis_checks.md` for analysis prerequisites and failure modes.

## Version History

- 1.2.0: Add deterministic `script_checks` to all three eval cases that pin the
  exact planner output (statuses, sorted `required_data`, PBC note, and the
  specific diffusive-regime / Yeh-Hummer / blocked-not-demoted warnings) so the
  evals discriminate the skill from a from-memory baseline.
- 1.1.0: Fix status demotion (blocked never downgraded to needs time axis),
  surface warnings/required-data/PBC in non-JSON mode, add diffusive-regime and
  Yeh-Hummer finite-size guidance, and enforce documented input caps.
- 1.0.0: Initial MD analysis planning skill.
