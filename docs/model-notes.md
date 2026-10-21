# Model implementation notes

This document records public, equation-level implementation decisions. It describes the implementation, not a claim of exact agreement with any non-public reference system.

## Model structure

The model represents the probit-scale out-of-school rate as a baseline cohort process plus age-specific cohort effects:

`Phi^-1(kappa[c,y,a]) = mu[c,y-a+1] + Theta[c,y,a]`.

Both terms are evaluated on a shared entry-year grid. This is required for observations where an older learner's entry year precedes the reporting window.

## Priors and parameterisation

- The annual baseline process is anchored at the paper's stated control year.
- Random-walk innovations and hierarchical scale parameters use non-centred parameterisations.
- Survey-series bias is represented with a shared scale and standard-normal latent effects.
- Administrative and survey observation error components are modelled separately.
- The age/cohort surface uses additive smoothing penalties corresponding to the published equations.

The non-centred forms are distribution-preserving reparameterisations intended to improve sampler geometry; they do not change the target model specification.

## Spline conventions

The implementation uses cubic B-splines with clamped boundary handling. The published methodology specifies the spline idea and knot spacing but does not expose every implementation detail needed to prove byte-for-byte equivalence. Boundary handling and knot sensitivity are therefore documented assumptions and validation targets.

## Observation handling

Administrative observations are retained on their native scale subject to the documented preparation rules. The model maps the latent probit-scale quantity through the normal CDF, so reported rates remain in [0, 1]. Any excluded observations are handled in the data-preparation layer rather than silently discarded inside inference.

## NumPyro and Stan

The Stan file provides an equation-level reference. The NumPyro implementation is the primary executable path for the public synthetic demonstration. Both implementations use the same named model components and equation references, while allowing language-specific parameterisation choices.

## Known limitations

- A complete empirical reproduction depends on authorised inputs that are not distributed here.
- Some spline and regional-grouping conventions require confirmation against an approved reference implementation.
- Public synthetic tests validate execution and invariants; they do not establish empirical agreement.
- Final claims require convergence diagnostics, sensitivity analysis, and comparison against an approved reference.

See [status.md](status.md), [performance.md](performance.md), and [reproducibility.md](reproducibility.md) for the release-level interpretation.