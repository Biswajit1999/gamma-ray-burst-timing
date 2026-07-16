from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from fermi_gbm_t90_reproducibility_lab.synthetic import SyntheticBurstSpec, make_synthetic_events


@pytest.fixture
def synthetic_events():
    return make_synthetic_events(SyntheticBurstSpec(), seed=2000)
