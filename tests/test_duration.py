from __future__ import annotations

import numpy as np
import pytest

from fermi_gbm_t90_reproducibility_lab.duration import estimate_t90
from fermi_gbm_t90_reproducibility_lab.exceptions import InsufficientDataError


def test_estimate_t90_rectangular_pulse_recovers_known_duration():
    bin_centers = np.arange(0.5, 20.5, 1.0)
    counts = np.zeros_like(bin_centers)
    counts[5:13] = 100.0  # an 8-second-wide rectangular pulse
    result = estimate_t90(bin_centers, counts)
    assert result.t90 == pytest.approx(8.0, abs=1.5)


def test_estimate_t90_rejects_nonpositive_total_counts():
    bin_centers = np.arange(10)
    counts = np.zeros(10)
    with pytest.raises(InsufficientDataError):
        estimate_t90(bin_centers, counts)


def test_estimate_t90_clips_negative_counts():
    bin_centers = np.arange(10, dtype=float)
    counts = np.array([-5, -5, 10, 20, 10, -5, -5, -5, -5, -5], dtype=float)
    result = estimate_t90(bin_centers, counts)
    assert result.total_counts == pytest.approx(40.0)
