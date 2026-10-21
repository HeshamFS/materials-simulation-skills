# Derived Quantities Guide

## Overview

Derived quantities are computed from raw simulation output to extract physical meaning. This guide explains each quantity and its physical interpretation.

## Volume Fraction

**Definition:** Fraction of domain with field value above/below threshold.

**Formula:** V_f = N_above / N_total

**Physical Meaning:**
- For order parameter φ ∈ [0,1]: fraction of phase with φ > 0.5
- For concentration: fraction above solubility limit
- For temperature: fraction above/below critical temperature

**Usage:**
```bash
python derived_quantities.py --input field.json --quantity volume_fraction \
    --field phi --threshold 0.5 --json
```

**Interpretation:**
- V_f = 0.5: Equal thresholded sample fractions; this alone does not establish equilibrium
- V_f → 0 or 1: Predominantly single phase
- Time evolution of V_f: Phase transformation kinetics

## Interface Area/Length

**Definition:** Surface area (3D) or perimeter (2D) of iso-surface at threshold.

**Method:** In 2D, interpolate contour segments on a fixed triangular subdivision
of each cell and sum their Euclidean lengths using dx and dy separately.
Threshold plateaus do not define a unique contour and are rejected. Curved
contours require a refinement study; triangle orientation can affect coarse
results. Only the domain spanned by sample coordinates is measured. 3D surface
area remains explicitly unimplemented.

**Physical Meaning:**
- Interfacial area controls reaction/diffusion rates
- Decreases during coarsening (curvature-driven)
- Increases during nucleation/growth

**Usage:**
```bash
python derived_quantities.py --input field.json --quantity interface_area \
    --field phi --threshold 0.5 --json
```

**Interpretation:**
- Coarsening exponents depend on conservation, transport mechanism, morphology and boundary conditions; no universal exponent is inferred by this tool.
- Sudden increase: New phase nucleation

## Gradient Magnitude

**Definition:** |∇φ| = √[(∂φ/∂x)² + (∂φ/∂y)² + ...]

**Method:** Central finite differences
- Interior: (φᵢ₊₁ - φᵢ₋₁) / (2Δx)
- Boundaries: Forward/backward differences

**Physical Meaning:**
- High gradients: Sharp interfaces, steep concentration profiles
- Low gradients: Smooth fields, equilibrium regions
- Maximum gradient: Interface width indicator

**Usage:**
```bash
python derived_quantities.py --input field.json --quantity gradient_magnitude \
    --field phi --json
```

**Interpretation:**
- Max|∇φ| ≈ 1/η for phase-field (η = interface width)
- Mean|∇φ| decreases during coarsening
- High gradients in wrong regions: Numerical instability

## Integral / Total Mass

**Definition:** ∫φ dV using tensor trapezoidal weights on nodal axes and midpoint
weights on cell-centered axes. Domain lengths without explicit spacing imply
nodal grids (L/(n-1)); explicit spacing alone defaults to cell samples. Set
`centering` to `node` or `cell` in input JSON to disambiguate. Contradictory
spacing/domain metadata is rejected. Mass and centroid use the same quadrature.
Centroid coordinates place the first sample at zero; absolute origin is not inferred.

**Physical Meaning:**
- Total amount of conserved quantity
- Should be constant for closed, source-free Cahn-Hilliard dynamics with compatible boundary conditions
- May change for Allen-Cahn (non-conserved)

**Usage:**
```bash
python derived_quantities.py --input field.json --quantity integral \
    --field concentration --json
```

**Conservation Check:**
- Select an absolute and relative tolerance from units, initial mass, resolution, solver accuracy and boundary fluxes. No universal numerical threshold proves conservation.

## Total Variation

**Definition:** This utility reports the discrete sum of neighbor absolute differences. In 2D it is an unweighted lattice diagnostic, not a physically scaled isotropic ∫|∇φ| dV. Do not compare its raw value across grids or units as a physical interface measurement.

**Physical Meaning:**
- Measures total "roughness" of field
- Related to interface area for binary fields
- Regularization term in image processing

**Usage:**
```bash
python derived_quantities.py --input field.json --quantity total_variation \
    --field phi --json
```

**Interpretation:**
- TV decreases: Smoothing/coarsening
- TV increases: Sharpening/nucleation
- Constant TV: Steady state

## Centroid

**Definition:** Center of mass weighted by field values

**Formula:**
- x_c = ∫x φ dV / ∫φ dV
- y_c = ∫y φ dV / ∫φ dV

**Physical Meaning:**
- Center of precipitate or inclusion
- Drift indicates asymmetric growth
- Multiple centroids for multi-particle systems

**Usage:**
```bash
python derived_quantities.py --input field.json --quantity centroid \
    --field phi --json
```

## Quantity Selection Guide

| Question | Quantity to Use |
|----------|----------------|
| How much of each phase? | volume_fraction |
| How large is the interface? | interface_area |
| How sharp is the interface? | gradient_magnitude (max) |
| Is mass conserved? | integral (over time) |
| Is the system coarsening? | total_variation or interface_area |
| Where is the particle? | centroid |

## Physical Units

All quantities assume consistent units based on grid spacing:

| Quantity | Units (if dx in meters) |
|----------|------------------------|
| Volume fraction | Dimensionless |
| Interface area | m² (3D) or m (2D) |
| Gradient | 1/m |
| Integral | m^d × [field units], d = field dimension |
| Total variation | [field units] for the discrete neighbor-difference diagnostic |
| Centroid | m |
