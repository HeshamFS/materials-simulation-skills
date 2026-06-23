# JSON schemas

The data structures the harness reads and writes. Field names are load-bearing —
the aggregator and graders depend on them exactly.

## `evals/evals.json` (authored per skill)

```json
{
  "skill_name": "numerical-stability",
  "evals": [
    {
      "id": 1,
      "prompt": "Realistic user message (file paths, numbers, context).",
      "expected_output": "Human-readable description of success.",
      "files": ["evals/files/input.json"],
      "assertions": [
        "Verifiable statement about the output",
        "The skill used cfl_checker.py"
      ],
      "script_checks": [
        {
          "description": "label",
          "cmd": ["scripts/cfl_checker.py", "--dx", "0.01", "--json"],
          "expect_exit": 0,
          "assert": [
            {"path": "metrics.fourier", "op": "approx", "value": 1e-4, "rel_tol": 1e-3},
            {"path": "stable", "op": "eq", "value": true}
          ]
        }
      ]
    }
  ]
}
```

- `assertions` — natural-language checks graded by an LLM judge (Layer 2).
- `script_checks` — deterministic checks graded by code (Layer 1, no LLM).
  - `cmd[0]` is relative to the skill directory.
  - `path` is a dotted path into the script's JSON output (list indices integer).
  - `op` ∈ `eq, ne, approx, gt, ge, lt, le, contains, in, type, exists, truthy, falsy`;
    `approx` takes `rel_tol`/`abs_tol`.

## trigger query set (for `run_trigger_eval.py --queries`)

```json
[
  {"query": "concrete, realistic prompt that SHOULD trigger the skill", "should_trigger": true},
  {"query": "tricky near-miss that should NOT trigger it", "should_trigger": false}
]
```

Design ~20: 8–10 positives (varied phrasing, casual + precise, implicit needs) and
8–10 **near-miss negatives** (share keywords but need something else). Avoid
obviously-irrelevant negatives — they test nothing.

## `grading.json` (one per run)

```json
{
  "expectations": [
    {"text": "assertion text", "passed": true, "evidence": "concrete quote/value"}
  ],
  "summary": {"passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67},
  "claims": [{"claim": "...", "type": "factual", "verified": true, "evidence": "..."}],
  "user_notes_summary": {"uncertainties": [], "needs_review": [], "workarounds": []},
  "eval_feedback": {"suggestions": [{"assertion": "...", "reason": "..."}], "overall": "..."}
}
```

Required: `expectations[].{text,passed,evidence}` and
`summary.{passed,failed,total,pass_rate}`.

## `timing.json` (one per run, written by the executor)

```json
{"duration_ms": 23332, "total_duration_seconds": 23.3, "total_tokens": 84852}
```

`total_tokens` is best-effort: only some CLIs expose usage in headless output
(Claude-style JSON envelope). `null`/`0` is acceptable when unavailable.

## `benchmark.json` (per iteration, written by `aggregate_benchmark.py`)

```json
{
  "metadata": {"skill_name": "...", "agent": "claude-code", "evals_run": [1, 2]},
  "runs": [
    {"eval_id": 1, "configuration": "with_skill", "run_number": 1,
     "result": {"pass_rate": 1.0, "passed": 2, "failed": 0, "total": 2,
                "time_seconds": 42.5, "tokens": 3800},
     "expectations": [{"text": "...", "passed": true, "evidence": "..."}]}
  ],
  "run_summary": {
    "with_skill":    {"pass_rate": {"mean": 1.0, "stddev": 0.0, "min": 1.0, "max": 1.0}, "time_seconds": {...}, "tokens": {...}},
    "without_skill": {"pass_rate": {"mean": 0.5, "stddev": 0.0, "min": 0.5, "max": 0.5}, "time_seconds": {...}, "tokens": {...}},
    "delta": {"pass_rate": "+0.50", "time_seconds": "+13.0", "tokens": "+1700"}
  },
  "notes": []
}
```

`configuration` must be exactly `with_skill` / `without_skill`. The headline number
is `run_summary.delta.pass_rate` — how much the skill improves over no skill.

## workspace layout

```
<skill>-workspace/
  iteration-N/
    eval-<id>-<slug>/
      with_skill/run-1/{workdir/, outputs/, response.txt, timing.json, run.json, grading.json}
      without_skill/run-1/{...}
    benchmark.json
    benchmark.md
```
