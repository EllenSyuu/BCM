"""Administrative-only loader: observations must map to the correct entry cohort."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from admin_only_model import load_admin_input

ENTRY_AGE = 6


def _write_panel(tmp_path, years, ages):
    rows = [("AAA", y, a, 0.1) for y in years for a in ages]
    path = tmp_path / "admin.csv"
    pd.DataFrame(rows, columns=["country", "year", "age", "oosc_rate"]).to_csv(path, index=False)
    return path


def _load(path):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # single temporary region
        return load_admin_input(path, entry_age=ENTRY_AGE)


def test_full_2000_2022_panel_loads(tmp_path):
    data = _load(_write_panel(tmp_path, range(2000, 2023), range(6, 18)))
    assert data.A_max == 12
    assert data.A_ey_idx.min() == 0
    assert data.A_ey_idx.max() == data.N_EY - 1


@pytest.mark.parametrize("age", [6, 9, 17])
def test_observation_maps_to_its_entry_cohort(tmp_path, age):
    ages = list(range(6, 18))
    data = _load(_write_panel(tmp_path, [2010], ages))
    ey_grid = np.arange(2000 - data.A_max + 1, 2023)
    assert len(ey_grid) == data.N_EY
    row = ages.index(age)  # one observation per age, in input order
    assert data.A_age[row] == age - ENTRY_AGE
    # the cohort that entered school at ENTRY_AGE and is `age` years old in 2010
    assert ey_grid[data.A_ey_idx[row]] == 2010 - (age - ENTRY_AGE)
