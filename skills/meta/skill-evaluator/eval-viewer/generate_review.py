#!/usr/bin/env python3
"""Render a skill-evaluation benchmark into a standalone HTML review page.

Turns the ``benchmark.json`` produced by ``aggregate_benchmark.py`` (the
with-skill vs. without-skill results) into a single self-contained HTML file you
can open in a browser — the spec's "put outputs in front of a human before you
self-grade" step. No server, no JavaScript framework, no third-party deps.

  python eval-viewer/generate_review.py <benchmark.json> -o review.html
  python eval-viewer/generate_review.py <benchmark.json> --open    # also open in browser

The page shows the with/without pass-rate delta, per-configuration stats, and an
expandable per-eval breakdown of each graded assertion (text, pass/fail, evidence).
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path


def _esc(x: object) -> str:
    return html.escape(str(x), quote=True)


def _stat_cell(stat: dict, pct: bool = False, suffix: str = "") -> str:
    if not stat:
        return "—"
    mean = stat.get("mean", 0)
    std = stat.get("stddev", 0)
    if pct:
        return f"{mean * 100:.0f}% ± {std * 100:.0f}%"
    return f"{mean:.1f}{suffix} ± {std:.1f}"


def render(benchmark: dict) -> str:
    meta = benchmark.get("metadata", {})
    rs = benchmark.get("run_summary", {})
    configs = [c for c in rs if c != "delta"]
    delta = rs.get("delta", {})
    runs = benchmark.get("runs", [])

    # Summary table rows.
    summary_rows = ""
    metrics = [("Pass rate", "pass_rate", True, ""), ("Time", "time_seconds", False, "s"), ("Tokens", "tokens", False, "")]
    for label, key, pct, suf in metrics:
        cells = "".join(f"<td>{_esc(_stat_cell(rs.get(c, {}).get(key, {}), pct, suf))}</td>" for c in configs)
        d = delta.get(key, "—")
        summary_rows += f"<tr><th>{_esc(label)}</th>{cells}<td class='delta'>{_esc(d)}</td></tr>"

    config_headers = "".join(f"<th>{_esc(c.replace('_', ' ').title())}</th>" for c in configs)

    # Per-eval breakdown: group runs by eval_id, then configuration.
    by_eval: dict = {}
    for r in runs:
        by_eval.setdefault(r.get("eval_id"), []).append(r)

    eval_blocks = ""
    for eval_id in sorted(by_eval, key=str):
        cfg_blocks = ""
        for r in sorted(by_eval[eval_id], key=lambda x: x.get("configuration", "")):
            res = r.get("result", {})
            pr = res.get("pass_rate", 0)
            cls = "good" if pr >= 0.999 else ("mid" if pr >= 0.5 else "bad")
            exps = ""
            for e in r.get("expectations", []):
                ok = e.get("passed")
                mark = "✓" if ok else "✗"
                mcls = "pass" if ok else "fail"
                exps += (f"<li class='{mcls}'><span class='mark'>{mark}</span> {_esc(e.get('text', ''))}"
                         f"<div class='evidence'>{_esc(e.get('evidence', ''))}</div></li>")
            cfg_blocks += (
                f"<div class='cfg'><div class='cfg-head {cls}'>"
                f"{_esc(r.get('configuration', '?'))} — {res.get('passed', 0)}/{res.get('total', 0)} "
                f"({pr * 100:.0f}%)</div><ul class='exps'>{exps or '<li>(no graded assertions)</li>'}</ul></div>"
            )
        eval_blocks += (f"<details class='eval'><summary>eval {_esc(eval_id)}</summary>"
                        f"<div class='cfgs'>{cfg_blocks}</div></details>")

    notes = "".join(f"<li>{_esc(n)}</li>" for n in benchmark.get("notes", []))
    notes_block = f"<h2>Notes</h2><ul class='notes'>{notes}</ul>" if notes else ""

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Skill eval review — {_esc(meta.get('skill_name', ''))}</title>
<style>
  body {{ font-family: system-ui, -apple-system, Segoe UI, sans-serif; max-width: 920px; margin: 2rem auto; padding: 0 1rem; color: #1a1a1a; }}
  h1 {{ font-size: 1.5rem; margin-bottom: .25rem; }}
  .meta {{ color: #555; margin-bottom: 1.5rem; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ddd; padding: .5rem .75rem; text-align: left; }}
  thead th {{ background: #f5f5f7; }}
  td.delta {{ font-weight: 700; }}
  details.eval {{ border: 1px solid #e3e3e3; border-radius: 8px; margin: .5rem 0; padding: .25rem .75rem; }}
  details.eval > summary {{ cursor: pointer; font-weight: 600; padding: .4rem 0; }}
  .cfgs {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
  .cfg {{ flex: 1; min-width: 280px; }}
  .cfg-head {{ font-weight: 600; padding: .3rem .5rem; border-radius: 6px; margin: .4rem 0; }}
  .cfg-head.good {{ background: #e6f6ec; }} .cfg-head.mid {{ background: #fff6e0; }} .cfg-head.bad {{ background: #fde7e7; }}
  ul.exps {{ list-style: none; padding-left: 0; }}
  ul.exps li {{ margin: .35rem 0; }}
  .mark {{ font-weight: 700; }}
  li.pass .mark {{ color: #1a7f37; }} li.fail .mark {{ color: #cf222e; }}
  .evidence {{ color: #555; font-size: .85rem; margin-left: 1.2rem; }}
</style></head><body>
<h1>Skill eval review: {_esc(meta.get('skill_name', '(unknown)'))}</h1>
<div class="meta">agent: <b>{_esc(meta.get('agent', 'n/a'))}</b> · evals: {_esc(', '.join(map(str, meta.get('evals_run', []))))}</div>
<h2>Summary</h2>
<table><thead><tr><th>Metric</th>{config_headers}<th>Delta</th></tr></thead>
<tbody>{summary_rows}</tbody></table>
<p>The <b>delta</b> in pass rate is the measure of the skill's value (with-skill minus baseline).</p>
<h2>Per-eval breakdown</h2>
{eval_blocks or '<p>(no runs)</p>'}
{notes_block}
</body></html>
"""


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Render a benchmark.json into a standalone HTML review")
    p.add_argument("benchmark", help="Path to benchmark.json (from aggregate_benchmark.py)")
    p.add_argument("-o", "--output", default=None, help="Output HTML path (default: review.html beside the benchmark)")
    p.add_argument("--open", action="store_true", dest="open_browser", help="Open the result in a browser")
    p.add_argument("--json", action="store_true", help="Print a summary as JSON instead of a status line")
    args = p.parse_args(argv)

    bench_path = Path(args.benchmark)
    if not bench_path.exists():
        print(f"benchmark not found: {bench_path}", file=sys.stderr)
        return 2
    benchmark = json.loads(bench_path.read_text(encoding="utf-8"))
    out = Path(args.output) if args.output else bench_path.with_name("review.html")
    out.write_text(render(benchmark), encoding="utf-8")

    delta = benchmark.get("run_summary", {}).get("delta", {})
    if args.json:
        print(json.dumps({"output": str(out), "delta": delta, "runs": len(benchmark.get("runs", []))}, indent=2))
    else:
        print(f"Wrote {out}  (pass-rate delta: {delta.get('pass_rate', 'n/a')})")
    if args.open_browser:
        import webbrowser
        webbrowser.open(out.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
