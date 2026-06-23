# Grader rubric

How to grade one run's outputs against its assertions and write `grading.json`.
Use this whether you grade inline, spawn a grader subagent, or drive a separate
coding-agent CLI as the judge. Adapted from the open-source `skill-creator`
reference grader and tightened for scientific/numerical skills.

## Core principle

A passing grade on a weak assertion is worse than useless — it manufactures false
confidence. You have two jobs: **grade the outputs**, and **critique the
assertions themselves**. When an assertion is trivially satisfiable, or an
important outcome has no assertion, say so in `eval_feedback`.

## Inputs

- `expectations` / `assertions`: the statements to grade (strings).
- The run's outputs directory (files the agent produced) and its captured
  response/transcript.
- Optionally `metrics.json` (tool calls) and `timing.json`.

## Process

1. **Read the transcript/response** fully — note the steps taken and the result.
2. **Examine every output file** relevant to the assertions. Do not rely on what
   the transcript *says* it produced — open the files and check. For non-text
   outputs, inspect them with appropriate tools.
3. **Grade each assertion** PASS/FAIL with concrete evidence:
   - **PASS** only with clear evidence of *genuine* task completion — substance,
     not surface compliance. A file with the right name but empty/wrong content is
     a FAIL.
   - **FAIL** when there is no evidence, evidence contradicts the assertion, the
     assertion can't be verified from the outputs, or the result is right only by
     coincidence.
   - **When uncertain, the burden of proof is on the assertion** → FAIL.
   - **No partial credit.** Each assertion is pass or fail.
4. **For numerical / scientific skills, re-derive the numbers.** If an assertion
   says "computes Fourier number Fo = 0.1", recompute it yourself (or run the
   skill's own script) and confirm the output's value matches the correct value —
   not merely that *a* number was produced. Catch right-method/wrong-number and
   wrong-conclusion errors. A claimed verdict ("stable") must follow from a
   correct quantity, not a plausible-looking one.
5. **Extract and verify claims** beyond the assertions — factual ("the matrix is
   1000×1000"), process ("used cfl_checker.py"), and quality ("converged")
   claims. Flag any that are unverifiable or false.
6. **Read `user_notes.md`** if present; surface uncertainties/workarounds even
   when assertions pass.
7. **Critique the assertions** (`eval_feedback`) — only when there's a clear gap:
   an assertion that would also pass for a wrong output; an important observed
   outcome no assertion covers; an assertion not checkable from the outputs. Keep
   the bar high: flag things the eval author would say "good catch" about.

## Output: grading.json

```json
{
  "expectations": [
    {"text": "Computes Fourier number Fo = alpha*dt/dx^2 = 1e-4", "passed": true,
     "evidence": "Ran cfl_checker.py from outputs/: metrics.fourier=0.0001; matches alpha*dt/dx^2 = 1e-5*1e-3/1e-4."},
    {"text": "Concludes the run is stable", "passed": true,
     "evidence": "Response states 'stable, Fo=1e-4 << 0.5 limit'; consistent with the recomputed value."}
  ],
  "summary": {"passed": 2, "failed": 0, "total": 2, "pass_rate": 1.0},
  "claims": [
    {"claim": "Fo limit for 1D explicit diffusion is 0.5", "type": "factual",
     "verified": true, "evidence": "Standard von Neumann result for FTCS."}
  ],
  "user_notes_summary": {"uncertainties": [], "needs_review": [], "workarounds": []},
  "eval_feedback": {
    "suggestions": [
      {"assertion": "References cfl_checker.py",
       "reason": "Mentioning the script name passes even if the wrong dt was used — also assert the recomputed Fo value."}
    ],
    "overall": "Assertions check presence; add value/conclusion checks for the numbers."
  }
}
```

Required fields the aggregator/viewer read: `expectations[].text`, `.passed`,
`.evidence`, and `summary.{passed,failed,total,pass_rate}`. Use those exact names.

## Guidelines

- Be objective and specific — quote the exact value or text you relied on.
- Apply the same standard to every assertion.
- Prefer a **script** for mechanical checks (valid JSON, exact number, file
  exists with content) — reuse the deterministic `run_script_checks.py` layer for
  anything expressible as a `script_check`, and reserve LLM judgment for the rest.
