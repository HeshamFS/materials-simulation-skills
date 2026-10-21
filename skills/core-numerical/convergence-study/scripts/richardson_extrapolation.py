#!/usr/bin/env python3
"""Richardson extrapolation for solution verification."""
import argparse
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "_support"))
from refinement_order import observed_order


def finite_float(raw):
    value = float(raw)
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("value must be finite")
    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description="Perform Richardson extrapolation to estimate grid/timestep-independent solution.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--spacings", type=str, required=True,
        help="Comma-separated spacings (e.g. 0.02,0.01)",
    )
    parser.add_argument(
        "--values", type=str, required=True,
        help="Comma-separated solution values at each spacing level",
    )
    parser.add_argument(
        "--order", type=finite_float, required=True,
        help="Assumed convergence order",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def compute_richardson_extrapolation(spacings, values, order):
    """Perform Richardson extrapolation.

    Parameters
    ----------
    spacings : list of float
        Grid spacings or timestep sizes (positive).
    values : list of float
        Solution values at each level.
    order : float
        Assumed convergence order (positive).

    Returns
    -------
    dict
        Results with extrapolated_value, error_estimate, relative_error_estimate,
        and optionally observed_order and order_consistent.
    """
    if len(spacings) != len(values):
        raise ValueError("spacings and values must have the same length")
    if len(spacings) > 10000:
        raise ValueError("too many refinement levels (max 10000)")
    if len(spacings) < 2:
        raise ValueError("At least 2 refinement levels required")
    if not math.isfinite(order) or order <= 0:
        raise ValueError("order must be positive")
    for s in spacings:
        if not math.isfinite(s) or s <= 0:
            raise ValueError("All spacings must be positive finite numbers")
    for v in values:
        if not math.isfinite(v):
            raise ValueError("All values must be finite numbers")

    if len(set(spacings)) != len(spacings):
        raise ValueError("Grid spacings must be distinct")

    # Sort by spacing descending (coarsest first)
    paired = sorted(zip(spacings, values), key=lambda x: -x[0])
    spacings_sorted = [p[0] for p in paired]
    values_sorted = [p[1] for p in paired]

    # Richardson extrapolation from finest two levels
    h_fine = spacings_sorted[-1]
    h_coarse = spacings_sorted[-2]
    f_fine = values_sorted[-1]
    f_coarse = values_sorted[-2]
    r = h_coarse / h_fine

    extrapolated_value = f_fine + (f_fine - f_coarse) / (r ** order - 1)
    error_estimate = abs(f_fine - f_coarse) / (r ** order - 1)
    relative_error_estimate = error_estimate / abs(extrapolated_value) if extrapolated_value != 0 else None

    result = {
        "extrapolated_value": extrapolated_value,
        "error_estimate": error_estimate,
        "relative_error_estimate": relative_error_estimate,
    }

    # With 3+ levels, compute observed order and check consistency
    if len(spacings_sorted) >= 3:
        h1 = spacings_sorted[-1]  # finest
        h2 = spacings_sorted[-2]
        f1 = values_sorted[-1]
        f2 = values_sorted[-2]
        f3 = values_sorted[-3]

        try:
            p = observed_order(h1, h2, spacings_sorted[-3], f1, f2, f3)
            result["observed_order"] = p
            result["order_consistent"] = abs(p-order)/order <= 0.1
            invalid = p <= 0
        except ValueError:
            result["observed_order"] = None
            result["order_consistent"] = False
            invalid = True
        if invalid:
            for key in ("extrapolated_value", "error_estimate", "relative_error_estimate"):
                result[key] = None
            result["note"] = "Oscillatory, divergent or unresolved sequence; estimate suppressed"

    return {
        "inputs": {
            "spacings": spacings_sorted,
            "values": values_sorted,
            "order": order,
        },
        "results": result,
    }


def main():
    args = parse_args()
    try:
        spacings = [float(x) for x in args.spacings.split(",")]
        values = [float(x) for x in args.values.split(",")]
    except ValueError:
        print("Error: spacings and values must be comma-separated numbers", file=sys.stderr)
        sys.exit(2)

    try:
        result = compute_richardson_extrapolation(spacings, values, args.order)
    except ValueError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        r = result["results"]
        print("Richardson Extrapolation")
        print("  assumed order: %.2f" % args.order)
        print("  extrapolated value: %s" % r["extrapolated_value"])
        print("  error estimate: %s" % r["error_estimate"])
        print("  relative error estimate: %s" % r["relative_error_estimate"])
        if "observed_order" in r and r["observed_order"] is not None:
            print("  observed order: %.4f" % r["observed_order"])
            print("  order consistent: %s" % r["order_consistent"])


if __name__ == "__main__":
    main()
