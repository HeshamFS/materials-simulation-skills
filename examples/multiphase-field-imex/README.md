# Multiphase-Field IMEX Example

This example focuses on IMEX splitting and operator splitting error estimates
for multiphase-field systems (Allen-Cahn + Cahn-Hilliard) with isotropic
coefficients.

Scenario (illustrative):
- Diffusion and high-order gradients treated implicitly
- Reaction/free-energy terms treated explicitly
- Coupling is moderate to strong

Run from repo root:

```bash
bash examples/multiphase-field-imex/run_imex_split.sh
bash examples/multiphase-field-imex/run_splitting_error.sh
```
