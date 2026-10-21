# Visualization plan

Status: **design**. Only F1 is implemented. Every figure must be rebuildable from code, state its data source and limits in its caption, and use the reference palette (validated: blue `#2a78d6` for estimates, orange `#eb6834` for flagged points, always paired with a second cue such as a hollow marker or label).

## Where figures live

| Data | Output location | Versioned? |
|---|---|---|
| Synthetic (demo) | `examples/synthetic_demo/output/` | No. A single reference copy of F1 is committed as `docs/assets/synthetic_recovery.svg`. |
| Real data (public, licensed or restricted inputs) | `<data root>/A.2. Processed/figures/<tag>/` | **Never.** Country-level estimates from restricted inputs stay in the private environment. |

Real-data figures are produced only in the private environment. Whether any aggregate real-data figure is published is a separate decision, made per figure.

## Figure list

| ID | Figure | Data | Priority | Status |
|---|---|---|---|---|
| F1 | Synthetic recovery: truth vs posterior | synthetic | must have | **implemented** |
| F2 | Convergence summary (R-hat, ESS, divergences) | synthetic and real | must have | planned |
| F3 | Country profile: rates by age over time, with observations | real (private); synthetic example | must have | planned |
| F4 | Paper comparison: paper value vs reproduced estimate | real (private) | must have | design only (below) |
| F5 | Posterior predictive check by source | synthetic and real | should have | planned |
| F6 | Variance components and survey bias by series | synthetic and real | should have | planned |
| F7 | Hold-out validation metrics (Table 2 analogue) | real (private) | should have | planned |
| F8 | Data coverage map: observations per country × year × source | synthetic (public); real (private) | should have | planned |
| F9 | Education-level rates, out-of-school populations, regional and global totals | real (private) | later | blocked: aggregation not implemented |
| F10 | Stan vs NumPyro parity (log density, posterior summaries) | synthetic | later | blocked: parity test not implemented |
| F11 | Sensitivity to spline knots and priors | synthetic and real | later | planned |

The real-data figures share one proposed entry point, `python src/python/report_figures.py --tag MF --figure <id>`. It does not exist yet; the synthetic versions would be added to `run_demo.py`.

## Specifications

### F1 Synthetic recovery (implemented)

- **Purpose:** show that the pipeline recovers a surface it was simulated from, and that interval coverage is close to nominal.
- **Input:** `synthetic_truth.csv`, `A.2. Processed/model_output/SYNTH/estimates.csv`, `demo_summary.json` and the model input (for the years with administrative data), all in the demo output directory.
- **Output:** `examples/synthetic_demo/output/synthetic_recovery.svg`; reference copy at `docs/assets/synthetic_recovery.svg`.
- **Command:** `python examples/synthetic_demo/run_demo.py` (draws it automatically); redraw only with `python examples/synthetic_demo/plot_recovery.py [--svg PATH]`.
- **Design:** panel A plots the posterior median against the true rate for every cell, with 90% intervals as vertical lines, a y = x reference, and hollow orange rings for true rates outside the interval. Panel B shows one relative age over time for each synthetic country (90% band, median, dashed truth, ticks for years with administrative data). The header reports coverage, mean absolute error and convergence diagnostics.
- **Caption (fixed in the figure):** simulated data; short run; convergence thresholds not met; a pipeline check, not a formal or empirical result.
- **Test:** `tests/test_synthetic_demo.py` checks that the SVG parses, reports the same coverage as `demo_summary.json`, and carries the caveat.

### F2 Convergence summary

- **Purpose:** make convergence auditable at a glance before any estimate is read.
- **Input:** `diagnostics.csv`, `run_info.json`.
- **Output:** `figures/<tag>/convergence.svg`.
- **Design:** for each parameter group (mu, alpha, survey bias, variance components, reported rates), a strip of R-hat values with a reference line at 1.01, and a second strip of ESS with a line at 400; the divergence count shown as text. Two charts with one axis each, not a dual-axis chart.
- **Caption:** run settings, seed, data tag, and whether the thresholds are met.

### F3 Country profile

