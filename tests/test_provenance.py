from __future__ import annotations

from fermi_gbm_t90_reproducibility_lab.provenance import (
    ManifestRow,
    append_manifest_row,
    get_git_commit,
    read_manifest,
    sha256_file,
)


def test_manifest_roundtrip(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    row = ManifestRow(
        product_id="glg_tte_n0_bn170817529_v00",
        source="HEASARC/Fermi-GBM",
        source_url="https://heasarc.gsfc.nasa.gov",
        retrieved_utc="2026-07-16T00:00:00+00:00",
        sha256="0" * 64,
        file_size_bytes=2100000,
        selection_reason="unit test",
        licence_or_terms="NASA/HEASARC public Fermi GBM archive data",
    )
    append_manifest_row(manifest_path, row)
    rows = read_manifest(manifest_path)
    assert len(rows) == 1
    assert rows[0]["product_id"] == "glg_tte_n0_bn170817529_v00"


def test_sha256_file_matches_known_content(tmp_path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"fermi-gbm-t90-reproducibility-lab")
    digest = sha256_file(path)
    assert len(digest) == 64
    assert digest == sha256_file(path)


def test_get_git_commit_never_raises(tmp_path):
    result = get_git_commit(tmp_path)
    assert isinstance(result, str)
    assert result != ""
