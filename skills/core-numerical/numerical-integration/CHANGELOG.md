# Changelog

All notable changes to this skill will be documented in this file.

## [1.2.0] - 2026-06-23

### Fixed
- **PI step-size controller (science fix)**: corrected the PI factor to the
  standard `err^(-alpha) * err_prev^(beta)` form with `alpha=0.7/(p+1)`,
  `beta=0.4/(p+1)` (Hairer & Wanner / `error_control.md`). The previous code
  applied `(threshold/prev_error)^0.3*exp`, which used the wrong sign on the
  previous-error exponent and a non-standard `beta=0.3`. (F4)
- **error_norm.py crash**: solution-based scaling with `rtol=0`, `atol=0` and
  default `min_scale=0` no longer raises an uncaught `ZeroDivisionError`
  (exit 1); it now raises a clean validation error and exits 2, consistent with
  the `--scale` path. (F1)

### Changed
- SKILL.md Error Handling table now quotes the exact strings the scripts emit
  (`rtol/atol must be a non-negative finite number`,
  `error_norm must be finite and non-negative`, the scale-positivity message,
  the argparse `--controller` invalid-choice message, and
  `Provide at least one stiff or non-stiff term`). (F3)
- SKILL.md controller documentation, frontmatter description, and Security
  allowlist corrected to the implemented controllers `{p, pi}` (removed the
  non-existent `i`/`pid` CLI controllers; PID retained in `error_control.md` as
  reference-only theory). (F2)
- evals.json eval #2 expected_output updated to reference the implemented
  `P`/`PI` controllers.

### Added
- Regression tests: PI-controller formula lock-in, error_norm scale-collapse
  validation, and CLI message/allowlist anti-drift checks.

## [1.1.0] - 2026-03-26

### Added
- Optimized description for agent discovery (agentskills.io compliant)
- Evaluation suite with test cases and assertions
- Security review documentation with risk tier classification
- Standardized metadata block (author, version, security_tier, tested_with)
- This CHANGELOG file

### Changed
- Updated SKILL.md frontmatter with metadata block

## [1.0.0] - 2026-02-25

### Added
- Initial release
- Integrator selection (RK, BDF, Rosenbrock, Adams), adaptive step-size control (I/PI/PID), IMEX operator splitting
- CLI scripts with --json output and argparse interface
- Reference documentation
