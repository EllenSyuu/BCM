# System architecture

The repository is organised as a research-engineering system with explicit boundaries between data preparation, probabilistic inference, diagnostics, and reporting.

source data -> data contracts and harmonisation -> validated model input -> NumPyro/JAX inference -> posterior diagnostics -> bounded reporting

## Main layers

| Layer | Responsibility |
|---|---|
| Data preparation | Convert source-specific records into validated country-year-age structures |
| Basis construction | Build entry-year and age/cohort spline bases |
| Model | Define latent cohort processes, survey bias, and observation likelihoods |
| Inference | Run NUTS with configurable warmup, draws, chains, thinning, and checkpoints |
| Diagnostics | Calculate R-hat, effective sample size, divergences, and finite-value checks |
| Reporting | Reconstruct bounded rates and write auditable tabular summaries |

## Design principles

- Keep restricted inputs outside the public repository.
- Make assumptions visible at module and documentation boundaries.
- Keep the statistical model separate from post-processing.
- Prefer deterministic synthetic tests for public verification.
- Treat convergence and validation as outputs, not hidden implementation details.