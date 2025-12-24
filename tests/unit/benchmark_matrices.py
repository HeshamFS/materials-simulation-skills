import numpy as np


def diag_with_condition(size: int, condition_number: float) -> np.ndarray:
    if size <= 1:
        raise ValueError("size must be > 1")
    if condition_number <= 1.0:
        raise ValueError("condition_number must be > 1")
    diag = np.linspace(1.0, condition_number, size)
    return np.diag(diag)


def poisson_1d(size: int) -> np.ndarray:
    if size < 2:
        raise ValueError("size must be >= 2")
    main = 2.0 * np.ones(size)
    off = -1.0 * np.ones(size - 1)
    matrix = np.diag(main) + np.diag(off, k=1) + np.diag(off, k=-1)
    return matrix


def stiffness_eigs(ratio: float) -> np.ndarray:
    if ratio <= 1.0:
        raise ValueError("ratio must be > 1")
    return np.array([-1.0, -ratio], dtype=float)
