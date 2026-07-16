"""Background models fit to pre/post-burst intervals, used to
background-subtract a binned light curve before T90 estimation.

Two model variants (constant and linear) support the "background-model
sensitivity" validation item.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fermi_gbm_t90_reproducibility_lab.exceptions import ConvergenceError, InsufficientDataError
from fermi_gbm_t90_reproducibility_lab.uncertainty import check_fit_convergence

BackgroundModel = str  # "constant" or "linear"


@dataclass(frozen=True)
class BackgroundFit:
    model: BackgroundModel
    coefficients: np.ndarray
    predicted: np.ndarray


def fit_background(
    bin_centers: np.ndarray,
    counts: np.ndarray,
    signal_start: float,
    signal_stop: float,
    model: BackgroundModel = "linear",
) -> BackgroundFit:
    """Fit a background model to bins outside [signal_start, signal_stop].

    Raises `InsufficientDataError` if too few background bins remain, and
    `ConvergenceError` (via check_fit_convergence) if the fit is
    ill-conditioned.
    """
    bin_centers = np.asarray(bin_centers, dtype=float)
    counts = np.asarray(counts, dtype=float)
    background_mask = (bin_centers < signal_start) | (bin_centers > signal_stop)
    bg_t = bin_centers[background_mask]
    bg_c = counts[background_mask]

    degree = {"constant": 0, "linear": 1}.get(model)
    if degree is None:
        raise ValueError(f"unknown background model '{model}', expected 'constant' or 'linear'")

    if bg_t.size < degree + 2:
        raise InsufficientDataError(
            f"fit_background: need at least {degree + 2} background bins for model '{model}', got {bg_t.size}"
        )

    coeffs, cov = np.polyfit(bg_t, bg_c, deg=degree, cov=True)
    residuals = bg_c - np.polyval(coeffs, bg_t)
    dof = bg_t.size - (degree + 1)
    if dof > 0:
        check_fit_convergence(cov, residuals=residuals, dof=dof)
    elif not np.all(np.isfinite(cov)):
        raise ConvergenceError("fit_background: non-finite covariance with zero degrees of freedom")

    predicted = np.polyval(coeffs, bin_centers)
    return BackgroundFit(model=model, coefficients=coeffs, predicted=predicted)
