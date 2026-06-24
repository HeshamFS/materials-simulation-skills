---
name: skill-evaluator
description: >
  Rigorously evaluate an Agent Skill end-to-end across ANY coding-agent CLI —
  verify its scripts emit the documented numbers (deterministic checks), test
  whether its description triggers on the right prompts, and measure whether an
  agent following the SKILL.md beats a no-skill baseline (with/without pass-rate
  delta, mean ± stddev, benchmarked). Use whenever you need to test, benchmark,
  validate, grade, or quantify a skill's quality, check if a skill "actually
  works," compare two skill versions, optimize a skill's triggering, or set up an
  eval suite — even if the user just says "is this skill any good," "does my skill
  work," or "benchmark this skill." Drives Claude Code, OpenAI Codex, Antigravity
  (agy), Cursor, GitHub Copilot, Amp, opencode, or Grok in headless mode.
license: Apache-2.0
compatibility: >
  Python 3.10+. The deterministic layer needs no network or API key. The trigger
  and quality layers require one supported coding-agent CLI installed and
  authenticated (claude, codex, agy, cursor-agent, copilot, amp, opencode, grok).
metadata:
  author: HeshamFS
  version: "1.0.2"
  security_tier: high
  last_reviewed: "2026-06-23"
  eval_cases: 4
  standards:
    - "Agent Skills standard / evaluation spec (agentskills.io)"
    - "Anthropic open-source skill-creator reference (evaluation methodology and grader rubric)"
    - "von Neumann stability analysis (FTCS Fourier-number example used in the grading rubric)"
    - "Held-out / with-vs-without baseline (A/B delta) evaluation methodology"
    - "Per-CLI vendor headless specifications (claude -p, codex exec, cursor-agent, copilot, amp, opencode, grok)"
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Skill Evaluator

Test whether a skill is **correct, discoverable, and valuable** — not just whether
its unit tests pass. The harness is agent-agnostic: it drives whichever coding-agent
CLI the user uses, because Agent Skills are portable across all of them.

## When to use which layer

Three layers, increasing cost and fidelity (full rationale in
`references/methodology.md`):

| Layer | Question | Script | Needs a CLI? |
|------|----------|--------|--------------|
| 1. Deterministic | Do the scripts emit the **documented** numbers? | `run_script_checks.py` | No |
| 2. Trigger | Does the **description** activate on the right prompts? | `run_trigger_eval.py` | Yes |
| 3. Quality | Does following the SKILL.md **beat no skill**? | `run_quality_eval.py` → grade → `aggregate_benchmark.py` | Yes |

