#!/usr/bin/env python3
"""Spatial convergence study via h-refinement analysis."""
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
        description="Analyze spatial convergence by computing observed order from grid refinement data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--spacings", type=str, required=True,
        help="Comma-separated grid spacings (e.g. 0.4,0.2,0.1)",
    )
    parser.add_argument(
        "--values", type=str, required=True,
        help="Comma-separated solution values at each spacing level",
    )
    parser.add_argument(
        "--expected-order", type=finite_float, default=None,
        help="Expected convergence order for assessment",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def compute_h_refinement(spacings, values, expected_order=None):
    """Compute spatial convergence order from grid refinement data.

    Parameters
    ----------
    spacings : list of float
        Grid spacings (must be positive).
    values : list of float
        Solution values corresponding to each spacing.
    expected_order : float or None
        Expected convergence order for assessment.

    Returns
    -------
    dict
        Results with observed_orders, mean_order, richardson_extrapolated_value,
        in_asymptotic_range, convergence_assessment, and notes.
    """
    if len(spacings) != len(values):
        raise ValueError("spacings and values must have the same length")
    if len(spacings) > 10000:
        raise ValueError("too many refinement levels (max 10000)")
    if len(spacings) < 2:
        raise ValueError("At least 2 refinement levels required")
    for s in spacings:
        if not math.isfinite(s) or s <= 0:
            raise ValueError("All spacings must be positive finite numbers")
    for v in values:
        if not math.isfinite(v):
            raise ValueError("All values must be finite numbers")

    if len(set(spacings)) != len(spacings):
        raise ValueError("Refinement levels must be distinct")
    if expected_order is not None and (not math.isfinite(expected_order) or expected_order <= 0):
        raise ValueError("expected_order must be positive and finite")

    # Sort by spacing descending (coarsest first)
    paired = sorted(zip(spacings, values), key=lambda x: -x[0])
    spacings_sorted = [p[0] for p in paired]
    values_sorted = [p[1] for p in paired]

    notes = []
    observed_orders = []

    invalid_sequence = False
    for i in range(len(spacings_sorted)-2):
        hs = spacings_sorted[i:i+3]
        fs = values_sorted[i:i+3]
        try:
            p = observed_order(*reversed(hs), *reversed(fs))
        except ValueError as exc:
            invalid_sequence = True
            notes.append(str(exc))
            continue
        observed_orders.append(p)
        if p <= 0:
            notes.append("Negative or zero observed order: possible divergence")

    # Mean order
    mean_order = None
    if observed_orders:
        mean_order = sum(observed_orders) / len(observed_orders)

    # Check for pre-asymptotic behavior
    if len(observed_orders) >= 2:
        in_asymptotic_range = True
        for i in range(len(observed_orders) - 1):
            p1 = observed_orders[i]
            p2 = observed_orders[i + 1]
            avg = (abs(p1) + abs(p2)) / 2.0
            if avg > 0 and abs(p1 - p2) / avg > 0.5:
                in_asymptotic_range = False
                notes.append("Pre-asymptotic behavior detected: observed order varies >50%% between consecutive pairs")
                break
        # A non-positive observed order means the solution is not converging.
        if mean_order is not None and mean_order <= 0:
            in_asymptotic_range = False
    elif len(observed_orders) == 1:
        # One triplet estimates order but cannot establish stability across
        # triplets. Non-positive order does establish failure to converge.
        in_asymptotic_range = False if mean_order <= 0 else None
    else:
        in_asymptotic_range = None

    # Richardson extrapolation from finest two levels
    richardson_extrapolated_value = None
    h_fine = spacings_sorted[-1]
    h_next = spacings_sorted[-2]
    f_fine = values_sorted[-1]
    f_next = values_sorted[-2]
    r = h_next / h_fine

    if invalid_sequence:
        in_asymptotic_range = False
        notes.append("Oscillatory or unresolved differences: Richardson estimate suppressed")
    elif mean_order is not None and mean_order > 0:
        richardson_extrapolated_value = f_fine + (f_fine - f_next) / (r ** mean_order - 1)
    elif mean_order is not None:
        # Non-positive observed order: solution appears to be diverging.
        # Do not fall back to expected order; an extrapolated value would be misleading.
        richardson_extrapolated_value = None
        notes.append(
            "Observed order is non-positive -- solution appears to be diverging; "
            "Richardson extrapolation is not meaningful and was not computed."
        )
    elif expected_order is not None and expected_order > 0:
        richardson_extrapolated_value = f_fine + (f_fine - f_next) / (r ** expected_order - 1)
        notes.append("Richardson extrapolation used expected order (no observed order available)")

    # Convergence assessment
    convergence_assessment = "unknown"
    if expected_order is not None and mean_order is not None:
        if abs(mean_order - expected_order) / expected_order <= 0.1:
            convergence_assessment = "PASS: observed order (%.2f) within 10%% of expected (%.2f)" % (
                mean_order, expected_order,
            )
        else:
            convergence_assessment = "FAIL: observed order (%.2f) differs from expected (%.2f) by >10%%" % (
                mean_order, expected_order,
            )
    elif mean_order is not None:
        convergence_assessment = "Observed order: %.2f (no expected order given for comparison)" % mean_order
    elif len(spacings_sorted) < 3:
        convergence_assessment = "Insufficient levels to compute observed order (need >= 3)"

    if invalid_sequence:
        convergence_assessment = "FAIL: oscillatory or unresolved refinement sequence"

    relative_order_error = None
    relative_order_error_overflow = False
    order_matches = None
    if expected_order is not None and mean_order is not None and not invalid_sequence:
        relative_order_error = abs(mean_order - expected_order) / expected_order
        order_matches = relative_order_error <= 0.1
        if not math.isfinite(relative_order_error):
            relative_order_error = None
            relative_order_error_overflow = True
    interpretation = []
    if mean_order is not None:
        interpretation.append(f"The observed convergence order p is {mean_order:.12g} (dimensionless).")
    else:
        interpretation.append("The observed convergence order is unresolved.")
    if order_matches is not None:
        difference = "outside finite floating-point range" if relative_order_error_overflow else f"{relative_order_error:.6g}"
        interpretation.append(f"Compare p with the expected order {expected_order:.12g}: relative difference {difference}, tolerance 0.1; agreement is {order_matches}.")
    if richardson_extrapolated_value is not None:
        interpretation.append(f"The Richardson estimate of the observable at zero spacing is {richardson_extrapolated_value:.12g}, in the same units as the input values. It is not an order and must not be compared with the expected order.")
    else:
        interpretation.append("No Richardson estimate is justified by this sequence.")
    interpretation.append("Order agreement is a refinement diagnostic, not proof of physical accuracy or of an asymptotic regime.")

    return {
        "inputs": {
            "spacings": spacings_sorted,
            "values": values_sorted,
            "expected_order": expected_order,
        },
        "results": {
            "observed_orders": observed_orders,
            "mean_order": mean_order,
            "richardson_extrapolated_value": richardson_extrapolated_value,
            "in_asymptotic_range": in_asymptotic_range,
            "convergence_assessment": convergence_assessment,
            "order_comparison": {
                "quantity": "mean_observed_order", "units": "dimensionless",
                "observed": mean_order, "expected": expected_order,
                "relative_difference": relative_order_error,
                "relative_difference_overflow": relative_order_error_overflow,
                "relative_tolerance": 0.1, "matches_expected": order_matches,
            },
            "extrapolation_evidence": {
                "quantity": "observable_at_zero_spacing",
                "units": "same_as_input_values",
                "value": richardson_extrapolated_value,
                "order_basis": ("observed" if mean_order is not None else "assumed") if richardson_extrapolated_value is not None else None,
            },
            "scientific_interpretation": " ".join(interpretation),
            "notes": notes,
        },
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
        result = compute_h_refinement(spacings, values, args.expected_order)
    except ValueError as exc:
        print("Error: %s" % exc, file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        r = result["results"]
        print("Spatial Convergence Study (h-refinement)")
        print("  levels: %d" % len(spacings))
        if r["observed_orders"]:
            print("  observed orders: %s" % ", ".join("%.4f" % o for o in r["observed_orders"]))
        if r["mean_order"] is not None:
            print("  mean order: %.4f" % r["mean_order"])
        if r["richardson_extrapolated_value"] is not None:
            print("  Richardson extrapolated value: %.6g" % r["richardson_extrapolated_value"])
        if r["in_asymptotic_range"] is not None:
            print("  in asymptotic range: %s" % r["in_asymptotic_range"])
        print("  assessment: %s" % r["convergence_assessment"])
        print("  interpretation: %s" % r["scientific_interpretation"])
        for note in r["notes"]:
            print("  note: %s" % note)


if __name__ == "__main__":
    main()
