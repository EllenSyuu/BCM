"""End-to-end synthetic demonstration of the Bayesian cohort model pipeline.

What it does
------------
1. Simulates a small panel (4 countries, 2 regions, 8 single ages, 2000-2022)
   from a known "true" out-of-school surface, with administrative observations
   in real space and biased, noisy survey observations in probit space.
2. Writes the model input in exactly the format produced by
   ``assemble_model_input.py`` (``model_input_SYNTH.npz`` + index JSON).
3. Runs the real fitting entry point, ``src/python/run_full_model.py``, with
   durable checkpoints (``--checkpoint-every 80`` by default).
4. Compares the posterior estimates with the known truth, writes a short
   report and draws the recovery figure (``synthetic_recovery.svg``).

No restricted, licensed or real data is read or produced. Every file is written
under ``--output-dir`` (default ``examples/synthetic_demo/output/``, git-ignored),
which is passed to the pipeline as ``BCM_DATA_DIR``.

Usage
-----
    python examples/synthetic_demo/run_demo.py            # about 1-2 minutes on a laptop CPU
    python examples/synthetic_demo/run_demo.py --quick    # smaller run used by the tests
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = REPO_ROOT / "src" / "python"
sys.path.insert(0, str(PYTHON_DIR))

from spline_basis import build_model_bases, ey_index, mu_anchor_index  # noqa: E402

TAG = "SYNTH"
YEARS = np.arange(2000, 2023)
A_MAX = 8                      # relative ages 1..8 (entry age .. entry age + 7)
ENTRY_AGE = 6
COUNTRIES = ["SYA", "SYB", "SYC", "SYD"]   # synthetic codes, not real ISO3 countries
REGIONS = ["Region 1", "Region 2"]
REGION_OF = {"SYA": 0, "SYB": 0, "SYC": 1, "SYD": 1}
SERIES = ["Survey A", "Survey B"]
WAVES = ["Wave 1", "Wave 2"]

FULL = {"warmup": 300, "samples": 160, "chains": 2, "thinning": 1, "checkpoint_every": 80}
QUICK = {"warmup": 80, "samples": 80, "chains": 1, "thinning": 1, "checkpoint_every": 40}


def true_probit(country: int, year: np.ndarray, age_rel: np.ndarray) -> np.ndarray:
    """Known probit-scale out-of-school surface used to simulate the data.

    Linear in entry cohort and age with a country-specific level and decline,
    so it lies inside the class of surfaces the model can represent.
    """
    level = np.array([-1.1, -0.6, -0.3, -1.4])[country]
    decline = np.array([0.030, 0.020, 0.035, 0.015])[country]
    entry_year = year - age_rel + 1
    return level - decline * (entry_year - 2000) + 0.06 * (age_rel - 1)


def simulate(seed: int) -> tuple[dict, dict, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    bases = build_model_bases(min_year=int(YEARS.min()), max_year=int(YEARS.max()), max_age=A_MAX)

    admin, survey = [], []
    for c, iso in enumerate(COUNTRIES):
        # country SYD has administrative data only every third year, to show interpolation
        admin_years = YEARS if iso != "SYD" else YEARS[::3]
        for y in admin_years:
            for a in range(1, A_MAX + 1):
                p = norm.cdf(true_probit(c, np.array(y), np.array(a)))
                admin.append((c, int(y), a, float(p + rng.normal(0, 0.02))))
        bias = rng.normal(0, 0.08, size=len(SERIES))
        for j in range(8):
            y, a = int(rng.choice(YEARS)), int(rng.integers(1, A_MAX + 1))
            s, w = j % len(SERIES), (j // 4) % len(WAVES)
            kappa = float(true_probit(c, np.array(y), np.array(a)))
            k_obs = kappa + bias[s] + rng.normal(0, 0.05)
            p_obs = float(norm.cdf(k_obs))
            se_real = 0.02
            survey.append((c, y, a, s, w, k_obs, float(norm.pdf(k_obs)), se_real, p_obs))

    adm = np.array(admin, dtype=float)
    sur = np.array(survey, dtype=float)
    a_ey = ey_index(adm[:, 1].astype(int), adm[:, 2].astype(int), bases.ey_grid) - 1
    s_ey = ey_index(sur[:, 1].astype(int), sur[:, 2].astype(int), bases.ey_grid) - 1
    arrays = dict(
        C=len(COUNTRIES), R=len(REGIONS), A_max=A_MAX, N_EY=len(bases.ey_grid),
        mu_anchor_idx=mu_anchor_index(bases.ey_grid),
        B1=bases.B1, B5=bases.B5,
        region_of_country=np.array([REGION_OF[c] for c in COUNTRIES]),
        A_obs=adm[:, 3], A_country=adm[:, 0].astype(int),
        A_region=np.array([REGION_OF[COUNTRIES[int(c)]] for c in adm[:, 0]]),
        A_age=adm[:, 2].astype(int) - 1, A_ey_idx=a_ey,
        K_obs=sur[:, 5], f_obs=sur[:, 6], nu=sur[:, 7],
        S_country=sur[:, 0].astype(int), S_age=sur[:, 2].astype(int) - 1, S_ey_idx=s_ey,
        S_series=sur[:, 3].astype(int), S_wave=sur[:, 4].astype(int),
        N_SERIES=len(SERIES), N_WAVE=len(WAVES),
    )
    index = {
        "sex": "MF", "countries": COUNTRIES, "regions": REGIONS, "series": SERIES, "waves": WAVES,
        "ey_grid": bases.ey_grid.tolist(), "A_max": A_MAX,
        "mu_anchor_year": 2000, "mu_anchor_idx": int(arrays["mu_anchor_idx"]),
        "reproduction_scope": "synthetic demonstration (simulated data; not an empirical estimate)",
        "min_entry": [ENTRY_AGE] * len(COUNTRIES), "dropped_no_region": [],
    }
    truth = pd.DataFrame(
        [(iso, int(y), a, float(norm.cdf(true_probit(c, np.array(y), np.array(a)))))
         for c, iso in enumerate(COUNTRIES) for y in YEARS for a in range(1, A_MAX + 1)],
        columns=["iso3", "year", "age_rel", "true_rate"],
    )
    return arrays, index, truth


def write_inputs(output_dir: Path, seed: int) -> pd.DataFrame:
    arrays, index, truth = simulate(seed)
    in_dir = output_dir / "A.2. Processed" / "model_input"
    in_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(in_dir / f"model_input_{TAG}.npz", **arrays)
    (in_dir / f"model_index_{TAG}.json").write_text(json.dumps(index, indent=1))
    truth.to_csv(output_dir / "synthetic_truth.csv", index=False)
    return truth


def run_model(output_dir: Path, settings: dict, seed: int) -> float:
    cmd = [
        sys.executable, str(PYTHON_DIR / "run_full_model.py"), "--tag", TAG,
        "--warmup", str(settings["warmup"]), "--samples", str(settings["samples"]),
        "--chains", str(settings["chains"]), "--thinning", str(settings["thinning"]),
        "--checkpoint-every", str(settings["checkpoint_every"]), "--seed", str(seed),
    ]
    env = os.environ | {"BCM_DATA_DIR": str(output_dir.resolve())}
    started = time.time()
    subprocess.run(cmd, check=True, env=env)
    return time.time() - started


def summarise(output_dir: Path, truth: pd.DataFrame, runtime_s: float, settings: dict) -> dict:
    out = output_dir / "A.2. Processed" / "model_output" / TAG
    est = pd.read_csv(out / "estimates.csv")
    run_info = json.loads((out / "run_info.json").read_text())
    merged = est.merge(truth, on=["iso3", "year", "age_rel"], how="inner", validate="one_to_one")
    covered = (merged["oos_q05"] <= merged["true_rate"]) & (merged["true_rate"] <= merged["oos_q95"])
    abs_err = (merged["oos_median"] - merged["true_rate"]).abs()
    per_country = (
        merged.assign(covered=covered, abs_err_pp=100 * abs_err)
        .groupby("iso3")
        .agg(cells=("covered", "size"), coverage_90=("covered", "mean"), mae_pp=("abs_err_pp", "mean"))
        .round(3)
    )
    summary = {
        "settings": settings,
        "runtime_seconds": round(runtime_s, 1),
        "estimated_cells": int(len(merged)),
        "coverage_of_true_rate_by_90pct_interval": round(float(covered.mean()), 3),
        "mean_absolute_error_percentage_points": round(float(100 * abs_err.mean()), 2),
        "rates_within_0_1": bool(est[["oos_median", "oos_q05", "oos_q95"]].stack().between(0, 1).all()),
        "diagnostics": run_info["diagnostics"],
        "per_country": per_country.reset_index().to_dict(orient="records"),
    }
    (output_dir / "demo_summary.json").write_text(json.dumps(summary, indent=1))

    lines = [
        "# Synthetic demo report",
        "",
        "Simulated data from a known out-of-school surface; this is not an empirical estimate.",
        "",
        f"- Settings: {settings}",
        f"- Runtime (including JAX compilation): {summary['runtime_seconds']} s",
        f"- Country x year x age cells estimated: {summary['estimated_cells']}",
        f"- Share of true rates inside the 90% posterior interval: "
        f"{summary['coverage_of_true_rate_by_90pct_interval']:.1%}",
        f"- Mean absolute error of the posterior median: "
        f"{summary['mean_absolute_error_percentage_points']} percentage points",
        f"- All reported rates within [0, 1]: {summary['rates_within_0_1']}",
        f"- Max R-hat: {run_info['diagnostics']['max_r_hat']:.3f}, "
        f"min ESS: {run_info['diagnostics']['min_n_eff']:.0f}, "
        f"divergences: {run_info['diagnostics']['divergences']}, "
        f"convergence thresholds met: {run_info['diagnostics']['convergence_passed']}",
        "",
        "Per country:",
        "",
        per_country.to_markdown() if _has_tabulate() else per_country.to_string(),
        "",
        "Short runs are for demonstration only; the convergence thresholds used for real fits",
        "(R-hat <= 1.01, ESS >= 400, no divergences) are not expected to be met here.",
    ]
    (output_dir / "demo_report.md").write_text("\n".join(lines) + "\n")
    return summary


def _has_tabulate() -> bool:
    try:
        import tabulate  # noqa: F401
    except ImportError:
        return False
    return True


def main(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--output-dir", type=Path, default=REPO_ROOT / "examples" / "synthetic_demo" / "output")
    ap.add_argument("--seed", type=int, default=2022)
    ap.add_argument("--quick", action="store_true", help="smaller sampler settings (used by the test suite)")
    args = ap.parse_args(argv)

    settings = dict(QUICK if args.quick else FULL, seed=args.seed)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoints = output_dir / "A.2. Processed" / "model_output" / TAG / "checkpoints"
    if checkpoints.exists():
        # a fresh demo should not resume a previous run with different settings
        import shutil
        shutil.rmtree(checkpoints)

    truth = write_inputs(output_dir, args.seed)
    runtime = run_model(output_dir, settings, args.seed)
    summary = summarise(output_dir, truth, runtime, settings)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from plot_recovery import plot_recovery  # noqa: E402

    figure = plot_recovery(output_dir)
    print((output_dir / "demo_report.md").read_text())
    print(f"Recovery figure: {figure}")
    print(f"Outputs written under: {output_dir}")
    return summary


if __name__ == "__main__":
    main()
