# Dataset Plan

## Mode

**real public Fermi GBM trigger data**

## Official sources and literature seeds

- Meegan et al. 2009, arXiv:0908.0450
- Fermi Science Support Center GBM data/tools
- Gamma-ray Data Tools documentation
- Scargle et al. 2013 Bayesian Blocks
- Stingray timing package, arXiv:1901.07681

## Acquisition rules

- Prefer official mission/archive endpoints and author-maintained catalogue deposits.
- Record product identifier, query, retrieval UTC, source URL, file size, checksum and licence/terms.
- Do not commit large raw FITS, HDF5 or catalogue files.
- Store a deterministic manifest under `data/manifest.csv`.
- Store only a tiny, clearly labelled synthetic/example dataset in `data/example/`.
- Never replace inaccessible real data with fabricated values while presenting them as observations.

## Required manifest columns

`product_id, source, source_url, retrieved_utc, sha256, file_size_bytes, selection_reason, licence_or_terms`

## FAIR contract

Every derived product must point to the raw product ID, software commit, configuration hash and transformation script.
