#!/usr/bin/env python3
import argparse
import json
import math
import sys
from typing import Dict

# Upper bound to reject unreasonable cell sizes
MAX_CELL_SIZE = 1e12


def _validate_cell_size(name: str, value: float) -> None:
    """Validate that a cell size is a finite positive number within bounds."""
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number, got {type(value).__name__}")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number, got {value}")
    if value > MAX_CELL_SIZE:
        raise ValueError(f"{name} exceeds maximum ({MAX_CELL_SIZE}), got {value}")


def compute_quality(dx: float, dy: float, dz: float) -> Dict[str, object]:
    for name, val in [("dx", dx), ("dy", dy), ("dz", dz)]:
        _validate_cell_size(name, val)

    sizes = [dx, dy, dz]
    aspect_ratio = max(sizes) / min(sizes)

    skewness = (max(sizes) - min(sizes)) / max(sizes)
    flags = []
    if aspect_ratio > 5.0:
        flags.append("high_aspect_ratio")
    if skewness > 0.5:
        flags.append("high_skewness")

    return {
        "aspect_ratio": aspect_ratio,
        "skewness": skewness,
        "quality_flags": flags,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Estimate mesh quality metrics from spacing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dx", type=float, required=True, help="Cell size in x")
    parser.add_argument("--dy", type=float, required=True, help="Cell size in y")
    parser.add_argument("--dz", type=float, required=True, help="Cell size in z")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result = compute_quality(args.dx, args.dy, args.dz)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    payload = {
        "inputs": {"dx": args.dx, "dy": args.dy, "dz": args.dz},
        "results": result,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Mesh quality")
    print(f"  aspect_ratio: {result['aspect_ratio']:.6g}")
    print(f"  skewness: {result['skewness']:.6g}")
    for flag in result["quality_flags"]:
        print(f"  flag: {flag}")


if __name__ == "__main__":
    main()
