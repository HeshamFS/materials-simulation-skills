#!/usr/bin/env python3
"""Validate Materials Simulation Skills repository quality gates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials_simulation_skills.skill_utils import validate_skills  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", help="Validate one skill by name")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    result = validate_skills(ROOT, skill_name=args.skill)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
        for warning in result["warnings"]:
            print(f"WARNING: {warning}", file=sys.stderr)
        print(f"Validated {result['summary']['skills']} skills")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
