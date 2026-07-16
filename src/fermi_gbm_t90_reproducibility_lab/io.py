"""Loading Fermi GBM TTE (Time-Tagged Event) FITS files.

Shared by scripts/fetch_data.py (post-download validation) and core.py (the
real-data pipeline), isolating the FITS structure so it is testable without
a real network call.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits

from fermi_gbm_t90_reproducibility_lab.exceptions import DataSchemaError

REQUIRED_COLUMNS = ("TIME", "PHA")


@dataclass(frozen=True)
class TTEData:
    trigger_name: str
    detector: str
    trigger_time_met: float
    event_times: np.ndarray  # seconds, relative to trigger time
    event_channels: np.ndarray  # PHA channel, 0-127


def load_tte(path: str | Path) -> TTEData:
    """Load a GBM TTE FITS file's EVENTS extension.

    Raises `DataSchemaError` for a missing file or missing/malformed
    required columns.
    """
    tte_path = Path(path)
    if not tte_path.is_file():
        raise DataSchemaError(f"TTE file not found: {tte_path}")

    try:
        with fits.open(tte_path) as hdul:
            events_hdu = None
            for hdu in hdul:
                if hdu.name.upper() == "EVENTS":
                    events_hdu = hdu
                    break
            if events_hdu is None:
                raise DataSchemaError(f"{tte_path}: no EVENTS extension found")

            data = events_hdu.data
            colnames = set(data.columns.names) if data is not None else set()
            missing = [c for c in REQUIRED_COLUMNS if c not in colnames]
            if missing:
                raise DataSchemaError(f"{tte_path}: EVENTS extension missing required columns: {missing}")

            primary_header = hdul[0].header
            trigtime = float(primary_header.get("TRIGTIME", 0.0))
            detector = str(primary_header.get("DETNAM", "UNKNOWN"))
            trigger_name = str(primary_header.get("OBJECT", primary_header.get("FILENAME", "UNKNOWN")))

            times = np.asarray(data["TIME"], dtype=float) - trigtime
            channels = np.asarray(data["PHA"], dtype=np.int64)
    except OSError as exc:
        raise DataSchemaError(f"{tte_path}: could not be opened as FITS: {exc}") from exc

    if times.size == 0:
        raise DataSchemaError(f"{tte_path}: TTE file has zero events")

    order = np.argsort(times)
    return TTEData(
        trigger_name=trigger_name, detector=detector, trigger_time_met=trigtime,
        event_times=times[order], event_channels=channels[order],
    )
