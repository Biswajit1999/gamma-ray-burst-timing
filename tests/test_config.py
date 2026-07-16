from __future__ import annotations

from fermi_gbm_t90_reproducibility_lab.config import load_config


def test_load_config_reads_real_project_config():
    cfg = load_config("config/analysis.yml")
    assert cfg.project.repository == "fermi-gbm-t90-reproducibility-lab"
    assert cfg.execution.seed == 20260713
    assert cfg.validation.bootstrap_resamples == 1000
