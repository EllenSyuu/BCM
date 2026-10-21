"""Synthetic recovery figure: known true rates vs posterior estimates.

Reads the outputs of ``run_demo.py`` and writes a self-contained SVG (no plotting
library needed). Panel A compares every estimated cell with its true rate; panel B
shows one relative age over time for each synthetic country, with the years that
have administrative observations marked.

Usage
-----
    python examples/synthetic_demo/plot_recovery.py                    # -> <output-dir>/synthetic_recovery.svg
    python examples/synthetic_demo/plot_recovery.py --svg docs/assets/synthetic_recovery.svg

The figure describes simulated data and a short demonstration run. It is not an
empirical estimate and not a convergence-checked result.
"""
from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1].parent
DEFAULT_OUTPUT = REPO_ROOT / "examples" / "synthetic_demo" / "output"
TAG = "SYNTH"
PANEL_B_AGE_REL = 4

# Reference palette (validated: blue/orange pass lightness, chroma, CVD and contrast checks)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
BLUE = "#2a78d6"        # posterior estimate
BLUE_BAND = "#cde2fb"   # 90% interval
ORANGE = "#eb6834"      # true rate outside the 90% interval (also drawn hollow)
FONT = "font-family='system-ui,-apple-system,Segoe UI,Helvetica,Arial,sans-serif'"


def _load(output_dir: Path) -> tuple[pd.DataFrame, dict, dict[str, list[int]]]:
    out = output_dir / "A.2. Processed" / "model_output" / TAG
    est = pd.read_csv(out / "estimates.csv")
    truth = pd.read_csv(output_dir / "synthetic_truth.csv")
    summary = json.loads((output_dir / "demo_summary.json").read_text())
    merged = est.merge(truth, on=["iso3", "year", "age_rel"], how="inner", validate="one_to_one")
    merged["covered"] = (merged["oos_q05"] <= merged["true_rate"]) & (merged["true_rate"] <= merged["oos_q95"])

    in_dir = output_dir / "A.2. Processed" / "model_input"
    index = json.loads((in_dir / f"model_index_{TAG}.json").read_text())
    with np.load(in_dir / f"model_input_{TAG}.npz") as z:
        ey = np.asarray(index["ey_grid"])[z["A_ey_idx"]]
        years = ey + z["A_age"]  # entry year = year - age_rel + 1, age index = age_rel - 1
        countries = z["A_country"]
    admin_years = {iso: sorted(set(years[countries == c].tolist())) for c, iso in enumerate(index["countries"])}
    return merged, summary, admin_years


class _Axes:
    """Linear data -> pixel mapping for one plotting rectangle."""

    def __init__(self, x0, y0, w, h, xlim, ylim):
        self.x0, self.y0, self.w, self.h = x0, y0, w, h
        self.xlim, self.ylim = xlim, ylim

    def x(self, v):
        return self.x0 + (v - self.xlim[0]) / (self.xlim[1] - self.xlim[0]) * self.w

    def y(self, v):
        return self.y0 + self.h - (v - self.ylim[0]) / (self.ylim[1] - self.ylim[0]) * self.h


def _nice(top: float, max_ticks: int = 4) -> tuple[float, np.ndarray]:
    """Round an axis maximum up to a tidy step and return (max, ticks)."""
    for step in (0.02, 0.05, 0.1, 0.2, 0.25):
        hi = float(np.ceil(top / step - 1e-9) * step)
        if hi / step <= max_ticks:
            return hi, np.round(np.arange(0, hi + step / 2, step), 4)
    return 1.0, np.round(np.linspace(0, 1, 5), 4)


def _text(x, y, s, size=12, color=INK_2, anchor="start", weight="normal"):
    return (f"<text x='{x:.1f}' y='{y:.1f}' {FONT} font-size='{size}' fill='{color}' "
            f"text-anchor='{anchor}' font-weight='{weight}'>{escape(str(s))}</text>")


def _frame(ax, xticks, yticks, xfmt, yfmt, xlabel=None, ylabel=None):
    parts = []
    for t in yticks:
        parts.append(f"<line x1='{ax.x0}' x2='{ax.x0 + ax.w}' y1='{ax.y(t):.1f}' y2='{ax.y(t):.1f}' "
                     f"stroke='{GRID}' stroke-width='1'/>")
        parts.append(_text(ax.x0 - 6, ax.y(t) + 4, yfmt(t), 11, anchor="end"))
    for t in xticks:
        parts.append(_text(ax.x(t), ax.y0 + ax.h + 16, xfmt(t), 11, anchor="middle"))
    parts.append(f"<line x1='{ax.x0}' x2='{ax.x0 + ax.w}' y1='{ax.y0 + ax.h}' y2='{ax.y0 + ax.h}' "
                 f"stroke='{INK_2}' stroke-width='1'/>")
    if xlabel:
        parts.append(_text(ax.x0 + ax.w / 2, ax.y0 + ax.h + 34, xlabel, 12, anchor="middle"))
    if ylabel:
        cx, cy = ax.x0 - 40, ax.y0 + ax.h / 2
        parts.append(f"<text transform='translate({cx:.1f},{cy:.1f}) rotate(-90)' {FONT} font-size='12' "
                     f"fill='{INK_2}' text-anchor='middle'>{escape(ylabel)}</text>")
    return parts


