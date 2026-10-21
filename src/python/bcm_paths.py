"""Single source of truth for where the pipeline reads and writes local data.

Every script resolves its inputs and outputs from one data root:

* ``BCM_DATA_DIR`` (environment variable), when set. Use this to keep licensed or
  restricted inputs in a private location outside the repository.
* otherwise ``<repository>/data``, which is listed in ``.gitignore``.

The root never depends on the current working directory or on how far a script
sits from the repository root. Paths below the root keep the local layout the
pipeline has always used (``A.1. Raw Sources`` and ``A.2. Processed``).
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"
DATA_DIR_ENV = "BCM_DATA_DIR"


def data_root() -> Path:
    """Return the absolute data root, honouring ``BCM_DATA_DIR`` when set."""
    configured = os.environ.get(DATA_DIR_ENV, "").strip()
    if not configured:
        return DEFAULT_DATA_DIR
    root = Path(configured).expanduser()
    if not root.is_absolute():
        raise ValueError(
            f"{DATA_DIR_ENV} must be an absolute path (got {configured!r}); "
            "relative paths would depend on the current working directory."
        )
    return root.resolve()


def raw_dir() -> Path:
    """Local raw inputs (downloaded public files and authorised local copies)."""
    return data_root() / "A.1. Raw Sources"


def processed_dir() -> Path:
    """Harmonised observations, model inputs and model outputs."""
    return data_root() / "A.2. Processed"


def cache_dir() -> Path:
    """Repository-local cache (for example the JAX compilation cache); git-ignored."""
    return REPO_ROOT / ".cache"
