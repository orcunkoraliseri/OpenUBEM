"""Per-phase montage (contact-sheet) PNGs — input-imputation arc, follow-up round 3.

For each phase A-E, tiles every PNG currently in
`docs/docs_ACTIVE/input/imputation/results/phase_<X>/` (schematic + quantitative +
scatter) onto one titled grid and writes it beside the parent PLAN:
`docs/docs_ACTIVE/input/imputation/phase_<X>_all_figures.png`.

Pure assembly — READ-ONLY on the source figures. No data, no new numbers, no
re-rendering, no modification/move of any existing PNG.

See docs/docs_ACTIVE/input/imputation/implementation/PLAN_figures_implementation.md
§10 (binding spec for T13).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.image import imread

from openubem.results.impute_figures import PALETTE, RESULTS_DIR, _style

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "docs" / "docs_ACTIVE" / "input" / "imputation"

PHASES = ["A", "B", "C", "D", "E"]
N_COLS = 3


def _sort_key(path: Path) -> tuple[int, str]:
    """Deterministic tile order (plan §10 T13): schematic first (by existing
    name), then `*_quant_*`, then `*_scatter_*`. Explicit key -> byte-stable
    re-runs (glob order is not guaranteed across filesystems).
    """
    name = path.stem
    if "_quant_" in name:
        category = 1
    elif "_scatter_" in name:
        category = 2
    else:
        category = 0
    return (category, name)


def _phase_dir(phase: str) -> Path:
    return RESULTS_DIR / f"phase_{phase}"


def build_phase_montage(phase: str) -> plt.Figure:
    """Build the contact-sheet figure for one phase. Does not save/close it."""
    _style()
    phase_dir = _phase_dir(phase)
    pngs = sorted(phase_dir.glob("*.png"), key=_sort_key)
    n = len(pngs)
    if n == 0:
        raise FileNotFoundError(f"phase_{phase} folder has zero PNGs — nothing to montage")

    ncols = min(N_COLS, n)
    nrows = -(-n // ncols)  # ceil

    fig = plt.figure(figsize=(ncols * 6.4, nrows * 3.3 + 0.9))
    gs = fig.add_gridspec(
        nrows, ncols, hspace=0.28, wspace=0.08,
        top=1.0 - 0.9 / (nrows * 3.3 + 0.9), bottom=0.02, left=0.02, right=0.98,
    )

    for i, png_path in enumerate(pngs):
        r, c = divmod(i, ncols)
        ax = fig.add_subplot(gs[r, c])
        img = imread(str(png_path))  # read-only: never modifies the source file
        # aspect="auto" fills the tile box completely (mild per-tile stretch)
        # rather than the default equal-aspect, which leaves most of the tile
        # blank and shrinks embedded plot text far below legibility.
        ax.imshow(img, aspect="auto")
        ax.axis("off")
        ax.set_title(png_path.stem, fontsize=10, color=PALETTE["ink_secondary"], pad=6)

    fig.suptitle(f"Phase {phase} — all figures ({n})", fontsize=18, color=PALETTE["ink"], y=0.998)
    return fig


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(path), dpi=170, facecolor=PALETTE["surface"])
    plt.close(fig)
    return path


def main() -> list[Path]:
    written: list[Path] = []
    for phase in PHASES:
        fig = build_phase_montage(phase)
        out_path = OUT_DIR / f"phase_{phase}_all_figures.png"
        written.append(_save(fig, out_path))
    return written


if __name__ == "__main__":
    for p in main():
        print(f"wrote {p}")
