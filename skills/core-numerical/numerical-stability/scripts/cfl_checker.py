#!/usr/bin/env python3
import argparse
import json
import math
import sys
from typing import Dict, List, Optional


def finite_float(raw):
    value = float(raw)
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("value must be finite")
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute CFL/Fourier numbers and suggest stable dt limits.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dx", type=finite_float, required=True, help="Grid spacing")
    parser.add_argument("--dt", type=finite_float, required=True, help="Time step")
    parser.add_argument("--velocity", type=finite_float, default=None, help="Advection velocity")
    parser.add_argument("--diffusivity", type=finite_float, default=None, help="Diffusivity")
    parser.add_argument("--reaction-rate", type=finite_float, default=None, help="Reaction rate")
    parser.add_argument("--dimensions", type=int, default=1, help="Spatial dimensions")
    parser.add_argument(
        "--scheme",
        choices=["explicit", "implicit"],
        default="explicit",
        help="Time integration scheme",
    )
    parser.add_argument("--advection-limit", type=finite_float, default=None, help="CFL limit")
    parser.add_argument("--diffusion-limit", type=finite_float, default=None, help="Fourier limit")
    parser.add_argument("--reaction-limit", type=finite_float, default=None, help="Reaction limit")
    parser.add_argument("--safety", type=finite_float, default=1.0, help="Safety factor for dt")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def compute_cfl(
    dx: float,
    dt: float,
    velocity: Optional[float],
    diffusivity: Optional[float],
    reaction_rate: Optional[float],
    dimensions: int,
    scheme: str,
    advection_limit: Optional[float],
    diffusion_limit: Optional[float],
    reaction_limit: Optional[float],
    safety: float,
) -> Dict[str, object]:
    notes: List[str] = []
    if not (math.isfinite(dx) and math.isfinite(dt)):
        raise ValueError("dx and dt must be finite")
    if dx <= 0 or dt <= 0:
        raise ValueError("dx and dt must be positive")
    if dimensions not in (1, 2, 3):
        raise ValueError("dimensions must be one of {1, 2, 3}")
    if not math.isfinite(safety) or safety <= 0:
        raise ValueError("safety must be positive")
    if safety > 1:
        raise ValueError("safety must be <= 1")
    if scheme not in {"explicit", "implicit"}:
        raise ValueError("scheme must be explicit or implicit")
    for name, value in (("advection_limit", advection_limit), ("diffusion_limit", diffusion_limit), ("reaction_limit", reaction_limit)):
        if value is not None and (not math.isfinite(value) or value <= 0):
            raise ValueError(f"{name} must be positive and finite")
    for name, val in (("velocity", velocity), ("diffusivity", diffusivity), ("reaction_rate", reaction_rate)):
        if val is not None and not math.isfinite(val):
            raise ValueError(f"{name} must be finite")

    v = None
    if velocity is not None:
        if velocity < 0:
            notes.append("Negative velocity detected; using absolute value for stability analysis")
        v = abs(velocity)
    d = None
    if diffusivity is not None:
        if diffusivity < 0:
            notes.append("Negative diffusivity: magnitude reported for diagnostics only; dissipative certificate unavailable")
        d = abs(diffusivity)
    k = None
    if reaction_rate is not None:
        if reaction_rate < 0:
            notes.append("Negative reaction rate detected; using absolute value for stability analysis")
        k = abs(reaction_rate)

    if advection_limit is None:
        advection_limit = 1.0 if scheme == "explicit" else math.inf
    if diffusion_limit is None:
        diffusion_limit = 1.0 / (2.0 * dimensions) if scheme == "explicit" else math.inf
    if reaction_limit is None:
        reaction_limit = 1.0 if scheme == "explicit" else math.inf

    cfl = None
    dt_max_adv = None
    if v is not None and v > 0:
        cfl = v * dt / dx
        if math.isfinite(advection_limit):
            dt_max_adv = advection_limit * dx / v
    elif v == 0:
        cfl = 0.0

    fo = None
    dt_max_diff = None
    if d is not None and d > 0:
        fo = d * dt / (dx ** 2)
        if math.isfinite(diffusion_limit):
            dt_max_diff = diffusion_limit * (dx ** 2) / d
    elif d == 0:
        fo = 0.0

    react = None
    dt_max_react = None
    if k is not None and k > 0:
        react = k * dt
        if math.isfinite(reaction_limit):
            dt_max_react = reaction_limit / k
    elif k == 0:
        react = 0.0

    criteria_applied: List[str] = []
    stable: Optional[bool] = True
    if scheme == "explicit":
        if cfl is not None and math.isfinite(advection_limit):
            criteria_applied.append("advection")
            stable = stable and (cfl <= advection_limit + 1e-12)
        if fo is not None and math.isfinite(diffusion_limit):
            criteria_applied.append("diffusion")
            stable = stable and (fo <= diffusion_limit + 1e-12)
        if react is not None and math.isfinite(reaction_limit):
            criteria_applied.append("reaction")
            stable = stable and (react <= reaction_limit + 1e-12)
    else:
        notes.append("Implicit scheme: stability limits are relaxed; check accuracy.")

    if not criteria_applied:
        stable = None
        notes.append("No stability criteria applied; provide velocity/diffusivity/reaction.")

    dt_candidates = [x for x in [dt_max_adv, dt_max_diff, dt_max_react] if x is not None]
    recommended_dt = min(dt_candidates) * safety if dt_candidates else None

    # A convex combination of individually monotone Euler updates is monotone
    # only when the SUM of their normalized loads is <= 1. Taking the minimum
    # separate dt bound is insufficient for an unsplit multiphysics update.
    combined_load = None
    if scheme == "explicit" and criteria_applied:
        combined_load = sum(value / limit for value, limit in
                            ((cfl, advection_limit), (fo, diffusion_limit), (react, reaction_limit))
                            if value is not None)
        stable = combined_load <= 1.0 + 1e-12
        recommended_dt = dt / combined_load * safety if combined_load > 0 else None
        if len(criteria_applied) > 1:
            notes.append("Unsplit update: sum of normalized advection, diffusion and decay loads must be <= 1.")
    if (diffusivity is not None and diffusivity < 0) or (reaction_rate is not None and reaction_rate < 0):
        stable = None
        recommended_dt = None
        notes.append("Negative diffusion or growth reaction is outside the dissipative model; no stable timestep is certified.")

    component_checks = []
    for name, value, limit in (("advection", cfl, advection_limit),
                               ("diffusion", fo, diffusion_limit),
                               ("reaction", react, reaction_limit)):
        if name in criteria_applied:
            component_checks.append({"component": name, "value": value,
                                     "limit": limit, "within_separate_limit": value <= limit + 1e-12})
    explanation = []
    for item in component_checks:
        relation = "within" if item['within_separate_limit'] else "above"
        explanation.append(f"The {item['component']} metric {item['value']:.12g} is {relation} its separate limit {item['limit']:.12g}.")
    if stable is not None and combined_load is not None:
        explanation.append(f"The combined normalized load is {combined_load:.12g}; the sufficient monotonicity bound is 1 (comparison tolerance 1e-12). This bound is {'satisfied' if stable else 'not satisfied'}.")
    else:
        explanation.append("No sufficient stability verdict is established for the supplied model.")
    explanation.append("Separate component limits do not establish the combined unsplit bound. This criterion applies only to the stated discretization assumptions.")
    return {
        "inputs": {
            "dx": dx,
            "dt": dt,
            "velocity": velocity,
            "diffusivity": diffusivity,
            "reaction_rate": reaction_rate,
            "dimensions": dimensions,
            "scheme": scheme,
            "safety": safety,
        },
        "metrics": {
            "cfl": cfl,
            "fourier": fo,
            "reaction": react,
        },
        "limits": {
            "advection_limit": advection_limit if math.isfinite(advection_limit) else None,
            "diffusion_limit": diffusion_limit if math.isfinite(diffusion_limit) else None,
            "reaction_limit": reaction_limit if math.isfinite(reaction_limit) else None,
        },
        "criteria_applied": criteria_applied,
        "recommended_dt": recommended_dt,
        "stable": stable,
        "combined_load": combined_load,
        "component_checks": component_checks,
        "scientific_interpretation": " ".join(explanation),
        "assumptions": "Sufficient monotonicity bound for forward Euler, total upwind advective Courant load, uniform Cartesian centered diffusion, and linear decay. Custom limits require an independently justified monotone component update. Not a certificate for arbitrary PDE schemes.",
        "notes": notes,
    }


