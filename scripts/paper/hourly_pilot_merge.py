from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.results import hourly as hr

CMP = ROOT / "openubem" / "outputs" / "comparisons"
CASE_CSV = CMP / "paper_hourly_pilot_case_list_2026-10-21.csv"
CHECK_CSV = CMP / "paper_hourly_check_2026-10-21.csv"
PROFILES_CSV = CMP / "paper_hourly_profiles_2026-10-21.csv"
FIGURE_PNG = ROOT / "openubem" / "outputs" / "paper_hourly_profiles.png"
VINTAGE = "adopted fleet 2026-09-30 IDFs re-run with hourly meters 2026-10-21; district hot water left out"

TOLERANCE = 0.001
ABS_FLOOR_KWH = 1e-6

RUN_PERIOD_SERIES = {
    "heating": "heating_kwh",
    "cooling": "cooling_kwh",
    "electricity": "electricity_kwh",
    "gas": "gas_kwh",
    "district_hot_water": hr.DISTRICT_COLUMN,
}
REFERENCE_SERIES = {
    "heating": ("heating_kwh",),
    "cooling": ("cooling_kwh",),
    "district_hot_water": (hr.DISTRICT_COLUMN,),
    "electricity_gas": ("electricity_kwh", "gas_kwh"),
}
REFERENCE_COLUMN = {
    "heating": "ref_heating_kwh",
    "cooling": "ref_cooling_kwh",
    "district_hot_water": "ref_district_hot_water_kwh",
    "electricity_gas": "ref_electricity_gas_kwh",
}


def rel_diff(value: float, reference: float) -> float:
    if pd.isna(value) or pd.isna(reference):
        return float("nan")
    if abs(value - reference) <= ABS_FLOOR_KWH:
        return 0.0
    return hr.relative_difference(float(value), float(reference))


def within(diff: float) -> bool:
    return bool(pd.notna(diff) and diff <= TOLERANCE)


def sum_nan(values: list[float]) -> float:
    present = [v for v in values if pd.notna(v)]
    return float(sum(present)) if present else float("nan")


def check_building(case: pd.Series, sidecar: dict | None) -> dict:
    row = {"task": case["task"], "city": case["city"], "cell": case["cell"],
           "osm_id": case["osm_id"], "stem": case["stem"]}
    if sidecar is None:
        row.update(status="missing", pass_run_period=False, pass_reference=False, passed=False)
        return row
    annual = sidecar["annual_kwh"]
    run_period = sidecar["run_period_kwh"]
    run_ok = True
    hourly = {}
    for name, column in RUN_PERIOD_SERIES.items():
        value = annual.get(column, float("nan"))
        reference = run_period.get(column, float("nan"))
        if pd.isna(value) and pd.isna(reference):
            value = reference = 0.0
        hourly[column] = value
        diff = rel_diff(value, reference)
        row[f"{name}_hourly_kwh"] = value
        row[f"{name}_run_period_kwh"] = reference
        row[f"{name}_diff_run_period"] = diff
        if not within(diff):
            run_ok = False
    ref_ok = True
    for name, columns in REFERENCE_SERIES.items():
        value = sum_nan([hourly.get(c, float("nan")) for c in columns])
        reference = float(case[REFERENCE_COLUMN[name]])
        diff = rel_diff(value, reference)
        row[f"{name}_t01_kwh"] = reference
        row[f"{name}_diff_t01"] = diff
        if not within(diff):
            ref_ok = False
    row.update(status="ok", pass_run_period=run_ok, pass_reference=ref_ok, passed=run_ok and ref_ok)
    return row


def load_sidecar(out_dir: Path, stem: str) -> dict | None:
    path = out_dir / f"{stem}.json"
    if not path.is_file() or not (out_dir / f"{stem}.csv.gz").is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def city_profiles(frames: list[pd.DataFrame], city: str, cell: str) -> pd.DataFrame:
    site, _ = hr.aggregate_site(frames)
    population = len(frames)
    rows = []
    for kind, profile in (("winter_avg_day", hr.winter_profile(site)), ("summer_avg_day", hr.summer_profile(site))):
        for _, p in profile.iterrows():
            for series in hr.COLUMNS:
                rows.append({"city": city, "cell": cell, "kind": kind, "series": series,
                             "hour": int(p["hour"]), "month": "", "day": "", "kwh": float(p[series]),
                             "population": population, "vintage": VINTAGE})
    for series, peak in hr.peaks(site).items():
        if peak is None:
            continue
        rows.append({"city": city, "cell": cell, "kind": "annual_peak", "series": series,
                     "hour": peak["hour"], "month": peak["month"], "day": peak["day"], "kwh": peak["kwh"],
                     "population": population, "vintage": VINTAGE})
    return pd.DataFrame(rows)


def plot_profiles(profiles: pd.DataFrame, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    colours = {"heating_kwh": "#d95f02", "cooling_kwh": "#1b9e77", "electricity_kwh": "#7570b3",
               "gas_kwh": "#666666"}
    cities = sorted(profiles["city"].unique())
    fig, axes = plt.subplots(2, len(cities), figsize=(4.2 * len(cities), 6.4), sharex=True, squeeze=False)
    for j, city in enumerate(cities):
        for i, kind in enumerate(("winter_avg_day", "summer_avg_day")):
            ax = axes[i][j]
            sub = profiles[(profiles["city"] == city) & (profiles["kind"] == kind)]
            for series, colour in colours.items():
                s = sub[sub["series"] == series].sort_values("hour")
                ax.plot(s["hour"], s["kwh"] / 1000.0, color=colour, label=series.replace("_kwh", ""))
            cell = sub["cell"].iloc[0] if len(sub) else ""
            ax.set_title(f"{city} ({cell}), {'winter' if i == 0 else 'summer'} average day", fontsize=9)
            ax.set_xlabel("hour of day")
            ax.set_ylabel("MWh per hour")
            ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def run(case_csv: Path, out_dir: Path, check_csv: Path, profiles_csv: Path, figure_png: Path) -> int:
    cases = pd.read_csv(case_csv)
    rows = [check_building(c, load_sidecar(out_dir, c["stem"])) for _, c in cases.iterrows()]
    check = pd.DataFrame(rows)
    check_csv.parent.mkdir(parents=True, exist_ok=True)
    check.to_csv(check_csv, index=False)
    failing = check[~check["passed"]]
    print(f"buildings {len(check)}, passed {int(check['passed'].sum())}, failed {len(failing)}")
    if len(failing):
        print(failing[["task", "city", "stem", "status", "pass_run_period", "pass_reference"]].to_string(index=False))
        return 1
    parts = []
    for (city, cell), g in cases.groupby(["city", "cell"]):
        frames = [pd.read_csv(out_dir / f"{s}.csv.gz") for s in g["stem"]]
        parts.append(city_profiles(frames, city, cell))
    profiles = pd.concat(parts, ignore_index=True)
    profiles.to_csv(profiles_csv, index=False)
    plot_profiles(profiles, figure_png)
    print("wrote", profiles_csv, figure_png)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check and merge the hourly pilot re-run")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--case-list", type=Path, default=CASE_CSV)
    parser.add_argument("--check-csv", type=Path, default=CHECK_CSV)
    parser.add_argument("--profiles-csv", type=Path, default=PROFILES_CSV)
    parser.add_argument("--figure", type=Path, default=FIGURE_PNG)
    args = parser.parse_args(argv)
    return run(args.case_list, args.out_dir, args.check_csv, args.profiles_csv, args.figure)


if __name__ == "__main__":
    raise SystemExit(main())
