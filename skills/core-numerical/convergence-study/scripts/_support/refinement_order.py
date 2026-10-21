"""Signed power-law order on three distinct grids. Author: Hesham Salama.

Solve (f3-f2)/(f2-f1) = r21**p * (r32**p-1)/(r21**p-1)
in the log domain, with its removable singularity at p=0 evaluated analytically.
"""
import math


def observed_order(h1, h2, h3, f1, f2, f3):
    if not all(math.isfinite(x) for x in (h1, h2, h3, f1, f2, f3)):
        raise ValueError("refinement inputs must be finite")
    if not 0 < h1 < h2 < h3:
        raise ValueError("refinement spacings must be positive and distinct")
    e21, e32 = f2-f1, f3-f2
    if not math.isfinite(e21) or not math.isfinite(e32):
        raise ValueError("refinement differences exceed floating-point range")
    if e21 == 0 or e32 == 0:
        raise ValueError("zero solution difference; order is unresolved")
    if (e21 > 0) != (e32 > 0):
        raise ValueError("Oscillatory convergence requires a separate model")
    a, b = math.log(h2)-math.log(h1), math.log(h3)-math.log(h2)
    target = math.log(abs(e32))-math.log(abs(e21))
    if math.isclose(a, b, rel_tol=1e-12, abs_tol=0):
        return target/a

    def log_expm1_abs(x):
        if x > 50:
            return x + math.log1p(-math.exp(-x))
        return math.log(abs(math.expm1(x)))

    def residual(p):
        if abs(p)*max(a,b) < 1e-7:
            # Taylor expansion avoids loss of precision near the removable pole.
            ratio_log = math.log(b/a) + p*(a+b)/2 + p*p*(b*b-a*a)/24
        else:
            ratio_log = p*a + log_expm1_abs(p*b)-log_expm1_abs(p*a)
        return ratio_log-target

    lo, hi = -1., 1.
    while residual(lo) > 0 and lo > -1024: lo *= 2
    while residual(hi) < 0 and hi < 1024: hi *= 2
    if residual(lo) > 0 or residual(hi) < 0:
        raise ValueError("observed order outside supported [-1024, 1024] range")
    for _ in range(120):
        mid = (lo+hi)/2
        err = residual(mid)
        if abs(err) < 1e-13:
            return mid
        if err < 0: lo = mid
        else: hi = mid
    p = (lo+hi)/2
    if abs(residual(p)) > 1e-10:
        raise ValueError("observed-order root residual did not converge")
    return p
