# Reproducibility guide

## Public synthetic run

Install the base environment, install the package in editable mode, run tests, then run the synthetic example:

    python -m pip install -r requirements/base.txt
    python -m pip install -e .
    pytest -q
    python examples/synthetic_demo/run_demo.py

The synthetic example does not require restricted data.

## Empirical runs

An empirical run requires authorised source data, a validated model-input contract, a recorded configuration and random seed, sufficient warmup and retained draws, convergence checks, and a documented comparison target.

Do not treat a run as final because sampling completed. Inspect diagnostics and record exclusions, sensitivity choices, and deviations from the published methodology.

## Release checklist

- No raw or restricted data is committed.
- No credentials or internal correspondence is committed.
- The exact environment is recorded.
- Tests pass from a clean checkout.
- Synthetic outputs are finite and bounded.
- MCMC diagnostics are archived for authorised runs.
- Public claims match the status documentation.