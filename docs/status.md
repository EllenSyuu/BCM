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

Nothing below has been compared with the published results. "Verified" means verified against the stated check, not against the paper.

## Engineering capabilities

| Area | Status | Evidence |
|---|---|---|
| Synthetic end-to-end run (simulate → `run_full_model.py` with checkpoints → estimates) | **verified** on synthetic data | `tests/test_synthetic_demo.py`; CI also runs the README demo |
| Checkpointed sampling, resume after interruption, single compiled run | **verified** on synthetic data, CPU, one chain | `tests/test_checkpointing.py`: chunked, resumed and single-run draws are bit-identical for the same seed |
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

Section, equation, table and figure numbers come from comments in the code and still need to be checked against the paper.

| Target | Paper location | Status | Code | Gap |
|---|---|---|---|---|
| Population denominators (WPP, Eurostat, SingStat) | App. A.1 | implemented, unverified | `fetch_public_data.py`, `build_population.py` | Uses the WPP 2024 revision; the paper's vintage differs |
| Administrative observations and exclusion rules | Sec. 2.1, App. A.2.1 | partial | private adapter; `harmonize_admin_data.py` | Step 3 not applied; two different implementations |
| Survey observations (DHS, MICS, IPUMS) | Table 1, App. A.2.2 | implemented, unverified | `harmonize_dhs.py`, `harmonize_mics.py`, `harmonize_ipums_census.py` | Cells with rate exactly 0 or 1 are dropped; to be checked against the paper |
| "Other" surveys (WIDE) | App. A.1 | partial | `harmonize_wide.py`, `reweight_wide.py` | Only education-level aggregates are available; handled by an approximate importance reweighting (documented deviation) |
| Model equations and priors | Sec. 3, App. B | implemented, unverified | `oosc_model_numpyro.py`, `oosc_cohort_model.stan` | Equation-by-equation check against the paper not done |
| MCMC settings | Sec. 3.4 | implemented, unverified | `run_full_model.py` defaults | Settings match the code's reading of the paper; no full run recorded |
| Country × year × single-age estimates with 90% intervals | Fig. 5 | implemented, unverified on real data | `run_full_model.py` → `estimates.csv` | Verified on synthetic data only |
| Separate fits by sex (M, F, MF) | Sec. 3.4 | implemented, unverified | `assemble_model_input.py --sex` | — |
| Education-level out-of-school rates (the SDG 4.1.4 indicator) | Results | not started | — | Aggregation from single ages to education levels |
| Out-of-school populations; regional and global aggregates | Results | not started | — | — |
| Hold-out validation | Sec. 3.5, Table 2, Sec. 4.4 | implemented, unverified | `holdout_validation.py` | Global parameters estimated on all data (documented leakage) |
| Comparison with officially published estimates | — | not started | — | — |
| Paper citation and version | — | blocked | `CITATION.cff` | Which paper version the code follows is not confirmed |
