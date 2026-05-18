# Simulation Failure Patterns

Common first-response mapping:

- NaN/Inf: timestep, invalid material state, division by zero, bad initial geometry.
- Exploding energy or pressure: overlaps, density, force-field mismatch, barostat/thermostat coupling.
- Nonconvergence: residual scaling, preconditioner, initial guess, bad Jacobian, overly tight tolerance.
- Missing potential/pseudopotential: species mapping, file path, functional mismatch, valence mismatch.
- Corrupted output or incomplete run: walltime, scratch, interrupted writes, disk quota, parallel filesystem.

Retry rules:

1. Preserve evidence.
2. Reduce to the smallest reproducing case.
3. Change one variable at a time.
4. Revalidate physical consistency after numerical recovery.
