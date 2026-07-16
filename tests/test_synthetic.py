from __future__ import annotations

import pytest

from fermi_gbm_t90_reproducibility_lab.synthetic import SyntheticBurstSpec, make_synthetic_events


def test_synthetic_events_deterministic_for_fixed_seed():
    spec = SyntheticBurstSpec()
    e1 = make_synthetic_events(spec, seed=42)
    e2 = make_synthetic_events(spec, seed=42)
    assert (e1.event_times == e2.event_times).all()


def test_synthetic_events_truth_t90_matches_burst_duration():
    spec = SyntheticBurstSpec(burst_duration=8.0)
    events = make_synthetic_events(spec, seed=1)
    assert events.truth_t90 == pytest.approx(8.0)


def test_synthetic_events_rejects_nonpositive_duration():
    with pytest.raises(ValueError):
        make_synthetic_events(SyntheticBurstSpec(burst_duration=0.0))


def test_synthetic_events_rejects_invalid_time_range():
    with pytest.raises(ValueError):
        make_synthetic_events(SyntheticBurstSpec(t_start=10.0, t_stop=5.0))
