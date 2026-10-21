"""End-to-end test of the README demo: simulate -> run_full_model.py (checkpointed) -> summary."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO = REPO_ROOT / "examples" / "synthetic_demo" / "run_demo.py"


def _load_demo():
    spec = importlib.util.spec_from_file_location("run_demo", DEMO)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_quick_demo_runs_end_to_end(tmp_path):
    summary = _load_demo().main(["--quick", "--output-dir", str(tmp_path)])

    out = tmp_path / "A.2. Processed" / "model_output" / "SYNTH"
    for name in ("estimates.csv", "diagnostics.csv", "parameters.csv", "run_info.json", "progress.txt"):
        assert (out / name).is_file(), name
    manifest = json.loads((out / "checkpoints" / "checkpoint.json").read_text())
    assert manifest["status"] == "sampling_complete"
    assert manifest["chunk_ends"] == [40, 80]  # --checkpoint-every 40 in quick mode

    estimates = pd.read_csv(out / "estimates.csv")
    assert len(estimates) == 4 * 23 * 8
    assert summary["estimated_cells"] == len(estimates)
    assert summary["rates_within_0_1"]
    # loose recovery bounds: a short run should still track the known surface
    assert summary["coverage_of_true_rate_by_90pct_interval"] > 0.6
    assert summary["mean_absolute_error_percentage_points"] < 3.0
    assert (tmp_path / "demo_report.md").is_file()
    assert (tmp_path / "demo_summary.json").is_file()
