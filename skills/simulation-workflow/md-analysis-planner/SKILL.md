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
  version: "1.2.1"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
  last_evaluated: "2026-06-23"
  eval_cases: 3
  last_reviewed: "2026-06-24"
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

### Input Validation

Inputs are scalar CLI values and booleans only. `plan_md_analysis` validates and
bounds every field before use; any violation raises `ValueError`, which `main`
catches to print a message on stderr and exit with code `2`:

- `system` must be non-empty (after stripping) and at most 256 characters.
- At most 64 goals are allowed; each goal at most 256 characters.
- `trajectory_format` at most 256 characters.
- `timestep_fs`, if given, must be a positive, finite number (`math.isfinite`
  and `> 0`).

Goals are not allowlisted: an unrecognized goal is not rejected but is reported
with status `needs review` and an "unknown goal" warning. The `--has-velocities`,
`--has-stress`, and `--unwrap-needed` flags are plain booleans and need no
validation.

### File Access

The script reads and writes no files; all I/O is stdin/args -> stdout (plain
text or JSON), with warnings additionally mirrored to stderr. It takes no path
arguments and opens no trajectory or output files, so there is no filesystem
sandboxing concern. There are no per-file size limits because no files are read;
input size is instead capped by the field/goal limits above.

### Tool Restrictions

Frontmatter `allowed-tools` is `Read, Bash, Write, Grep, Glob`:

- `Bash` is used only to run the bundled `scripts/md_analysis_planner.py`.
- `Read`, `Write`, `Grep`, and `Glob` are used only to inspect, edit, and search
  this skill's own files (the script, references, and SKILL.md) when authoring
  analysis plans; they are not used to touch trajectory data.

### Safety Measures

- No use of `eval`, `exec`, `os.system`, or dynamic imports.
- The script spawns no subprocesses and executes no external analysis programs;
  it only parses arguments with `argparse` and computes a plan in-process.
- Output is structured JSON produced via `json.dumps` (or deterministic plain
  text), never interpolated shell.
- Denial-of-service caps (`MAX_GOALS = 64`, `MAX_SYSTEM_LEN = 256`,
  `MAX_FIELD_LEN = 256`) bound the work so a planning helper never materializes
  pathological input.

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
