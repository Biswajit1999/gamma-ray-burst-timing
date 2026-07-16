from __future__ import annotations

import numpy as np
import pytest

from fermi_gbm_t90_reproducibility_lab.background import fit_background
from fermi_gbm_t90_reproducibility_lab.exceptions import InsufficientDataError


def test_fit_background_constant_model_recovers_flat_rate():
    bin_centers = np.linspace(-20, 20, 40)
    counts = np.full(40, 50.0)
    fit = fit_background(bin_centers, counts, signal_start=-5, signal_stop=5, model="constant")
    assert fit.predicted == pytest.approx(50.0, abs=1.0)


def test_fit_background_linear_model_recovers_slope():
    bin_centers = np.linspace(-20, 20, 40)
    counts = 50.0 + 0.5 * bin_centers
    counts_bg_only = np.concatenate([counts[bin_centers < -5], counts[bin_centers > 5]])
    fit = fit_background(bin_centers, counts, signal_start=-5, signal_stop=5, model="linear")
    assert fit.coefficients[0] == pytest.approx(0.5, abs=0.1)
    assert counts_bg_only.size > 0  # sanity check on test setup


def test_fit_background_rejects_unknown_model():
    bin_centers = np.linspace(-20, 20, 40)
    counts = np.full(40, 50.0)
    with pytest.raises(ValueError):
        fit_background(bin_centers, counts, signal_start=-5, signal_stop=5, model="quadratic")


def test_fit_background_rejects_too_few_background_bins():
    bin_centers = np.array([-1.0, 0.0, 1.0])
    counts = np.array([10.0, 10.0, 10.0])
    with pytest.raises(InsufficientDataError):
        fit_background(bin_centers, counts, signal_start=-2, signal_stop=2, model="linear")
