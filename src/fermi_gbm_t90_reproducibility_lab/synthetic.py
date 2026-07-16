"""Synthetic GRB-like event-time generator with a known injected T90 duration
on a known constant background rate.

Shared by pytest fixtures (conftest.py) and any --demo CLI path so there is
one source of truth for the injected ground truth.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SyntheticBurstSpec:
    t_start: float = -20.0
    t_stop: float = 40.0
    background_rate_hz: float = 50.0
    burst_start: float = 0.0
    burst_duration: float = 8.0
    burst_peak_rate_hz: float = 300.0


@dataclass(frozen=True)
class SyntheticEvents:
    event_times: np.ndarray
    truth_t90: float
    truth_burst_start: float
    truth_burst_stop: float


def make_synthetic_events(spec: SyntheticBurstSpec = SyntheticBurstSpec(), seed: int = 20260713) -> SyntheticEvents:
    """Simulate a Poisson event-time series: constant background plus a
    rectangular-profile burst pulse of known duration and rate.

    The rectangular pulse profile makes the injected T90 exactly equal to
    `burst_duration` (up to Poisson counting noise), giving a clean,
    unambiguous injection-recovery target.
    """
    if spec.burst_duration <= 0:
        raise ValueError("burst_duration must be positive")
    if spec.t_stop <= spec.t_start:
        raise ValueError("t_stop must be greater than t_start")

    rng = np.random.default_rng(seed)
    duration = spec.t_stop - spec.t_start

    n_background = rng.poisson(spec.background_rate_hz * duration)
    background_times = rng.uniform(spec.t_start, spec.t_stop, size=n_background)

    burst_stop = spec.burst_start + spec.burst_duration
    n_burst = rng.poisson(spec.burst_peak_rate_hz * spec.burst_duration)
    burst_times = rng.uniform(spec.burst_start, burst_stop, size=n_burst)

    all_times = np.sort(np.concatenate([background_times, burst_times]))
    return SyntheticEvents(
        event_times=all_times, truth_t90=spec.burst_duration,
        truth_burst_start=spec.burst_start, truth_burst_stop=burst_stop,
    )
