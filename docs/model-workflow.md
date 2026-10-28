# Model workflow

How an observation becomes an estimate. Equation-level choices and known deviations are in [model-notes.md](model-notes.md); which parts are verified is in [status.md](status.md). Dashed elements are planned, not implemented.

```mermaid
flowchart TB
  A["Cohort indexing<br/>relative age a, entry year = year − a + 1"] --> B["Spline bases on the entry-year grid"]
  B --> MU["Baseline mu<br/>random walk with drift"]
  B --> TH["Cohort variation Theta<br/>smoothed over age and cohort"]
  MU --> K["Latent probit rate kappa"]
  TH --> K
  K --> L1["Administrative likelihood"]
  K --> L2["Survey likelihood<br/>with series bias"]
  L1 --> N["NUTS inference"]
  L2 --> N
  N --> R["Age-specific out-of-school rates<br/>median and 90% interval"]
  R -.-> AGG["Education-level rates and aggregates"]
  classDef plan fill:#ffffff,stroke:#8a8984,stroke-dasharray:5 3,color:#52514e
  class AGG plan
```

1. **Cohort indexing.** Each observation (country, year, single age, sex) is mapped to a relative age (1 = the country's minimum entry age) and to the year its cohort entered school.
2. **Spline bases.** Cubic B-spline bases are built on the entry-year grid: annual knots for the baseline and five-year knots for the cohort variation (`spline_basis.py`).
3. **Baseline mu.** A random walk with a country-specific drift on the annual spline coefficients, anchored at 2000, with regional drift scales.
4. **Cohort variation Theta.** A surface of age-by-cohort changes with smoothing penalties in both directions; the entry age carries no change.
5. **Latent rate kappa.** The probit-scale out-of-school rate is mu plus Theta.
6. **Likelihoods.** Administrative rates are compared in real space (the normal CDF of kappa, with administrative and regional noise); survey rates in probit space (kappa plus a country-by-series bias, with sampling and wave noise).
7. **Inference.** NUTS in Stan through the R package (`r/oosccohort`, model in `inst/stan/oosc_cohort_model.stan`) or in NumPyro (`oosc_model_numpyro.py`). The two implementations are tested to define the same log density.
8. **Outputs.** `run_full_model.py` reports the posterior median and 90% interval for every country × year × relative age, plus diagnostics and variance components.
9. **Planned.** Aggregation from single ages to education levels, out-of-school populations, and regional and global totals.

## Checkpointing and resumption

With `--checkpoint-every N`, sampling runs in chunks. Each chunk's draws and the sampler state are written before `checkpoint.json` advances, so an interrupted run resumes from the last saved state and reproduces the draws of an uninterrupted run. With `--checkpoint-every 0` the sampler runs once; for the same seed it returns identical draws (`tests/test_checkpointing.py`, CPU, one chain).

```mermaid
flowchart TB
  start(["run_full_model.py"]) --> m{"checkpoint.json<br/>exists?"}
  m -- "no" --> w["Warm-up, save state_000000.pkl"]
  m -- "yes, same settings" --> r["Load last state from manifest"]
  m -- "yes, different settings" --> x["Stop with an error"]
  w --> c["Sample next chunk<br/>(--checkpoint-every iterations)"]
  r --> c
  c --> s["Save samples_N.npz and state_N.pkl,<br/>then update manifest"]
  s --> d{"all draws done?"}
  d -- "no" --> c
  d -- "yes" --> f["posterior_draws.npz,<br/>status sampling_complete"]
  start -. "--checkpoint-every 0" .-> one["Single compiled run<br/>(identical draws)"] --> f
```
