# Reproducibility guide

## Environment

Dependencies are declared once, in `pyproject.toml`:

- core: `numpy`, `scipy`, `pandas`, `jax`, `numpyro`;
- `data` extra: `requests`, `openpyxl`, `eurostat`, `pyreadstat` (public-data download and survey harmonisation);
- `stan` extra: `cmdstanpy` (needs a C++ toolchain; only for the Stan reference model);
- `dev` extra: `pytest`, `ruff`.

`requirements.lock` pins exact versions for the core, `data` and `dev` sets. It is a universal lock: one file for Linux, macOS and Windows, with version markers where the resolver picks different versions for Python 3.11 and for 3.12 and newer. CI installs it on Python 3.11 and 3.13.

Install exactly what CI tests:

    python -m pip install -r requirements.lock
    python -m pip install --no-deps -e .

The editable install makes the modules in `src/python/` importable (for example `import oosc_model_numpyro`). Use editable mode: modules locate the repository from their own source path.

To change a dependency, edit `pyproject.toml` and regenerate the lock with [uv](https://docs.astral.sh/uv/):

    uv pip compile pyproject.toml --extra data --extra dev --universal --python-version 3.11 --annotation-style line -o requirements.lock

Keep the two header lines at the top of the file, then run the tests on Python 3.11 and 3.13 before committing.

## Public synthetic run

    pytest -q
    python examples/synthetic_demo/run_demo.py

Neither command needs restricted or licensed data. The demo writes only under `examples/synthetic_demo/output/`.

## Determinism

With the same seed and sampler settings, `run_full_model.py` returns bit-identical draws whether it runs as one compiled run (`--checkpoint-every 0`) or in checkpointed chunks, including after an interrupted run is resumed. `tests/test_checkpointing.py` checks this on CPU with one chain. Behaviour on GPUs and with several chains run in parallel is unverified.

## Empirical runs

An empirical run needs authorised source data under the data root (`BCM_DATA_DIR`), a validated model input, a recorded configuration and random seed, enough warm-up and retained draws, convergence checks, and a documented comparison target.

Sampling finishing does not make a run final. `run_full_model.py` writes `run_info.json` with the settings and a convergence summary (max R-hat, min ESS, divergences); inspect it, and record exclusions, sensitivity choices and deviations from the published methodology.

## Release checklist

- No raw or restricted data, internal identifiers or credentials are committed.
- `requirements.lock` is current and CI passes on every supported Python version.
- Tests and the synthetic demo pass from a clean clone.
- Synthetic outputs are finite and bounded.
- MCMC diagnostics are archived for authorised runs.
- Claims in the README and `docs/status.md` match the evidence.
