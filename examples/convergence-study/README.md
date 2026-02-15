# Convergence Study Examples

Demonstrations of spatial/temporal convergence analysis, Richardson extrapolation, and Grid Convergence Index (GCI) calculation.

## Examples

| Script | Description |
|--------|-------------|
| `run_h_refinement.sh` | Spatial convergence study with 4 grid levels and 2nd-order expected convergence |
| `run_gci.sh` | Grid Convergence Index calculation for 3 mesh levels |
| `run_richardson.sh` | Richardson extrapolation from 2 grid levels with assumed order |

## Running

```bash
cd /path/to/materials-simulation-skills
bash examples/convergence-study/run_h_refinement.sh
bash examples/convergence-study/run_gci.sh
bash examples/convergence-study/run_richardson.sh
```

## Use Cases

- **Solution verification**: Confirm that a numerical method converges at its formal order
- **Discretization error estimation**: Bound the error from finite grid spacing or timestep
- **Mesh independence studies**: Demonstrate that results are independent of grid resolution
- **Code verification**: Verify that a simulation code correctly implements its numerical scheme
