"""T26 -- Harvest Stage-6 (UTCI/microclimate) cluster fleet sweep.

Run AFTER the 12-cell sbatch array submitted by the T26 staging work
(scratchpad/t26_cluster_stage/run_array.sbatch, job 1158633) has completed on
Speed. Fetches the LIGHTWEIGHT per-cell Stage-6 artifacts (manifest, exposure
metrics, parcel summary, classified UTCI rasters) -- never the multi-gigabyte
hourly stacks (06_mc_{tmrt,utci,ta,wind,flags}_hourly.tif), which are left on
the cluster -- and builds a 12-cell cross-city comparison table + figure.

Mirrors scripts/cluster/t18_harvest_layout_assign.py's pull -> aggregate ->
compare pattern; metrics are UTCI/microclimate instead of EUI.

Rule 11 (CLAUDE.md): the only remote operations here are `ssh ... tar czf -`
(read-only fetch) and `ssh ... du -sh` (size query) -- both lightweight ops.
No python/srun/compute is ever run on the login node; all parsing/aggregation
happens locally after the fetch.

Usage:
    py -3 scripts/cluster/t26_harvest_utci_cluster.py [--cells ...] [--skip-fetch]

Outputs:
    openubem/outputs/comparisons/t26_utci_cluster_cell_summary.csv
    openubem/outputs/comparisons/t26_utci_cluster_comparison.png
    scratchpad/t26_harvest_work/out/<cell>/06_mc_manifest.parquet (+ small artifacts)
    scratchpad/t26_harvest_work/logs/*.log
    scratchpad/t26_harvest_work/remote_output_sizes.csv
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

REMOTE_HOST = "speed-submit2"
REMOTE_BASE = "/speed-scratch/o_iseri/openubem_utci_mc"
JOB_ID = "1158633"

ALL_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]
CITY_OF = {c: c.split("_")[0].upper() for c in ALL_CELLS}
ZONE_OF = {c: c.split("_", 1)[1] for c in ALL_CELLS}
# 1-indexed array-task mapping, matching scratchpad/t26_cluster_stage/cell_list.txt
ARRAY_TASK_OF = {cell: i + 1 for i, cell in enumerate(ALL_CELLS)}

WORK_DIR = REPO / "scratchpad" / "t26_harvest_work"
OUT_DIR = WORK_DIR / "out"
LOGS_DIR = WORK_DIR / "logs"
SIZES_CSV = WORK_DIR / "remote_output_sizes.csv"

OUTPUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
OUTPUT_CSV = OUTPUT_DIR / "t26_utci_cluster_cell_summary.csv"
OUTPUT_PNG = OUTPUT_DIR / "t26_utci_cluster_comparison.png"

# Lightweight artifacts only -- never the *_hourly.tif stacks (multi-GB).
_FETCH_FILES = (
    "06_mc_manifest.parquet",
    "06_mc_exposure_metrics.json",
    "06_mc_summary.gpkg",
    "06_mc_utci_mean_class.tif",
    "06_mc_utci_peak_class.tif",
)

# dataviz skill validated categorical palette, first 3 slots (light mode) --
# these clear the all-pairs CVD/normal-vision floor for a 3-series chart.
CITY_COLOR = {"NYC": "#2a78d6", "LA": "#eb6834", "AUSTIN": "#1baf7a"}


def _ssh(cmd: str, timeout: int = 60) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def fetch_cell(cell: str) -> Path:
    dest = OUT_DIR / cell
    dest.mkdir(parents=True, exist_ok=True)
    remote_cell_dir = f"{REMOTE_BASE}/out/{cell}"
    remote_cmd = f"cd {remote_cell_dir} && tar czf - --ignore-failed-read {' '.join(_FETCH_FILES)}"
    tgz = WORK_DIR / f"fetch_{cell}.tgz"

    with open(tgz, "wb") as fh:
        proc = subprocess.Popen(
            ["ssh", REMOTE_HOST, remote_cmd],
            stdout=fh, stderr=subprocess.PIPE, text=True,
        )
        _, err = proc.communicate(timeout=300)

    if tgz.stat().st_size == 0:
        tgz.unlink(missing_ok=True)
        raise RuntimeError(f"empty fetch for {cell}; remote stderr: {err.strip()[:400]}")

    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(str(dest), filter="data")
    tgz.unlink(missing_ok=True)
    return dest


def fetch_logs() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    remote_cmd = f"cd {REMOTE_BASE}/logs && tar czf - --ignore-failed-read *.log"
    tgz = WORK_DIR / "fetch_logs.tgz"
    with open(tgz, "wb") as fh:
        proc = subprocess.Popen(["ssh", REMOTE_HOST, remote_cmd], stdout=fh, stderr=subprocess.PIPE, text=True)
        _, err = proc.communicate(timeout=120)
    if tgz.stat().st_size == 0:
        tgz.unlink(missing_ok=True)
        print(f"  WARNING: empty logs fetch; remote stderr: {err.strip()[:400]}", file=sys.stderr)
        return
    with tarfile.open(tgz, "r:gz") as tf:
        tf.extractall(str(LOGS_DIR), filter="data")
    tgz.unlink(missing_ok=True)


def fetch_remote_sizes(cells: list[str]) -> pd.DataFrame:
    """Lightweight `du -sh` per cell (never downloads the multi-GB hourly stacks)."""
    rows = []
    for cell in cells:
        out = _ssh(f"du -sh {REMOTE_BASE}/out/{cell}/", timeout=30).strip()
        size_str = out.split("\t")[0].strip() if "\t" in out else out
        rows.append({"cell": cell, "remote_output_size": size_str})
    df = pd.DataFrame(rows)
    df.to_csv(SIZES_CSV, index=False)
    return df


def _parse_runtime_from_log(cell: str) -> "float | None":
    task = ARRAY_TASK_OF[cell]
    log_path = LOGS_DIR / f"utci_mc_t26_{JOB_ID}_{task}.log"
    if not log_path.exists():
        return None
    txt = log_path.read_text(errors="replace")
    import re
    m = re.search(r"wrote artifacts to .* in ([\d.]+)s", txt)
    return float(m.group(1)) if m else None


def _idd_fallback_flag(cell: str) -> bool:
    task = ARRAY_TASK_OF[cell]
    log_path = LOGS_DIR / f"utci_mc_t26_{JOB_ID}_{task}.log"
    if not log_path.exists():
        return False
    return "falling back to eppy bundled IDD" in log_path.read_text(errors="replace")


def parse_cell(cell: str, sizes: pd.DataFrame) -> dict:
    cell_dir = OUT_DIR / cell
    manifest_path = cell_dir / "06_mc_manifest.parquet"
    exposure_path = cell_dir / "06_mc_exposure_metrics.json"

    row: dict = {"cell": cell, "city": CITY_OF[cell], "zone": ZONE_OF[cell]}

    if manifest_path.exists():
        mf = pd.read_parquet(manifest_path).iloc[0]
        row["n_buildings"] = int(mf["n_buildings"])
        row["n_excluded_no_height"] = int(mf["n_excluded_no_height"])
        row["pct_excluded_no_height"] = 100.0 * mf["n_excluded_no_height"] / mf["n_buildings"] if mf["n_buildings"] else None
        row["domain_rows"], row["domain_cols"] = int(mf["domain_shape"][0]), int(mf["domain_shape"][1])
        row["window_mode"] = mf["window_mode"]
        row["window_n_hours"] = int(mf["window_n_hours"])
        row["vegetation_tier"] = mf["vegetation_tier"]
        row["wall_temp_tier"] = mf["wall_temp_tier"]
        row["wind_tier"] = mf["wind_tier"]
        row["ta_tier"] = mf["ta_tier"]
        row["svf_mean"] = float(mf["svf_mean"]) if mf["svf_mean"] is not None else None
        # Honest-finding flag (T26 harvest discovery, not a T18/T19/T20 bug): some cells'
        # source 01_buildings.gpkg has height_m entirely NaN for every building (verified
        # directly against the fixture file, not just the manifest counter) -- the DSM then
        # contains zero building massing and svf_mean == 1.0 (fully open sky). This is a
        # materially different scenario from the other cells' partial-exclusion gap.
        row["zero_building_massing"] = bool(
            mf["n_buildings"] > 0 and mf["n_excluded_no_height"] == mf["n_buildings"]
        )

        total_cell_hours = row["domain_rows"] * row["domain_cols"] * row["window_n_hours"]
        row["total_domain_cell_hours"] = total_cell_hours
        row["wind_clamp_cell_hours"] = int(mf["wind_clamp_cell_hours"])
        row["wind_clamp_pct_of_domain_cell_hours"] = (
            100.0 * mf["wind_clamp_cell_hours"] / total_cell_hours if total_cell_hours else None
        )
        row["wind_macdonald_domain_invalid_cell_hours"] = int(mf["wind_macdonald_domain_invalid_cell_hours"])
        row["wind_macdonald_numerical_anomaly_cell_hours"] = int(mf["wind_macdonald_numerical_anomaly_cell_hours"])
        row["ta_clamp_cell_hours"] = int(mf["ta_clamp_cell_hours"])
        try:
            flags = json.loads(mf["utci_flag_counts"]) if isinstance(mf["utci_flag_counts"], str) else dict(mf["utci_flag_counts"])
        except Exception:
            flags = {}
        row["utci_flag_ta"] = flags.get("ta")
        row["utci_flag_tmrt"] = flags.get("tmrt")
        row["utci_flag_wind"] = flags.get("wind")
        row["utci_flag_vapour"] = flags.get("vapour")
        row["git_commit"] = mf["git_commit"]
        row["started_utc"] = mf["started_utc"]
        row["ended_utc"] = mf["ended_utc"]
        try:
            dt = (pd.Timestamp(mf["ended_utc"]) - pd.Timestamp(mf["started_utc"])).total_seconds()
            row["manifest_elapsed_s"] = dt
        except Exception:
            row["manifest_elapsed_s"] = None
    else:
        row["parse_error"] = "manifest.parquet missing"

    if exposure_path.exists():
        exp = json.loads(exposure_path.read_text())
        row["area_hours_extreme_heat_m2h"] = exp.get("area_hours_extreme_heat_m2h")
        row["person_hours_extreme_heat_h"] = exp.get("person_hours_extreme_heat_h")
        row["ctsi_mean_degc_h"] = exp.get("ctsi_mean_degc_h")
        row["ctsi_max_degc_h"] = exp.get("ctsi_max_degc_h")
        row["utci_peak_max_c"] = exp.get("utci_peak_max_c")
        row["utci_mean_mean_c"] = exp.get("utci_mean_mean_c")

    row["runtime_s_from_log"] = _parse_runtime_from_log(cell)
    size_row = sizes[sizes["cell"] == cell]
    row["remote_output_size"] = size_row.iloc[0]["remote_output_size"] if not size_row.empty else None
    row["idd_fallback_warning_in_log"] = _idd_fallback_flag(cell)

    return row


def build_figure(df: pd.DataFrame) -> None:
    df = df.sort_values(["city", "zone"], key=lambda s: s.map({v: i for i, v in enumerate(["centre", "urban", "suburban", "rural"])}) if s.name == "zone" else s)
    order = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
             "la_centre", "la_urban", "la_suburban", "la_rural",
             "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]
    df = df.set_index("cell").loc[order].reset_index()
    colors = [CITY_COLOR[c] for c in df["city"]]
    x = range(len(df))
    # Honest-finding markup (see parse_cell): 3/12 cells have zero building massing in the
    # DSM (svf_mean == 1.0, height_m entirely missing upstream) -- flag their tick labels so
    # the figure cannot be misread as 12 comparable urban-canyon runs.
    zero_mass = df["zero_building_massing"].tolist() if "zero_building_massing" in df.columns else [False] * len(df)
    xticklabels = [f"{c}*" if flag else c for c, flag in zip(df["cell"], zero_mass)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle(
        "T26 -- 12-cell cross-city Stage-6 (UTCI) sweep\n"
        "vegetation=none, wall_temp=empirical, wind=cost730, window=hottest_week, res=2.0 m "
        "(same tiers as CP-4's nyc_centre live-smoke evidence)\n"
        "* = zero building massing in DSM (height_m missing for 100% of buildings upstream; "
        "svf_mean=1.0, open-field result, not an urban canyon)",
        fontsize=10.5, y=0.99,
    )

    from matplotlib.patches import Patch
    city_handles = [Patch(facecolor=c, label=city) for city, c in CITY_COLOR.items()]

    ax = axes[0, 0]
    ax.bar(x, df["utci_mean_mean_c"], color=colors)
    ax.set_title("Mean UTCI (domain-mean of the mean-over-window field)")
    ax.set_ylabel("degC")
    ax.set_xticks(list(x)); ax.set_xticklabels(xticklabels, rotation=60, ha="right", fontsize=8)
    ax.axhline(26.0, color="gray", linestyle="--", linewidth=0.8, label="CTSI baseline 26 degC")
    ax.axhline(32.0, color="firebrick", linestyle=":", linewidth=0.8, label="strong heat stress 32 degC")
    threshold_handles, threshold_labels = ax.get_legend_handles_labels()
    ax.legend(
        handles=city_handles + threshold_handles,
        labels=[h.get_label() for h in city_handles] + threshold_labels,
        fontsize=7, loc="upper left",
    )

    ax = axes[0, 1]
    ax.bar(x, df["utci_peak_max_c"], color=colors)
    ax.set_title("Peak UTCI (domain-max of the peak-over-window field)")
    ax.set_ylabel("degC")
    ax.set_xticks(list(x)); ax.set_xticklabels(xticklabels, rotation=60, ha="right", fontsize=8)
    ax.axhline(46.0, color="firebrick", linestyle=":", linewidth=0.8, label="PHEH/extreme-heat threshold 46 degC")
    ax.legend(fontsize=7, loc="upper left")

    ax = axes[1, 0]
    ax.bar(x, df["ctsi_mean_degc_h"], color=colors)
    ax.set_title("Mean CTSI (cumulative thermal-stress index, mean over domain)")
    ax.set_ylabel("degC*h")
    ax.set_xticks(list(x)); ax.set_xticklabels(xticklabels, rotation=60, ha="right", fontsize=8)

    ax = axes[1, 1]
    ax.bar(x, df["wind_clamp_pct_of_domain_cell_hours"], color=colors)
    ax.set_title("Wind clamp-flag rate\n(% of domain rows x cols x window-hours)")
    ax.set_ylabel("%")
    ax.set_xticks(list(x)); ax.set_xticklabels(xticklabels, rotation=60, ha="right", fontsize=8)

    fig.tight_layout()
    fig.subplots_adjust(top=0.80, hspace=0.6)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PNG, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="T26 harvest: fetch + aggregate 12-cell UTCI cluster sweep")
    parser.add_argument("--cells", nargs="+", default=ALL_CELLS, choices=ALL_CELLS)
    parser.add_argument("--skip-fetch", action="store_true",
                         help="Use already-staged scratchpad/t26_harvest_work/out/<cell>/ files.")
    args = parser.parse_args()

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    print(f"T26 harvest -- work dir: {WORK_DIR}")
    print(f"  Cells: {args.cells}")

    if not args.skip_fetch:
        fetch_logs()
        for cell in args.cells:
            print(f"  [{cell}] fetching lightweight artifacts ...")
            fetch_cell(cell)
    else:
        print("  --skip-fetch: using already-staged local files.")

    sizes = fetch_remote_sizes(args.cells)

    rows = [parse_cell(cell, sizes) for cell in args.cells]
    df = pd.DataFrame(rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nCell-summary CSV: {OUTPUT_CSV}")

    build_figure(df)
    print(f"Comparison figure: {OUTPUT_PNG}")

    print("\n### Per-cell runtime / output size / clamp-flag summary ###")
    cols = ["cell", "runtime_s_from_log", "remote_output_size",
            "wind_clamp_cell_hours", "wind_clamp_pct_of_domain_cell_hours",
            "ta_clamp_cell_hours", "n_excluded_no_height", "pct_excluded_no_height"]
    print(df[cols].to_string(index=False))

    print(f"\nTotal buildings across 12 cells: {int(df['n_buildings'].sum())}")
    print(f"Total excluded (no height): {int(df['n_excluded_no_height'].sum())}")


if __name__ == "__main__":
    main()
