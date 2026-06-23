# Changelog

## 1.1.0 - 2026-06-23

- Fixed `dag_pattern` to compose branch (relax/static/property) and sweep (screen/campaign) structures instead of overwriting one with the other; a high-throughput relax-static-DOS screening now reports `map over structures -> (relax -> static -> property branches) -> collect -> rank` (F4).
- One-off recommendations now emit a concrete forward-looking entry in `migration_triggers` (when to move to a workflow engine) instead of an empty list (F2).
- Documented the AiiDA gating and the fixed recommendation precedence in SKILL.md Decision Guidance so the prose matches the implemented thresholds (F3).
- Hardened input validation to match the Security section: `runs` capped at 1,000,000 and rejected for non-positive/boolean values; `task` length-capped at 2000 chars, `code`/`preferred` at 100 chars; invalid input exits with code 2.
- Repaired the `atomate2_vasp_dos` and `one_off_exploration` eval cases so expected_outputs/assertions test derived behavior rather than echoed inputs (F1, F2).
- Added regression unit tests for the DAG composition, one-off migration trigger, and input-validation bounds.

## 1.0.0 - 2026-05-18

- Initial workflow engine mapping skill.
