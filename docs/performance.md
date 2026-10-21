# Performance and reliability

The execution path is designed for long-running Bayesian inference where compilation, memory pressure, and interruption are practical engineering constraints.

## Implemented optimisations

- Fixed model arrays are placed on the JAX device once before inference.
- Single-run mode avoids rebuilding sampler objects for every small checkpoint.
- `run_full_model.py` enables the JAX compilation cache by default (in the git-ignored `.cache/jax/`).
- Reporting rates are reconstructed in bounded chunks.
- Country-level post-processing limits peak memory.
- Durable manifests and posterior chunks make checkpointed runs resumable.

## What is preserved

These are execution and storage optimisations; they do not change the likelihood, the priors, the chain settings or the convergence criteria. With the same seed and settings, the single compiled run (`--checkpoint-every 0`), the checkpointed run and a resumed run return bit-identical draws. `tests/test_checkpointing.py` checks this on CPU with one chain; GPUs and parallel multi-chain runs are unverified.

## Benchmarking policy

Runtime claims must include hardware, software versions, chain settings, and whether compilation time is included. Short smoke tests demonstrate execution only; they are not evidence that a full empirical fit converges or completes within a particular time.

A benchmark record should include hardware, backend, chains, warmup and draws, compile time, sampling time, peak memory, R-hat, effective sample size, and divergences.