# Validation scope

Author: Hesham Salama <hesham.salama@rub.de>.

The numerical tools report evidence under explicit assumptions. Passing a test
qualifies the tested equation, input domain and implementation path. It does not
certify every materials model, solver, platform or agent explanation.

## Reproducible checks

```sh
python -m pytest tests/
python tools/validate_skills.py
python tools/run_skill_evals.py
python tools/build_index.py --check
```

The independent analytic tests in `tests/unit/test_independent_science.py`,
`test_repair_heldout.py` and `test_live_repairs.py` cover stability bounds,
manufactured refinement laws, quadrature, contour geometry, rank and norm
scaling, statistical precision, crystal metadata and evaluator controls.
Despite its historical filename, `test_live_repairs.py` runs deterministic
regressions; it does not launch an external materials solver.

The evaluator tests use controlled local subprocesses. These establish behavior
of the harness, including failure handling and configuration isolation. They
are not live coding-agent evaluations or an operating-system security sandbox.
The [deterministic explanation renderer](../skills/GROUNDED_EXPLANATIONS.md)
covers four tools and consumes trusted tool output. It does not authenticate
arbitrary JSON or validate unrestricted model prose.

## Interpreting results

- The combined CFL bound assumes the documented explicit discretization and
  linear decay model. Separate component bounds do not certify a mixed update.
- A positive observed order or agreement with an expected order does not prove
  an asymptotic regime. One triplet supplies only one order estimate.
- GCI is an engineering error estimate under its assumptions, not a statistical
  confidence interval. Nonconvergent or unresolved sequences cannot support
  a Richardson estimate.
- Nodal and cell-centered samples use different quadrature. Inconsistent grid
  metadata is rejected; units and physical meaning remain caller obligations.
- A Bravais/space-group metadata match does not determine symmetry from atomic
  positions. A surrogate fit does not establish physical predictive validity.
- A validator's check-pass fraction is not a probability of physical correctness.
  A result file is not proof of successful solver execution.

## Not established by these checks

There is no blanket guarantee of scientifically correct output for all inputs.
Full floating-point dynamic-range coverage, every external solver/model,
parallel execution, HPC schedulers and all supported operating systems require
their own evidence. Live agent trigger accuracy and scientific uplift require
fresh paired runs, recorded model and adapter versions, credentials and quotas.
The current regression suite does not establish that uplift.

OpenPhase solver changes and the unresolved two-dimensional phase-field spatial
refinement test are outside this package change. Their exclusion is not a pass
or a relaxation of the original acceptance tolerance. Model-specific conservation,
convergence and benchmark tests remain required before relying on solver results.
