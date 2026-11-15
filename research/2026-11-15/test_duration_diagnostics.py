import numpy as np
import pytest
from duration_diagnostics import interpolated_duration,background_ensemble

def test_uniform_analytic():
    assert interpolated_duration(np.arange(11),np.ones(10))==pytest.approx((.5,9.5,9.))

def test_uniform_refinement():
    a=interpolated_duration(np.linspace(0,10,11),np.ones(10))
    b=interpolated_duration(np.linspace(0,10,101),np.ones(100)*.1)
    assert a==pytest.approx(b)

def test_background_spread():
    d,s=background_ensemble(np.arange(6),[2,4,10,4,2],[[0]*5,[1]*5])
    assert d.shape==(2,)
    assert s==pytest.approx(abs(d[0]-d[1]))

def test_reject_invalid():
    with pytest.raises(ValueError): interpolated_duration([0,1,1],[1,2])
    with pytest.raises(ValueError): interpolated_duration([0,1,2],[-1,-2])
    with pytest.raises(ValueError): background_ensemble([0,1],[1],[[-1]])
