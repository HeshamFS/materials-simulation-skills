#!/usr/bin/env python3
"""Generate (or check) the machine-readable skill index and Claude marketplace manifest.

  python tools/build_index.py            # write skills_index.json + .claude-plugin/marketplace.json
  python tools/build_index.py --check    # CI: fail if the committed files are stale

The generated files are deterministic (sorted, no timestamps), so --check is a
reliable freshness gate.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from materials_simulation_skills.skill_index import (  # noqa: E402
    build_index,
    build_marketplace,
    dumps,
)

INDEX_PATH = ROOT / "skills_index.json"
MARKET_PATH = ROOT / ".claude-plugin" / "marketplace.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if committed files are stale")
    args = parser.parse_args()

    index = build_index(ROOT)
    market = build_marketplace(index)
    index_text = dumps(index)
    market_text = dumps(market)

    if args.check:
        stale = []
        for path, text in ((INDEX_PATH, index_text), (MARKET_PATH, market_text)):
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != text:
                stale.append(path.relative_to(ROOT).as_posix())
        if stale:
            print(f"Stale generated files: {', '.join(stale)}. "
                  f"Run `python tools/build_index.py` and commit.", file=sys.stderr)
            return 1
        print("skills_index.json and marketplace.json are up to date.")
        return 0

    MARKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(index_text, encoding="utf-8")
    MARKET_PATH.write_text(market_text, encoding="utf-8")
    s = index["summary"]
    print(f"Wrote {INDEX_PATH.name}: {s['skills']} skills, {s['scripts']} scripts, "
          f"{s['deterministic_checks']} deterministic checks, "
          f"{s['eval_coverage'] * 100:.0f}% eval coverage, {len(index['bundles'])} bundles.")
    print(f"Wrote {MARKET_PATH.relative_to(ROOT).as_posix()}: {len(market['plugins'])} plugins.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
