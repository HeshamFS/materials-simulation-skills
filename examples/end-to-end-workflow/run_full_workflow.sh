#!/usr/bin/env bash
# End-to-end workflow demonstrating how multiple skills chain together.
#
# Pipeline:
#   1. Stability check (CFL) -> recommended dt
#   2. Stiffness detection -> integrator choice
#   3. Integrator selection based on stiffness
#   4. Timestep planning with recommended dt
#   5. Mesh quality assessment
#   6. DOE sampling for parameter study
#   7. Derived quantity computation (post-processing)
#   8. Result validation
set -euo pipefail

SKILLS="skills"

echo "============================================================"
echo "  End-to-End Simulation Workflow Demo"
echo "============================================================"
echo

# ---- Step 1: CFL stability check ----
echo "=== Step 1: CFL Stability Check ==="
python3 "$SKILLS/core-numerical/numerical-stability/scripts/cfl_checker.py" \
    --dx 0.01 --dt 0.0001 --velocity 1.0 --diffusivity 0.01 \
    --dimensions 2 --scheme explicit --json
echo

# ---- Step 2: Stiffness detection ----
echo "=== Step 2: Stiffness Detection ==="
python3 "$SKILLS/core-numerical/numerical-stability/scripts/stiffness_detector.py" \
    --eigs=-1,-10,-100,-10000 --json
echo

# ---- Step 3: Integrator selection (stiff system) ----
echo "=== Step 3: Integrator Selection ==="
python3 "$SKILLS/core-numerical/numerical-integration/scripts/integrator_selector.py" \
    --stiff --implicit-allowed --jacobian-available --json
echo

# ---- Step 4: Timestep planning ----
echo "=== Step 4: Timestep Planning ==="
python3 "$SKILLS/core-numerical/time-stepping/scripts/timestep_planner.py" \
    --dt-target 0.0001 --dt-limit 0.0002 --safety 0.9 \
    --ramp-steps 5 --preview-steps 5 --json
echo

# ---- Step 5: Mesh quality ----
echo "=== Step 5: Mesh Quality Check ==="
python3 "$SKILLS/core-numerical/mesh-generation/scripts/mesh_quality.py" \
    --dx 0.01 --dy 0.01 --dz 0.02 --json
echo

# ---- Step 6: DOE sampling ----
echo "=== Step 6: Design of Experiments ==="
python3 "$SKILLS/simulation-workflow/parameter-optimization/scripts/doe_generator.py" \
    --params 3 --budget 10 --method lhs --seed 42 --json
echo

# ---- Step 7: Post-processing (derived quantities from sample data) ----
echo "=== Step 7: Post-Processing (Volume Fraction) ==="
python3 "$SKILLS/simulation-workflow/post-processing/scripts/derived_quantities.py" \
    --input examples/post-processing/field_output.json \
    --quantity volume_fraction --field phi --threshold 0.5 --json
echo

# ---- Step 8: Result validation ----
echo "=== Step 8: Result Validation ==="
METRICS_TMP=$(mktemp --suffix=.json)
cat > "$METRICS_TMP" <<'METRICS'
{"mass_initial": 1.0, "mass_final": 1.0001, "energy_history": [1.0, 0.95, 0.9, 0.85], "field_min": 0.0, "field_max": 1.0}
METRICS
python3 "$SKILLS/simulation-workflow/simulation-validator/scripts/result_validator.py" \
    --metrics "$METRICS_TMP" --bound-min 0 --bound-max 1 --json
rm -f "$METRICS_TMP"
echo

echo "============================================================"
echo "  Workflow Complete - All 8 steps passed"
echo "============================================================"
