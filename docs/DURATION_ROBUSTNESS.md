# T90 quantile, background and Poisson robustness (25 October 2026)

Tracks scientific-scope issue #1. Independent NumPy implementation in `src/fermi_gbm_t90_reproducibility_lab/duration_robustness.py` does not change the existing catalogue pipeline.

1. **Bin-edge-interpolated T5/T95/T90** from nonnegative background-subtracted counts. Quantile times assume a uniform excess rate within each bin. Negative residuals are clipped; this biases weak/noisy bursts and is not a detection test. The supplied signal window includes only complete bins.
2. **Background-mask and model sensitivity.** Fits constant or linear rates to fully off-burst bins, using bin-width weights, and recomputes T90 for explicitly supplied exclusion buffers. Poisson rate-weighting is approximate if rates vary strongly.
3. **Counting-noise sensitivity.** Seeded parametric Poisson resampling with a fresh off-burst fit on every draw. This is conditional on the observed bin counts as plug-in rates; it omits detector response, calibration systematics and correlated background errors. Failed realizations are reported.

**Important definition:** for a noiseless rectangular pulse lasting 8 s, the true interval between the 5th and 95th percentiles is **7.2 s**, not 8 s. The existing `synthetic.py` fixture labels the full 8 s pulse duration as `truth_t90`; this is a separate known semantic discrepancy and must be addressed with a focused follow-up that updates existing tests and reported benchmarks together. This module deliberately leaves the legacy fixture and pipeline unchanged.

## Reproduce

```bash
python -m pip install -e '.[dev]'
python -m pytest -q tests/test_duration_robustness.py
python scripts/run_duration_robustness.py --output outputs/grb_synthetic.json
```

No new Fermi observational result or GRB classification is claimed. All numerical acceptance tests here use declared deterministic or seeded synthetic inputs. Before integrating this estimator into catalogue processing, compare on official GBM TTE products and quantify dependence on detector, channel selection, window placement and burst morphology.
