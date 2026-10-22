from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CMP = ROOT / "openubem" / "outputs" / "comparisons"
BASE_CSV = CMP / "open65_reparse_fleet_eui_2026-09-29.csv"
OPEN35_CSV = CMP / "open35_resim_fleet_eui_2026-09-30.csv"
OPEN38_CSV = CMP / "open38_fix_rerun_2026-09-30.csv"
SUMMARY_JSON = CMP / "open38_fix_summary_2026-09-30.json"
OUT_CSV = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"

ENDUSES = [
    "heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2",
    "equipment_eui_kwh_m2", "fans_eui_kwh_m2", "pumps_eui_kwh_m2",
    "dhw_eui_kwh_m2", "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2",
]
KEEP = ["cell", "city", "osm_id", "archetype_id", "parse_status", "floor_area_m2",
        "total_kwh", "total_eui_kwh_m2", "gwp_total_kgco2"] + ENDUSES + ["data_quality_flag"]


def _prep(df: pd.DataFrame, source: str, keep: list[str] | None = None) -> pd.DataFrame:
    out = df.copy()
    if "city" not in out.columns:
        out["city"] = out["cell"].str.split("_", n=1).str[0]
    if "total_kwh" not in out.columns:
        out["total_kwh"] = out["total_eui_kwh_m2"] * out["floor_area_m2"]
    out["source"] = source
    return out[(keep or KEEP) + ["source"]]


def apply_overlays(base: pd.DataFrame, open35_targets: pd.DataFrame, open38_cooking: pd.DataFrame,
                   keep: list[str] | None = None) -> pd.DataFrame:
    fleet = _prep(base, "base", keep)
    t35 = _prep(open35_targets, "open35", keep)
    fleet = pd.concat([fleet[~fleet["osm_id"].isin(t35["osm_id"])], t35], ignore_index=True)
    c38 = _prep(open38_cooking, "open38", keep)
    fleet = pd.concat([fleet[~fleet["osm_id"].isin(c38["osm_id"])], c38], ignore_index=True)
    return fleet


def select_open35(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["role"] == "target") & (df["parse_status"] == "success")]


def select_open38(df: pd.DataFrame) -> pd.DataFrame:
    ok = df["parse_status"].eq("success") & df["terminal"].eq("completed")
    return df[ok & df["group"].str.contains("cooking") & (df["mode"] == "auto")]


def pooled(fleet: pd.DataFrame) -> tuple[float, float]:
    return (float(fleet["total_kwh"].sum() / fleet["floor_area_m2"].sum()),
            float(fleet["gwp_total_kgco2"].sum() / 1000.0))


def main() -> None:
    base = pd.read_csv(BASE_CSV)
    t35 = select_open35(pd.read_csv(OPEN35_CSV))
    c38 = select_open38(pd.read_csv(OPEN38_CSV))
    fleet = apply_overlays(base, t35, c38)
    fleet = fleet.sort_values(["cell", "osm_id"]).reset_index(drop=True)
    fleet.to_csv(OUT_CSV, index=False)
    eui, carbon = pooled(fleet)
    ref = json.loads(SUMMARY_JSON.read_text())
    print("rows", len(fleet), "unique", fleet["osm_id"].is_unique)
    print("sources", fleet["source"].value_counts().to_dict())
    print("pooled_eui", round(eui, 4), "ref", ref["pooled_eui_c2"])
    print("carbon_t", round(carbon, 2), "ref", ref["carbon_t_c2"])
    print("overlay rows: open35", len(t35), "open38", len(c38))


if __name__ == "__main__":
    main()
