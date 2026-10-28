"""The committed Stan/NumPyro parity fixture must match the current NumPyro model.

If this test fails after a change to oosc_model_numpyro.py or spline_basis.py,
regenerate the fixture with `python tests/make_stan_parity_fixture.py`; the R
package test then checks the Stan model against the new values.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "tests" / "make_stan_parity_fixture.py"
COMMITTED = REPO_ROOT / "r" / "oosccohort" / "tests" / "testthat" / "fixtures" / "numpyro_parity.json"


def test_committed_fixture_matches_current_model(tmp_path):
    # run in a subprocess: the generator switches JAX to float64, which must not leak into other tests
    out = tmp_path / "fixture.json"
    subprocess.run([sys.executable, str(GENERATOR), "--out", str(out)], check=True, capture_output=True)
    committed = json.loads(COMMITTED.read_text())
    fresh = json.loads(out.read_text())

    assert committed["seed"] == fresh["seed"]
    assert committed["ey_grid"] == fresh["ey_grid"]
    for key in ("B1", "B5"):
        np.testing.assert_allclose(committed["stan_data"][key], fresh["stan_data"][key], atol=1e-12)
    for key, value in fresh["stan_data"].items():
        if key not in ("B1", "B5"):
            np.testing.assert_allclose(committed["stan_data"][key], value, atol=1e-12, err_msg=key)
    np.testing.assert_allclose(committed["numpyro_log_density"], fresh["numpyro_log_density"], rtol=1e-10)
    assert "no real data" in committed["description"]
