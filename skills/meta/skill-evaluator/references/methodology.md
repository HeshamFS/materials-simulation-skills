# Evaluation methodology

The rigorous practices behind the harness, distilled from the Agent Skills
evaluation spec and the open-source `skill-creator` reference. Read this when you
want to do more than run the scripts — when you want the results to actually
*mean* something.

## Three layers, increasing cost and fidelity

1. **Deterministic `script_checks`** (`run_script_checks.py`) — no LLM, no network.
   Verifies a skill's scripts emit the *documented* numbers for an eval prompt.
   Catches doc↔code drift; always run it; cheap enough for CI.
2. **Trigger / discovery eval** (`run_trigger_eval.py`) — does the *description*
   activate the skill on the right prompts and stay quiet on near-misses?
3. **Output-quality eval** (`run_quality_eval.py` + grading + `aggregate_benchmark.py`)
   — does an agent *following the SKILL.md* produce a better answer than no skill?

Run them in that order. Each is independently useful; together they tell you
whether a skill is correct, discoverable, and valuable.

## The with/without delta is the point

A skill's value is **not** its absolute pass rate — it's the **delta** between
with-skill and without-skill on the same prompts. If the agent already aces a task
without the skill, the skill adds nothing there (and may add latency/tokens). Always
run the baseline. Baseline = no skill (new skill) or the previous version
(improving one). Weigh the pass-rate gain against the time/token cost in the delta.

## Write discriminating assertions

An assertion is only worth having if it **passes when the skill genuinely succeeds
and fails when it doesn't**.

- Good: "metrics.fourier equals alpha·dt/dx² = 1e-4" (re-derivable, discriminating).
- Weak: "mentions cfl_checker.py" (a wrong run that names the script still passes).
- Weak: "the output is good" (ungradable).

For numbers, assert the **value and the conclusion**, not just that a number
appeared. Anything mechanically checkable should become a `script_check` rather
than an LLM assertion — code is more reliable and reusable. The grader actively
critiques weak assertions (`eval_feedback`); act on that.

## Designing trigger queries

~20 queries, realistic and specific (file paths, numbers, context, casual phrasing,
typos). 8–10 **positives** with varied phrasing including implicit needs; 8–10
**near-miss negatives** that share keywords but need a different tool. Avoid
obviously-irrelevant negatives — they test nothing. Run each query several times
(default 3) for a stable trigger rate; if you optimize the description, hold out
~40% of queries and select on the held-out score to avoid overfitting. Note: simple
one-step prompts may not trigger any skill (the agent just does them) — make
positives substantive enough that consulting a skill actually helps.

## Put outputs in front of a human before you self-grade

Automated grading only checks what you thought to assert. Generate the human-review
artifacts (the outputs, the benchmark table) and look at them — or have the user
look — *before* you conclude. This catches "technically passes, misses the point."
Record specific, actionable feedback per eval; empty feedback means it looked fine.

## Blind comparison (optional, for "is the new version better?")

Give two outputs to an independent judge **without revealing which is which** and
have it score holistic quality (correctness, completeness, organization, usability).
Two versions can pass identical assertions yet differ a lot in quality. Then analyze
*why* the winner won — which instruction or script made the difference — and feed
that into the next revision.

## Analyze patterns, not just averages

- Assertions that pass in **both** configs don't measure skill value — replace them.
- Assertions that fail in **both** are broken or too hard — fix them.
- Assertions that pass **with** and fail **without** are where the skill earns its
  keep — understand the mechanism.
- High variance across repeats → flaky eval or ambiguous instructions; tighten.
- Time/token outliers → read the transcript for wasted steps; trim the skill.

## Improving the skill (the loop)

Generalize from failures (don't overfit to the test prompts); keep the skill lean
(remove instructions that cause wasted work); explain the *why* behind each rule
(reasoning beats rigid ALWAYS/NEVER); and bundle repeated work — if every run
reinvents the same helper, make it a tested `script` in the skill. Then rerun all
cases into `iteration-<N+1>/`, re-grade, re-review. Stop when results satisfy you,
feedback is consistently empty, or gains plateau.
