# Security and data-handling policy

## Scope

This repository contains code, documentation, tests and synthetic examples only. It must never contain restricted or licensed data, outputs computed from such data, credentials, or internal identifiers of any organisation. See [PUBLICATION_NOTES.md](PUBLICATION_NOTES.md) for the data and publication boundary and [docs/data-sources.md](docs/data-sources.md) for how local inputs are configured.

## Reporting a problem

If you find a security vulnerability, or content that looks like it should not be public (for example data rows, credentials, internal paths or names), please do not copy the content into a public issue. Open an issue that only names the file and commit, or contact the maintainer through their GitHub profile, and it will be handled privately.

## Contributor checklist

- Keep inputs under `BCM_DATA_DIR` or the git-ignored `data/` directory; never add data files to Git.
- Do not commit notebooks with outputs, logs, model outputs, PDFs or office documents.
- Run the test suite on synthetic data only.
