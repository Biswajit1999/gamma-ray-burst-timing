"""Time-binning policies applied to event-time data before T5/T95/T90 estimation.

Two policies: fixed-width histogram binning, and Bayesian Blocks (Scargle
et al. 2012, arXiv:1207.5578) via astropy.stats.bayesian_blocks -- a real,
pinned-dependency implementation, not hand-rolled.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from astropy.stats import bayesian_blocks

from fermi_gbm_t90_reproducibility_lab.exceptions import InsufficientDataError


@dataclass(frozen=True)
class BinnedLightCurve:
    bin_edges: np.ndarray
    bin_centers: np.ndarray
    counts: np.ndarray


def fixed_width_bins(event_times: np.ndarray, t_start: float, t_stop: float, bin_width: float) -> BinnedLightCurve:
    """Histogram event times into fixed-width bins over [t_start, t_stop]."""
    if bin_width <= 0:
        raise ValueError("bin_width must be positive")
    if t_stop <= t_start:
        raise ValueError("t_stop must be greater than t_start")
    n_bins = max(1, int(np.ceil((t_stop - t_start) / bin_width)))
    edges = t_start + np.arange(n_bins + 1) * bin_width
    counts, edges = np.histogram(event_times, bins=edges)
    centers = 0.5 * (edges[:-1] + edges[1:])
    return BinnedLightCurve(bin_edges=edges, bin_centers=centers, counts=counts.astype(float))


def bayesian_block_bins(event_times: np.ndarray, p0: float = 0.05, pre_bin_width: float = 0.064) -> BinnedLightCurve:
    """Adaptive Bayesian Blocks binning (Scargle et al. 2012) via astropy.

    Real-data note (found empirically, not assumed): astropy's
    `bayesian_blocks(..., fitness="events")` applied directly to raw photon
    time-stamps scales far worse than O(n log n) in practice -- a real,
    exceptionally bright GBM trigger (bn130427324) with ~3.4e5 events in even
    a narrow 70-second window took over 37 minutes to complete. This is
    exactly what standard GBM Bayesian-Blocks light-curve tools do to avoid
    that cost: pre-bin the photon time-tags into fine, fixed-width bins
    (`pre_bin_width`, default 64 ms, well below the shortest physically
    resolvable structure this project targets) and run Bayesian Blocks with
    the `fitness="measures"` cost function on the resulting (time, counts)
    series instead of on individual photon arrival times. This is both the
    standard real-world approach and dramatically faster (independent of raw
    event count, only the pre-bin count matters).

    Raises `InsufficientDataError` if there are too few events, or too few
    pre-bins, to form a meaningful block structure.
    """
    times = np.asarray(event_times, dtype=float)
    times = times[np.isfinite(times)]
    if times.size < 5:
        raise InsufficientDataError("bayesian_block_bins requires at least 5 finite event times")

    pre_binned = fixed_width_bins(times, t_start=float(times.min()), t_stop=float(times.max()), bin_width=pre_bin_width)
    if pre_binned.bin_centers.size < 5:
        raise InsufficientDataError("bayesian_block_bins: fewer than 5 pre-bins available for Bayesian Blocks")

    # "measures" fitness needs a per-bin uncertainty; Poisson counting
    # uncertainty with a floor of 1 count avoids zero-uncertainty bins.
    sigma = np.sqrt(np.maximum(pre_binned.counts, 1.0))
    edges = bayesian_blocks(pre_binned.bin_centers, pre_binned.counts, sigma, fitness="measures", p0=p0)
    edges = np.asarray(edges, dtype=float)
    if edges.size < 2:
        raise InsufficientDataError("Bayesian Blocks produced fewer than 2 edges")

    counts, edges = np.histogram(times, bins=edges)
    centers = 0.5 * (edges[:-1] + edges[1:])
    return BinnedLightCurve(bin_edges=edges, bin_centers=centers, counts=counts.astype(float))
