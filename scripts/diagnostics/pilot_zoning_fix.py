"""Pilot resim: prove zoning multi-floor fix for ~50 affected la_urban buildings.

Usage:
    py -3 scripts/diagnostics/pilot_zoning_fix.py

Outputs to runtime/zoning_pilot/:
  - idfs/           regenerated IDFs for pilot subset
  - sim_out/        EnergyPlus outputs
  - pilot_results.csv  per-building EUI comparison
Read-only against r7_service_loads.csv (never overwrites).
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

PILOT_DIR   = REPO / "runtime" / "zoning_pilot"
IDF_DIR     = PILOT_DIR / "idfs"
SIM_DIR     = PILOT_DIR / "sim_out"
R7_PATH     = REPO / "docs" / "validations" / "overAll" / "results" / "r7_service_loads.csv"
GDF_PATH    = REPO / "runtime" / "ubem_validation" / "cases" / "la_urban" / "01_buildings.gpkg"
CZ_PATH     = REPO / "runtime" / "ubem_validation" / "cases" / "la_urban" / "02a_climate_epw.parquet"
EPW_PATH    = (
    REPO / "runtime" / "ubem_validation" / "cases" / "la_urban"
    / "weather" / "weather"
    / "USA_CA_Los.Angeles.Downtown-USC.Campus.722874_TMYx.2011-2025.epw"
)
EP_EXE      = Path(r"C:\EnergyPlusV23-1-0\energyplus.exe")

PILOT_ARCHETYPES = {"MidriseApartment", "MediumOffice", "SmallOffice", "RetailStandalone"}
LEVELS_TIERS = [2, 3, 4, 5, 6, 7]
PER_LEVEL_CAPS = {"MidriseApartment": 4, "MediumOffice": 3, "SmallOffice": 3, "RetailStandalone": 3}


def select_pilot(r7: pd.DataFrame) -> pd.DataFrame:
    la = r7[
        (r7["cell"] == "la_urban")
        & (r7["simulation_status"] == "success")
        & (r7["footprint_area_m2"] < 500)
        & (r7["levels"] > 1)
        & (r7["archetype_id"].isin(PILOT_ARCHETYPES))
    ].copy()

    parts = []
    for arch, cap in PER_LEVEL_CAPS.items():
        sub = la[la["archetype_id"] == arch].sort_values("levels")
        for lv in LEVELS_TIERS:
            parts.append(sub[sub["levels"] == lv].head(cap))
    return pd.concat(parts).drop_duplicates("osm_id").reset_index(drop=True)


def run_step2_for_pilot(pilot_oids: list[str], raw_gdf: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    """Re-run Step 2 for the pilot buildings to get enriched GDF with wwr etc.
    Uses cached climate sidecar (02a_climate_epw.parquet) to skip climate zone API call."""
    import pandas as pd
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    climate_sidecar = pd.read_parquet(str(CZ_PATH))

    pilot_raw = raw_gdf[raw_gdf["osm_id"].isin(pilot_oids)].copy()
    print(f"  pilot buildings in raw GDF: {len(pilot_raw)}")

    bc = BuildingClassifier()
    pilot_input = pilot_raw[_INPUT_SCHEMA_COLUMNS].copy()
    pilot_input["levels"] = pilot_input["levels"].astype("Int64")
    gdf_26 = bc.classify(pilot_input)

    cz_map = dict(zip(climate_sidecar["osm_id"], climate_sidecar["climate_zone"]))
    prov_map = dict(zip(climate_sidecar["osm_id"], climate_sidecar["provenance_climate_zone"]))
    gdf_26["climate_zone"] = pd.Categorical(gdf_26["osm_id"].map(cz_map), categories=list(_CLIMATE_ZONE_VOCAB))
    gdf_26["epw_path"] = str(EPW_PATH)
    gdf_26["provenance_climate_zone"] = pd.Categorical(
        gdf_26["osm_id"].map(prov_map), categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )

    gdf_57, schedule_library = enrich_semantics(gdf_26)
    return gdf_57, schedule_library


def regenerate_idfs(enriched_gdf: gpd.GeoDataFrame, schedule_library: dict,
                    full_gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    from openubem.idf.builder import run_step3

    IDF_DIR.mkdir(parents=True, exist_ok=True)
    print(f"  Generating {len(enriched_gdf)} IDFs ...")
    manifest = run_step3(enriched_gdf, schedule_library, PILOT_DIR, n_jobs=4)
    print(f"  Generated: {(manifest['generation_status']=='success').sum()}/{len(manifest)}")
    return manifest


def verify_zone_names(idf_path: Path, expected_floors: int) -> tuple[bool, list[str]]:
    """Check IDF has expected number of floor zones named _F{i}_."""
    import re
    text = idf_path.read_text(encoding="utf-8", errors="replace")
    zone_rx = re.compile(r"_F(\d+)_WHOLE", re.IGNORECASE)
    floors_found = set(int(m.group(1)) for m in zone_rx.finditer(text))
    ok = len(floors_found) == expected_floors
    return ok, sorted(floors_found)


EP_IDD = EP_EXE.parent / "Energy+.idd"


def run_energyplus_local(idf_path: Path, epw: Path, work_dir: Path) -> bool:
    work_dir.mkdir(parents=True, exist_ok=True)
    # Copy IDD to work_dir (required when cwd != EP install dir)
    idd_dest = work_dir / "Energy+.idd"
    if not idd_dest.exists():
        shutil.copy2(EP_IDD, idd_dest)
    cmd = [
        str(EP_EXE),
        "-w", str(epw),
        "-d", str(work_dir),
        "-x",   # ExpandObjects — required for HVACTemplate objects (DESIGN §3C)
        "-r",   # readVarsESO → eplusout.csv
        str(idf_path),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=600, cwd=str(work_dir))
    end_file = work_dir / "eplusout.end"
    if not end_file.exists():
        return False
    return "EnergyPlus Completed Successfully" in end_file.read_text(errors="replace")


def parse_sql_eui(sql_path: Path, osm_id: str, footprint_area_m2: float,
                  num_floors: int) -> dict | None:
    J_TO_KWH = 1.0 / 3.6e6
    floor_area = footprint_area_m2 * num_floors

    mapping = {
        "Zone Ideal Loads Zone Total Heating Energy": "heating_eui_kwh_m2",
        "Zone Ideal Loads Zone Total Cooling Energy": "cooling_eui_kwh_m2",
        "Zone Lights Electricity Energy": "lighting_eui_kwh_m2",
        "Zone Electric Equipment Electricity Energy": "equipment_eui_kwh_m2",
    }
    var_list = "','".join(mapping.keys())

    try:
        with sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True) as conn:
            rows = conn.execute(
                f"""SELECT d.Name, SUM(r.Value) as total_j
                    FROM ReportData r
                    JOIN ReportDataDictionary d
                      ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
                    WHERE d.ReportingFrequency='Hourly'
                      AND d.Units='J'
                      AND d.Name IN ('{var_list}')
                    GROUP BY d.Name"""
            ).fetchall()
    except Exception as e:
        print(f"  SQL error for {osm_id}: {e}")
        return None

    if not rows:
        print(f"  No hourly J data for {osm_id}")
        return None

    totals: dict[str, float] = {name: val * J_TO_KWH for name, val in rows}

    result = {}
    for ep_var, col in mapping.items():
        total_kwh = totals.get(ep_var, 0.0)
        result[col] = total_kwh / floor_area if floor_area > 0 else 0.0

    result["total_eui_kwh_m2"] = sum(result.values())
    return result


def main():
    print("=" * 72)
    print("PILOT ZONING FIX: IDF regeneration + local E+ resim")
    print("=" * 72)

    assert EPW_PATH.exists(), f"EPW not found: {EPW_PATH}"
    assert EP_EXE.exists(), f"EnergyPlus not found: {EP_EXE}"

    print("\n[1] Loading data ...")
    r7 = pd.read_csv(R7_PATH)
    raw_gdf = gpd.read_file(str(GDF_PATH))
    pilot_r7 = select_pilot(r7)
    print(f"  Pilot subset: {len(pilot_r7)} buildings")
    print(f"  Archetype counts:\n{pilot_r7['archetype_id'].value_counts().to_string()}")
    print(f"  Levels counts:\n{pilot_r7['levels'].value_counts().sort_index().to_string()}")

    pilot_r7.to_csv(PILOT_DIR / "pilot_subset_definition.csv", index=False)

    pilot_oids = list(pilot_r7["osm_id"].astype(str))

    print("\n[2] Re-running Step 2 for pilot buildings (classify + enrich) ...")
    enriched_gdf, schedule_library = run_step2_for_pilot(pilot_oids, raw_gdf)
    print(f"  Enriched GDF: {len(enriched_gdf)} rows, CRS={enriched_gdf.crs}")
    print(f"  wwr sample: {list(enriched_gdf['wwr'].head(3))}")

    # Merge r7 osm_id → archetype_id to also update pilot_r7 with Step-2 archetype
    arch_map = dict(zip(enriched_gdf["osm_id"].astype(str), enriched_gdf["archetype_id"]))
    pilot_r7["archetype_id_step2"] = pilot_r7["osm_id"].astype(str).map(arch_map)
    pilot_r7.to_csv(PILOT_DIR / "pilot_subset_definition.csv", index=False)

    print("\n[3] Regenerating IDFs with patched zoning ...")
    manifest = regenerate_idfs(enriched_gdf, schedule_library, raw_gdf)

    success_mask = manifest["generation_status"] == "success"
    print(f"  Generation success: {success_mask.sum()}/{len(manifest)}")
    print(f"  Zoning strategy counts: {manifest['zoning_strategy'].value_counts().to_dict()}")

    print("\n  [3b] Verifying zone names in IDFs ...")
    zone_check_rows = []
    for _, mrow in manifest[success_mask].iterrows():
        oid = str(mrow["osm_id"])
        idf_path = Path(str(mrow["idf_path"]))
        r7_row = pilot_r7[pilot_r7["osm_id"] == oid]
        if len(r7_row) == 0:
            continue
        expected_floors = int(r7_row.iloc[0]["levels"])
        strategy = str(mrow["zoning_strategy"])
        if strategy == "one_zone_per_floor":
            ok, floors_found = verify_zone_names(idf_path, expected_floors)
            zone_check_rows.append({
                "osm_id": oid,
                "expected_floors": expected_floors,
                "floors_found": len(floors_found),
                "ok": ok,
            })
        elif strategy == "single_zone":
            zone_check_rows.append({
                "osm_id": oid,
                "expected_floors": expected_floors,
                "floors_found": 1,
                "ok": False,
                "note": "still single_zone — check archetype routing",
            })

    zdf = pd.DataFrame(zone_check_rows)
    if len(zdf) > 0:
        print(f"  Zone check: {zdf['ok'].sum()}/{len(zdf)} IDFs have correct floor count")
        fails = zdf[~zdf["ok"]]
        if len(fails) > 0:
            print(f"  Zone check failures:")
            print(fails.to_string())
    else:
        print("  No zone check rows generated")

    print("\n[4] Running EnergyPlus locally ...")
    sim_results = []
    n_success = 0
    n_fail = 0
    for i, (_, mrow) in enumerate(manifest[success_mask].iterrows()):
        oid = str(mrow["osm_id"])
        idf_path = Path(str(mrow["idf_path"]))
        safe_oid = oid.replace("/", "_")
        work_dir = SIM_DIR / safe_oid

        print(f"  [{i+1}/{success_mask.sum()}] {oid} ...", end=" ", flush=True)
        ok = run_energyplus_local(idf_path, EPW_PATH, work_dir)
        if ok:
            n_success += 1
            print("OK")
        else:
            n_fail += 1
            print("FAIL")
            end_f = work_dir / "eplusout.end"
            if end_f.exists():
                print(f"    end: {end_f.read_text()[:200]}")

        sim_results.append({
            "osm_id": oid,
            "sim_status": "success" if ok else "failed",
            "sql_path": str(work_dir / "eplusout.sql") if ok else "",
        })

    sim_df = pd.DataFrame(sim_results)
    print(f"\n  E+ simulation: {n_success}/{len(sim_results)} success, {n_fail} failed")

    # Build lookup maps from enriched_gdf (Step-2) for levels/footprint/archetype
    enrich_map = {str(r["osm_id"]): r for _, r in enriched_gdf.iterrows()}

    print("\n[5] Parsing SQL and comparing before/after EUI ...")
    comparison_rows = []
    for _, srow in sim_df[sim_df["sim_status"] == "success"].iterrows():
        oid = str(srow["osm_id"])
        sql_path = Path(srow["sql_path"])
        r7_row = pilot_r7[pilot_r7["osm_id"] == oid]
        if len(r7_row) == 0:
            continue
        r7_r = r7_row.iloc[0]
        # Use enriched_gdf for levels/footprint/archetype (canonical post-Step-2 values)
        enriched_row = enrich_map.get(oid)
        if enriched_row is not None:
            footprint = float(enriched_row["footprint_area_m2"])
            levels = int(enriched_row["levels"])
            archetype = str(enriched_row["archetype_id"])
        else:
            footprint = float(r7_r["footprint_area_m2"])
            levels = int(r7_r["levels"])
            archetype = str(r7_r["archetype_id"])

        new_eui = parse_sql_eui(sql_path, oid, footprint, levels)
        if new_eui is None:
            continue

        comparison_rows.append({
            "osm_id": oid,
            "archetype_id": archetype,
            "levels": levels,
            "footprint_area_m2": footprint,
            # Before (old single_zone sim from r7)
            "old_lighting_eui": r7_r["lighting_eui_kwh_m2"],
            "old_equipment_eui": r7_r["equipment_eui_kwh_m2"],
            "old_heating_eui": r7_r["heating_eui_kwh_m2"],
            "old_cooling_eui": r7_r["cooling_eui_kwh_m2"],
            "old_total_eui": r7_r["total_eui_kwh_m2"],
            # After (new one_zone_per_floor)
            "new_lighting_eui": new_eui["lighting_eui_kwh_m2"],
            "new_equipment_eui": new_eui["equipment_eui_kwh_m2"],
            "new_heating_eui": new_eui["heating_eui_kwh_m2"],
            "new_cooling_eui": new_eui["cooling_eui_kwh_m2"],
            "new_total_eui": new_eui["total_eui_kwh_m2"],
        })

    cdf = pd.DataFrame(comparison_rows)
    if len(cdf) == 0:
        print("  ERROR: no comparison rows — all parses failed")
        sys.exit(1)

    # Derived columns
    cdf["lighting_ratio"] = cdf["new_lighting_eui"] / cdf["old_lighting_eui"].replace(0, float("nan"))
    cdf["expected_ratio"] = cdf["levels"].astype(float)
    cdf["ratio_vs_expected"] = cdf["lighting_ratio"] / cdf["expected_ratio"]

    cdf.to_csv(PILOT_DIR / "pilot_results.csv", index=False)
    print(f"  Comparison rows: {len(cdf)}")
    print(f"  Saved: {PILOT_DIR / 'pilot_results.csv'}")

    print("\n[6] Summary statistics ...")
    print("\n  Per-archetype median EUI (before vs after):")
    for arch in cdf["archetype_id"].unique():
        sub = cdf[cdf["archetype_id"] == arch]
        print(f"\n  {arch} (n={len(sub)}):")
        print(f"    OLD lighting median: {sub['old_lighting_eui'].median():.2f} kWh/m2")
        print(f"    NEW lighting median: {sub['new_lighting_eui'].median():.2f} kWh/m2")
        print(f"    OLD total median:    {sub['old_total_eui'].median():.2f} kWh/m2")
        print(f"    NEW total median:    {sub['new_total_eui'].median():.2f} kWh/m2")
        print(f"    lighting_ratio median (new/old): {sub['lighting_ratio'].median():.3f}")
        print(f"    expected ratio (= levels): {sub['levels'].median():.1f}")

    print("\n  Lighting-vs-levels check (new_lighting / expected_value_for_1floor):")
    check = cdf.groupby("levels")["new_lighting_eui"].agg(["median", "std", "count"]).rename(
        columns={"median": "new_lighting_median", "std": "new_lighting_std", "count": "n"}
    )
    print(check.to_string())

    print("\n  Old lighting × levels (should be constant if bug present):")
    cdf["old_lit_times_levels"] = cdf["old_lighting_eui"] * cdf["levels"]
    old_check = cdf.groupby("levels")["old_lit_times_levels"].agg(["median", "std"])
    print(old_check.to_string())

    print("\n  New lighting × levels (should vary if bug is fixed):")
    cdf["new_lit_times_levels"] = cdf["new_lighting_eui"] * cdf["levels"]
    new_check = cdf.groupby("levels")["new_lit_times_levels"].agg(["median", "std"])
    print(new_check.to_string())

    print(f"\n  Zoning strategy in new manifest: {manifest['zoning_strategy'].value_counts().to_dict()}")

    print("\n[7] GO / NO-GO assessment ...")
    old_constant = cdf["old_lit_times_levels"].std() / cdf["old_lit_times_levels"].mean()
    new_range = cdf["new_lighting_eui"].std() / cdf["new_lighting_eui"].mean()
    print(f"  Old lighting × levels CV: {old_constant:.3f} (low = was constant = bug confirmed)")
    print(f"  New lighting EUI CV: {new_range:.3f} (natural building-level variation)")

    lighting_rose = (cdf["new_lighting_eui"] > cdf["old_lighting_eui"]).mean()
    print(f"  Fraction of buildings where lighting EUI rose: {lighting_rose:.2%}")

    all_single_zone = (manifest[success_mask]["zoning_strategy"] == "one_zone_per_floor").all()
    print(f"  All affected buildings now one_zone_per_floor: {all_single_zone}")

    sim_pass_rate = n_success / len(sim_results) if sim_results else 0.0
    print(f"  Sim pass rate: {sim_pass_rate:.1%}")

    go = (
        lighting_rose > 0.90
        and sim_pass_rate >= 0.95
        and all_single_zone
    )
    print(f"\n  VERDICT: {'GO' if go else 'NO-GO'}")

    return cdf, manifest


if __name__ == "__main__":
    main()
