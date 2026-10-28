# Paper audit: code vs published methodology

**Reference document.** Dharamshi, A., Barakat, B., Antoninis, M. & Montoya, S. *A Bayesian Cohort Model for Estimating SDG Indicator 4.1.4: Out-of-School Rates. A proposal by the UNESCO Institute for Statistics and the Global Education Monitoring Report.* Technical Cooperation Group on the Indicators for SDG 4, 9th meeting, document WG/HHS/2, 22 November 2022 (paper dated 28 August 2022). Section, equation, table and figure numbers below, and in the code comments, refer to this version. A later version was posted as a SocArXiv preprint in 2023 (doi:10.31235/osf.io/sqwb2); it has not been audited here.

**Scope.** This audit compares the code with the text of the paper, line by line. It is a manual check of the specification. It does not establish numerical agreement with the published results, which needs a full fit on the restricted inputs (see [status.md](status.md)). The paper itself is not redistributed in this repository.

**Outcome.** Every model equation, prior and sampler setting matches the paper. The remaining differences concern data vintages, the validation and sensitivity variants, and details the paper does not specify. No change to the model is needed.

Legend: **match** — the code implements what the paper states. **interpretation** — the paper does not pin this down; the code's choice is recorded. **differs** — the code deviates from the paper, with the reason. **missing** — described in the paper but not implemented.

## 1. Model specification (Sec. 3, App. B)

| # | Paper | Code | Verdict |
|---|---|---|---|
| M1 | Administrative likelihood, real space: A_i ~ N(κ, σ² + ω²_r) (Eq. 1, 16) | Normal with mean Φ(probit-scale κ) and sd √(σ² + ω²_r) | match |
| M2 | Survey likelihood, probit space: Φ⁻¹(S_j) ~ N(Φ⁻¹(κ) + β_{c,s}, (ν²_j + η²_w) / f(Φ⁻¹(S_j))²), f the standard normal pdf (Eq. 2, 17) | Normal with sd √((ν² + η²) / f²), f evaluated at the observed probit value | match |
| M3 | Φ⁻¹(κ_{c,y,a}) = μ_{c,y−a+1} + Θ_{c,y,a} (Eq. 3, 18) | Both terms evaluated at the entry year y − a + 1 | match |
| M4 | a = 1 is the minimum entry age over all years (Sec. 3) | Relative age counted from each country's minimum official primary entry age | match |
| M5 | μ_{c,y} = Σ_k B⁽¹⁾_k(y) μ*_{c,k}, annual knots (Eq. 4, 19) | `B1`, cubic B-spline with annual knots on the entry-year grid | match (degree: see I1) |
| M6 | μ*_{c,k+1} = γ_c + μ*_{c,k} + ε_{c,k} (Eq. 5, 20) | Same recursion, run forward and backward from the 2000 anchor | match (anchor: see I2) |
| M7 | γ_c ~ N⁻(0, σ²_{γ,r[c]}): drift constrained to be negative (Eq. 6, 22) | γ = −σ_{γ,r}·\|z\|, z half-normal | match |
| M8 | σ_{γ,r} ~ N⁺(0, 0.02²) (Eq. 7, 23) | HalfNormal(0.02) per region | match |
| M9 | ε_{c,k} ~ N(0, σ²_μ), σ_μ ~ N⁺(0, 0.1²) (Eq. 8–9, 28–29) | Non-centred: ε = σ_μ·z, σ_μ ~ HalfNormal(0.1) | match |
| M10 | μ*_{c,0} ~ N(0, 2²), the year-2000 value (Eq. 27) | `mu_star_2000` ~ Normal(0, 2) | match |
| M11 | Θ_{c,y,a} = Σ_{g=1}^{a−1} Σ_k B⁽⁵⁾_k(y−a+1) α_{c,g,k}, 5-year knots (Eq. 10, 21) | Cumulative sum of α over ages, times `B5` at the entry year; Θ = 0 at a = 1 | match |
| M12 | α_{c,g,k} ~ N(α_{c,g−1,k}, τ⁻¹_{α1}) (Eq. 11, 24) | Penalty on differences along age with sd τ₁^{−1/2} | match |
| M13 | α_{c,g,k} ~ N(α_{c,g,k−1}, τ⁻¹_{α2}) (Eq. 12, 25) | Penalty on differences along spline index with sd τ₂^{−1/2} | match |
| M14 | Σ_{g=1}^{a−1} α_{c,g,k} ~ N(0, 2²) (Eq. 13, 26) | Column sums over all age rows ~ Normal(0, 2) | match (upper limit: see I3) |
| M15 | τ_{α1}, τ_{α2} ~ N⁺(0, 1²) (Eq. 14–15, 30–31) | HalfNormal(1) | match |
| M16 | β_{c,s} ~ N(0, σ²_{β,s}), σ_{β,s} ~ N⁺(0, 0.1²) (Eq. 32–33) | Non-centred, one scale per series shared across countries | match |
| M17 | σ, ω_r, η_w ~ N⁺(0, σ²_σ), σ_σ ~ N⁺(0, 0.01²) (Eq. 34–37) | Non-centred: each = σ_σ·\|z\|, σ_σ ~ HalfNormal(0.01) | match |
| M18 | ν_j and η_w in real space, moved to probit space by the delta method (Sec. 3.3.2, App. B) | Same | match |

