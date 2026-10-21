#!/usr/bin/env python3
"""
Derived Quantities Calculator - Compute physical quantities from simulation data.

Calculates derived quantities like interface area, volume fractions,
gradients, fluxes, and integrals from raw simulation field data.

Usage:
    python derived_quantities.py --input field.json --quantity volume_fraction --field phi --threshold 0.5 --json
    python derived_quantities.py --input field.json --quantity gradient_magnitude --field phi --json
"""

import argparse
import json
import math
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

# Security limits
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
FIELD_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.-]*$")


def finite_float(raw):
    value = float(raw)
    if not math.isfinite(value):
        raise argparse.ArgumentTypeError("value must be finite")
    return value


def _validate_file_size(filepath: str) -> None:
    size = os.path.getsize(filepath)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds size limit ({size} > {MAX_FILE_SIZE}): {filepath}")


def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load JSON file with size validation."""
    _validate_file_size(filepath)
    with open(filepath, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {filepath}")
    return data


def get_field_data(data: Dict[str, Any], field_name: str) -> Optional[List]:
    """Extract field data as nested list."""
    if field_name in data:
        return data[field_name]
    if "fields" in data and field_name in data["fields"]:
        field_data = data["fields"][field_name]
        if isinstance(field_data, dict) and "values" in field_data:
            return field_data["values"]
        return field_data
    if "_data" in data and field_name in data["_data"]:
        return data["_data"][field_name]
    return None


def flatten_field(field: Any) -> List[float]:
    """Flatten nested list to 1D array."""
    if not isinstance(field, list):
        if isinstance(field, (int, float)):
            return [float(field)]
        return []

    result = []
    for item in field:
        result.extend(flatten_field(item))
    return result


def get_field_shape(field: List) -> List[int]:
    """Get shape of nested list."""
    shape = []
    current = field
    while isinstance(current, list):
        shape.append(len(current))
        if len(current) > 0:
            current = current[0]
        else:
            break
    return shape


class GridSpacing(dict):
    """Spacing dictionary retaining quadrature conventions per physical axis."""
    def __init__(self, *args, centering=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.centering = centering or {}


def get_grid_spacing(data, shape):
    convention = data.get("centering")
    if convention not in (None, "node", "cell"):
        raise ValueError("centering must be node or cell")
    spacing = GridSpacing()
    for axis, key in enumerate(("dx", "dy", "dz")):
        n = shape[-1-axis] if axis < len(shape) else None
        length = data.get(("Lx", "Ly", "Lz")[axis])
        d = data.get(key)
        mode = convention or "cell"
        if length is not None and (not math.isfinite(length) or length <= 0):
            raise ValueError("Domain lengths must be positive and finite")
        if d is None and length is not None and n is not None:
            mode = convention or "node"
            if mode == "node" and n < 2:
                raise ValueError("Nodal integration needs at least two nodes per axis")
            d = length / (n-1 if mode == "node" else n)
        elif d is not None and length is not None and n is not None:
            node_ok = math.isclose(d*(n-1), length, rel_tol=1e-6)
            cell_ok = math.isclose(d*n, length, rel_tol=1e-6)
            if convention is None and node_ok:
                mode = "node"
            elif not (node_ok if mode == "node" else cell_ok):
                raise ValueError("Explicit spacing is inconsistent with domain length and centering")
        d = 1.0 if d is None else float(d)
        if not math.isfinite(d) or d <= 0:
            raise ValueError("Grid spacing must be positive and finite")
        spacing[key] = d
        spacing.centering[key] = mode
    return spacing


def _field_array(field):
    import numpy as np
    try:
        arr = np.asarray(field, dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValueError("Field must be a rectangular numeric array") from exc
    if not np.all(np.isfinite(arr)):
        raise ValueError("Field values must be finite")
    if arr.ndim not in (1,2,3):
        raise ValueError("Field must have one, two or three dimensions")
    return arr


def compute_volume_fraction(
    field: List,
    threshold: float = 0.5,
    above: bool = True
) -> Dict[str, Any]:
    """Compute volume fraction above/below threshold."""
    values = flatten_field(field)

    if not values:
        return {"volume_fraction": None, "count_above": 0, "total": 0}

    # Check for NaN/Inf values that would silently corrupt results
    for v in values:
        if not math.isfinite(v):
            raise ValueError(
                f"Field contains non-finite value ({v}); cannot compute volume fraction"
            )

    if above:
        count = sum(1 for v in values if v >= threshold)
    else:
        count = sum(1 for v in values if v < threshold)

    total = len(values)
    fraction = count / total

    return {
        "threshold": threshold,
        "condition": "above" if above else "below",
        "volume_fraction": fraction,
        "count": count,
        "total": total
    }


def compute_interface_area_2d(field, threshold, dx, dy):
    """Length of the linearly interpolated level set on a fixed triangulation.

    Sample positions are separated by dx,dy. This measures the sampled-domain
    contour, with no boundary extension. Curved contours require refinement.
    """
    arr = _field_array(field)
    if arr.ndim != 2 or not math.isfinite(threshold):
        raise ValueError("A finite threshold and 2D field are required")
    if any(not math.isfinite(d) or d <= 0 for d in (dx,dy)):
        raise ValueError("Spacing must be finite and positive")
    ny,nx = arr.shape
    segments = set()
    cells = 0
    for j in range(ny-1):
        for i in range(nx-1):
            corners = [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]
            crossed = False
            for tri in ((0,1,2),(0,2,3)):
                pts = [corners[k] for k in tri]
                vals = [float(arr[y,x])-threshold for x,y in pts]
                if all(v == 0 for v in vals):
                    raise ValueError("Level set contains a flat triangle; contour length is undefined")
                hits = []
                for a,b in ((0,1),(1,2),(2,0)):
                    va,vb = vals[a],vals[b]
                    pa,pb = pts[a],pts[b]
                    if va == 0: hits.append(pa)
                    if (va < 0 < vb) or (vb < 0 < va):
                        t = abs(va)/(abs(va)+abs(vb))
                        hits.append((pa[0]+t*(pb[0]-pa[0]),pa[1]+t*(pb[1]-pa[1])))
                hits = list(dict.fromkeys(hits))
                if len(hits) == 2:
                    segments.add(tuple(sorted(hits)))
                    crossed = True
            cells += crossed
    length = math.fsum(math.hypot((b[0]-a[0])*dx,(b[1]-a[1])*dy) for a,b in segments)
    return {"threshold": threshold, "interface_length": length, "cells_crossed": cells,
            "method": "marching_triangles_linear_interpolation"}


def compute_interface_area(
    field: List,
    threshold: float,
    spacing: Dict[str, float]
) -> Dict[str, Any]:
    """Compute interface area for 2D/3D fields."""
    shape = get_field_shape(field)

    if len(shape) == 2:
        return compute_interface_area_2d(
            field, threshold, spacing["dx"], spacing["dy"]
        )

    # For 1D, count crossings
    if len(shape) == 1:
        crossings = 0
        for i in range(len(field) - 1):
            if (field[i] - threshold) * (field[i + 1] - threshold) < 0:
                crossings += 1
        return {
            "threshold": threshold,
            "crossings": crossings,
            "method": "1d_crossing_count"
        }

    return {"error": "3D interface area not implemented", "shape": shape}


def compute_gradient_2d(
    field: List[List[float]],
    dx: float,
    dy: float
) -> Tuple[List[List[float]], List[List[float]]]:
    """Compute gradient of 2D field using central differences."""
    ny = len(field)
    if ny == 0:
        return [], []
    nx = len(field[0])
    # Validate uniform row lengths (ragged arrays would crash)
    for j in range(ny):
        if len(field[j]) != nx:
            raise ValueError(
                f"Ragged array: row 0 has {nx} columns but row {j} has {len(field[j])}"
            )

    if nx < 2 or ny < 2:
        raise ValueError("2D gradients require at least two samples on each axis")
    if any(not math.isfinite(d) or d <= 0 for d in (dx,dy)):
        raise ValueError("Spacing must be finite and positive")

    grad_x = [[0.0] * nx for _ in range(ny)]
    grad_y = [[0.0] * nx for _ in range(ny)]

    for j in range(ny):
        for i in range(nx):
            # X gradient
            if i == 0:
                grad_x[j][i] = (field[j][1] - field[j][0]) / dx
            elif i == nx - 1:
                grad_x[j][i] = (field[j][nx - 1] - field[j][nx - 2]) / dx
            else:
                grad_x[j][i] = (field[j][i + 1] - field[j][i - 1]) / (2 * dx)

            # Y gradient
            if j == 0:
                grad_y[j][i] = (field[1][i] - field[0][i]) / dy
            elif j == ny - 1:
                grad_y[j][i] = (field[ny - 1][i] - field[ny - 2][i]) / dy
            else:
                grad_y[j][i] = (field[j + 1][i] - field[j - 1][i]) / (2 * dy)

    return grad_x, grad_y


def compute_gradient_magnitude(
    field: List,
    spacing: Dict[str, float]
) -> Dict[str, Any]:
    """Compute gradient magnitude of field."""
    # Check for NaN/Inf in input field
    flat = flatten_field(field)
    for v in flat:
        if not math.isfinite(v):
            raise ValueError(
                f"Field contains non-finite value ({v}); cannot compute gradient"
            )

    shape = get_field_shape(field)

    if len(shape) == 1:
        # 1D gradient — need at least 2 elements
        if shape[0] < 2:
            return {
                "gradient_magnitude": [0.0] * shape[0],
                "max": 0.0,
                "mean": 0.0,
                "method": "central_difference_1d",
                "notes": ["Single-element field; gradient is zero"]
            }
        dx = spacing["dx"]
        grad = []
        for i in range(len(field)):
            if i == 0:
                g = (field[1] - field[0]) / dx
            elif i == len(field) - 1:
                g = (field[-1] - field[-2]) / dx
            else:
                g = (field[i + 1] - field[i - 1]) / (2 * dx)
            grad.append(abs(g))

        return {
            "gradient_magnitude": grad,
            "max": max(grad),
            "mean": sum(grad) / len(grad),
            "method": "central_difference_1d"
        }

    if len(shape) == 2:
        grad_x, grad_y = compute_gradient_2d(
            field, spacing["dx"], spacing["dy"]
        )

        # Compute magnitude
        ny, nx = shape
        mag = [[0.0] * nx for _ in range(ny)]
        all_mag = []

        for j in range(ny):
            for i in range(nx):
                m = math.hypot(grad_x[j][i], grad_y[j][i])
                mag[j][i] = m
                all_mag.append(m)

        return {
            "gradient_magnitude": mag,
            "max": max(all_mag),
            "mean": sum(all_mag) / len(all_mag),
            "method": "central_difference_2d"
        }

    return {"error": "Gradient not implemented for this dimension", "shape": shape}


def compute_integral(field, spacing):
    """Tensor trapezoid for nodal axes; midpoint sums for cell samples."""
    import numpy as np
    arr = _field_array(field)
    if arr.size == 0:
        return {"integral": 0.0, "mean_value": None, "cell_volume": 0.0, "total_cells": 0, "domain_volume": 0.0, "method": "none"}
    weighted = arr.copy()
    volume = 1.0
    cell_volume = 1.0
    nodal = False
    for axis,n in enumerate(arr.shape):
        key = ("dx","dy","dz")[arr.ndim-1-axis]
        d = spacing[key]
        if not math.isfinite(d) or d <= 0:
            raise ValueError("Spacing must be positive and finite")
        cell_volume *= d
        isnode = getattr(spacing,"centering",{}).get(key,"cell") == "node"
        w = np.ones(n)*d
        if isnode:
            if n < 2: raise ValueError("Nodal quadrature needs two nodes per axis")
            w[[0,-1]] *= 0.5
            nodal = True
        dims = [1]*arr.ndim
        dims[axis] = n
        weighted *= w.reshape(dims)
        volume *= float(w.sum())
    integral = math.fsum(weighted.ravel())
    return {"integral": integral, "mean_value": integral/volume,
            "cell_volume": cell_volume, "total_cells": int(arr.size), "domain_volume": volume,
            "method": f"tensor_trapezoid_{arr.ndim}d" if nodal else f"midpoint_quadrature_{arr.ndim}d"}


def compute_total_variation(field: List, spacing: Dict[str, float]) -> Dict[str, Any]:
    """Compute total variation (sum of absolute gradients)."""
    shape = get_field_shape(field)

    if len(shape) == 1:
        dx = spacing["dx"]
        tv = sum(abs(field[i + 1] - field[i]) for i in range(len(field) - 1))
        return {
            "total_variation": tv,
            "normalized_tv": tv / ((len(field) - 1) * dx) if len(field) > 1 else 0,
            "method": "1d_difference"
        }

    if len(shape) == 2:
        ny, nx = shape
        tv = 0.0

        for j in range(ny):
            for i in range(nx - 1):
                tv += abs(field[j][i + 1] - field[j][i])

        for j in range(ny - 1):
            for i in range(nx):
                tv += abs(field[j + 1][i] - field[j][i])

        domain_area = (nx * spacing["dx"]) * (ny * spacing["dy"])
        return {
            "total_variation": tv,
            "normalized_tv": tv / domain_area if domain_area > 0 else 0,
            "method": "2d_difference"
        }

    return {"error": "TV not implemented for this dimension", "shape": shape}


def compute_mass(field: List, spacing: Dict[str, float]) -> Dict[str, Any]:
    """Compute total mass (integral of field)."""
    result = compute_integral(field, spacing)
    return {
        "total_mass": result["integral"],
        "mean_density": result["mean_value"],
        "volume": result["domain_volume"],
        "method": result["method"]
    }


def compute_centroid(field, spacing):
    """Quadrature-weighted centroid; first sample coordinate is zero on each axis."""
    import numpy as np
    arr = _field_array(field)
    if arr.ndim > 2:
        return {"error": "Centroid not implemented for this dimension"}
    total = compute_integral(field,spacing)["integral"]
    result = {"total": total, "coordinate_origin": "first sample"}
    for axis in range(arr.ndim):
        label = ("x","y")[arr.ndim-1-axis]
        coord = np.arange(arr.shape[axis])*spacing["d"+label]
        shape=[1]*arr.ndim
        shape[axis]=arr.shape[axis]
        numerator = compute_integral((arr*coord.reshape(shape)).tolist(),spacing)["integral"]
        result["centroid_"+label] = numerator/total if total != 0 else None
    return result


QUANTITY_FUNCTIONS = {
    "volume_fraction": compute_volume_fraction,
    "interface_area": compute_interface_area,
    "gradient_magnitude": compute_gradient_magnitude,
    "integral": compute_integral,
    "total_variation": compute_total_variation,
    "mass": compute_mass,
    "centroid": compute_centroid
}


def main():
    parser = argparse.ArgumentParser(
        description="Compute derived quantities from simulation data"
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input field file (JSON)"
    )
    parser.add_argument(
        "--quantity", "-q",
        required=True,
        choices=list(QUANTITY_FUNCTIONS.keys()),
        help="Quantity to compute"
    )
    parser.add_argument(
        "--field", "-f",
        required=True,
        help="Field name to use"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=finite_float,
        default=0.5,
        help="Threshold for volume_fraction/interface_area (default: 0.5)"
    )
    parser.add_argument(
        "--dx",
        type=finite_float,
        help="Grid spacing in x (overrides file data)"
    )
    parser.add_argument(
        "--dy",
        type=finite_float,
        help="Grid spacing in y (overrides file data)"
    )
    parser.add_argument(
        "--dz",
        type=finite_float,
        help="Grid spacing in z (overrides file data)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    try:
        # Load data
        if not os.path.exists(args.input):
            print(f"Error: File not found: {args.input}", file=sys.stderr)
            sys.exit(1)

        data = load_json_file(args.input)

        # Validate and get field data
        if not FIELD_NAME_PATTERN.match(args.field):
            print(f"Error: Invalid field name: {args.field!r}", file=sys.stderr)
            sys.exit(1)
        field = get_field_data(data, args.field)
        if field is None:
            print(f"Error: Field '{args.field}' not found", file=sys.stderr)
            sys.exit(1)

        shape = get_field_shape(field)

        # Get grid spacing
        spacing = get_grid_spacing(data, shape)
        if args.dx is not None:
            if args.dx <= 0: raise ValueError("Spacing must be positive")
            spacing["dx"] = args.dx
        if args.dy is not None:
            if args.dy <= 0: raise ValueError("Spacing must be positive")
            spacing["dy"] = args.dy
        if args.dz is not None:
            if args.dz <= 0: raise ValueError("Spacing must be positive")
            spacing["dz"] = args.dz

        # Compute quantity
        if args.quantity == "volume_fraction":
            result = compute_volume_fraction(field, args.threshold)
        elif args.quantity == "interface_area":
            result = compute_interface_area(field, args.threshold, spacing)
        elif args.quantity == "gradient_magnitude":
            result = compute_gradient_magnitude(field, spacing)
            # Don't include full field in output by default
            if "gradient_magnitude" in result and isinstance(result["gradient_magnitude"], list):
                del result["gradient_magnitude"]
        else:
            func = QUANTITY_FUNCTIONS[args.quantity]
            result = func(field, spacing)

        # Add metadata
        result["source_file"] = args.input
        result["field"] = args.field
        result["quantity"] = args.quantity
        result["shape"] = shape
        result["spacing"] = spacing

        # Output
        if args.json:
            envelope = {
                "inputs": {
                    "input_file": args.input,
                    "quantity": args.quantity,
                    "field": args.field,
                    "threshold": args.threshold,
                    "dx": spacing["dx"],
                    "dy": spacing["dy"],
                },
                "results": result,
            }
            print(json.dumps(envelope, indent=2))
        else:
            print(f"Derived Quantity: {args.quantity}")
            print(f"Source: {args.input}")
            print(f"Field: {args.field}")
            print(f"Shape: {shape}")
            print(f"Grid spacing: dx={spacing['dx']}, dy={spacing['dy']}")
            print()

            # Print main result based on quantity
            if args.quantity == "volume_fraction":
                print(f"Threshold: {result['threshold']}")
                print(f"Condition: {result['condition']}")
                print(f"Volume fraction: {result['volume_fraction']:.6f}")
                print(f"Count: {result['count']} / {result['total']}")

            elif args.quantity == "interface_area":
                if "interface_length" in result:
                    print(f"Interface length: {result['interface_length']:.6f}")
                    print(f"Cells crossed: {result['cells_crossed']}")
                elif "crossings" in result:
                    print(f"Crossings: {result['crossings']}")

            elif args.quantity == "gradient_magnitude":
                print(f"Max gradient: {result['max']:.6g}")
                print(f"Mean gradient: {result['mean']:.6g}")

            elif args.quantity == "integral":
                print(f"Integral: {result['integral']:.6g}")
                print(f"Mean value: {result['mean_value']:.6g}")

            elif args.quantity == "total_variation":
                print(f"Total variation: {result['total_variation']:.6g}")
                print(f"Normalized TV: {result['normalized_tv']:.6g}")

            elif args.quantity == "mass":
                print(f"Total mass: {result['total_mass']:.6g}")
                print(f"Mean density: {result['mean_density']:.6g}")
                print(f"Volume: {result['volume']:.6g}")

            elif args.quantity == "centroid":
                if result.get("centroid_x") is not None:
                    print(f"Centroid X: {result['centroid_x']:.6g}")
                if result.get("centroid_y") is not None:
                    print(f"Centroid Y: {result['centroid_y']:.6g}")

            print(f"\nMethod: {result.get('method', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
