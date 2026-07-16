from __future__ import annotations

import json

import pytest

from fermi_gbm_t90_reproducibility_lab.exceptions import DataSchemaError
from fermi_gbm_t90_reproducibility_lab.results_io import Metric, validate_summary, write_summary


def test_write_summary_roundtrips_to_valid_json(tmp_path):
    path = tmp_path / "summary.json"
    metrics = [Metric(name="test_metric", estimate=1.5, units="seconds", sample_size=10)]
    payload = write_summary(path, "test project", "synthetic_demo", metrics, {"git_commit": "abc"}, [])
    assert path.is_file()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == payload
    validate_summary(loaded)


def test_validate_summary_rejects_missing_key():
    with pytest.raises(DataSchemaError):
        validate_summary({"project": "x", "data_kind": "y", "metrics": [], "warnings": []})
