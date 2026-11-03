from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location("hourly_pilot_cases", ROOT / "scripts" / "paper" / "hourly_pilot_cases.py")
hp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hp)

CMP = ROOT / "openubem" / "outputs" / "comparisons"
FLEET_CSV = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"
OUT_CSV = CMP / "paper_scenario_case_list_2026-10-21.csv"
MAX_WAVE = 10000
LARGE_ARCHETYPES = ("MediumOffice", "LargeOffice")
COLUMNS = ["task", "cell", "osm_id", "stem", "source", "archetype", "city", "idf_path", "epw_name",
           "wave", "wave_task", "geo_cell", "floor_area_m2"]


def measure_cell_names() -> list[str]:
    from openubem.scenarios.campaign import build_full_factorial_campaign

    return [c.name for c in build_full_factorial_campaign() if c.name != "baseline"]


def build_case_list(fleet: pd.DataFrame, epws: dict[str, str], cells: list[str],
                    max_wave: int = MAX_WAVE) -> pd.DataFrame:
    base = fleet.sort_values(["cell", "osm_id"]).reset_index(drop=True)
    rows = []
    for cell in cells:
        part = pd.DataFrame({
            "cell": cell,
            "osm_id": base["osm_id"],
            "stem": base["osm_id"].map(hp.stem_of),
            "source": base["source"],
            "archetype": base["archetype_id"],
            "city": base["city"],
            "idf_path": [hp.remote_idf_path(s, c, o) for s, c, o in zip(base["source"], base["cell"], base["osm_id"])],
            "epw_name": base["cell"].map(epws),
            "geo_cell": base["cell"],
            "floor_area_m2": base["floor_area_m2"],
        })
        rows.append(part)
    cases = pd.concat(rows, ignore_index=True)
    cases["_large"] = cases["archetype"].isin(LARGE_ARCHETYPES)
    cases = cases.sort_values(["_large", "cell", "city", "osm_id"], ascending=[False, True, True, True]).reset_index(drop=True)
    n_waves = max(1, math.ceil(len(cases) / max_wave))
    cases["wave"] = (cases.index % n_waves) + 1
    cases = cases.drop(columns="_large")
    cases = cases.sort_values(["wave"], kind="stable").reset_index(drop=True)
    cases["wave_task"] = cases.groupby("wave").cumcount() + 1
    cases.insert(0, "task", range(1, len(cases) + 1))
    return cases[COLUMNS]


def check_case_list(cases: pd.DataFrame, n_buildings: int, cells: list[str], max_wave: int = MAX_WAVE) -> list[str]:
    problems = []
    expected = n_buildings * len(cells)
    if len(cases) != expected:
        problems.append(f"rows {len(cases)} != {len(cells)} cells x {n_buildings} buildings = {expected}")
    if cases.duplicated(["cell", "stem"]).any():
        problems.append("(cell, stem) not unique")
    sizes = cases.groupby("wave").size()
    if (sizes > max_wave).any():
        problems.append(f"a wave has more than {max_wave} tasks: {sizes.to_dict()}")
    for wave, g in cases.groupby("wave"):
        if sorted(g["wave_task"]) != list(range(1, len(g) + 1)):
            problems.append(f"wave {wave}: wave_task is not 1..{len(g)}")
    if cases[COLUMNS].isna().any().any():
        problems.append("null in a case-list column")
    if set(cases["cell"]) != set(cells):
        problems.append("cells in the list differ from the campaign cells")
    for col in ("idf_path", "epw_name", "stem", "archetype"):
        if cases[col].astype(str).str.contains(",").any():
            problems.append(f"comma inside {col}")
    return problems


def main() -> None:
    fleet = pd.read_csv(FLEET_CSV)
    epws = hp.epw_by_cell()
    cells = measure_cell_names()
    cases = build_case_list(fleet, epws, cells)
    problems = check_case_list(cases, int(fleet["osm_id"].nunique()), cells)
    print("cells", cells)
    print("rows", len(cases), "buildings", fleet["osm_id"].nunique())
    print("rows per wave", cases.groupby("wave").size().to_dict())
    print("sources", cases["source"].value_counts().to_dict())
    if problems:
        raise SystemExit("STOP: " + "; ".join(problems))
    cases.to_csv(OUT_CSV, index=False)
    print("wrote", OUT_CSV)


if __name__ == "__main__":
    main()
