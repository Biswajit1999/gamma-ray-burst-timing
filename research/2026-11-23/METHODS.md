# Low-count on/off duration sensitivity (2026-11-23)

Author: Biswajit Jana. Python implementation prepared with AI coding assistance; review and execution required.

## Scope and assumptions
Independent Poisson counts in source/on and background/off windows; known positive exposure scaling alpha. Net = on - alpha*off; estimated variance = on + alpha² off. This is a plug-in estimator, not a posterior uncertainty interval. Duration uses positive-part net counts and uniform-within-bin T5/T95 interpolation; clipping negative residuals introduces bias. Seeded bootstrap samples on and off from observed counts, reports 2.5/50/97.5% quantiles and valid-draw fraction; intervals are conditional on the fitted counts and fixed background scale, not calibrated catalogue intervals. No detector response, energy-dependent efficiency, burst-selection uncertainty or background-model systematics included.

## Reproduce
From this directory: `python -m pytest -q test_poisson_duration.py`. Requires numpy and pytest. The script imports the sibling module. Numerical outputs are synthetic only. No archival files were read, and no Fermi result is replaced.

## Next validation
Compare to injected known-duration low-count synthetic bursts across background levels and run a coverage study before applying to provenance-verified GBM time-tagged events. Issue #6.
