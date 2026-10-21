# Grounded scientific explanations

Author: Hesham Salama <hesham.salama@rub.de>.

The optional deterministic renderer covers `crystal_mapper`, `h_refinement`,
`cfl_checker`, and `md_analysis_planner`. It separates decisions, quantities,
units and limits without using a language model's prose.

Capture a tool's JSON directly, verify that its recorded inputs match the user's
request, then pass that JSON on stdin to:

```sh
python -m materials_simulation_skills.scientific_explanations --tool h_refinement
```

The result contains `decision` (true, false or null), `reason`, provenance, and
`model_prose_used: false`. A null decision means insufficient evidence, never a
pass. Keep warnings and the stated scope. For crystal declarations, a consistent
Bravais/space-group pair is not atomic-structure symmetry verification. For
refinement, compare the dimensionless observed order with the expected order;
the extrapolated observable is a different quantity. For mixed explicit
updates, separate component limits do not establish the combined bound.

This is a renderer for **trusted tool output**, not an authenticity or scientific
validator for arbitrary JSON. Never pass model-authored or model-modified tool
JSON to it. A calling agent must reject omitted or altered input parameters
before rendering. Use the returned explanation as the final scientific text;
adding unverified model prose removes this guarantee. Other tools, arbitrary
scientific claims, and native coding-agent adapters are outside this renderer's
coverage. Local-model tool selection and unrestricted explanations remain
separate evaluation targets.
