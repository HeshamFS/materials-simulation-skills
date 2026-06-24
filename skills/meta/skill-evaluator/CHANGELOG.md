# Changelog — skill-evaluator

## v1.0.2 (2026-06-24)

- Added `eval-viewer/generate_review.py`: renders a `benchmark.json` into a
  standalone HTML review (with/without pass-rate delta, per-configuration stats,
  and an expandable per-eval breakdown of each graded assertion). Supports the
  "put outputs in front of a human before self-grading" step; no server or
  third-party dependencies. Wired into the Step-3 quality-eval flow in SKILL.md.

## v1.0.1 (2026-06-24)

- Added a **Verification checklist** section (7 evidence-based items) tying a
  trustworthy verdict to concrete artifacts per layer: the `run_script_checks.py`
  summary counts and exit status, hand re-derivation of at least one numeric
  assertion, `cases_without_checks` coverage gaps, positives+negatives trigger
  pass counts, `--runs-per-query` ≥ 3 stability, and the `run_summary.delta.pass_rate`
  (mean ± stddev) with grading driven by the actual `outputs/`.
- Added a **Common pitfalls & rationalizations** table (6 rows) covering the
  failure modes specific to this harness: treating exit 0 as correctness, trusting
  weak/`exists`/`truthy` assertions, positives-only trigger sets, single-run trigger
  rates, reading absolute pass rate instead of the with/without delta, and grading
  from the transcript instead of the output files.

## v1.0.0 (2026-06-23)

Initial release. An agent-agnostic harness for rigorously evaluating Agent Skills,
modeled on the Agent Skills evaluation spec and the open-source `skill-creator`
reference.

- **Three evaluation layers**: deterministic `script_checks` (no LLM/CI-safe),
  trigger/discovery eval, and with-skill-vs-baseline output-quality eval with the
  pass-rate delta.
- **Pluggable per-CLI adapters** (`agent_adapters.py`) for Claude Code, OpenAI
  Codex, Google Antigravity (`agy`), Cursor, GitHub Copilot, Amp, opencode, and
  Grok — each researched official-docs-first and cross-checked (headless command,
  skills directory, auto-approve flag, auth).
- Gemini CLI was retired 2026-06-18 and replaced by Antigravity CLI; the
  `gemini`/`gemini-cli` aliases resolve to the `antigravity` adapter.
- `--dry-run` on every runner prints the exact per-CLI command without executing,
  so adapter wiring is verifiable with no CLI installed and no tokens spent.
- Bundled references: adapter matrix, methodology, grader rubric, JSON schemas.
- `aggregate_benchmark.py` produces `benchmark.json`/`.md` with mean ± stddev and
  the with/without delta.
