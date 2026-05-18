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

`scripts/md_analysis_planner.py` emits:

- `analysis_plan`
- `required_data`
- `equilibration_checks`
- `pbc_handling`
- `warnings`

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

If velocities, stress, or timestep information is missing, downgrade dependent analyses and report warnings.

## Limitations

This skill plans analysis and prerequisites; it does not parse large trajectories directly.

## Security

- Inputs are scalar CLI values and booleans only.
- The script does not read trajectory files or execute external analysis programs.
- The skill uses `Bash` only to run the bundled script.

## References

- See `references/md_analysis_checks.md` for analysis prerequisites and failure modes.

## Version History

- 1.0.0: Initial MD analysis planning skill.
