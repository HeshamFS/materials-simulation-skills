# End-to-End Simulation Workflow

Demonstrates how multiple skills chain together in a typical materials simulation workflow.

## Pipeline Steps

| Step | Skill | Purpose |
|------|-------|---------|
| 1 | numerical-stability | CFL check to determine stable time step |
| 2 | numerical-stability | Stiffness detection to guide integrator choice |
| 3 | numerical-integration | Select integrator based on stiffness result |
| 4 | time-stepping | Plan time step schedule with CFL-recommended dt |
| 5 | mesh-generation | Verify mesh quality metrics |
| 6 | parameter-optimization | Generate DOE samples for parameter study |
| 7 | post-processing | Compute derived quantities from field data |
| 8 | simulation-validator | Validate conservation and bounds |

## Running

```bash
bash examples/end-to-end-workflow/run_full_workflow.sh
```

Each step produces JSON output that could feed into the next in an automated pipeline.
