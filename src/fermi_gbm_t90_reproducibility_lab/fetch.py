"""Live HEASARC query helpers for the Fermi GBM Burst Catalog and real
GBM TTE file download URLs.

Isolated network I/O so it can be mocked/skipped in tests; the only caller
in real-data mode is scripts/fetch_data.py.
"""
from __future__ import annotations

from fermi_gbm_t90_reproducibility_lab.exceptions import ArchiveAccessError

HEASARC_TTE_BASE_URL = "https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/bursts"


def query_gbm_burst_catalog(n_triggers: int):
    """Live, row-limited query of the Fermi GBM Burst Catalog (fermigbrst)
    for a deterministic sample of real triggers, including the official
    catalogue T90 value for cross-checking this project's own estimate.
    """
    try:
        from astroquery.heasarc import Heasarc
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ArchiveAccessError("astroquery is not installed in this environment") from exc

    try:
        heasarc = Heasarc()
        table = heasarc.query_region(
            position="0 0", mission="fermigbrst", radius="180 degree",
        )
    except Exception as exc:  # noqa: BLE001
        raise ArchiveAccessError(f"HEASARC fermigbrst query failed: {exc}") from exc

    if table is None or len(table) == 0:
        raise ArchiveAccessError("HEASARC fermigbrst query returned zero rows")

    table.sort("NAME")
    return table[:n_triggers]


def trigger_name_to_bn(trigger_name: str) -> str:
    """Convert a catalogue trigger name (e.g. 'GRB170817529') to the GBM
    'bn' file-naming convention (e.g. 'bn170817529')."""
    digits = "".join(ch for ch in trigger_name if ch.isdigit())
    if len(digits) < 9:
        raise ArchiveAccessError(f"could not parse a valid trigger ID from '{trigger_name}'")
    return f"bn{digits[:9]}"


def tte_download_url(bn: str, detector: str) -> str:
    """Real GBM TTE file URL for a given trigger ID and detector code
    (e.g. 'n0', 'n1', ..., 'b0', 'b1')."""
    year = f"20{bn[2:4]}"
    return f"{HEASARC_TTE_BASE_URL}/{year}/{bn}/current/glg_tte_{detector}_{bn}_v00.fit"
