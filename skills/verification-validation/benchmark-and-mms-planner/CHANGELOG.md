# Changelog

## 1.1.0 - 2026-06-23

### Fixed
- Unknown model families now resolve to `general` exactly once, so benchmark-case
  selection and the `include_time_refinement` decision stay consistent. Previously an
  unlisted transient PDE (e.g. `magnetohydrodynamics`) received the general benchmark
  cases but was told to skip time refinement, which is wrong for transient problems. (F2)
- Observed-order acceptance threshold (`accept_observed_order_min`) now uses a relative
  tolerance band (10% high risk, 20% otherwise) floored at first-order convergence instead
  of a fixed absolute offset, so strictness is consistent across formal orders and never
  drops below 1.0. (F3)

### Added
- `effective_model` field in the output exposes the resolved model family so callers can
  see when a fallback to `general` occurred.
- 256-character caps on the `model` and `quantity` string inputs (exit code 2 on
  oversized input), matching the SKILL.md "## Security" claims.

### Documentation
- Documented the `uncertainty_plan` and `effective_model` output fields, the
  `refinement_protocol` sub-fields, and the observed-order acceptance heuristic in
  SKILL.md and `references/vv_patterns.md`. (F1)

## 1.0.0 - 2026-05-18

- Initial benchmark and MMS planning skill.
