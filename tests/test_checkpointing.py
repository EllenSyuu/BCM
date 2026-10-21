"""Checkpointed MCMC: chunked sampling, resume after interruption, and agreement
with the single compiled run (regression tests for the UnboundLocalError that
broke every run with checkpoint_every > 0)."""
from __future__ import annotations

import json
import shutil

import numpy as np
import pytest

import oosc_model_numpyro as m

SETTINGS = dict(num_warmup=40, num_samples=20, num_chains=1, seed=3, thinning=2, progress_bar=False)


@pytest.fixture(scope="module")
def data():
    return m._build_synthetic_data(seed=0)


@pytest.fixture(scope="module")
def chunked(data, tmp_path_factory):
    directory = tmp_path_factory.mktemp("chunked")
    samples, extras = m.run_mcmc_checkpointed(data, checkpoint_dir=directory, checkpoint_every=10, **SETTINGS)
    return directory, samples, extras


@pytest.fixture(scope="module")
def single(data, tmp_path_factory):
    directory = tmp_path_factory.mktemp("single")
    samples, extras = m.run_mcmc_checkpointed(data, checkpoint_dir=directory, checkpoint_every=0, **SETTINGS)
    return directory, samples, extras


def _assert_same_draws(left: dict, right: dict) -> None:
    assert set(left) == set(right)
    for name in left:
        np.testing.assert_array_equal(left[name], right[name], err_msg=name)


def test_chunked_sampling_completes_with_expected_shapes_and_files(chunked):
    directory, samples, extras = chunked
    retained = SETTINGS["num_samples"] // SETTINGS["thinning"]
    assert samples["sigma_sigma"].shape == (SETTINGS["num_chains"], retained)
    assert samples["alpha"].shape[:2] == (SETTINGS["num_chains"], retained)
    assert extras["diverging"].shape == (SETTINGS["num_chains"], retained)
    assert all(np.isfinite(v).all() for v in samples.values())

    manifest = json.loads((directory / "checkpoint.json").read_text())
    assert manifest["status"] == "sampling_complete"
    assert manifest["completed_steps"] == SETTINGS["num_samples"]
    assert manifest["chunk_ends"] == [10, 20]
    for name in ("samples_000010.npz", "samples_000020.npz", "state_000010.pkl", "posterior_draws.npz"):
        assert (directory / name).is_file(), name


def test_resume_after_interruption_reproduces_uninterrupted_draws(data, chunked, tmp_path):
    directory, samples, extras = chunked
    interrupted = tmp_path / "interrupted"
    shutil.copytree(directory, interrupted)
    # simulate a crash after the first checkpoint: the second chunk was never written
    for name in ("samples_000020.npz", "state_000020.pkl", "posterior_draws.npz"):
        (interrupted / name).unlink()
    manifest = json.loads((interrupted / "checkpoint.json").read_text())
    manifest.update(completed_steps=10, chunk_ends=[10], status="sampling")
    (interrupted / "checkpoint.json").write_text(json.dumps(manifest))

    resumed, resumed_extras = m.run_mcmc_checkpointed(
        data, checkpoint_dir=interrupted, checkpoint_every=10, **SETTINGS
    )

    _assert_same_draws(samples, resumed)
    _assert_same_draws(extras, resumed_extras)
    resumed_manifest = json.loads((interrupted / "checkpoint.json").read_text())
    assert resumed_manifest["status"] == "sampling_complete"
    assert resumed_manifest["completed_steps"] == SETTINGS["num_samples"]
    assert resumed_manifest["chunk_ends"] == [10, 20]
    with np.load(interrupted / "posterior_draws.npz") as saved:
        np.testing.assert_array_equal(saved["sample__sigma_sigma"], samples["sigma_sigma"])


def test_completed_checkpoint_is_reloaded_without_resampling(data, chunked):
    directory, samples, _ = chunked
    reloaded, _ = m.run_mcmc_checkpointed(data, checkpoint_dir=directory, checkpoint_every=10, **SETTINGS)
    _assert_same_draws(samples, reloaded)


def test_single_compiled_run_matches_checkpointed_run(chunked, single):
    """With the same seed and settings both execution modes return identical draws."""
    _, chunked_samples, chunked_extras = chunked
    directory, single_samples, single_extras = single
    _assert_same_draws(chunked_samples, single_samples)
    _assert_same_draws(chunked_extras, single_extras)
    manifest = json.loads((directory / "checkpoint.json").read_text())
    assert manifest["status"] == "sampling_complete"
    assert manifest["execution_mode"] == "single_compiled_run"


def test_changed_settings_refuse_to_resume(data, chunked):
    directory, _, _ = chunked
    with pytest.raises(ValueError, match="do not match"):
        m.run_mcmc_checkpointed(data, checkpoint_dir=directory, checkpoint_every=10, **(SETTINGS | {"seed": 4}))


@pytest.mark.parametrize("checkpoint_every", [-1, 3])
def test_invalid_checkpoint_interval_is_rejected(data, tmp_path, checkpoint_every):
    with pytest.raises(ValueError, match="multiple of thinning"):
        m.run_mcmc_checkpointed(data, checkpoint_dir=tmp_path, checkpoint_every=checkpoint_every, **SETTINGS)
