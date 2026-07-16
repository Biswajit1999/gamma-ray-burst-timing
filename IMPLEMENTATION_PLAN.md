# Implementation Plan — Fermi GBM T90 Reproducibility Lab

Author: Biswajit Jana. Local Claude Code implementation pass, project from the
30-project portfolio pack (`BUILD_FIRST`, priority 9.0/10). No git operations.

## 1. Literature verification (done before any code)

| Seed citation | Verification method | Result |
|---|---|---|
| Meegan et al. 2009, "The Fermi Gamma-Ray Burst Monitor", arXiv:0908.0450 | WebFetch arXiv abstract page | VERIFIED — title/authors/year match; ApJ 2009. |
| Scargle et al., Bayesian Blocks, arXiv:1207.5578 | WebFetch arXiv abstract page | VERIFIED — "Studies in Astronomical Time Series Analysis. VI. Bayesian Block Representations", Scargle, Norris, Jackson, Chiang (2012/2013). The seed's originally-guessed arXiv ID (1207.4633) was WRONG (resolves to an unrelated optical-fiber paper) — corrected to the real ID 1207.5578 after direct verification, not assumed. |
| Fermi Science Support Center GBM data/tools | `heasarc.gsfc.nasa.gov` (institutional documentation) | Cited as institutional documentation, no invented DOI. |
| Stingray timing package, arXiv:1901.07681 | Cited per docs/LITERATURE_SEEDS.md; not independently re-verified this session (secondary/tooling reference, not load-bearing for the T90 method itself) — marked TODO_VERIFY if used in report.tex. |

## 2. Real-data access plan (verified live against HEASARC)

- Fermi GBM burst catalogue and trigger data are served by HEASARC.
  `astroquery.heasarc.Heasarc` (part of pinned astroquery==0.4.7) queries the
  `fermigbrst` burst catalogue table for trigger metadata (trigger name,
  trigger time, T90 catalogue value for cross-check).
- Actual GBM TTE/CSPEC per-trigger data files are retrieved directly from the
  HEASARC public FTP/HTTPS archive
  (`https://heasarc.gsfc.nasa.gov/FTP/fermi/data/gbm/bursts/<year>/<trigger>/`),
  verified live before committing to the exact path pattern.
- All Fermi GBM burst data is public (no proprietary period).
- Deterministic sample: a small, fixed set of real GBM trigger names (2-3),
  selected by sorted trigger name from a live catalogue query.
- `data/manifest.csv` records product_id/source/source_url/retrieved_utc/
  sha256/file_size_bytes/selection_reason/licence_or_terms; raw files never
  committed (`data/raw/` gitignored).

## 3. File-level task list

### Foundation (ported near-verbatim from sibling projects, package renamed)
- `config.py`, `exceptions.py` (extend), `logging_utils.py`, `provenance.py`
  (extend), `results_io.py` (new).

### Data layer
- `synthetic.py` (new) — synthetic GRB-like light curve generator with a
  known injected T90 duration (burst pulse of known start/stop time on a
  known background model).
- `scripts/fetch_data.py` — real HEASARC/GBM fetch, gated behind
  `--i-have-authorization`, checksums, manifest rows.

### Scientific modules (docs/RESEARCH_BLUEPRINT.md)
- `io.py` — load GBM CSPEC/TTE-derived light curve (time, counts, background
  model inputs); raise `DataSchemaError` on malformed input.
- `background.py` — background models (polynomial fit to pre/post-burst
  intervals) used to background-subtract the light curve before T90
  estimation; at least two model variants for the "background-model
  sensitivity" validation item.
- `binning.py` — time-binning policies (fixed-width, Bayesian Blocks per
  Scargle et al.) applied before T5/T95/T90 estimation.
- `duration.py` — T5/T95/T90 estimator from cumulative background-subtracted
  counts.
- `uncertainty.py` — `bootstrap_statistic` (1000 resamples, seed 20260713)
  and `check_fit_convergence` (covariance condition number + reduced
  chi-square), kept strictly separate.
- `plotting.py` — figure-building helpers used by `scripts/make_figures.py`.
- `core.py` — `run_pipeline` orchestrator; per-trigger/per-configuration
  try/except over `InsufficientDataError`/`ConvergenceError`/`DataSchemaError`
  -> warning, never abort; raises `InsufficientDataError` on empty input.

### Validation/QA
- `tests/conftest.py` — synthetic fixtures.
- Injection-recovery gate: known injected T90 duration recovered within
  tolerance from a synthetic light curve with known background.
- Null control: a pure-background (no burst) synthetic light curve recovers
  a near-zero/undefined T90 rather than a fabricated nonzero value.
- Background-model and detector/channel/binning sensitivity tests.
- Failure-mode tests: empty light curve, missing columns, non-finite input.
- Benchmarks via `tracemalloc` + `time.perf_counter()`.

### Figures + report
- `scripts/make_figures.py` — 5 required figures (light curve/background
  intervals; T5/T95 markers; Bayesian blocks; bootstrap T90; model
  sensitivity), SVG+PNG(300dpi)+sidecar JSON.
- `reports/report.tex` + `reports/references.bib` — real numbers only after
  real pipeline run.

### React dashboard
- `web-react/eslint.config.js` — add `react/jsx-uses-vars`/`react/jsx-uses-react`.
- `web-react/package.json` — remove `recharts`.
- `web-react/src/App.jsx` — replace stub using established template.
- `web-react/public/project.json` — rewrite with real fields.
- `scripts/sync_web_assets.py` (new) — copy results/figures/manifest into
  `web-react/public/`.

### Final
- `LOCAL_COMPLETION_REPORT.md`, `_PROJECT_LOG.md` — filled in after real-data
  run.

## 4. Environment

Dedicated conda env `fermi-gbm-t90-reproducibility-lab`, Python 3.11, installed
from this project's own `pyproject.toml`.

## 5. Stop conditions encountered

None yet identified as hard blockers.
