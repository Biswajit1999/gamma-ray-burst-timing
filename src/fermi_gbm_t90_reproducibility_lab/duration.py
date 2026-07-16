"""T5/T95/T90 duration estimation from a background-subtracted binned light curve.

T90 is the time interval over which the cumulative background-subtracted
counts rise from 5% to 95% of the total (Kouveliotou et al. 1993 convention,
the standard duration definition also used by the Fermi GBM Burst Catalog).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fermi_gbm_t90_reproducibility_lab.exceptions import InsufficientDataError


@dataclass(frozen=True)
class DurationResult:
    t5: float
    t95: float
    t90: float
    total_counts: float


def estimate_t90(bin_centers: np.ndarray, background_subtracted_counts: np.ndarray) -> DurationResult:
    """Estimate T5, T95, T90 from a background-subtracted count series.

    Raises `InsufficientDataError` if the total background-subtracted
    counts are non-positive (no detectable excess above background).
    """
    bin_centers = np.asarray(bin_centers, dtype=float)
    counts = np.asarray(background_subtracted_counts, dtype=float)
    clipped = np.clip(counts, a_min=0.0, a_max=None)
    total = float(np.sum(clipped))

    if total <= 0:
        raise InsufficientDataError("estimate_t90: total background-subtracted counts is non-positive")

    cumulative = np.cumsum(clipped)
    cumulative_frac = cumulative / total

    t5_idx = int(np.searchsorted(cumulative_frac, 0.05))
    t95_idx = int(np.searchsorted(cumulative_frac, 0.95))
    t5_idx = min(t5_idx, bin_centers.size - 1)
    t95_idx = min(t95_idx, bin_centers.size - 1)

    t5 = float(bin_centers[t5_idx])
    t95 = float(bin_centers[t95_idx])
    return DurationResult(t5=t5, t95=t95, t90=t95 - t5, total_counts=total)
