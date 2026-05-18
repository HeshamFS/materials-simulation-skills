#!/usr/bin/env python3
"""Compute current README metrics from repository contents."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials_simulation_skills.skill_utils import collect_metrics  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-tests", action="store_true", help="Run pytest collection")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    metrics = collect_metrics(ROOT, include_tests=args.include_tests)
    if args.json:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    else:
        print(
            f"{metrics['skills']} skills | {metrics['scripts']} scripts | "
            f"{metrics.get('tests', 'unknown')} tests | {metrics['eval_cases']} eval cases | "
            f"{metrics['assertions']} assertions"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
