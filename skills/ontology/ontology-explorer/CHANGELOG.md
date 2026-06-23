# Changelog

All notable changes to this skill will be documented in this file.

## [1.2.0] - 2026-06-23

### Fixed
- `property_lookup.py --class`: now resolves the user-supplied name to its
  canonical class label (exact → case-insensitive → space-normalized) before
  domain matching, so spaceless inputs like `UnitCell` return the same
  properties as `Unit Cell`. Previously `UnitCell` returned an empty list,
  inconsistent with `class_browser.py`. Unknown class names now raise a clear
  `Class 'X' not found` error instead of silently returning `[]`.
- Domain matching in both `property_lookup.py` and `class_browser.py` now
  normalizes both sides identically and splits union domains on `|`, so the two
  tools agree on identical input and union domains match per-class.
- SKILL.md union-domain guidance no longer cites a fabricated
  `hasVector → SimulationCell | UnitCell` example (no such union exists in the
  bundled summaries); it now uses a neutral `A | B` placeholder.
- Conversational Workflow Example is now reproducible: it shows the actual
  search/property-lookup command sequence that produces each listed class and
  the relationship chain, instead of a single search plus a curated answer.
- evals.json: corrected example terms in case 1 (real roots: Material,
  Computational Sample, Structure, Unit Cell) and case 3 (real matching
  classes: Lattice Parameter, Lattice Vector; property `has lattice parameter`).

### Security
- Implemented the documented input-validation controls that were previously
  doc-only: `--class`/`--property`/`--search` are validated against a
  safe-character allowlist (`^[\w \-/()]{1,128}$`) and a 128-char length cap;
  search results are capped at 200 entries; `owl_parser.py` now rejects
  non-`https://` URLs (plain `http://` is refused) instead of fetching them.
  All bad input exits with code 2.

### Changed
- Frontmatter description scoped to the actually-registered ontologies
  (CMSO, ASMO); the broader OCDO ecosystem is described as planned.

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
- OWL/XML parsing, class hierarchy browsing, property lookup, keyword search, ontology summarization for CMSO/OCDO ecosystem
- CLI scripts with --json output and argparse interface
- Reference documentation
