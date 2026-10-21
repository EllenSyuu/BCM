# Performance and reliability

The execution path is designed for long-running Bayesian inference where compilation, memory pressure, and interruption are practical engineering constraints.

## Implemented optimisations

- Fixed model arrays are placed on the JAX device once before inference.
- Single-run mode avoids rebuilding sampler objects for every small checkpoint.
- JAX compilation caching can be enabled through runner configuration.
- Reporting rates are reconstructed in bounded chunks.
- Country-level post-processing limits peak memory.
- Durable manifests and posterior chunks make checkpointed runs resumable.

## What is preserved

These are execution and storage optimisations. They do not intentionally change the likelihood, prior structure, chain settings, retained draws, posterior quantiles, or convergence criteria.

## Benchmarking policy

Runtime claims must include hardware, software versions, chain settings, and whether compilation time is included. Short smoke tests demonstrate execution only; they are not evidence that a full empirical fit converges or completes within a particular time.

A benchmark record should include hardware, backend, chains, warmup and draws, compile time, sampling time, peak memory, R-hat, effective sample size, and divergences.