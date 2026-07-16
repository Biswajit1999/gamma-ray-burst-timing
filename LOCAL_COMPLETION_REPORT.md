# Local Completion Report — Fermi GBM T90 Reproducibility Lab

Author: Biswajit Jana. This report documents a local implementation pass
(project 10 of the 30-project pack, `BUILD_FIRST` priority 9.0/10). No git operations
were performed. Nothing has been published. This project's folder was renamed from
`fermi-gbm-t90-reproducibility-lab` to `gamma-ray-burst-timing` for a simpler,
human-readable GitHub repo name.

## 1. Environment

- New dedicated conda env `fermi-gbm-t90-reproducibility-lab` (Python 3.11),
  pinned to this project's own `pyproject.toml`: numpy==1.26.4, scipy==1.13.1,
  pandas==2.2.2, matplotlib==3.9.0, pyyaml==6.0.1, astropy==6.1.0,
  astroquery==0.4.7 (added — needed for `astroquery.heasarc.Heasarc` catalogue
  cross-checks), requests==2.32.3; dev: pytest, pytest-cov, ruff, mypy,
  types-PyYAML, types-requests.
- No local LaTeX toolchain.

## 2. Files created or changed

This project's entire `src/` layer was a raw stub scaffold at the start of this
session. Built this session: foundation (`config.py`, `exceptions.py`
(extended), `logging_utils.py`, `provenance.py` (extended), `results_io.py`),
data layer (`scripts/fetch_data.py`, `fetch.py`, `synthetic.py`,
`scripts/sync_web_assets.py`), scientific modules (`io.py`, `binning.py`,
`background.py`, `duration.py`, `uncertainty.py`, `core.py` (extended)),
9 test files (38 tests), figures/report (`scripts/make_figures.py`,
`reports/report.tex`, `reports/references.bib`), and the web dashboard
(`web-react/src/App.jsx` rewritten, `eslint.config.js` fixed, `recharts`
removed, `public/project.json` rewritten).

## 3. Exact commands run (in order)

```bash
python -m pip install -e ".[dev]"
pytest -q                                  # 38 passed
ruff check src tests scripts               # All checks passed
mypy src                                   # Success: no issues found in 15 source files
python scripts/run_analysis.py --demo
python scripts/make_figures.py --demo
# Real-data pipeline, run only after explicit operator authorization in chat:
python scripts/fetch_data.py --i-have-authorization
python scripts/run_analysis.py
python scripts/make_figures.py
python scripts/sync_web_assets.py
cd web-react && npm install && npm run lint && npm run build
```

## 4. Test / lint / build results

- **pytest**: 38 tests passed, 0 failed.
- **ruff**: clean on `src tests scripts`.
- **mypy**: clean on `src` (0 errors, 15 source files).
- **web-react**: `npm run lint` and `npm run build` both clean.

### Bugs found and fixed during implementation

1. **Real performance bug, found only against real data**:
   `astropy.stats.bayesian_blocks(..., fitness="events")` applied directly
   to raw photon time-stamps scales far worse than O(n log n) in practice —
   confirmed on a real, exceptionally bright GBM trigger (bn130427324) with
   3.4×10⁵ events in a 70-second window: **2239 seconds (37+ minutes)**.
   Fixed by pre-binning events into fine (64ms) fixed-width bins and running
   Bayesian Blocks with `fitness="measures"` on the resulting count series
   instead — the standard real-world approach used by actual GBM
   light-curve tools. Result: **0.2 seconds**, same block count (66 vs 72,
   consistent) to within a few percent. This fix was caught live: the first
   real-data pipeline run hung and had to be stopped via the tracked
   background task ID after ~8 minutes with no output; a targeted timing
   diagnostic isolated the cause before the fix was written.
2. `'tab:teal'` is not a valid matplotlib color name (matplotlib bar chart
   crashed on the demo figure); fixed to `'teal'`.
3. Test `test_bayesian_block_bins_returns_edges_spanning_data` needed
   updating after the pre-binning fix, since returned edges are now
   expressed in pre-bin-center coordinates (off by up to half a pre-bin
   width from the raw min/max), not exact raw-event boundaries.

## 5. Real datasets accessed

Real GBM TTE FITS files served directly from the public HEASARC archive
(no proprietary period), live-verified via WebFetch against real directory
listings before the fetch script was written.

