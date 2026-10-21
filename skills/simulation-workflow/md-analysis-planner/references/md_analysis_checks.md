# MD Analysis Checks

Common prerequisites:

- RDF: positions, periodic cell, species labels, cutoff, bin width.
- Coordination: RDF-informed cutoff or chemistry-informed cutoff.
- MSD/diffusion: unwrapped positions (plus cell and image flags to perform the unwrap), time axis, diffusive time window. Verify the diffusive regime (log-log MSD-vs-time slope ~1) before fitting D = lim MSD/(2*d*t), and assess finite-size effects. The Yeh-Hummer 1/L hydrodynamic correction (xi ~= 2.837) assumes an isotropic bulk fluid in a 3D periodic cubic box and requires L, T and shear viscosity eta. Do not automatically apply it to solids, ballistic motion, confinement, anisotropic transport or other cell geometries. Report raw and corrected estimates separately, with the applicability argument. Reference: https://doi.org/10.1021/jp0477147.
- VACF/VDOS: velocities and uniform time spacing.
- Stress-strain: stress or virial, strain history, deformation direction.
- Bond angles: neighbor definition and species triplets.

Do not fit transport properties across startup transients. Use block averaging or independent trajectories when possible.
