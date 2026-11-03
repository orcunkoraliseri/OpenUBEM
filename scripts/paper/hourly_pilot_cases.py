from __future__ import annotations

import ntpath
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CMP = ROOT / "openubem" / "outputs" / "comparisons"
FLEET_CSV = CMP / "paper_adopted_fleet_per_building_2026-10-21.csv"
DHW_CSV = CMP / "paper_adopted_fleet_dhw-fix_per_building_2026-10-21.csv"
OUT_CSV = CMP / "paper_hourly_pilot_case_list_2026-10-21.csv"
PHASE_E = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"

SPEED_FLEETS = "/speed-scratch/o_iseri/openubem/fleets"
REMOTE_DIR = {
    "base": "t07_resim_2026-09-09",
    "open35": "open35_resim_2026-09-30_full",
    "open38": "open38_fix_rerun_2026-09-30_full",
}
MIN_BUILDINGS = 50

REFERENCE_COLUMNS = {
    "ref_heating_kwh": "heating_eui_kwh_m2 x floor_area_m2",
    "ref_cooling_kwh": "cooling_eui_kwh_m2 x floor_area_m2",
    "ref_district_hot_water_kwh": "dhw_district_removed_eui_kwh_m2 (dhw-fix table, = dhw_district_eui_kwh_m2) x floor_area_m2",
    "ref_electricity_gas_kwh": "total_kwh - ref_district_hot_water_kwh",
}
END_USE_COLUMNS = (
    "heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2", "equipment_eui_kwh_m2",
    "fans_eui_kwh_m2", "pumps_eui_kwh_m2", "dhw_eui_kwh_m2", "cooking_eui_kwh_m2",
    "refrigeration_eui_kwh_m2",
)


def stem_of(osm_id: str) -> str:
    return osm_id.replace("/", "_", 1)


def remote_idf_path(source: str, cell: str, osm_id: str) -> str:
    stem = stem_of(osm_id)
    name = stem if source == "base" else f"auto__{cell}__{stem}"
    return f"{SPEED_FLEETS}/{REMOTE_DIR[source]}/idfs/{name}.idf"


def epw_by_cell(phase_e: Path = PHASE_E) -> dict[str, str]:
    out = {}
    for d in sorted(p for p in phase_e.iterdir() if p.is_dir()):
        manifest = pd.read_parquet(d / "04_simulation_manifest.parquet", columns=["epw_path"])
        names = {ntpath.basename(str(x)) for x in manifest["epw_path"].dropna().unique()}
        if len(names) != 1:
            raise SystemExit(f"STOP: {d.name} has {len(names)} weather files in its manifest: {sorted(names)}")
        out[d.name] = names.pop()
    return out


def pooled_eui(frame: pd.DataFrame) -> float:
    return float(frame["total_kwh"].sum() / frame["floor_area_m2"].sum())


def pick_cell(fleet: pd.DataFrame, city: str, min_buildings: int = MIN_BUILDINGS) -> dict:
    sub = fleet[fleet["city"] == city]
    city_eui = pooled_eui(sub)
    rows = []
    for cell, g in sub.groupby("cell"):
        if len(g) < min_buildings:
            continue
        eui = pooled_eui(g)
        rows.append({"city": city, "cell": cell, "buildings": len(g), "cell_eui": eui,
                     "city_eui": city_eui, "gap": abs(eui - city_eui)})
    if not rows:
        raise SystemExit(f"STOP: no cell of {city} has {min_buildings} buildings")
    rows.sort(key=lambda r: (r["gap"], r["buildings"]))
    return rows[0]


def build_case_list(fleet: pd.DataFrame, dhw: pd.DataFrame, epws: dict[str, str]) -> tuple[pd.DataFrame, list[dict]]:
    picks = [pick_cell(fleet, city) for city in sorted(fleet["city"].unique())]
    cells = [p["cell"] for p in picks]
    sel = fleet[fleet["cell"].isin(cells)].merge(
        dhw[["osm_id", "dhw_district_removed_eui_kwh_m2"]], on="osm_id", how="left", validate="one_to_one")
    sel = sel.sort_values(["city", "cell", "osm_id"]).reset_index(drop=True)
    area = sel["floor_area_m2"]
    out = pd.DataFrame({
        "city": sel["city"],
        "cell": sel["cell"],
        "osm_id": sel["osm_id"],
        "stem": sel["osm_id"].map(stem_of),
        "source": sel["source"],
        "idf_path": [remote_idf_path(s, c, o) for s, c, o in zip(sel["source"], sel["cell"], sel["osm_id"])],
        "epw_name": sel["cell"].map(epws),
        "floor_area_m2": area,
        "ref_heating_kwh": sel["heating_eui_kwh_m2"] * area,
        "ref_cooling_kwh": sel["cooling_eui_kwh_m2"] * area,
        "ref_district_hot_water_kwh": sel["dhw_district_removed_eui_kwh_m2"] * area,
    })
    out["ref_electricity_gas_kwh"] = sel["total_kwh"] - out["ref_district_hot_water_kwh"]
    out.insert(0, "task", range(1, len(out) + 1))
    return out, picks


def check_case_list(cases: pd.DataFrame, fleet: pd.DataFrame, picks: list[dict]) -> list[str]:
    problems = []
    expected = int(sum(p["buildings"] for p in picks))
    if len(cases) != expected:
        problems.append(f"rows {len(cases)} != buildings of the chosen cells {expected}")
    if not cases["stem"].is_unique:
        problems.append("stem not unique")
    if not cases["idf_path"].is_unique:
        problems.append("idf_path not unique")
    if cases[list(REFERENCE_COLUMNS) + ["epw_name", "floor_area_m2"]].isna().any().any():
        problems.append("null in a reference, epw_name or floor_area column")
    return problems


def main() -> None:
    fleet = pd.read_csv(FLEET_CSV)
    dhw = pd.read_csv(DHW_CSV)
    epws = epw_by_cell()
    cases, picks = build_case_list(fleet, dhw, epws)
    for p in picks:
        print(f"{p['city']}: cell {p['cell']}, buildings {p['buildings']}, "
              f"cell EUI {p['cell_eui']:.3f} vs city EUI {p['city_eui']:.3f} kWh/m2 (gap {p['gap']:.3f})")
    print("rows", len(cases), cases["source"].value_counts().to_dict())
    print("epw", cases.groupby("cell")["epw_name"].first().to_dict())
    problems = check_case_list(cases, fleet, picks)
    sel = fleet[fleet["osm_id"].isin(cases["osm_id"])]
    parts = sum(sel[c] for c in END_USE_COLUMNS) * sel["floor_area_m2"]
    gap = (sel["total_kwh"] - parts).abs()
    print(f"total_kwh minus nine end uses: max abs {gap.max():.3f} kWh, "
          f"max relative {(gap / sel['total_kwh']).max():.2e}")
    if problems:
        raise SystemExit("STOP: " + "; ".join(problems))
    cases.to_csv(OUT_CSV, index=False)
    print("wrote", OUT_CSV)


if __name__ == "__main__":
    main()