def build_svg(merged: pd.DataFrame, summary: dict, admin_years: dict[str, list[int]]) -> str:
    W, H = 980, 660
    pct = lambda v: f"{v * 100:.0f}%"  # noqa: E731
    d = summary["diagnostics"]
    s = summary["settings"]
    parts = [f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {W} {H}' width='{W}' height='{H}' "
             f"role='img' aria-labelledby='t d'>",
             "<title id='t'>Synthetic recovery: true out-of-school rates vs posterior estimates</title>",
             f"<desc id='d'>Simulated data. {summary['coverage_of_true_rate_by_90pct_interval']:.1%} of "
             f"{summary['estimated_cells']} true rates fall inside the 90% posterior interval; mean absolute "
             f"error {summary['mean_absolute_error_percentage_points']} percentage points. Short demonstration "
             f"run; convergence thresholds not met.</desc>",
             f"<rect width='{W}' height='{H}' fill='{SURFACE}'/>"]

    # header
    parts.append(_text(24, 34, "Synthetic recovery check: known true rates vs posterior estimates", 18, INK,
                       weight="600"))
    parts.append(_text(24, 56, f"{summary['estimated_cells']} country × year × age cells · "
                       f"{summary['coverage_of_true_rate_by_90pct_interval']:.1%} of true rates inside the 90% "
                       f"interval (nominal 90%) · mean absolute error "
                       f"{summary['mean_absolute_error_percentage_points']} percentage points", 13, INK))
    parts.append(_text(24, 76, f"Simulated data, short run ({s['chains']} chains × {s['samples']} draws, "
                       f"{s['warmup']} warm-up): max R-hat {d['max_r_hat']:.2f}, min ESS {d['min_n_eff']:.0f}, "
                       f"{d['divergences']} divergences.", 12))
    parts.append(_text(24, 94, "Convergence thresholds (R-hat ≤ 1.01, ESS ≥ 400) are not met: this is a pipeline "
                       "check on simulated data, not a formal or empirical result.", 12))

    # legend
    ly = 122
    parts += [f"<rect x='24' y='{ly - 8}' width='22' height='10' fill='{BLUE_BAND}'/>",
              _text(52, ly + 1, "90% posterior interval", 12),
              f"<line x1='210' x2='232' y1='{ly - 3}' y2='{ly - 3}' stroke='{BLUE}' stroke-width='2'/>",
              _text(238, ly + 1, "posterior median", 12),
              f"<line x1='370' x2='392' y1='{ly - 3}' y2='{ly - 3}' stroke='{INK}' stroke-width='2' "
              f"stroke-dasharray='5 3'/>",
              _text(398, ly + 1, "true rate", 12),
              f"<circle cx='497' cy='{ly - 3}' r='4' fill='none' stroke='{ORANGE}' stroke-width='2'/>",
              _text(507, ly + 1, "true rate outside the interval", 12),
              f"<line x1='705' x2='705' y1='{ly - 9}' y2='{ly + 2}' stroke='{INK_2}' stroke-width='2'/>",
              _text(713, ly + 1, "year with administrative data", 12)]

    # panel A: estimate vs truth for every cell
    hi, ticks = _nice(max(merged["oos_q95"].max(), merged["true_rate"].max()), max_ticks=7)
    ax = _Axes(84, 176, 360, 380, (0, hi), (0, hi))
    parts.append(_text(24, 158, "A  Every estimated cell", 13, INK, weight="600"))
    parts += _frame(ax, ticks, ticks, pct, pct, "true rate", "posterior median (90% interval)")
    parts.append(f"<line x1='{ax.x(0):.1f}' y1='{ax.y(0):.1f}' x2='{ax.x(hi):.1f}' y2='{ax.y(hi):.1f}' "
                 f"stroke='{INK_2}' stroke-width='1' stroke-dasharray='4 3'/>")
    parts.append(_text(ax.x(hi * 0.93) - 8, ax.y(hi * 0.93), "y = x", 11, anchor="end"))
    # one <path> per mark type keeps the SVG small (736 cells)
    intervals = "".join(f"M{ax.x(r.true_rate):.1f} {ax.y(r.oos_q05):.1f}V{ax.y(r.oos_q95):.1f}"
                        for r in merged.itertuples())
    parts.append(f"<path d='{intervals}' stroke='{BLUE_BAND}' stroke-width='1.5' fill='none'/>")
    dot = lambda cx, cy, rad: (f"M{cx - rad:.1f} {cy:.1f}a{rad} {rad} 0 1 0 {2 * rad} 0"  # noqa: E731
                               f"a{rad} {rad} 0 1 0 {-2 * rad} 0")
    inside = "".join(dot(ax.x(r.true_rate), ax.y(r.oos_median), 2.2) for r in merged.itertuples() if r.covered)
    outside = "".join(dot(ax.x(r.true_rate), ax.y(r.oos_median), 3.5) for r in merged.itertuples() if not r.covered)
    parts.append(f"<path d='{inside}' fill='{BLUE}'/>")
    parts.append(f"<path d='{outside}' fill='none' stroke='{ORANGE}' stroke-width='1.5'/>")

    # panel B: one relative age over time, one small multiple per country
    parts.append(_text(480, 158, f"B  Relative age {PANEL_B_AGE_REL} over time, by synthetic country",
                       13, INK, weight="600"))
    sub = merged[merged["age_rel"] == PANEL_B_AGE_REL]
    countries = sorted(sub["iso3"].unique())
    pw, ph, gx, gy = 180, 150, 50, 72
    for i, iso in enumerate(countries):
        c = sub[sub["iso3"] == iso].sort_values("year")
        ymax, yt = _nice(max(c["oos_q95"].max(), c["true_rate"].max()), max_ticks=3)
        bx = _Axes(530 + (i % 2) * (pw + gx), 196 + (i // 2) * (ph + gy), pw, ph, (2000, 2022), (0, ymax))
        parts.append(_text(bx.x0, bx.y0 - 8, f"{iso}" + (" · admin data every 3rd year" if
                                                         len(admin_years.get(iso, [])) < 23 else ""), 12, INK))
        parts += _frame(bx, [2000, 2011, 2022], yt, lambda v: str(int(v)), pct)
        band = [f"{bx.x(y):.1f},{bx.y(v):.1f}" for y, v in zip(c["year"], c["oos_q95"], strict=True)]
        band += [f"{bx.x(y):.1f},{bx.y(v):.1f}" for y, v in zip(c["year"][::-1], c["oos_q05"][::-1], strict=True)]
        parts.append(f"<polygon points='{' '.join(band)}' fill='{BLUE_BAND}'/>")
        med = " ".join(f"{bx.x(y):.1f},{bx.y(v):.1f}" for y, v in zip(c["year"], c["oos_median"], strict=True))
        parts.append(f"<polyline points='{med}' fill='none' stroke='{BLUE}' stroke-width='2' "
                     f"stroke-linejoin='round'/>")
        tru = " ".join(f"{bx.x(y):.1f},{bx.y(v):.1f}" for y, v in zip(c["year"], c["true_rate"], strict=True))
        parts.append(f"<polyline points='{tru}' fill='none' stroke='{INK}' stroke-width='2' "
                     f"stroke-dasharray='5 3'/>")
        for y in admin_years.get(iso, []):
            parts.append(f"<line x1='{bx.x(y):.1f}' x2='{bx.x(y):.1f}' y1='{bx.y0 + ph - 6:.1f}' "
                         f"y2='{bx.y0 + ph:.1f}' stroke='{INK_2}' stroke-width='2'/>")

    parts.append(_text(24, H - 16, f"Source: examples/synthetic_demo, simulated data, seed {s.get('seed', 'n/a')}. "
                       "Rebuild: python examples/synthetic_demo/run_demo.py. Underlying table: estimates.csv.", 11))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def plot_recovery(output_dir: Path = DEFAULT_OUTPUT, svg_path: Path | None = None) -> Path:
    merged, summary, admin_years = _load(output_dir)
    svg_path = svg_path or output_dir / "synthetic_recovery.svg"
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    svg_path.write_text(build_svg(merged, summary, admin_years), encoding="utf-8")
    return svg_path


def main(argv: list[str] | None = None) -> Path:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT, help="run_demo.py output directory")
    ap.add_argument("--svg", type=Path, default=None, help="where to write the SVG")
    args = ap.parse_args(argv)
    path = plot_recovery(args.output_dir.resolve(), args.svg)
    print(f"Wrote {path}")
    return path


if __name__ == "__main__":
    main()