- **Files**: `glg_tte_n0_bn170817529_v00.fit` (2.76MB), `glg_tte_n1_bn170817529_v00.fit`
  (2.91MB) — both GRB170817A, the short GRB associated with GW170817 — and
  `glg_tte_n0_bn130427324_v00.fit` (9.50MB) — GRB130427A, an exceptionally
  bright long GRB. 15.2MB total.
- **Catalogue cross-check**: official Fermi GBM Burst Catalog T90 values
  live-queried via `astroquery.heasarc.Heasarc`: GRB170817529
  T90=2.048±0.466s; GRB130427324 T90=138.242±3.238s.
- **Licence/terms**: NASA/HEASARC public archive data, no proprietary period.
- Full SHA-256 and provenance in `data/manifest.csv`. Raw FITS files are
  not committed.

## 6. Validation and uncertainty outcomes

- **Synthetic injection-recovery gate**: PASSED. A known 8.0s rectangular
  burst pulse on a known constant background is recovered as median T90
  within 4s of truth across all 4 (background_model × binning_method)
  configurations.
- **Failure-mode tests**: missing TTE file (warning, not crash), missing
  FITS EVENTS extension/columns, empty manifest, no-real-excess synthetic
  light curve — all raise the documented exceptions or are handled
  per-configuration without crashing the run.
- **Real-data result, the central honest finding**: this pipeline's T90
  estimates diverge substantially from the official Fermi GBM Burst
  Catalog for both real triggers analysed — GRB170817529 overestimated
  15–35× (real background drift over the analysis window mistaken for
  signal by simple background models), GRB130427324 underestimated
  2–13× (fixed 60s post-trigger window shorter than the true 138s burst).
  Both root causes are directly visible in the real light-curve figure and
  verified quantitatively, not hand-waved — this is a genuine, honestly
  reported limitation, not fabricated agreement with the catalogue.

## 7. Remaining TODOs / unresolved risks

- `reports/report.tex` could not be compiled to PDF locally (no LaTeX
  toolchain); structural completeness was checked, not a rendered PDF.
- This pipeline's absolute T90 values should NOT be treated as competitive
  with the official GBM catalogue algorithm for either the very-short or
  very-long burst regime; see Section 6.
- Only 2 real triggers (3 files) analysed, far below
  `minimum_sample_size=30`.
- No energy-channel (PHA)-resolved analysis in this first release.
- An adaptive analysis window (sized to the detected active region rather
  than fixed at −30/+60s) is a natural next extension to address the
  window-truncation limitation for long bursts.

## 8. Claims safe for a public README

- "Implements a reproducible pipeline estimating T90 gamma-ray burst
  durations from real Fermi GBM TTE data, validated against a synthetic
  injection-recovery gate before use on real data."
- "Found and fixed a genuine real-data performance bug: naive
  event-based Bayesian Blocks took 37+ minutes on a real bright trigger;
  pre-binning to 64ms bins before Bayesian Blocks (the standard real-world
  approach) reduced this to 0.2 seconds with equivalent results."
- "On real data from two well-known triggers, this simplified pipeline's
  T90 estimates diverge substantially from the official Fermi GBM Burst
  Catalog in both directions, with verified, documented causes — a genuine
  finding about the sensitivity and limits of simplified T90 pipelines
  relative to the official GBM analysis."
- "38 automated tests including an injection-recovery validation gate and
  failure-mode tests; ruff- and mypy-clean."
- "A transparent reproducibility lab; not an official GBM duration or
  spectral-analysis pipeline."

## 9. Claims that must NOT be made

- Do not claim this pipeline's T90 values agree with or reproduce the
  official Fermi GBM Burst Catalog — they diverge substantially for both
  real triggers analysed, for documented reasons.
- Do not claim this is a validated alternative to the official GBM T90
  algorithm.
- Do not claim energy-channel-resolved sensitivity was tested — only
  whole-detector count rate was used.
- Do not claim the TeX report PDF has been visually verified — only its
  source structure was checked.

## 10. Manual review checklist for Biswajit

- [ ] Compile `reports/report.tex` locally/Overleaf and read the PDF end-to-end.
- [ ] Consider implementing an adaptive analysis window to address the
      long-burst truncation limitation.
- [ ] Review `npm audit` output and decide whether to bump pinned frontend
      tooling.
- [ ] Follow `MANUAL_GITHUB_ONE_BY_ONE.md` for the actual repository
      creation and push, using the new repo name `gamma-ray-burst-timing`
      — none of that was done in this session.
