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
  version: "1.0.0"
  security_tier: high
  last_reviewed: "2026-06-23"
  eval_cases: 4
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
high-variance evals, time/token tradeoffs. **Put outputs in front of the user
before concluding.**

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
