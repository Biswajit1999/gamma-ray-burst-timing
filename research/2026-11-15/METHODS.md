# GRB duration diagnostics — 15 November 2026

Two isolated numerical analyses: linear within-bin interpolation of cumulative 5%/95% crossings and T90 sensitivity across alternative *assumed* background arrays. Negative net bins are clipped, which may bias weak bursts. These methods do not replace the existing centre-of-bin catalogue pipeline. Background-model range is **not** an uncertainty interval.

Run from this directory: `python -m pytest test_duration_diagnostics.py -q`. Optional reproducible figure: `python make_duration_diagnostic_figure.py`; the figure uses deterministic synthetic Gaussian-shaped counts and writes `figures/fig06_synthetic_background_sensitivity.png`. No GBM archive data were used. Compare event-level estimates, low-count Poisson models, and background windows before applying to observations.

Prepared with AI coding assistance under the maintainer's direction; no astronomical discovery or new observation claimed.
