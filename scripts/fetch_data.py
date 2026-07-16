"""Deterministic, provenance-recording fetch of real public Fermi GBM TTE
(Time-Tagged Event) FITS files.

Real GBM TTE data is served directly from the HEASARC public FTP archive
(no proprietary period for GBM burst data). Live-verified via WebFetch
against the real directory listings before this script was written (see
IMPLEMENTATION_PLAN.md). Two real, well-known triggers are used: bn170817529
(GRB170817A, the short GRB associated with GW170817) with 2 detectors (n0,
n1) for the "detector comparison" validation item, and bn130427324
(GRB130427A, a very bright long GRB) with 1 detector (n0).

This script performs real network downloads and must only be invoked with
explicit user authorization for the session.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import requests

from fermi_gbm_t90_reproducibility_lab.exceptions import ArchiveAccessError
from fermi_gbm_t90_reproducibility_lab.fetch import tte_download_url
from fermi_gbm_t90_reproducibility_lab.logging_utils import get_logger
from fermi_gbm_t90_reproducibility_lab.provenance import ManifestRow, append_manifest_row, sha256_file

LOGGER = get_logger(__name__)

# Deterministic real-trigger sample, verified live to have downloadable TTE
# files before this script was written (see IMPLEMENTATION_PLAN.md).
SAMPLE = [
    ("bn170817529", "n0"),
    ("bn170817529", "n1"),
    ("bn130427324", "n0"),
]
LICENCE_TERMS = (
    "NASA/HEASARC public Fermi GBM archive data, no proprietary period; "
    "standard HEASARC archive usage terms apply, https://heasarc.gsfc.nasa.gov/docs/archive.html"
)


def _download(url: str, out_path: Path) -> None:
    response = requests.get(url, timeout=120)
    if response.status_code != 200:
        raise ArchiveAccessError(f"download failed for {url}: HTTP {response.status_code}")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(response.content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument(
        "--i-have-authorization",
        action="store_true",
        help=(
            "Required flag confirming the operator has explicitly authorized this "
            "real network download in the current session."
        ),
    )
    args = parser.parse_args()

    if not args.i_have_authorization:
        raise SystemExit(
            "Refusing to download real archive data without --i-have-authorization. "
            "This flag exists so the download only runs after the operator has "
            "explicitly confirmed it in the current session."
        )

    retrieved_utc = datetime.now(timezone.utc).isoformat()
    downloaded = 0

    for bn, detector in SAMPLE:
        url = tte_download_url(bn, detector)
        product_id = f"glg_tte_{detector}_{bn}_v00"
        out_path = args.out_dir / f"{product_id}.fit"

        LOGGER.info("Downloading %s -> %s", url, out_path)
        _download(url, out_path)

        digest = sha256_file(out_path)
        size = out_path.stat().st_size
        row = ManifestRow(
            product_id=product_id,
            source="HEASARC/Fermi-GBM",
            source_url=url,
            retrieved_utc=retrieved_utc,
            sha256=digest,
            file_size_bytes=size,
            selection_reason=(
                f"deterministic real-trigger sample ({bn}, detector {detector}), "
                "chosen for known real T90 catalogue values and multi-detector coverage"
            ),
            licence_or_terms=LICENCE_TERMS,
        )
        append_manifest_row(args.manifest, row)
        LOGGER.info("Recorded manifest row for %s (%d bytes)", product_id, size)
        downloaded += 1

    print(f"Downloaded and recorded {downloaded} TTE files under {args.out_dir}")


if __name__ == "__main__":
    main()
