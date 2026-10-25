import numpy as np
import pytest

from fermi_gbm_t90_reproducibility_lab.duration_robustness import (
    interpolated_t90, fitted_duration, background_window_sensitivity,
    poisson_duration_uncertainty,
)


def _counts():
    edges=np.arange(-20.,41.,1.)
    centre=(edges[:-1]+edges[1:])/2
    baseline=50.+0.2*centre
    source=np.where((centre>=0)&(centre<8),300.,0.)
    return edges,baseline+source


def test_rectangular_burst_true_t90_is_90_percent_of_duration():
    edges=np.arange(0.,9.)
    result=interpolated_t90(edges,np.ones(8)*100)
    assert result.t5==pytest.approx(0.4)
    assert result.t95==pytest.approx(7.6)
    assert result.t90==pytest.approx(7.2)


def test_variable_bin_width_interpolation():
    edges=[0.,1.,3.,7.,8.]
    counts=[1.,2.,4.,1.] # constant excess rate of 1 count/s
    assert interpolated_t90(edges,counts).t90==pytest.approx(7.2)


def test_background_fit_recovers_expected_duration():
    edges,counts=_counts()
    for model in ("constant","linear"):
        duration, baseline=fitted_duration(edges,counts,(0.,8.),model)
        assert duration.t90==pytest.approx(7.2,abs=0.06)
        assert baseline>0


def test_sensitivity_returns_all_models_and_buffers():
    edges,counts=_counts()
    result=background_window_sensitivity(edges,counts,(0.,8.),(0.,3.),("constant","linear"))
    assert len(result)==4
    assert all(abs(x.t90_s-7.2)<0.08 for x in result)


def test_poisson_seed_reproducibility_and_interval():
    edges,counts=_counts()
    a=poisson_duration_uncertainty(edges,counts,(0.,8.),"linear",n_draws=100,seed=42)
    b=poisson_duration_uncertainty(edges,counts,(0.,8.),"linear",n_draws=100,seed=42)
    assert a==b
    assert a.low_s < 7.2 < a.high_s
    assert a.successful_draws==100


def test_null_control_rejected():
    edges=np.arange(-10.,11.)
    with pytest.raises(ValueError):
        fitted_duration(edges,np.zeros(20),(0.,5.))


def test_bad_edges_and_bad_poisson_counts_rejected():
    with pytest.raises(ValueError):
        interpolated_t90([0,1,1,3],[1,2,3])
    with pytest.raises(ValueError):
        poisson_duration_uncertainty(np.arange(5.),np.array([1.,-1.,2.,3.]),(1.,3.))


def test_insufficient_offburst_bins_rejected():
    with pytest.raises(ValueError):
        fitted_duration(np.arange(10.),np.ones(9),(1.,8.),"linear",buffer_s=3.)


def test_poisson_draw_count_validation():
    edges,counts=_counts()
    with pytest.raises(ValueError):
        poisson_duration_uncertainty(edges,counts,(0.,8.),n_draws=3)
