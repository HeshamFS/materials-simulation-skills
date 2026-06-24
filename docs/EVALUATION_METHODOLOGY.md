# Evaluation Methodology

How this project knows its skills work — the practices behind the "validated, not
just curated" claim. This complements [EVAL_HARNESS.md](EVAL_HARNESS.md) (the
tooling) and [PROTOCOL.md](PROTOCOL.md) (the conformance rules) by explaining the
*reasoning* and reporting the *results*.

## Two different questions

A skill can fail in two independent ways, so we test for both:

1. **Is the script correct?** Does `compute_cfl()` return the right number? —
   answered by the unit/integration suite (1283 tests on the pure-function cores
   and the CLI/JSON contracts, across Python 3.10–3.12).
2. **Does the *skill* work as a skill?** When an agent reads `SKILL.md` and follows
   it on a realistic prompt, does it pick the right script, pass the right
   arguments, trigger when it should, and reach the scientifically correct, useful
   answer? Script tests say nothing about this — it is the harder, more important
   question, and the one most skill collections never ask.

## Three evaluation layers

| Layer | Question | Mechanism | Cost |
|---|---|---|---|
| 1. Deterministic | Do scripts emit the **documented** numbers for a realistic prompt? | `script_checks` graded by code | free, in CI |
| 2. Trigger | Does the **description** activate the skill on the right prompts and stay quiet on near-misses? | run the prompt through an agent CLI, detect skill consultation | needs a CLI |
| 3. Output-quality | Does an agent **following the SKILL.md** beat *no skill*? | with-skill vs. baseline executor + grading | needs a CLI |

### Layer 1 — deterministic `script_checks` (100% coverage)

Every one of the **101 eval cases** carries machine-checkable `script_checks`
that run the script and assert its exact `--json` output (**117 checks, 686
assertions**). This is the durable guard against the single largest defect class
we found — *documentation drifting from code* — and it runs in CI with no LLM or
network. Coverage is enforced: a stale or missing check fails the build.

### Layer 2 & 3 — agent-agnostic, measured uplift

Skills are exercised end-to-end by the [`skill-evaluator`](../skills/meta/skill-evaluator)
across coding-agent CLIs (Claude Code, Codex, Antigravity, Cursor, Copilot, Amp,
opencode, Grok). The headline metric is the **delta**: the with-skill minus
without-skill pass rate on the *same* prompts. A skill that the agent already
handles perfectly without help has a delta near zero — and we treat that as a
signal to make the eval more discriminating, not as success.

## What the evaluation found

The skills were audited end-to-end: each was handed to a *fresh* agent that used
it on its eval prompts, ran the scripts, recomputed every numeric claim, and
checked the physics against authoritative references — and **every finding was
re-verified by an independent skeptic** before counting.

**83 confirmed problems** (3 critical, 16 high, 36 medium, 28 low), e.g.:

- A flagship worked example computed the Fourier number **wrong by 1000×** and
  reached the opposite stability verdict.
- Generated SLURM scripts placed `set -euo pipefail` before the `#SBATCH` lines,
  so the scheduler **ignored every directive** (confirmed against the SchedMD spec).
- A bottleneck detector read the wrong JSON keys and **always reported "no
  bottlenecks."**

All 83 were fixed and locked behind regression tests + `script_checks`.

**Measured uplift** (with vs. without, graded strictly):

- **with-skill mean pass rate ≈ 0.99**, **baseline ≈ 0.64**, **mean delta ≈ +0.35**.
- 22 of 23 domain skills scored a perfect 1.0 with the skill.
- The evaluation also *honestly* surfaced its own limits: six planner-style skills
  initially showed ~0 delta (their assertions passed without the skill) — fixed by
  adding discriminating, script-pinned checks; and one skill was caught
  *hallucinating* fixture values even with the skill — fixed by grounding its
  evals in real fixtures.

## How conformance is enforced

CI (`validate-quality` job) runs on every push:

```bash
mss validate                     # spec-valid frontmatter, name rules, Security subsections, evals, changelog
mss eval                         # every deterministic script_check passes (doc<->code drift gate)
python tools/build_index.py --check   # the machine-readable index/marketplace are fresh
python -m pytest tests/          # 3.10-3.12 matrix: script correctness + CLI/JSON + protocol conformance
```

The Layer-3 LLM-judge is wired as an **opt-in** CI job (runs when an agent
credential is configured) so it never blocks the deterministic gate.

## Honest caveats

- Much of the measured delta comes from **tool-invocation assertions** (the
  baseline often reaches the right conclusion but doesn't run the named script);
  the skill's value there is *reproducible, script-backed evidence*, which we
  consider legitimate but distinct from raw correctness.
- The newest CLIs (Antigravity, Grok) are *medium* confidence — adapter commands
  are verified, but full live runs depend on quota/auth.
- Token accounting is best-effort; only some CLIs report usage headlessly.

## Reproducing

```bash
pip install -e ".[dev]"
mss eval                 # Layer 1, deterministic, no credentials
# Layer 3 (needs a coding-agent CLI + key), dry-run first to inspect commands:
python skills/meta/skill-evaluator/scripts/run_quality_eval.py \
  --skill skills/core-numerical/numerical-stability --agent <cli> --workspace ws --dry-run
```
