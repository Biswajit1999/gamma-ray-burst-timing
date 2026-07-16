"""Pipeline orchestration: per-trigger/per-detector, per-background-model,
per-binning-method T90 estimation, plus the retained starter smoke-test
functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from fermi_gbm_t90_reproducibility_lab.background import fit_background
from fermi_gbm_t90_reproducibility_lab.binning import bayesian_block_bins, fixed_width_bins
from fermi_gbm_t90_reproducibility_lab.config import AnalysisConfig
from fermi_gbm_t90_reproducibility_lab.duration import DurationResult, estimate_t90
from fermi_gbm_t90_reproducibility_lab.exceptions import (
    ConvergenceError,
    DataSchemaError,
    InsufficientDataError,
)
from fermi_gbm_t90_reproducibility_lab.io import load_tte


@dataclass(frozen=True)
class Summary:
    count: int
    median: float
    mad: float


def validate_numeric(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError("values must be one-dimensional")
    if arr.size == 0:
        raise ValueError("values must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError("values contain non-finite entries")
    return arr


def robust_summary(values: np.ndarray) -> Summary:
    arr = validate_numeric(values)
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    return Summary(count=int(arr.size), median=median, mad=mad)


def demo_series(seed: int = 20260713, size: int = 128) -> np.ndarray:
    """Return deterministic synthetic data labelled only for smoke testing."""
    if size < 8:
        raise ValueError("size must be at least 8")
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=1.0, size=size)


BACKGROUND_MODELS = ("constant", "linear")
BINNING_METHODS = ("fixed_1s", "bayesian_blocks")


@dataclass
class ConfigResult:
    trigger: str
    detector: str
    background_model: str
    binning_method: str
    duration: DurationResult


@dataclass
class PipelineResult:
    results: list[ConfigResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _t90_for_configuration(
    event_times: np.ndarray,
    background_model: str,
    binning_method: str,
    signal_window: tuple[float, float] = (-5.0, 15.0),
    analysis_window: tuple[float, float] = (-30.0, 60.0),
) -> DurationResult:
    """Estimate T90 for one (background_model, binning_method) configuration.

    Real GBM TTE files span the full MULTIACCUM readout window (hundreds of
    seconds, tens of thousands of background events) -- standard burst
    analysis practice (and this project's own docs/RESEARCH_BLUEPRINT.md
    scope) restricts to a window around the trigger before binning, both for
    physical relevance and because astropy.stats.bayesian_blocks scales
    poorly (well beyond O(n log n)) on very large event counts; running it
    unrestricted on a full real TTE file was empirically confirmed to hang
    rather than complete in a reasonable time.
    """
    windowed = event_times[(event_times >= analysis_window[0]) & (event_times <= analysis_window[1])]
    if windowed.size < 5:
        raise InsufficientDataError(
            f"_t90_for_configuration: only {windowed.size} events in analysis window {analysis_window}"
        )

    if binning_method == "fixed_1s":
        binned = fixed_width_bins(windowed, t_start=float(np.min(windowed)), t_stop=float(np.max(windowed)), bin_width=1.0)
    elif binning_method == "bayesian_blocks":
        binned = bayesian_block_bins(windowed)
    else:
        raise ValueError(f"unknown binning method '{binning_method}'")

    bg = fit_background(binned.bin_centers, binned.counts, signal_start=signal_window[0], signal_stop=signal_window[1], model=background_model)
    subtracted = binned.counts - bg.predicted
    return estimate_t90(binned.bin_centers, subtracted)


def run_pipeline(manifest_rows: list[dict[str, str]], raw_dir: Path, config: AnalysisConfig) -> PipelineResult:
    """Run T90 estimation over every (trigger/detector) TTE file listed in
    the manifest, across every (background_model, binning_method)
    combination.

    Per-configuration failures are caught and converted to warnings; a
    single bad configuration never aborts the whole run. Raises
    `InsufficientDataError` immediately if the manifest is empty.
    """
    if not manifest_rows:
        raise InsufficientDataError("run_pipeline: manifest_rows is empty")

    results: list[ConfigResult] = []
    warnings: list[str] = []

    for row in manifest_rows:
        product_id = row.get("product_id", "UNKNOWN")
        tte_path = Path(raw_dir) / f"{product_id}.fit"
        try:
            tte = load_tte(tte_path)
        except DataSchemaError as exc:
            warnings.append(f"{product_id}: skipped (load failure): {exc}")
            continue

        for background_model in BACKGROUND_MODELS:
            for binning_method in BINNING_METHODS:
                try:
                    duration = _t90_for_configuration(tte.event_times, background_model, binning_method)
                    results.append(
                        ConfigResult(
                            trigger=tte.trigger_name, detector=tte.detector,
                            background_model=background_model, binning_method=binning_method,
                            duration=duration,
                        )
                    )
                except (InsufficientDataError, ConvergenceError, DataSchemaError) as exc:
                    warnings.append(
                        f"{product_id} [{background_model}/{binning_method}]: skipped: {exc}"
                    )
                    continue

    return PipelineResult(results=results, warnings=warnings)
