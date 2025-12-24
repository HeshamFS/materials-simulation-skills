# Linear Solvers Example

This example uses a coupled, block-structured system typical of multiphase-field
or multiphysics discretizations. It demonstrates matrix characterization,
solver selection, preconditioner hints, and convergence diagnostics.

Files:
- `coupled_block_matrix.txt`: Small block system with off-diagonal coupling
- `run_full_preflight.sh`: Run all linear-solver preflight checks
- `run_full_preflight_converged.sh`: Same workflow with a converged residual history
Includes scaling and residual norm checks.

Run:

```bash
bash examples/linear-solvers/run_full_preflight.sh
```
