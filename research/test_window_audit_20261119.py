import numpy as np
import pytest
from window_audit_20261119 import quantile_duration, window_sweep, background_ensemble

def test_uniform_pulse():
    assert quantile_duration(np.arange(11), np.ones(10)) == (0.5, 9.5, 9.0)

def test_window_truncation():
    x = window_sweep(np.arange(21), np.ones(20), [10, 20])
    assert x[0,-1] == 9 and x[1,-1] == 18

def test_background_models():
    x = background_ensemble(np.arange(11), np.ones(10)*5, np.array([np.zeros(10), np.ones(10)*2]))
    assert np.allclose(x, 9)

def test_invalid():
    with pytest.raises(ValueError):
        quantile_duration([0,1,1],[1,2])
    with pytest.raises(ValueError):
        quantile_duration([0,1,2],[-1,2])
