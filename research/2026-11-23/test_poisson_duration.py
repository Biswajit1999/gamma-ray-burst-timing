import numpy as np
import pytest
from poisson_duration import on_off_net, t90_from_net, poisson_t90_bootstrap

def test_on_off_variance():
    net, var = on_off_net([10, 20], [4, 8], 0.5)
    np.testing.assert_allclose(net, [8, 16])
    np.testing.assert_allclose(var, [11, 22])

def test_uniform_duration():
    assert t90_from_net([10, 10], [0, 1, 2]) == pytest.approx(1.8)

def test_bootstrap_seed():
    a = poisson_t90_bootstrap(np.array([50, 80, 50]), np.array([5, 5, 5]), .2, [0,1,2,3], 100, 123)
    b = poisson_t90_bootstrap(np.array([50, 80, 50]), np.array([5, 5, 5]), .2, [0,1,2,3], 100, 123)
    np.testing.assert_array_equal(a[0], b[0])
    assert a[1] == 1

def test_invalid_counts():
    with pytest.raises(ValueError):
        on_off_net([1, -1], [1, 1], 1)

def test_zero_signal():
    with pytest.raises(ValueError):
        t90_from_net([-1, 0], [0, 1, 2])
