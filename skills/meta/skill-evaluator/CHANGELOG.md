# Changelog — skill-evaluator

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
