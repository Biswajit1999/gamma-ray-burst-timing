from __future__ import annotations

import numpy as np
import pytest
from astropy.io import fits

from fermi_gbm_t90_reproducibility_lab.exceptions import DataSchemaError
from fermi_gbm_t90_reproducibility_lab.io import load_tte


def _write_synthetic_tte(path, times, channels, trigtime=1000.0, detector="n0", trigger_name="bn200101000"):
    primary = fits.PrimaryHDU()
    primary.header["TRIGTIME"] = trigtime
    primary.header["DETNAM"] = detector
    primary.header["OBJECT"] = trigger_name
    cols = [
        fits.Column(name="TIME", array=times + trigtime, format="D"),
        fits.Column(name="PHA", array=channels, format="I"),
    ]
    events_hdu = fits.BinTableHDU.from_columns(cols, name="EVENTS")
    fits.HDUList([primary, events_hdu]).writeto(path, overwrite=True)


def test_load_tte_reads_synthetic_fits_correctly(tmp_path):
    times = np.array([0.1, 0.5, -0.2, 1.0])
    channels = np.array([10, 20, 5, 15])
    path = tmp_path / "synth_tte.fit"
    _write_synthetic_tte(path, times, channels, trigtime=500.0, detector="n1", trigger_name="bn200101000")

    tte = load_tte(path)
    assert tte.detector == "n1"
    assert tte.trigger_name == "bn200101000"
    # event_times are relative to trigger time and sorted
    np.testing.assert_allclose(np.sort(times), tte.event_times)


def test_load_tte_missing_file_raises():
    with pytest.raises(DataSchemaError):
        load_tte("does_not_exist.fit")


def test_load_tte_missing_events_extension_raises(tmp_path):
    path = tmp_path / "malformed.fit"
    fits.HDUList([fits.PrimaryHDU()]).writeto(path, overwrite=True)
    with pytest.raises(DataSchemaError):
        load_tte(path)


def test_load_tte_missing_column_raises(tmp_path):
    primary = fits.PrimaryHDU()
    cols = [fits.Column(name="TIME", array=np.arange(5, dtype=float), format="D")]
    events_hdu = fits.BinTableHDU.from_columns(cols, name="EVENTS")
    path = tmp_path / "missing_col.fit"
    fits.HDUList([primary, events_hdu]).writeto(path, overwrite=True)
    with pytest.raises(DataSchemaError):
        load_tte(path)