- **Purpose:** the reproduction's counterpart to the paper's country figures: estimated rates by age over time, with the data that informed them.
- **Input:** `estimates.csv`, `model_observations_<tag>.csv`, `parameters.csv` (survey bias).
- **Output:** `figures/<tag>/country_<ISO3>.svg` (real data, private); `examples/synthetic_demo/output/country_SYA.svg` (synthetic).
- **Design:** small multiples by relative age; 90% band and median line. Administrative observations drawn as filled dots and survey observations as hollow markers, shown both raw and bias-adjusted, so identity is never carried by colour alone.
- **Caption:** country, sex, data sources and their counts; "real data, not for publication" on private outputs.

### F5 Posterior predictive check

- **Input:** posterior draws (`checkpoints/posterior_draws.npz`) and model input. Requires a small helper that reuses the model's own observation equations rather than a new copy.
- **Design:** observed vs predicted, faceted by source (administrative, each survey series), with the predictive 90% coverage per source in each panel title.

### F6 Variance components and survey bias

- **Input:** `parameters.csv`.
- **Design:** a dot-and-interval chart per parameter (median, 5–95%), grouped by family, with region, wave and series labels taken from the index file.

### F7 Hold-out validation

- **Input:** `holdout_<variant>.csv` from `holdout_validation.py`.
- **Design:** for each variant (model, no-bias, simple) and source, a small table plus a dot chart of aMSE, aMAE and coverage at 80/90/95% against nominal. The caption repeats the documented leakage caveat (global parameters fitted on all data).

### F8 Data coverage map

- **Design:** a heatmap of country × year with one sequential single-hue ramp for observation counts, faceted by source. The synthetic version shows the every-third-year gap for SYD.

## F4 Paper-comparison visualization (design only)

No paper values or reproduced values are entered until the paper check is done. Nothing below is a result.

### Comparison table (source of truth for the figure)

The figure is drawn from one table per run. The paper value columns, filled from the published paper with a page and table reference, are public. The reproduced columns come from restricted-data fits and stay private.

| Column | Meaning |
|---|---|
| `target_id` | Stable identifier, for example `T2_aMAE_admin` or `F5_<country>_<year>_<age>` |
| `paper_version` | `2023 SocArXiv` or `2022 UIS/GEMR` (to be confirmed) |
| `paper_location` | Table, figure or page in that version |
| `quantity`, `unit` | What is compared (rate, population, error metric) and its unit |
| `country_or_region`, `year`, `sex`, `level_or_age` | Cell identifiers |
| `paper_value`, `paper_lo`, `paper_hi` | As published; interval columns empty if not published |
| `reproduced_median`, `reproduced_lo`, `reproduced_hi` | From this reproduction |
| `difference` | `reproduced_median − paper_value`, in the quantity's unit |
| `tolerance` | Agreed tolerance for this target (rule below) |
| `status` | `within tolerance`, `outside tolerance`, `not reproduced`, or `paper value unverified` |
| `run_id`, `git_sha` | Which run and code produced the reproduced value |
| `note` | Known deviation that explains a difference (for example WIDE excluded or a different WPP vintage) |

**Proposed tolerance rule, to be agreed before any comparison:** for rates, |difference| ≤ max(1 percentage point, half the width of the published 90% interval); for counts and error metrics, a relative tolerance fixed per target. The rule is fixed before results are seen and is printed on the figure.

### Figure design

- **Panel A, value comparison:** one row per target. A black tick marks the published value (with its interval, if published) and a blue dot with a 90% interval marks the reproduced estimate. Rows are grouped by paper table or figure.
- **Panel B, deviation:** the difference for each row on a shared zero-centred axis, with the tolerance shown as a grey band. Points outside the band are drawn as hollow orange rings with a text label, never by colour alone.
- **Status column:** a text label for each row (`within tolerance`, `outside`, `not reproduced`, `paper value unverified`), so status does not depend on colour.
- **Caption:** paper version and location, tolerance rule, run id and git SHA, number of targets in each status, and the list of documented deviations.
- **Publication:** values from restricted-data fits are not published by default. A public version would show only the status counts and aggregate deviation statistics, and only after an explicit decision.
