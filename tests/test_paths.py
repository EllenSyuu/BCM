"""Data-root resolution: one configurable root, never implicitly outside the repository."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

import bcm_paths

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"


def test_repo_root_is_detected():
    assert bcm_paths.REPO_ROOT == REPO_ROOT
    assert (bcm_paths.REPO_ROOT / "pyproject.toml").is_file()


def test_default_root_is_inside_the_repository(monkeypatch):
    monkeypatch.delenv("BCM_DATA_DIR", raising=False)
    root = bcm_paths.data_root()
    assert root == REPO_ROOT / "data"
    assert root.is_relative_to(REPO_ROOT)
    assert bcm_paths.raw_dir().is_relative_to(root)
    assert bcm_paths.processed_dir().is_relative_to(root)
    assert bcm_paths.cache_dir().is_relative_to(REPO_ROOT)


def test_blank_variable_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("BCM_DATA_DIR", "   ")
    assert bcm_paths.data_root() == REPO_ROOT / "data"


def test_explicit_absolute_root_is_used(monkeypatch, tmp_path):
    monkeypatch.setenv("BCM_DATA_DIR", str(tmp_path))
    assert bcm_paths.data_root() == tmp_path.resolve()
    assert bcm_paths.processed_dir() == tmp_path.resolve() / "A.2. Processed"


def test_relative_root_is_rejected(monkeypatch):
    monkeypatch.setenv("BCM_DATA_DIR", "relative/data")
    with pytest.raises(ValueError, match="absolute"):
        bcm_paths.data_root()


def test_no_module_derives_paths_from_its_own_location_or_the_working_directory():
    offenders = []
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "parents[3]" in text or 'Path("A. Data' in text or '"A. Data"' in text:
            offenders.append(path.relative_to(REPO_ROOT).as_posix())
    assert offenders == []


@pytest.mark.parametrize(
    "module, attributes",
    [
        ("assemble_model_input", ["PROC", "STRUCT", "OUT_DIR", "COUNTRY_CODE_MAPPING"]),
        ("build_population", ["WPP", "OUT", "COUNTRY_CODE_MAPPING"]),
        ("harmonize_dhs", ["RAW", "OUT"]),
        ("harmonize_ipums_census", ["RAW", "OUT", "COUNTRY_MAP"]),
        ("harmonize_wide", ["RAW", "OUT"]),
        ("harmonize_mics", ["RAW", "OUT"]),
        ("fetch_public_data", ["POP_DIR", "WPP_DIR"]),
    ],
)
def test_module_paths_follow_the_configured_root(module, attributes, tmp_path):
    code = (
        f"import sys; sys.path.insert(0, {str(SRC / 'python')!r}); import {module} as m; "
        f"print('\\n'.join(str(getattr(m, a)) for a in {attributes!r}))"
    )
    env = os.environ | {"BCM_DATA_DIR": str(tmp_path)}
    env.pop("BCM_ADMIN_REFERENCE_DIR", None)
    env.pop("BCM_COUNTRY_CODE_MAPPING", None)
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=tmp_path, env=env, capture_output=True, text=True, check=True
    )
    for line in result.stdout.strip().splitlines():
        assert Path(line).is_relative_to(tmp_path.resolve()), line
