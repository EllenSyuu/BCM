# oosccohort

R package for the Bayesian cohort model of out-of-school rates (SDG indicator 4.1.4), implemented with Stan through **rstan**.

> **Status: work in progress.** The model is checked against the paper equation by equation ([paper audit](../../docs/paper-audit.md)), and its log density agrees with the independent NumPyro implementation in this repository. Agreement with the published estimates has not been verified yet. This is an independent implementation, not an official UNESCO product, and it does not produce official estimates.

Reproduced work: Dharamshi, A., Barakat, B., Antoninis, M. & Montoya, S. (2022). *A Bayesian Cohort Model for Estimating SDG Indicator 4.1.4: Out-of-School Rates.* UNESCO Institute for Statistics and Global Education Monitoring Report, TCG 9 document WG/HHS/2.

## Installation

From a clone of the repository:

```r
install.packages(c("rstan", "jsonlite", "testthat"))
install.packages("r/oosccohort", repos = NULL, type = "source")
```

rstan needs a C++ toolchain (see the [RStan getting-started guide](https://github.com/stan-dev/rstan/wiki/RStan-Getting-Started)). The model compiles the first time it is used, which takes a few minutes, and is then cached.

## Workflow

```r
library(oosccohort)

sim <- simulate_oosc(seed = 2022)            # synthetic countries SYA-SYD; replace with your own tables
data <- prepare_oosc_data(sim$countries, sim$admin, sim$survey)
fit <- fit_oosc(data)                        # paper settings: 4 chains, 2,000 + 2,000 iterations, thin 8
oosc_diagnostics(fit)
rates <- oosc_rates(fit)                     # median and 90% interval by country, year and single age
```

`fit_oosc()` uses the paper's sampler settings by default. For a quick try, use for example `fit_oosc(data, chains = 2, iter_warmup = 300, iter_sampling = 160, thin = 1)`; short runs do not meet the convergence thresholds.

## Input data

Three tables, checked by `validate_countries()`, `validate_admin()` and `validate_survey()` (see `?data_contract`):

| Table | Required columns |
|---|---|
| `countries` | `country`, `region`, `entry_age` (minimum official primary entry age); optional `max_age` |
| `admin` | `country`, `year`, `age`, `rate` (1 − enrolment / population; may be negative) |
| `survey` | `country`, `year`, `age`, `rate` (0–1), `se` (sampling standard error, real space), `series`, `wave` |

`prepare_oosc_data()` applies the paper's rules: administrative rates below −0.1 are dropped and other negative values kept (Sec. 2.1); survey rates of exactly 0 or 1 are dropped. Run one fit per sex population (male, female, total), as in the paper.

## What is implemented

| | |
|---|---|
| Model | Paper Eq. 1–37: real-space administrative likelihood, probit-space survey likelihood with series bias, smoothed random walk with negative drift for the entry-age baseline, two-dimensional P-spline cohort changes, shared variance scaling |
| Sampler | rstan NUTS, as in the paper (Stan 2.32 here; the paper used 2.21.5) |
| Outputs | Age-specific rates with credible intervals; convergence diagnostics |
| Not yet | Education-level rates, out-of-school populations and regional totals; validation and sensitivity variants (Tables 2–3) |

## Tests

```r
Sys.setenv(NOT_CRAN = "true")                # also runs the Stan tests (compiles the model)
testthat::test_local("r/oosccohort")
```

The Stan tests check that the Stan model's log density matches the NumPyro model at fixed parameter values (agreement to about 1e-10 in the log-density difference) and that a short fit on simulated data recovers the known rates.
