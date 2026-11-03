from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CMP = ROOT / "openubem" / "outputs" / "comparisons"
FLEET_CSV = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"
BASE_CSV = CMP / "open65_reparse_fleet_eui_2026-09-29.csv"
OUT_CSV = CMP / "paper_hourly_case_list_2026-10-21.csv"

SPEED_FLEETS = "/speed-scratch/o_iseri/openubem/fleets"
REMOTE_OUT_DIR = {
    "base": "t07_resim_2026-09-09",
    "open35": "open35_resim_2026-09-30_full",
    "open38": "open38_fix_rerun_2026-09-30_full",
}
EXPECTED = 8139


def stem_of(osm_id: str) -> str:
    return osm_id.replace("/", "_", 1)


def remote_sql_path(source: str, cell: str, osm_id: str) -> str:
    stem = stem_of(osm_id)
    folder = stem if source == "base" else f"auto__{cell}__{stem}"
    return f"{SPEED_FLEETS}/{REMOTE_OUT_DIR[source]}/out/{folder}/eplusout.sql"


def build_case_list(fleet: pd.DataFrame) -> pd.DataFrame:
    cases = fleet[["cell", "osm_id", "source"]].copy()
    cases = cases.sort_values(["cell", "osm_id"]).reset_index(drop=True)
    cases["stem"] = cases["osm_id"].map(stem_of)
    cases["sql_path"] = [remote_sql_path(s, c, o)
                         for s, c, o in zip(cases["source"], cases["cell"], cases["osm_id"])]
    cases.insert(0, "task", range(1, len(cases) + 1))
    return cases


def main() -> None:
    fleet = pd.read_csv(FLEET_CSV)
    cases = build_case_list(fleet)
    base = pd.read_csv(BASE_CSV, usecols=["stem", "osm_id"]).set_index("osm_id")["stem"]
    on_base = cases[cases["source"] == "base"]
    mismatch = (on_base["osm_id"].map(base) != on_base["stem"]).sum()
    print("rows", len(cases), "unique sql_path", cases["sql_path"].is_unique)
    print(cases["source"].value_counts().to_dict())
    print("base stem mismatches vs open65 table", int(mismatch))
    if len(cases) != EXPECTED or not cases["sql_path"].is_unique or mismatch:
        raise SystemExit("STOP: case list does not match the adopted fleet")
    cases.to_csv(OUT_CSV, index=False)
    print("wrote", OUT_CSV)


if __name__ == "__main__":
    main()
