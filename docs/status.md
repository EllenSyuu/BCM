# Project status

**Overall:** work in progress. This is **not** a completed reproduction.

Status labels used below:

| Label | Meaning |
|---|---|
| **verified** | An automated test in this repository checks it, and CI runs that test. The scope of the check is stated. |
| **implemented, unverified** | Code exists, but no test or recorded comparison in this repository shows it is correct. |
| **partial** | Only part of the target is implemented. |
| **not started** | No code exists. |
| **blocked** | Cannot proceed without a missing input. |

No reproduced number has been compared with the published results yet. "Verified" means verified against the stated check, not against the paper. The specification itself has been checked against the paper by hand; see [paper-audit.md](paper-audit.md).

## Engineering capabilities

| Area | Status | Evidence |
|---|---|---|
| Synthetic end-to-end run (simulate → `run_full_model.py` with checkpoints → estimates) | **verified** on synthetic data | `tests/test_synthetic_demo.py`; CI also runs the README demo |
| Checkpointed sampling, resume after interruption, single compiled run | **verified** on synthetic data, CPU, one chain | `tests/test_checkpointing.py`: chunked, resumed and single-run draws are bit-identical for the same seed |
| Synthetic recovery figure (`plot_recovery.py`) | **verified** on synthetic data | `tests/test_synthetic_demo.py` checks the SVG and its reported coverage |
| Data-root configuration (`BCM_DATA_DIR`) | **verified** | `tests/test_paths.py` |
| Spline bases and entry-year indexing | **verified** (unit level) | `tests/test_public_synthetic.py` |
| NumPyro model has a finite joint density on synthetic inputs | **verified** (unit level) | `tests/test_public_synthetic.py` |
| Administrative-only loader maps observations to the right entry cohort | **verified** (unit level) | `tests/test_admin_only.py` |
| Stan reference model | implemented, unverified | No automated comparison with the NumPyro model |
| Public-data acquisition and survey harmonisers (DHS, MICS, IPUMS, WIDE) | implemented, unverified | No tests; real inputs are licensed and not in the repository |
| Administrative exclusion rules (Appendix A.2.1) | partial | `harmonize_admin_data.py` has an internal self-check but is not called by the pipeline; real-data runs use a private adapter whose rules differ |
| Hold-out validation, country refits, WIDE reweighting | implemented, unverified | Each module carries its own copy of the country-level model |
| Full empirical fit | unverified | No run outputs or diagnostics are recorded in this repository |
| Installation | modules importable after `pip install --no-deps -e .` | CI import check; this is a set of flat modules, not yet a structured package |

## Reproduction matrix

Locations refer to the 2022 TCG version of the paper (WG/HHS/2). "Audited" means the code was checked against the paper's text by hand ([paper-audit.md](paper-audit.md)); it does not mean the numbers agree.

| Target | Paper location | Status | Code | Gap |
|---|---|---|---|---|
| Population denominators (WPP, Eurostat, SingStat) | App. A.1 | implemented, unverified | `fetch_public_data.py`, `build_population.py` | Uses the WPP 2024 revision; the paper uses WPP 2019 (audit D5) |
| Administrative observations and exclusion rules | Sec. 2.1, App. A.2.1 | partial | private adapter; `harmonize_admin_data.py` | Step 3 not applied; two different implementations |
| Survey observations (DHS, MICS, IPUMS) | Table 1, App. A.2.2 | implemented, unverified | `harmonize_dhs.py`, `harmonize_mics.py`, `harmonize_ipums_census.py` | Cells with rate exactly 0 or 1 are dropped; to be checked against the paper |
| "Other" surveys (WIDE) | App. A.1 | partial | `harmonize_wide.py`, `reweight_wide.py` | Only education-level aggregates are available; handled by an approximate importance reweighting (documented deviation) |
| Model equations and priors | Sec. 3, App. B | implemented, **audited: matches the paper** | `oosc_model_numpyro.py`, `oosc_cohort_model.stan` | All 18 specification items match (audit §1); 8 open points are recorded as interpretations (audit §6); no numerical comparison yet |
| MCMC settings | Sec. 3.4, App. C | implemented, **audited: matches the paper** | `run_full_model.py` defaults | Chains, iterations and thinning match; NumPyro instead of Stan; target acceptance rate not stated in the paper; no full run recorded |
| Country × year × single-age estimates with 90% intervals | Fig. 5 | implemented, unverified on real data | `run_full_model.py` → `estimates.csv` | Verified on synthetic data only |
| Separate fits by sex (M, F, MF) | Sec. 3.4 | implemented, unverified | `assemble_model_input.py --sex` | — |
| Education-level out-of-school rates (the SDG 4.1.4 indicator) | Sec. 1, 3 | not started | — | The paper does not specify the aggregation method; a proposal is in audit I8 |
| Out-of-school populations; regional and global aggregates | Sec. 4.2, Fig. 7 | not started | — | Rates × population, summed to countries and SDG regions (audit O2) |
| Hold-out validation | Sec. 3.5, Table 2, Sec. 4.4 | implemented, unverified | `holdout_validation.py` | Global parameters estimated on all data instead of a refit (audit V1); MuRW and MuK5 variants missing (V5) |
| Sensitivity analysis | Sec. 4.5, Table 3 | not started | — | τ prior scales and knot spacings (audit V6) |
| Comparison with officially published estimates | — | not started | — | — |
| Paper citation and version | — | resolved | `CITATION.cff` | The code follows the 2022 TCG version (WG/HHS/2); the 2023 SocArXiv version is listed but not audited |