def main() -> None:
    args = parse_args()
    try:
        payload = compute_cfl(
            dx=args.dx,
            dt=args.dt,
            velocity=args.velocity,
            diffusivity=args.diffusivity,
            reaction_rate=args.reaction_rate,
            dimensions=args.dimensions,
            scheme=args.scheme,
            advection_limit=args.advection_limit,
            diffusion_limit=args.diffusion_limit,
            reaction_limit=args.reaction_limit,
            safety=args.safety,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return

    print("CFL check")
    print(f"  scheme: {args.scheme}")
    cfl = payload["metrics"]["cfl"]
    if cfl is not None:
        print(f"  CFL: {cfl:.6g} (limit {payload['limits']['advection_limit']})")
    else:
        print("  CFL: n/a")
    fo = payload["metrics"]["fourier"]
    if fo is not None:
        print(f"  Fourier: {fo:.6g} (limit {payload['limits']['diffusion_limit']})")
    else:
        print("  Fourier: n/a")
    react = payload["metrics"]["reaction"]
    if react is not None:
        print(f"  Reaction: {react:.6g} (limit {payload['limits']['reaction_limit']})")
    else:
        print("  Reaction: n/a")
    stable = payload["stable"]
    stable_label = "unknown" if stable is None else str(stable)
    print(f"  stable: {stable_label}")
    print(f"  interpretation: {payload['scientific_interpretation']}")
    recommended_dt = payload["recommended_dt"]
    if recommended_dt is not None:
        print(f"  recommended_dt: {recommended_dt:.6g}")
    for note in payload["notes"]:
        print(f"  note: {note}")


if __name__ == "__main__":
    main()
