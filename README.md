# Bayesian Cohort Model Reproduction

[![CI](https://github.com/EllenSyuu/BCM/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/EllenSyuu/BCM/actions/workflows/ci.yml?query=branch%3Amain)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An independent, public-safe reproduction of a Bayesian cohort model for estimating out-of-school rates for SDG indicator 4.1.4.

> **Scope boundary:** This is not the official UNESCO, UIS, or GEM Report model. It does not publish official estimates. Restricted administrative inputs are intentionally excluded.

**Reproduced work:** Dharamshi, A., Antoninis, M., Montoya, S. & Barakat, B. F. (2023). *A Bayesian cohort model for estimating out-of-school rates and populations.* SocArXiv. https://doi.org/10.31235/osf.io/sqwb2 [TODO: verify citation — the Stan source header cites a 2022 UIS/GEMR version with a different title; confirm which version the code's section and equation numbers follow.]

**Data boundary:** Restricted inputs are stored locally or in a separate private environment and are never committed to this repository.

## Why this project matters

The project reconstructs an age-by-country-year probabilistic model from the published methodology and turns it into a reproducible data and inference pipeline.

- Bayesian hierarchical modelling with NumPyro/JAX
- equation-level Stan reference implementation
- spline-based cohort effects and survey-bias terms
- explicit data contracts and harmonisation logic
- checkpointable MCMC, convergence diagnostics, and bounded post-processing
- synthetic end-to-end tests that run without restricted data

## Engineering highlights

| Capability | Implementation |
|---|---|
| Probabilistic inference | NumPyro NUTS with JAX/XLA |
| Reference model | Stan implementation aligned to published equations |
| Performance | Device-cached inputs, single-compile execution, chunked reporting |
| Reliability | Restartable checkpoints, manifests, progress tracking |
| Validation | Synthetic smoke tests, parameter diagnostics, bounded-rate checks |
| Data safety | Public code and synthetic examples only |

## Quick start

    python -m pip install -r requirements/base.txt
    pytest -q

Run the public synthetic demonstration:

    python examples/synthetic_demo/run_demo.py

The demo validates execution and output constraints; it is not an empirical estimate.

## Repository map

    src/python/             Executable public Python modules
    src/stan/                Equation-level Stan reference
    examples/                Public synthetic demonstrations
    tests/                   Automated tests
    docs/                    Architecture, status, provenance, performance
    scripts/                 Reproducible command-line entry points

Start with:

- [Project status](docs/status.md)
- [System architecture](docs/architecture.md)
- [Model implementation notes](docs/model-notes.md)
- [Performance and reliability](docs/performance.md)
- [Reproducibility guide](docs/reproducibility.md)
- [Data and publication boundary](PUBLICATION_NOTES.md)

## Reproducibility statement

A complete empirical reproduction requires authorised administrative inputs that are not distributable in this repository. Public readers can run the synthetic pipeline, inspect the model translation, execute the tests, and audit the documented assumptions.

Claims are deliberately separated into **implemented**, **tested**, **validated**, and **complete reproduction**. The last label is reserved for a run with all required inputs and documented validation.

See [CITATION.cff](CITATION.cff).