# Research Blueprint

## Technical title

Fermi GBM T90 Reproducibility Lab

## Category

Gamma-ray instrumentation / timing data science

## Bounded scientific question

How sensitive are T90 duration estimates to background model, detector, energy channel and time binning?

## Gap statement

A transparent reproducibility lab; not an official GBM duration or spectral-analysis pipeline.

## First-release scope

The first release must be completable as a focused 4–6 hour implementation pass after data access is working. It must deliver one reproducible analysis pipeline, one deterministic example/smoke dataset, tests, 4–6 figures, a concise TeX report and a deployable research webpage.

## Validation and uncertainty

- synthetic known-duration injection
- bootstrap T5/T95/T90
- background-model sensitivity
- detector/channel comparison

## Required figures

1. light curve/background intervals
2. T5/T95 markers
3. Bayesian blocks
4. bootstrap T90
5. model sensitivity

## Reusable scientific modules

- `fetch.py`
- `io.py`
- `binning.py`
- `background.py`
- `duration.py`
- `uncertainty.py`
- `plotting.py`

## Explicit exclusions

- No novelty claim beyond the bounded dataset/question/method combination.
- No causal claim from descriptive catalogue correlations.
- No hidden manual data editing.
- No unsupported precision beyond the input uncertainties.
- No production-pipeline replacement claim.
