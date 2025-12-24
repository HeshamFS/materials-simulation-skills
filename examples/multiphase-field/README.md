# Multiphase Field Example

This example is a compact preflight for a multiphase-field simulation with
multiple order parameters and a conserved concentration field. The numbers are
representative of a diffusion-dominated microstructure problem and are intended
to stress the stability and integration tooling.

Scenario (illustrative):
- 2D grid, dx = 2e-9 m, interface width ~ 5*dx
- Effective diffusion D_eff = 1e-14 m^2/s
- Allen-Cahn relaxation rate k = 200 1/s (stiff)
- Trial dt = 1e-5 s (intentionally aggressive)

Scripts:
- `run_full_preflight.sh`: Run all preflight checks
- `run_stability_precheck.sh`: CFL/Fourier/reaction check (expect reaction limit violation)
- `run_stability_adjusted.sh`: Reduced dt to satisfy reaction limit
- `run_integration_selector.sh`: Integrator recommendation for stiff system
- `run_error_norm_multifield.sh`: Error norm on multi-field vector
- `run_adaptive_step_reject.sh`: Step controller with rejection
- `run_matrix_condition_coupled.sh`: Conditioning of a coupled operator block

Run from repo root:

```bash
bash examples/multiphase-field/run_full_preflight.sh
```
