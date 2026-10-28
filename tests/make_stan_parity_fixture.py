"""Generate the Stan <-> NumPyro parity fixture used by the R package tests.

The fixture is a small, fully synthetic model input (random observations, no
real data) together with:

* the spline bases built by ``spline_basis.py``;
* two parameter points drawn from the priors;
* the NumPyro joint log density at each point.

The R package tests (``r/oosccohort/tests/testthat/test-parity.R``) rebuild the
bases in R and evaluate the Stan model's log density at the same two points.
Normalising constants differ between the two libraries (Stan's ``~`` drops
them), so the tests compare the *difference* in log density between the two
points, which must agree to numerical precision.

Usage:
    python tests/make_stan_parity_fixture.py            # rewrites the committed fixture
    python tests/make_stan_parity_fixture.py --out PATH
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src" / "python"))

import jax  # noqa: E402

jax.config.update("jax_enable_x64", True)  # float64, so the comparison is not limited by float32 rounding

from numpyro.infer.util import log_density  # noqa: E402
from scipy.stats import norm  # noqa: E402

from oosc_model_numpyro import ModelData, model  # noqa: E402
from spline_basis import build_model_bases, ey_index, mu_anchor_index  # noqa: E402

DEFAULT_OUT = REPO_ROOT / "r" / "oosccohort" / "tests" / "testthat" / "fixtures" / "numpyro_parity.json"
SEED = 20221122


def build_case(seed: int = SEED) -> dict:
    rng = np.random.default_rng(seed)
    C, R, A_max, N_SERIES, N_WAVE = 3, 2, 4, 2, 3
    bases = build_model_bases(min_year=2000, max_year=2022, max_age=A_max)
    grid = bases.ey_grid
    region_of_country = np.array([0, 0, 1])

    n_a, n_s = 40, 12
    a_country = rng.integers(0, C, n_a)
    a_year = rng.integers(2000, 2023, n_a)
    a_age = rng.integers(1, A_max + 1, n_a)                  # 1-indexed relative age
    a_obs = np.round(rng.uniform(-0.08, 0.6, n_a), 4)        # admin rates may be negative
    s_country = rng.integers(0, C, n_s)
    s_year = rng.integers(2000, 2023, n_s)
    s_age = rng.integers(1, A_max + 1, n_s)
    s_rate = np.round(rng.uniform(0.05, 0.7, n_s), 4)
    k_obs = norm.ppf(s_rate)

    data = ModelData(
        C=C, R=R, A_max=A_max, N_EY=len(grid), mu_anchor_idx=mu_anchor_index(grid),
        B1=bases.B1, B5=bases.B5, region_of_country=region_of_country,
        A_obs=a_obs, A_country=a_country, A_region=region_of_country[a_country],
        A_age=a_age - 1, A_ey_idx=ey_index(a_year, a_age, grid) - 1,
        K_obs=k_obs, f_obs=norm.pdf(k_obs), nu=np.round(rng.uniform(0.01, 0.05, n_s), 4),
        S_country=s_country, S_age=s_age - 1, S_ey_idx=ey_index(s_year, s_age, grid) - 1,
        S_series=rng.integers(0, N_SERIES, n_s), S_wave=rng.integers(0, N_WAVE, n_s),
        N_SERIES=N_SERIES, N_WAVE=N_WAVE,
    )
    K1, K5 = bases.B1.shape[1], bases.B5.shape[1]

    def draw_point() -> dict:
        half = lambda scale, *shape: np.abs(rng.normal(0.0, scale, shape))  # noqa: E731
        return {
            "sigma_gamma_r": half(0.02, R),
            "gamma_z": half(1.0, C),
            "sigma_mu": float(abs(rng.normal(0, 0.1))) + 0.01,
            "mu_star_2000": rng.normal(-1.0, 0.5, C),
            "mu_eps_z": rng.normal(0, 1, (C, K1 - 1)),
            "tau_alpha1": float(abs(rng.normal(0, 1))) + 0.2,
            "tau_alpha2": float(abs(rng.normal(0, 1))) + 0.2,
            "alpha": rng.normal(0, 0.1, (C, A_max - 1, K5)),
            "sigma_beta": half(0.1, N_SERIES),
            "beta_z": rng.normal(0, 1, (C, N_SERIES)),
            "sigma_sigma": float(abs(rng.normal(0, 0.01))) + 0.01,
            "sigma_adm_z": float(abs(rng.normal(0, 1))) + 0.1,
            "omega_r_z": half(1.0, R) + 0.1,
            "eta_w_z": half(1.0, N_WAVE) + 0.1,
        }

    points = [draw_point(), draw_point()]
    log_densities = [float(log_density(model, (data,), {}, p)[0]) for p in points]

    # Everything is written with 1-based indices, as the Stan model expects.
    stan_data = {
        "C": C, "R": R, "A_max": A_max, "N_EY": int(len(grid)), "N_K1": int(K1),
        "MU_ANCHOR": int(data.mu_anchor_idx) + 1, "N_K5": int(K5),
        "N_SERIES": N_SERIES, "N_WAVE": N_WAVE,
        "B1": bases.B1.tolist(), "B5": bases.B5.tolist(),
        "region_of_country": (region_of_country + 1).tolist(),
        "N_A": n_a, "A_obs": a_obs.tolist(), "A_country": (a_country + 1).tolist(),
        "A_region": (data.A_region + 1).tolist(), "A_age": a_age.tolist(),
        "A_ey_idx": (data.A_ey_idx + 1).tolist(),
        "N_S": n_s, "K_obs": k_obs.tolist(), "f_obs": data.f_obs.tolist(), "nu": data.nu.tolist(),
        "S_country": (s_country + 1).tolist(), "S_age": s_age.tolist(),
        "S_ey_idx": (data.S_ey_idx + 1).tolist(),
        "S_series": (data.S_series + 1).tolist(), "S_wave": (data.S_wave + 1).tolist(),
    }
    return {
        "description": "Synthetic Stan/NumPyro parity case generated by tests/make_stan_parity_fixture.py. "
                       "Random values only; no real data.",
        "seed": seed,
        "ey_grid": grid.tolist(),
        "observations": {"A_year": a_year.tolist(), "S_year": s_year.tolist()},
        "stan_data": stan_data,
        "points": [{k: np.asarray(v).tolist() for k, v in p.items()} for p in points],
        "numpyro_log_density": log_densities,
    }


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(build_case(), indent=None, separators=(",", ":")) + "\n")
    print(f"Wrote {args.out}")
    return args.out


if __name__ == "__main__":
    main()
