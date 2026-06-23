# Skill Evaluation Harness

This project distinguishes two very different questions:

1. **Do the scripts compute correctly?** — answered by the unit/integration test
   suite (`tests/`, 1269 tests). These call each script's pure-function core and
   CLI directly.
2. **Do the *skills* work as skills?** — i.e. when an agent reads a `SKILL.md`
   and follows it on a realistic prompt, does it pick the right script, pass the
   right arguments, trigger when it should, and reach the scientifically correct,
   useful answer? This is what the **evaluation harness** addresses, following the
   [Agent Skills evaluation spec](https://agentskills.io/skill-creation/evaluating-skills).

The harness has **three layers**, all built. Layer 1 ships as a repo CI gate;
Layers 2–3 ship as the agent-agnostic [`skill-evaluator`](../skills/meta/skill-evaluator/)
skill (driven through whichever coding-agent CLI you use). What remains is breadth
and polish — tracked on the [roadmap](../ROADMAP.md).

| Layer | Question | Where | Needs a CLI / key? |
|------|----------|-------|--------------------|
| 1. Deterministic `script_checks` | Do the scripts emit the **documented** numbers? | `mss eval` / `tools/run_skill_evals.py` (CI) and `skill-evaluator/scripts/run_script_checks.py` | No |
| 2. Trigger / discovery | Does the **description** activate on the right prompts? | `skill-evaluator/scripts/run_trigger_eval.py` | Yes |
| 3. Output-quality (with/without delta) | Does following the `SKILL.md` **beat no skill**? | `skill-evaluator/scripts/run_quality_eval.py` → grade → `aggregate_benchmark.py` | Yes |

---

## Layer 1 — Deterministic `script_checks` (built, CI-gated)

The spec's own advice: *"For assertions that can be checked by code … use a
verification script — scripts are more reliable than LLM judgment for mechanical
checks and reusable across iterations."*

Each eval case in a skill's `evals/evals.json` may carry an optional
`script_checks` array. Each check runs one script with concrete arguments and
grades its `--json` output against machine-checkable assertions. This catches the
single largest defect class found in the audit — **drift between what a
`SKILL.md` documents and what its scripts actually emit** (wrong numbers, renamed
fields, changed thresholds) — and prevents regression, with no LLM or network.

### Format

```jsonc
{
  "id": 1,
  "prompt": "… heat equation … dx=0.01 dt=0.001 alpha=1e-5 … will it blow up?",
  "expected_output": "Fourier analysis showing stable, Fo=1e-4 << 0.5.",
  "assertions": ["Computes Fo = alpha*dt/dx^2 = 1e-4", "…"],   // graded by Layer 3
  "script_checks": [                                            // graded by Layer 1
    {
      "description": "Stable heat eqn: Fo=1e-4 << 0.5",
      "cmd": ["scripts/cfl_checker.py", "--dx", "0.01", "--dt", "0.001",
              "--diffusivity", "1e-5", "--json"],
      "expect_exit": 0,
      "assert": [
        { "path": "metrics.fourier", "op": "approx", "value": 1e-4, "rel_tol": 1e-3 },
        { "path": "stable", "op": "eq", "value": true }
      ]
    }
  ]
}
```

- `cmd[0]` is resolved **relative to the skill directory**, so checks stay
  portable when a skill is copied into another agent's skills folder.
- `path` is a dotted path into the JSON (`metrics.fourier`, `results.coefficients.2`).
- `op` ∈ `eq, ne, approx, gt, ge, lt, le, contains, in, type, exists, truthy, falsy`.
  `approx` accepts `rel_tol` / `abs_tol`.

### Running

```bash
mss eval                      # all skills; exits non-zero if any check fails
mss eval --skill mesh-generation
mss eval --json               # structured output for tooling
python tools/run_skill_evals.py   # standalone, same behavior (used in CI)
```

CI runs `tools/run_skill_evals.py` in the `validate-quality` job. The engine and
every seeded check are themselves tested in `tests/integration/test_eval_runner.py`.
The same engine is vendored standalone in
`skill-evaluator/scripts/run_script_checks.py` so the skill is portable.

### Coverage today

Seeded checks act as **skill-level regression guards** for the highest-risk
behaviors fixed in the audit (CFL/Fourier verdicts, GCI/Richardson observed
order, mesh skewness vs. anisotropy, least-squares solver selection, finite-
difference stencils), plus the `skill-evaluator` adapter registry. Extending
coverage = adding `script_checks` to more eval cases. Cases with no `script_checks`
are reported as "LLM-judge only".

---

## Layers 2 & 3 — agent-agnostic, via the `skill-evaluator` skill (built)

Layer 1 verifies the *scripts* produce the documented numbers. It does **not**
verify the parts that make a skill a skill: that its **description triggers** the
skill, and that an agent **reading the SKILL.md** chooses the right script and
reasons correctly. Those require running prompts through an actual agent, so they
live in the [`skill-evaluator`](../skills/meta/skill-evaluator/) skill, which is
**agent-agnostic** — it drives whichever coding-agent CLI you use.

### Pluggable per-CLI adapters

`skill-evaluator/scripts/agent_adapters.py` encodes, for each supported CLI, the
exact headless command, the auto-approve flag (so a run never hangs on a
permission prompt), where to install a skill so the CLI discovers it, and the auth
env var. Supported: **Claude Code, OpenAI Codex, Google Antigravity (`agy`),
Cursor, GitHub Copilot, Amp, opencode, Grok**. See
[`skill-evaluator/references/adapters.md`](../skills/meta/skill-evaluator/references/adapters.md)
for the matrix, sources, and caveats.

> Note: Google retired the **Gemini CLI on 2026-06-18** and replaced it with
> **Antigravity CLI** (`agy`); the `gemini` alias resolves to the `antigravity`
> adapter.

Every runner supports `--dry-run`, which prints the exact per-CLI command without
executing — so adapter wiring is verifiable with no CLI installed and no tokens
spent.

### Layer 2 — Trigger / discovery eval

```bash
python skills/meta/skill-evaluator/scripts/run_trigger_eval.py \
  --skill <path> --agent <cli> --queries queries.json --runs-per-query 3 --json
```

Runs a labelled query set (~20: half should-trigger, half tricky near-misses,
each run several times) through the chosen CLI with the skill installed, and
reports the trigger rate vs. the expected label. Directly targets the
**trigger-gaps** the audit surfaced.

### Layer 3 — Output-quality eval (the with/without delta)

The official spec loop, agent-agnostic:

1. For each eval case, run the prompt twice in **clean working directories** via
   the chosen CLI: **with_skill** (skill installed) and **without_skill** (clean
   baseline; Claude Code additionally gets `--bare`).
2. Capture `outputs/`, `response.txt`, and `timing.json` (`duration_ms`, and
   `total_tokens` where the CLI reports it).
3. **Grade** each natural-language `assertion` → `grading.json` (see
   [`grader.md`](../skills/meta/skill-evaluator/references/grader.md): require
   concrete evidence, re-derive numbers, no partial credit, critique weak
   assertions). Mechanical assertions defer to Layer 1.
4. **Aggregate** → `benchmark.json`/`.md` with the **delta**: the with-skill minus
   without-skill pass rate is *the* measure of a skill's value, traded off against
   its extra tokens/time.

```bash
# Dry-run the plan (no tokens):
python skills/meta/skill-evaluator/scripts/run_quality_eval.py \
  --skill <path> --agent <cli> --workspace <skill>-workspace --dry-run
# Real run, then aggregate:
python skills/meta/skill-evaluator/scripts/run_quality_eval.py \
  --skill <path> --agent <cli> --workspace <skill>-workspace --iteration 1
python skills/meta/skill-evaluator/scripts/aggregate_benchmark.py \
  <skill>-workspace/iteration-1 --skill-name <name> --agent <cli> --json
```

```
<skill>-workspace/iteration-N/
  eval-<id>-<slug>/with_skill/run-1/{workdir,outputs,response.txt,timing.json,grading.json}
  eval-<id>-<slug>/without_skill/run-1/{...}
  benchmark.json  benchmark.md
```

For "is the new version actually better?", use the **blind comparison** described
in [`methodology.md`](../skills/meta/skill-evaluator/references/methodology.md)
(a judge sees both outputs without knowing which is which).

---

## How the layers complement the test suite

| Question | Mechanism | Where |
|---|---|---|
| Does the function compute the right number? | unit tests on the pure core | `tests/unit/` |
| Does the CLI emit valid, schema-correct JSON? | integration tests | `tests/integration/` |
| Does the script emit the **documented** number for a realistic prompt? | `script_checks` (Layer 1) | `mss eval` (CI) |
| Does the skill's **description trigger** it on the right prompts? | trigger eval (Layer 2) | `skill-evaluator` |
| Does an agent **following the SKILL.md** beat no skill? | with/without LLM-judge (Layer 3) | `skill-evaluator` |
