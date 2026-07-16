from __future__ import annotations

import numpy as np
import pytest

from fermi_gbm_t90_reproducibility_lab.binning import bayesian_block_bins, fixed_width_bins
from fermi_gbm_t90_reproducibility_lab.exceptions import InsufficientDataError


def test_fixed_width_bins_counts_total_events():
    times = np.array([0.1, 0.5, 1.2, 1.8, 2.5])
    binned = fixed_width_bins(times, t_start=0.0, t_stop=3.0, bin_width=1.0)
    assert binned.counts.sum() == pytest.approx(5.0)
    assert binned.bin_centers.size == 3


def test_fixed_width_bins_rejects_nonpositive_width():
    with pytest.raises(ValueError):
        fixed_width_bins(np.array([0.0, 1.0]), t_start=0.0, t_stop=1.0, bin_width=0.0)


def test_fixed_width_bins_rejects_invalid_range():
    with pytest.raises(ValueError):
        fixed_width_bins(np.array([0.0]), t_start=5.0, t_stop=1.0, bin_width=1.0)


def test_bayesian_block_bins_rejects_too_few_events():
    with pytest.raises(InsufficientDataError):
        bayesian_block_bins(np.array([0.1, 0.2]))


def test_bayesian_block_bins_returns_edges_spanning_data():
    rng = np.random.default_rng(1)
    times = np.sort(rng.uniform(0, 10, 50))
    binned = bayesian_block_bins(times)
    # Edges are derived from pre-binned bin *centers* (see binning.py
    # docstring on why events are pre-binned before Bayesian Blocks), so the
    # first/last edge can be offset from the raw min/max by up to half a
    # pre-bin width (default 0.064s), not exactly equal.
    assert binned.bin_edges[0] <= times.min() + 0.064
    assert binned.bin_edges[-1] >= times.max() - 0.064
