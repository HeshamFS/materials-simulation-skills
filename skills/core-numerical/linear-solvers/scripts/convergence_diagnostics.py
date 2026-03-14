#!/usr/bin/env python3
import argparse
import json
import math
import sys
from typing import List, Tuple

# Maximum number of residual entries to prevent resource exhaustion
MAX_LIST_LENGTH = 100_000


def parse_list(raw: str) -> List[float]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        raise ValueError("residual list must be a comma-separated list")
    if len(parts) > MAX_LIST_LENGTH:
        raise ValueError(
            f"residual list length ({len(parts)}) exceeds limit ({MAX_LIST_LENGTH})"
        )
    values = [float(p) for p in parts]
    if any(not math.isfinite(v) for v in values):
        raise ValueError("residual list contains non-finite values")
    return values


def compute_diagnostics(residuals: List[float]) -> Tuple[float, bool, str]:
    if len(residuals) < 2:
        raise ValueError("residual list must have at least 2 entries")
    if any(r <= 0 or not math.isfinite(r) for r in residuals):
        raise ValueError("residuals must be positive and finite")

    ratios = [residuals[i + 1] / residuals[i] for i in range(len(residuals) - 1)]
    avg_ratio = sum(ratios) / len(ratios)
    stagnation = avg_ratio > 0.95

    if avg_ratio < 0.2:
        action = "Convergence is fast; consider tightening tolerance."
    elif stagnation:
        action = "Stagnation detected; strengthen preconditioner or change method."
    else:
        action = "Convergence is acceptable; continue monitoring."

    return avg_ratio, stagnation, action


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze residual convergence behavior.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--residuals", required=True, help="Comma-separated residuals")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        residuals = parse_list(args.residuals)
        rate, stagnation, action = compute_diagnostics(residuals)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    payload = {
        "inputs": {"residuals": residuals},
        "results": {
            "rate": rate,
            "stagnation": stagnation,
            "recommended_action": action,
        },
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("Convergence diagnostics")
    print(f"  rate: {rate:.6g}")
    print(f"  stagnation: {stagnation}")
    print(f"  action: {action}")


if __name__ == "__main__":
    main()
