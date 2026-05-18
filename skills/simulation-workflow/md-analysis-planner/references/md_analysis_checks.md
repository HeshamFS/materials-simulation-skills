# MD Analysis Checks

Common prerequisites:

- RDF: positions, periodic cell, species labels, cutoff, bin width.
- Coordination: RDF-informed cutoff or chemistry-informed cutoff.
- MSD/diffusion: unwrapped positions, time axis, diffusive time window, finite-size caveat.
- VACF/VDOS: velocities and uniform time spacing.
- Stress-strain: stress or virial, strain history, deformation direction.
- Bond angles: neighbor definition and species triplets.

Do not fit transport properties across startup transients. Use block averaging or independent trajectories when possible.
