from __future__ import annotations

import numpy as np
import pytest
from astropy.io import fits

from fermi_gbm_t90_reproducibility_lab.config import load_config
from fermi_gbm_t90_reproducibility_lab.core import run_pipeline
from fermi_gbm_t90_reproducibility_lab.exceptions import InsufficientDataError
from fermi_gbm_t90_reproducibility_lab.synthetic import SyntheticBurstSpec, make_synthetic_events


def _write_synthetic_tte(path, events, trigtime=1000.0, detector="n0", trigger_name="bn200101000"):
    primary = fits.PrimaryHDU()
    primary.header["TRIGTIME"] = trigtime
    primary.header["DETNAM"] = detector
    primary.header["OBJECT"] = trigger_name
    channels = np.zeros(events.event_times.size, dtype=np.int64)
    cols = [
        fits.Column(name="TIME", array=events.event_times + trigtime, format="D"),
        fits.Column(name="PHA", array=channels, format="I"),
    ]
    events_hdu = fits.BinTableHDU.from_columns(cols, name="EVENTS")
    fits.HDUList([primary, events_hdu]).writeto(path, overwrite=True)


def test_run_pipeline_injection_recovery_recovers_known_t90(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    config = load_config("config/analysis.yml")

    spec = SyntheticBurstSpec(burst_duration=8.0, background_rate_hz=50.0, burst_peak_rate_hz=300.0)
    events = make_synthetic_events(spec, seed=10)
    _write_synthetic_tte(raw_dir / "synth1.fit", events)

    manifest_rows = [{"product_id": "synth1"}]
    result = run_pipeline(manifest_rows, raw_dir, config)

    assert len(result.results) > 0
    t90_values = [r.duration.t90 for r in result.results]
    median_t90 = float(np.median(t90_values))
    # Recovered median T90 across all (background_model, binning_method)
    # configurations should be close to the injected truth (8.0 s).
    assert abs(median_t90 - events.truth_t90) < 4.0


def test_run_pipeline_null_control_no_burst_still_produces_estimate(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    config = load_config("config/analysis.yml")

    # burst_peak_rate_hz == background_rate_hz: no real excess above background.
    spec = SyntheticBurstSpec(burst_duration=8.0, background_rate_hz=50.0, burst_peak_rate_hz=50.0)
    events = make_synthetic_events(spec, seed=11)
    _write_synthetic_tte(raw_dir / "synth1.fit", events)

    manifest_rows = [{"product_id": "synth1"}]
    result = run_pipeline(manifest_rows, raw_dir, config)
    # Some configurations may legitimately fail to find a positive excess
    # (InsufficientDataError, recorded as a warning) since there is no real
    # burst signal; this must not crash the whole run.
    assert len(result.results) + len(result.warnings) > 0


def test_run_pipeline_raises_on_empty_manifest(tmp_path):
    config = load_config("config/analysis.yml")
    with pytest.raises(InsufficientDataError):
        run_pipeline([], tmp_path, config)


def test_run_pipeline_warns_not_crashes_on_missing_file(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    config = load_config("config/analysis.yml")
    manifest_rows = [{"product_id": "missing_trigger"}]
    result = run_pipeline(manifest_rows, raw_dir, config)
    assert len(result.results) == 0
    assert any("missing_trigger" in w for w in result.warnings)
