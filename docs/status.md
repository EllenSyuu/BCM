# Public project status

**Release:** public engineering preview  
**Scope:** SDG 4.1.4 out-of-school-rate cohort model

## Capability matrix

| Area | Status | Evidence |
|---|---|---|
| Repository structure | Ready | Public package, tests, examples, and documentation |
| Model translation | Implemented | NumPyro implementation plus Stan reference |
| Synthetic execution | Tested | Automated smoke and constraint checks |
| Public-data preparation | Implemented in modules | Source-specific coverage varies |
| MCMC reliability | Implemented | Checkpoints, manifests, progress, diagnostics |
| Performance path | Implemented | Cached inputs, single-compile mode, chunked reporting |
| Full empirical fit | Restricted-input dependent | Required administrative input is not distributable |
| Final paper comparison | Not claimed | Requires complete authorised inputs and validation |

## What “done” means here

- **Implemented:** code exists and has a defined interface.
- **Tested:** an automated or controlled check passed.
- **Validated:** output was compared against a stated reference.
- **Complete reproduction:** all required inputs, diagnostics, validation targets, and deviations are documented.

The project intentionally does not call itself a complete empirical reproduction until the last condition is met.