Always run Layer 1 (it's free). Add Layers 2–3 when you can run a coding-agent CLI.

## Step 0 — pick the agent CLI

Ask the user which coding agent they use, then map it to an adapter id. Supported:
`claude-code`, `openai-codex`, `antigravity` (the `agy` CLI that replaced Gemini
CLI on 2026-06-18), `cursor-cli`, `github-copilot-cli`, `amp`, `opencode`,
`grok-cli`. See the full matrix and auth in `references/adapters.md`, or run:

```bash
python scripts/agent_adapters.py list
```

Confirm the binary is installed and the auth env var is set (the matrix lists it).
**Before any real run, dry-run it** to see the exact command:

```bash
python scripts/agent_adapters.py build <agent> --prompt "test" --workdir /tmp/wd
```

## Step 1 — deterministic script checks (always)

```bash
python scripts/run_script_checks.py --skill <path-to-skill> --json
```

Runs the `script_checks` in the skill's `evals/evals.json`, executing each script
and grading its `--json` output against machine-checkable assertions. Exit non-zero
on any failure — safe for CI. If the skill has few/no `script_checks`, add them for
every eval whose answer is computable (schema in `references/schemas.md`); this is
the cheapest, most durable guard against doc↔code drift.

## Step 2 — trigger / discovery eval

Does the description fire on the right prompts and stay quiet on near-misses?

```bash
# Dry-run first (prints the per-CLI commands, runs nothing):
python scripts/run_trigger_eval.py --skill <path> --agent <agent> --dry-run

# Real run with a labelled query set (~20: half should-trigger, half near-miss):
python scripts/run_trigger_eval.py --skill <path> --agent <agent> \
  --queries queries.json --runs-per-query 3 --json
```

Design the query set per `references/methodology.md` (positives + tricky
negatives). Without `--queries`, the skill's eval prompts are used as
should-trigger cases — add negatives for a real discrimination test.

## Step 3 — output-quality eval (the with/without delta)

The headline measure: does an agent following the SKILL.md beat no skill?

```bash
# 1. Dry-run the plan (no tokens spent):
python scripts/run_quality_eval.py --skill <path> --agent <agent> \
  --workspace <skill>-workspace --dry-run

# 2. Real run: with-skill AND no-skill baseline, isolated clean dirs each:
python scripts/run_quality_eval.py --skill <path> --agent <agent> \
  --workspace <skill>-workspace --iteration 1 --json
```

This installs the skill into a temp project skills dir for the with-skill run,
runs a clean baseline without it, and captures `outputs/`, `response.txt`, and
`timing.json` per run.

**Then grade each run** against its `assertions` and write `grading.json`
(`references/grader.md` — re-derive numbers, require concrete evidence, no partial
credit, critique weak assertions). For mechanically checkable assertions, reuse
Layer 1 rather than eyeballing.

**Then aggregate** into the benchmark with the delta:

```bash
python scripts/aggregate_benchmark.py <skill>-workspace/iteration-1 \
  --skill-name <name> --agent <agent> --json
```

`run_summary.delta.pass_rate` is the value of the skill. Surface patterns the
averages hide (`references/methodology.md`): non-discriminating assertions,
high-variance evals, time/token tradeoffs.

**Then generate the review and put it in front of the user *before* you self-grade**
(a standalone HTML page — no server needed):

```bash
python eval-viewer/generate_review.py <skill>-workspace/iteration-1/benchmark.json -o review.html
```

It renders the with/without delta, per-configuration stats, and an expandable
per-eval breakdown of each graded assertion (text, pass/fail, evidence).

## Step 4 — iterate

Improve the skill from the signals (failed assertions, weak-assertion feedback,
transcripts, human review), generalizing rather than overfitting, keeping it lean,
explaining the *why*, and bundling repeated work into scripts. Rerun into
`iteration-<N+1>/` and compare. Stop when results satisfy the user, feedback is
empty, or gains plateau. For "is the new version actually better?", use the blind
comparison described in `references/methodology.md`.

## Outputs to report

- Layer 1: checks passed / assertions passed; any doc↔code drift found.
- Layer 2: trigger pass rate (positives that fired, negatives that stayed quiet).
- Layer 3: with-skill vs. without-skill pass rate **delta**, plus time/token cost.

## Reference files

- `references/adapters.md` — per-CLI headless command, skills dir, auth, caveats.
- `references/methodology.md` — the rigorous practices (read for non-trivial evals).
- `references/grader.md` — how to grade a run into `grading.json`.
- `references/schemas.md` — exact JSON shapes for every file.
- `eval-viewer/generate_review.py` — render a benchmark into a standalone HTML review.

## Verification checklist

Do not report a verdict until each item that applies to the layers you ran is satisfied:

- [ ] Layer 1: ran `run_script_checks.py --json`, recorded the `summary` line (`checks_passed/checks`, `assertions_passed/assertions`), and confirmed `ok: true` (process exit 0) — a non-zero exit means doc↔code drift, not a passing skill.
- [ ] Layer 1: for at least one numeric assertion, re-derived the expected value by hand and confirmed the script's emitted value matches it (e.g. `approx` within the stated `rel_tol`/`abs_tol`) — not merely that the assertion's `passed` flag is true.
- [ ] Layer 1: recorded `cases_without_checks`; if any computable eval lacks a `script_check`, noted it as a coverage gap rather than treating the run as fully verified.
- [ ] Layer 2: ran `run_trigger_eval.py` with a labelled set containing both positives AND tricky negatives, and recorded the per-class pass counts (positives that fired at rate ≥ threshold, negatives that stayed below) — a positives-only run measures recall, not discrimination.
- [ ] Layer 2: used `--runs-per-query` ≥ 3 and recorded each query's `trigger_rate`; flagged any query whose rate sits near the `--threshold` as unstable rather than counting it as a clean pass/fail.
- [ ] Layer 3: ran BOTH `with_skill` and a `without_skill` baseline, then reported `run_summary.delta.pass_rate` (the headline value) with mean ± stddev — never an absolute with-skill pass rate alone.
- [ ] Layer 3: graded each run from the actual files in its `outputs/` (re-deriving numbers / opening artifacts per `references/grader.md`), recorded concrete `evidence` per expectation, and put the outputs or `benchmark.md` in front of the user before concluding.

## Common pitfalls & rationalizations

| Tempting shortcut | Why it's wrong / what to do |
|---|---|
| "The script ran and exited 0, so the skill is correct." | Exit 0 only means the process did not crash; `run_script_checks.py` returns non-zero only when an assertion or `expect_exit` fails. Read the `assertions_passed/assertions` count and re-derive at least one number — a script can run fine and still emit the wrong value. |
| "The assertion passed, so the number is right." | A weak assertion (e.g. "mentions cfl_checker.py", or `exists`/`truthy` on a field) passes even for a wrong run. Use value+conclusion assertions (`approx`/`eq` with a re-derived expected), and act on the grader's `eval_feedback` that flags trivially-satisfiable assertions. |
| "All my trigger queries fired, so discovery works." | A positives-only set measures recall, not precision; an over-eager description that triggers on everything also passes. You need tricky near-miss negatives that stay below `--threshold` — without them the discrimination test is meaningless. |
| "One run per query is enough to read the trigger rate." | Detection is a heuristic over the transcript and triggering is stochastic; a single run gives a 0/1 rate. Use `--runs-per-query` ≥ 3 and treat rates hovering at the threshold as unstable, not decisive. |
| "With-skill pass rate is high, so the skill is valuable." | Value is the with/without **delta**, not the absolute rate. If the agent already aces the task without the skill, the delta is ~0 and the skill may only add latency/tokens. Always run the `without_skill` baseline and report `delta.pass_rate`. |
| "Assertions passed, no need to open the output files." | Automated grading only checks what you thought to assert, and a transcript can claim work it did not do. Open the files in `outputs/`, re-derive the numbers, read `user_notes.md`, and review `benchmark.md` (or have the user review it) before declaring the skill good. |

## Security

### Input Validation
- `--agent` is resolved against a fixed allowlist of known adapter ids/aliases
  (`agent_adapters.py`); unknown values are rejected (exit 2).
- `--skill` must be a directory containing `SKILL.md` or the runners exit 2.
- `script_checks` operators and dotted paths are matched against fixed sets; no
  user string is ever `eval()`'d or passed to a shell.

### File Access
- The deterministic layer runs a skill's own scripts with the real interpreter and
  reads only that skill's `evals/evals.json`.
- The quality/trigger layers create isolated working directories under a
  user-supplied workspace, copy the skill into them, and write results there.

### Tool Restrictions
- **Bash**: runs the harness Python scripts and the selected coding-agent CLI.
- **Read/Grep/Glob**: inspect skills and results. **Write**: scaffold workspaces.

### Safety Measures
- No `eval()`/`exec()`; subprocess calls use explicit argument lists (never
  `shell=True`); commands are built from the adapter spec, not string-concatenated.
- **The trigger/quality layers pass each CLI's auto-approve flag** (e.g.
  `--dangerously-skip-permissions`), which runs the agent with reduced safeguards.
  Only evaluate skills you trust, ideally inside a sandbox/container. Always
  `--dry-run` first to inspect the exact command. Auth is read from environment
  variables, never passed as command arguments.

## Limitations
- Layers 2–3 require a supported CLI installed and authenticated; otherwise use
  Layer 1 only.
- Trigger detection is a cross-tool heuristic (did the transcript consult the
  skill?); for the most precise detection on Claude Code, parse its stream-json
  tool-use events.
- Token accounting is best-effort — only some CLIs report usage in headless output.
- New CLIs (Antigravity, Grok) are *medium* confidence; verify flags with the
  vendor `--help` and `--dry-run`.
