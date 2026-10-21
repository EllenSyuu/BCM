"""Make the pipeline modules importable without installing the project."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for source_dir in (REPO_ROOT / "src" / "python", REPO_ROOT / "src" / "admin"):
    if str(source_dir) not in sys.path:
        sys.path.insert(0, str(source_dir))
