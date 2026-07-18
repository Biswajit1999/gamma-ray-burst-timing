"""Generate the 5 required figures (docs/FIGURE_AND_UI_SPEC.md) as SVG + 300 dpi
PNG, each with a sidecar JSON recording git commit, config hash, sample size
and units.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401 - importing registers the SciencePlots styles

from fermi_gbm_t90_reproducibility_lab import __version__
from fermi_gbm_t90_reproducibility_lab.background import fit_background
from fermi_gbm_t90_reproducibility_lab.binning import bayesian_block_bins, fixed_width_bins
from fermi_gbm_t90_reproducibility_lab.config import load_config
from fermi_gbm_t90_reproducibility_lab.core import BACKGROUND_MODELS, BINNING_METHODS, demo_series
from fermi_gbm_t90_reproducibility_lab.duration import estimate_t90
from fermi_gbm_t90_reproducibility_lab.io import load_tte
from fermi_gbm_t90_reproducibility_lab.plotting import plot_demo
from fermi_gbm_t90_reproducibility_lab.provenance import get_git_commit, read_manifest, sha256_config
from fermi_gbm_t90_reproducibility_lab.synthetic import SyntheticBurstSpec, make_synthetic_events

plt.style.use(["science", "no-latex"])


def _sidecar(path: Path, *, data_kind: str, sample_size: int, units: str, config_path: Path, extra: dict | None = None) -> None:
    payload = {
        "figure": path.stem,
        "data_kind": data_kind,
        "sample_size": sample_size,
        "units": units,
        "git_commit": get_git_commit(Path(__file__).resolve().parents[1]),
        "config_sha256": sha256_config(config_path) if config_path.is_file() else None,
        "package_version": __version__,
    }
    if extra:
        payload.update(extra)
    path.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _save(fig, out_dir: Path, name: str) -> Path:
    svg_path = out_dir / f"{name}.svg"
    png_path = out_dir / f"{name}.png"
    fig.savefig(svg_path, dpi=180)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    return png_path


def _make_figures_common(out_dir: Path, config_path: Path, data_kind: str, event_times: np.ndarray, tag: str, signal_window=(-5.0, 15.0)) -> None:
    binned = fixed_width_bins(event_times, t_start=float(np.min(event_times)), t_stop=float(np.max(event_times)), bin_width=1.0)
    bg = fit_background(binned.bin_centers, binned.counts, signal_start=signal_window[0], signal_stop=signal_window[1], model="linear")
    subtracted = binned.counts - bg.predicted
    duration = estimate_t90(binned.bin_centers, subtracted)

    # 1. light curve / background intervals
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.step(binned.bin_centers, binned.counts, where="mid", color="tab:blue", label="counts/bin")
    ax.plot(binned.bin_centers, bg.predicted, "--", color="tab:red", label="background model")
    ax.axvspan(signal_window[0], signal_window[1], color="orange", alpha=0.15, label="signal window")
    ax.set_xlabel("Time since trigger (s)")
    ax.set_ylabel("Counts / 1s bin")
    ax.set_title(f"Light curve and background - {tag} (n={event_times.size} events)")
    ax.legend(fontsize=8)
    path = _save(fig, out_dir, "fig01_lightcurve_background")
    _sidecar(path, data_kind=data_kind, sample_size=event_times.size, units="counts vs seconds", config_path=config_path)

    # 2. T5/T95 markers
    fig, ax = plt.subplots(figsize=(8, 4.5))
    cumulative = np.cumsum(np.clip(subtracted, 0, None))
    cumulative_frac = cumulative / cumulative[-1] if cumulative[-1] > 0 else cumulative
    ax.plot(binned.bin_centers, cumulative_frac, color="tab:purple")
    ax.axvline(duration.t5, color="tab:green", ls="--", label=f"T5={duration.t5:.2f}s")
    ax.axvline(duration.t95, color="tab:red", ls="--", label=f"T95={duration.t95:.2f}s")
    ax.axhline(0.05, color="gray", lw=0.5)
    ax.axhline(0.95, color="gray", lw=0.5)
    ax.set_xlabel("Time since trigger (s)")
    ax.set_ylabel("Cumulative fraction of background-subtracted counts")
    ax.set_title(f"T5/T95 markers - {tag} (T90={duration.t90:.2f}s)")
    ax.legend(fontsize=8)
    path = _save(fig, out_dir, "fig02_t5_t95_markers")
    _sidecar(path, data_kind=data_kind, sample_size=event_times.size, units="fraction vs seconds", config_path=config_path)

    # 3. Bayesian blocks
    try:
        bb = bayesian_block_bins(event_times[(event_times > signal_window[0] - 10) & (event_times < signal_window[1] + 10)])
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.stairs(bb.counts, bb.bin_edges, color="tab:blue", fill=True, alpha=0.6)
        ax.set_xlabel("Time since trigger (s)")
        ax.set_ylabel("Counts per Bayesian block")
        ax.set_title(f"Bayesian blocks - {tag} ({bb.bin_centers.size} blocks)")
        path = _save(fig, out_dir, "fig03_bayesian_blocks")
        _sidecar(path, data_kind=data_kind, sample_size=bb.bin_centers.size, units="counts vs seconds", config_path=config_path)
    except Exception:  # noqa: BLE001
        pass

    # 4. bootstrap T90
    rng = np.random.default_rng(20260713)
    bootstrap_t90s = []
    for _ in range(200):
        resampled = rng.choice(event_times, size=event_times.size, replace=True)
        resampled.sort()
        try:
            b_binned = fixed_width_bins(resampled, t_start=float(np.min(resampled)), t_stop=float(np.max(resampled)), bin_width=1.0)
            b_bg = fit_background(b_binned.bin_centers, b_binned.counts, signal_start=signal_window[0], signal_stop=signal_window[1], model="linear")
            b_sub = b_binned.counts - b_bg.predicted
            bootstrap_t90s.append(estimate_t90(b_binned.bin_centers, b_sub).t90)
        except Exception:  # noqa: BLE001
            continue
    fig, ax = plt.subplots(figsize=(6, 4.5))
    if bootstrap_t90s:
        ax.hist(bootstrap_t90s, bins=20, color="tab:blue", alpha=0.7)
        ax.axvline(duration.t90, color="tab:red", ls="--", label=f"point estimate={duration.t90:.2f}s")
        ax.legend(fontsize=8)
    ax.set_xlabel("Bootstrap-resampled T90 (s)")
    ax.set_ylabel("Count")
    ax.set_title(f"Bootstrap T90 distribution - {tag} (n={len(bootstrap_t90s)} resamples)")
    path = _save(fig, out_dir, "fig04_bootstrap_t90")
    _sidecar(path, data_kind=data_kind, sample_size=len(bootstrap_t90s), units="seconds", config_path=config_path)

    # 5. model sensitivity (background model x binning method)
    sensitivity = {}
    for model in BACKGROUND_MODELS:
        for method in BINNING_METHODS:
            try:
                if method == "fixed_1s":
                    m_binned = binned
                else:
                    m_binned = bayesian_block_bins(event_times)
                m_bg = fit_background(m_binned.bin_centers, m_binned.counts, signal_start=signal_window[0], signal_stop=signal_window[1], model=model)
                m_sub = m_binned.counts - m_bg.predicted
                sensitivity[f"{model}/{method}"] = estimate_t90(m_binned.bin_centers, m_sub).t90
            except Exception:  # noqa: BLE001
                continue
    fig, ax = plt.subplots(figsize=(7, 4.5))
    if sensitivity:
        ax.bar(list(sensitivity.keys()), list(sensitivity.values()), color="teal")
        ax.set_ylabel("T90 (s)")
        ax.set_xlabel("background model / binning method")
        plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
    ax.set_title(f"T90 sensitivity to background model and binning - {tag}")
    path = _save(fig, out_dir, "fig05_model_sensitivity")
    _sidecar(path, data_kind=data_kind, sample_size=len(sensitivity), units="seconds", config_path=config_path)


def make_demo_figures(out_dir: Path, config_path: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    events = make_synthetic_events(SyntheticBurstSpec(), seed=2000)
    _make_figures_common(out_dir, config_path, "synthetic_demo", events.event_times, "SYNTHETIC DEMO", signal_window=(events.truth_burst_start - 2, events.truth_burst_stop + 2))
    print(f"Wrote 5 demo figures (SVG+PNG+JSON) to {out_dir}")


def make_real_figures(out_dir: Path, config_path: Path, manifest_path: Path, raw_dir: Path) -> None:
    config = load_config(config_path)
    manifest_rows = read_manifest(manifest_path)
    if not manifest_rows:
        raise SystemExit(
            "data/manifest.csv has no rows. Run scripts/fetch_data.py (with explicit "
            "operator authorization) and scripts/run_analysis.py before generating real figures."
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    data_kind = config.input.data_mode

    first_product_id = manifest_rows[0]["product_id"]
    tte = load_tte(raw_dir / f"{first_product_id}.fit")
    tag = f"{tte.trigger_name} {tte.detector}"

    _make_figures_common(out_dir, config_path, data_kind, tte.event_times, tag)
    print(f"Wrote 5 real-data figures (SVG+PNG+JSON) to {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=Path("figures"))
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    if args.demo:
        plot_demo(demo_series(), args.out_dir / "fig00_smoke_test.png")
        make_demo_figures(args.out_dir, args.config)
        return

    make_real_figures(args.out_dir, args.config, args.manifest, args.raw_dir)


if __name__ == "__main__":
    main()