The variance convention is consistent: the paper writes N(mean, variance) throughout (for example N⁺(0, 0.02²)), and the code passes the corresponding standard deviation. The non-centred forms change the sampler geometry, not the model.

## 2. Inference (Sec. 3.4, App. C)

| # | Paper | Code | Verdict |
|---|---|---|---|
| S1 | NUTS, Stan 2.21.5 via R (rstan) 4.0.2 | R package `oosccohort`: rstan (Stan 2.32 tested). Python pipeline: NumPyro/JAX. The two implementations have matching log densities (parity test) | match (Stan via rstan; newer Stan version) |
| S2 | 4 chains, 2,000 burn-in and 2,000 sampling iterations per chain | `run_full_model.py` defaults: `--chains 4 --warmup 2000 --samples 2000` | match |
| S3 | Thinned to 1,000 draws per population | `--thinning 8`: 4 × 2,000 / 8 = 1,000 | match |
| S4 | Separate fits for male, female and total populations | `assemble_model_input.py --sex M/F/MF` | match |
| S5 | Target acceptance rate not stated | 0.99 | interpretation (I6) |
| S6 | Convergence: trace plots, ESS, R-hat | R-hat, ESS and divergences recorded in `run_info.json`; thresholds R-hat ≤ 1.01, ESS ≥ 400 | match (thresholds are this project's) |

## 3. Data and pre-processing (Sec. 2, App. A)

| # | Paper | Code | Verdict |
|---|---|---|---|
| D1 | Administrative observations below −0.1 excluded; other negative values kept (Sec. 2.1) | Same cut-off | match |
| D2 | Enrolment summed across education levels for each country-age-sex-year (App. A.2.1) | Same | match |
| D3 | Exclusion steps 1 and 2 (missing expected level; missing prior level at the first age of a level) | Implemented | match |
| D4 | Exclusion step 3: country-specific higher age threshold where delayed enrolment is consistently large | Not applied: it needs per-country judgments that the paper does not list | differs |
| D5 | Population: WPP **2019** revision, Eurostat for European countries, SingStat for Singapore, each 2000–2021 | WPP **2024** revision; Eurostat and SingStat as in the paper | differs (vintage) |
| D6 | Survey rates from weighted attendance responses; sampling errors from a clustered jackknife (App. A.2.2) | Same, for DHS, MICS and IPUMS | match |
| D7 | IPUMS extracts capped at one million records | Deterministic subsample of whole households to one million records | match |
| D8 | "Other" surveys from WIDE, 16 national surveys (App. A.1) | WIDE is available only as education-level aggregates, so it is left out of the main fit; `reweight_wide.py` adds it approximately afterwards | differs (data availability) |
| D9 | Survey rates of exactly 0 or 1 (probit undefined) — not discussed | Dropped | interpretation (I5) |
| D10 | Seven SDG regions (Fig. 7) | Seven SDG regions | match |
| D11 | Waves: DHS4–8 and MICS2–6 separately; census and "Other" each pooled (Fig. 8) | Same grouping | match |

## 4. Validation and sensitivity (Sec. 3.5, 4.4, 4.5)

| # | Paper | Code | Verdict |
|---|---|---|---|
| V1 | Drop 20% of each country's observations at random and **refit the model** | `holdout_validation.py` drops 20% per country but refits each country with global parameters fixed at full-data medians | differs (documented leakage) |
| V2 | Compare held-out data with bias-adjusted median κ: MSE, MAE, and aMSE/aMAE using max(0, A_i) | Same metrics | match |
| V3 | Coverage of prediction intervals; the text says coverage is reported "for the entire sample" | Coverage computed on the held-out observations | interpretation (I7) |
| V4 | Variants: Simple (negatives set to 0.0032%, probit −4), NoBias | Implemented | match |
| V5 | Variants: MuRW (random walk without drift, no smoothing) and MuK5 (5-year knots for μ) | Not implemented | missing |
| V6 | Sensitivity (Table 3): τ prior scales 0.5 and 2; 3- and 8-year knots for α | Not implemented | missing |

## 5. Outputs (Sec. 4)

| # | Paper | Code | Verdict |
|---|---|---|---|
| O1 | Country × year × age rates with 90% intervals, 2000–2022 (Fig. 5, 6) | `estimates.csv` | match |
| O2 | Out-of-school populations: rates × country-year-age population, summed to countries and SDG regions (Sec. 4.2, Fig. 7) | Not implemented | missing |
| O3 | Education-level rates "through post-processing aggregation steps" (Sec. 1, 3); the method is not specified | Not implemented | missing (I8) |
| O4 | Posterior total standard error by source: σ + ω_r (administrative), ν_j + η_w (survey), as plain sums (Fig. 8) | Variance components in `parameters.csv`; the Fig. 8 summary is not produced | missing |

## 6. Interpretations the paper leaves open

| # | Question | Choice in the code |
|---|---|---|
| I1 | Spline degree and boundary knots | Cubic B-splines with clamped boundary knots |
| I2 | Equation 27 indexes the year-2000 coefficient as k = 0, but cohorts observed at older ages entered school before 2000 | The entry-year grid extends before 2000; the coefficient whose Greville abscissa is 2000 is the anchor, and the random walk runs both ways from it |
| I3 | Upper limit a − 1 in Eq. 13 when the constraint applies to a whole column | Sum over all age rows of each column |
| I4 | Prior on the first age row of α beyond Eq. 12–13 | None beyond Eq. 12–13 (improper flat base, as in the paper) |
| I5 | Survey cells with rate exactly 0 or 1 | Dropped |
| I6 | Target acceptance rate | 0.99 (Stan's default is 0.8) |
| I7 | Whether coverage uses held-out or all observations | Held-out observations |
| I8 | Aggregation from single ages to education levels | Not chosen yet. Proposed: population-weighted mean of single-age rates over the level's official age range in each year, using that year's entry age and duration |

## 7. Comparison targets for the full fit

Published values that a full fit can be checked against. They are taken from the paper; reproduced values will only be recorded after a full run.

| Target | Published value | Location |
|---|---|---|
| Observations: administrative / census / DHS / MICS / other | 92,036 / 4,254 / 6,030 / 6,197 / 1,689 (110,206 total, 192 countries) | Table 1, App. A.1 |
| Countries with administrative data / with survey data | 187 / 135 | App. A.1 |
| Share of observations that are negative | 15.4% | Sec. 2.1 |
| Out-of-sample validation, full model | MSE 0.0051, aMSE 0.0046, MAE 0.0435, aMAE 0.0389; coverage 0.88 / 0.93 / 0.95 at 80 / 90 / 95% | Table 2 |
| Validation, other variants | MuK5, MuRW, Simple, NoBias rows | Table 2 |
| Sensitivity variants | τ and knot-spacing rows | Table 3 |
| Median total standard error, all observations | 0.0725 | Sec. 4.3 |
| Global out-of-school population | about 400 million (2000) to about 250 million (2022) | Sec. 4.2, Fig. 7 |
| Country curves | Argentina, Burkina Faso, Chad, D.R. Congo, Lesotho, Mexico, Morocco, Sweden (visual comparison only; no values are tabulated) | Fig. 5, 6 |

Because the inputs differ (D4, D5, D8) and the implementation differs (S1), exact agreement is not expected. **Proposed tolerances**, to be confirmed by the maintainer before any results are seen:

- **Observation counts:** within 5% per source, with any larger gap explained.
- **Validation metrics (Table 2):** MSE and MAE within 15% relative; coverage within ±0.03.
- **Median total standard error:** within 15% relative.
- **Global out-of-school population:** within 10% for each reported year.
- **Country curves:** the published median curves should lie inside the reproduced 90% intervals for most ages and years; this is checked visually and reported as such.

## 8. Next steps arising from the audit

1. Implement the missing validation variants (V5) and sensitivity runs (V6) so that Tables 2 and 3 can be compared row by row.
2. Implement the population aggregation (O2), then the education-level rates (O3, after choosing I8).
3. Make the hold-out validation refit the model (V1), at least for the full model, or state the leakage next to every reported number.
4. Optionally add a WPP 2019 input path (D5) to separate the effect of the population vintage from everything else.
