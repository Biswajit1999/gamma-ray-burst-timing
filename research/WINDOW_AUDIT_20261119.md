# Conditional observation-window sensitivity (19 November 2026)

Three independent operations: (1) interpolate 5% and 95% cumulative positive-excess counts within time bins; (2) recompute T90 after progressively longer **complete-bin** observation windows; (3) recompute T90 for externally supplied background count models, explicitly clipping negative excess to zero. A rectangular uniform pulse of width D has T90 = 0.9 D, not D.

Run from the repository root: `python -m pytest -q research/test_window_audit_20261119.py`.

These are deterministic synthetic checks, **not** new Fermi GBM estimates. Window truncation cannot reconstruct unobserved photons. A change in estimated T90 across right boundaries is evidence of estimator sensitivity, not necessarily burst activity. The background models are hypothetical and are not refitted to off-burst data. No confidence interval or catalogue accuracy is claimed. Existing observational outputs and estimator remain untouched.

Research lead and requested Git author: Biswajit Jana. Python implementation developed with AI coding assistance and requires independent scientific review.
