"""Complete the pilot resim: simulate the 11 remaining buildings, then run full analysis.

Picks up where pilot_zoning_fix.py left off.
Outputs pilot_results.csv + final GO/NO-GO summary.
"""
from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

PILOT_DIR = REPO / "runtime" / "zoning_pilot"
IDF_DIR   = PILOT_DIR / "idfs"
SIM_DIR   = PILOT_DIR / "sim_out"
R7_PATH   = REPO / "docs" / "validations" / "overAll" / "results" / "r7_service_loads.csv"
GDF_PATH  = REPO / "runtime" / "ubem_validation" / "cases" / "la_urban" / "01_buildings.gpkg"
CZ_PATH   = REPO / "runtime" / "ubem_validation" / "cases" / "la_urban" / "02a_climate_epw.parquet"
EPW_PATH  = (
    REPO / "runtime" / "ubem_validation" / "cases" / "la_urban"
    / "weather" / "weather"
    / "USA_CA_Los.Angeles.Downtown-USC.Campus.722874_TMYx.2011-2025.epw"
)
EP_EXE  = Path(r"C:\EnergyPlusV23-1-0\energyplus.exe")
EP_IDD  = EP_EXE.parent / "Energy+.idd"

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


def run_step2_for_pilot(pilot_oids: list[str], raw_gdf: gpd.GeoDataFrame):
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    climate_sidecar = pd.read_parquet(str(CZ_PATH))
    pilot_raw = raw_gdf[raw_gdf["osm_id"].isin(pilot_oids)].copy()
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


def run_energyplus_local(idf_path: Path, epw: Path, work_dir: Path) -> bool:
    work_dir.mkdir(parents=True, exist_ok=True)
    idd_dest = work_dir / "Energy+.idd"
    if not idd_dest.exists():
        shutil.copy2(EP_IDD, idd_dest)
    cmd = [
        str(EP_EXE), "-w", str(epw), "-d", str(work_dir), "-x", "-r", str(idf_path),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=600, cwd=str(work_dir))
    end_file = work_dir / "eplusout.end"
    if not end_file.exists():
        return False
    return "EnergyPlus Completed Successfully" in end_file.read_text(errors="replace")


def parse_sql_eui(sql_path: Path, osm_id: str, footprint_area_m2: float, num_floors: int) -> dict | None:
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
                    JOIN ReportDataDictionary d ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex
                    WHERE d.ReportingFrequency='Hourly' AND d.Units='J'
                      AND d.Name IN ('{var_list}')
                    GROUP BY d.Name"""
            ).fetchall()
    except Exception as e:
        print(f"  SQL error for {osm_id}: {e}")
        return None
    if not rows:
        return None
    totals = {name: val * J_TO_KWH for name, val in rows}
    result = {}
    for ep_var, col in mapping.items():
        total_kwh = totals.get(ep_var, 0.0)
        result[col] = total_kwh / floor_area if floor_area > 0 else 0.0
    result["total_eui_kwh_m2"] = sum(result.values())
    return result


def main():
    print("=" * 72)
    print("PILOT COMPLETION: simulate remaining 11 buildings + full analysis")
    print("=" * 72)

    assert EPW_PATH.exists(), f"EPW not found: {EPW_PATH}"
    assert EP_EXE.exists(), f"EnergyPlus not found: {EP_EXE}"

    # Load subset definition and manifest from previous run
    r7 = pd.read_csv(R7_PATH)
    raw_gdf = gpd.read_file(str(GDF_PATH))
    pilot_r7 = select_pilot(r7)
    print(f"  Pilot subset: {len(pilot_r7)} buildings")

    # Load manifest from previous IDF generation
    manifest_path = PILOT_DIR / "03_idf_manifest.parquet"
    manifest = pd.read_parquet(str(manifest_path))
    print(f"  Manifest loaded: {len(manifest)} rows, strategies: {manifest['zoning_strategy'].value_counts().to_dict()}")

    # Find missing simulations
    done_dirs = {d.name for d in SIM_DIR.iterdir() if d.is_dir()}
    def to_dir_name(osm_id):
        return str(osm_id).replace("/", "_")

    missing_mask = ~manifest["osm_id"].astype(str).apply(to_dir_name).isin(done_dirs)
    missing = manifest[missing_mask & (manifest["generation_status"] == "success")]
    already_done = manifest[~missing_mask & (manifest["generation_status"] == "success")]
    print(f"  Already simulated: {len(already_done)}, still needed: {len(missing)}")

    # Re-run Step 2 for missing buildings to get enriched attributes
    if len(missing) > 0:
        print(f"\n[2] Re-running Step 2 for {len(missing)} missing buildings ...")
        missing_oids = list(missing["osm_id"].astype(str))
        enriched_gdf, schedule_library = run_step2_for_pilot(list(pilot_r7["osm_id"].astype(str)), raw_gdf)
    else:
        print("\n[2] All buildings already simulated. Re-running Step 2 for full analysis ...")
        enriched_gdf, schedule_library = run_step2_for_pilot(list(pilot_r7["osm_id"].astype(str)), raw_gdf)

    enrich_map = {str(r["osm_id"]): r for _, r in enriched_gdf.iterrows()}

    # Simulate missing buildings
    if len(missing) > 0:
        print(f"\n[4] Simulating {len(missing)} remaining buildings ...")
        n_new_success = 0
        for i, (_, mrow) in enumerate(missing.iterrows()):
            oid = str(mrow["osm_id"])
            idf_path = Path(str(mrow["idf_path"]))
            safe_oid = oid.replace("/", "_")
            work_dir = SIM_DIR / safe_oid
            print(f"  [{i+1}/{len(missing)}] {oid} ...", end=" ", flush=True)
            ok = run_energyplus_local(idf_path, EPW_PATH, work_dir)
            if ok:
                n_new_success += 1
                print("OK")
            else:
                print("FAIL")
                end_f = work_dir / "eplusout.end"
                if end_f.exists():
                    print(f"    end: {end_f.read_text()[:200]}")
        print(f"  New sims: {n_new_success}/{len(missing)} success")

    # Now analyze ALL 47
    print("\n[5] Parsing SQL for all 47 buildings ...")
    success_mask = manifest["generation_status"] == "success"
    comparison_rows = []
    n_parsed = 0
    n_missing_sql = 0

    for _, mrow in manifest[success_mask].iterrows():
        oid = str(mrow["osm_id"])
        safe_oid = oid.replace("/", "_")
        work_dir = SIM_DIR / safe_oid
        sql_path = work_dir / "eplusout.sql"

        r7_rows = pilot_r7[pilot_r7["osm_id"] == oid]
        if len(r7_rows) == 0:
            continue

        r7_r = r7_rows.iloc[0]
        enriched_row = enrich_map.get(oid)
        if enriched_row is not None:
            footprint = float(enriched_row["footprint_area_m2"])
            lv_raw = enriched_row["levels"]
            levels = int(r7_r["levels"]) if pd.isna(lv_raw) else int(lv_raw)
            archetype = str(enriched_row["archetype_id"])
        else:
            footprint = float(r7_r["footprint_area_m2"])
            levels = int(r7_r["levels"])
            archetype = str(r7_r["archetype_id"])

        if not sql_path.exists():
            n_missing_sql += 1
            continue

        new_eui = parse_sql_eui(sql_path, oid, footprint, levels)
        if new_eui is None:
            n_missing_sql += 1
            continue

        comparison_rows.append({
            "osm_id": oid,
            "archetype_id": archetype,
            "levels": levels,
            "footprint_area_m2": footprint,
            "old_lighting_eui": r7_r["lighting_eui_kwh_m2"],
            "old_equipment_eui": r7_r["equipment_eui_kwh_m2"],
            "old_heating_eui": r7_r["heating_eui_kwh_m2"],
            "old_cooling_eui": r7_r["cooling_eui_kwh_m2"],
            "old_total_eui": r7_r["total_eui_kwh_m2"],
            "new_lighting_eui": new_eui["lighting_eui_kwh_m2"],
            "new_equipment_eui": new_eui["equipment_eui_kwh_m2"],
            "new_heating_eui": new_eui["heating_eui_kwh_m2"],
            "new_cooling_eui": new_eui["cooling_eui_kwh_m2"],
            "new_total_eui": new_eui["total_eui_kwh_m2"],
        })
        n_parsed += 1

    print(f"  Parsed: {n_parsed}, missing SQL: {n_missing_sql}")

    cdf = pd.DataFrame(comparison_rows)
    if len(cdf) == 0:
        print("ERROR: no comparison rows")
        sys.exit(1)

    cdf["lighting_ratio"] = cdf["new_lighting_eui"] / cdf["old_lighting_eui"].replace(0, float("nan"))
    cdf["expected_ratio"] = cdf["levels"].astype(float)
    cdf["ratio_vs_expected"] = cdf["lighting_ratio"] / cdf["expected_ratio"]

    cdf.to_csv(PILOT_DIR / "pilot_results.csv", index=False)
    print(f"  Saved: {PILOT_DIR / 'pilot_results.csv'}")

    print("\n[6] Summary statistics ...")
    print("\n  Per-archetype median EUI (before vs after):")
    for arch in sorted(cdf["archetype_id"].unique()):
        sub = cdf[cdf["archetype_id"] == arch]
        print(f"\n  {arch} (n={len(sub)}):")
        print(f"    OLD lighting median: {sub['old_lighting_eui'].median():.3f} kWh/m2")
        print(f"    NEW lighting median: {sub['new_lighting_eui'].median():.3f} kWh/m2")
        print(f"    OLD total median:    {sub['old_total_eui'].median():.3f} kWh/m2")
        print(f"    NEW total median:    {sub['new_total_eui'].median():.3f} kWh/m2")
        print(f"    lighting_ratio median (new/old): {sub['lighting_ratio'].median():.3f}")
        print(f"    expected ratio (= median levels): {sub['levels'].median():.1f}")

    print("\n  Lighting-vs-levels check (new lighting EUI should be constant per archetype):")
    check = cdf.groupby(["archetype_id", "levels"])["new_lighting_eui"].agg(["median", "std", "count"])
    print(check.to_string())

    print("\n  OLD lighting × levels (should be constant — bug fingerprint):")
    cdf["old_lit_times_levels"] = cdf["old_lighting_eui"] * cdf["levels"]
    old_check = cdf.groupby("levels")["old_lit_times_levels"].agg(["median", "std"])
    print(old_check.to_string())

    print("\n  lighting_ratio vs expected_ratio (should be 1.0 for all rows):")
    ratio_check = cdf[["osm_id","archetype_id","levels","old_lighting_eui","new_lighting_eui","lighting_ratio","expected_ratio","ratio_vs_expected"]].sort_values(["archetype_id","levels"])
    print(ratio_check.to_string(index=False))

    print("\n[7] GO / NO-GO assessment ...")
    old_constant = cdf["old_lit_times_levels"].std() / cdf["old_lit_times_levels"].mean()
    new_range = cdf["new_lighting_eui"].std() / cdf["new_lighting_eui"].mean()
    print(f"  Old lighting × levels CV: {old_constant:.3f}  (low = was constant = bug confirmed)")
    print(f"  New lighting EUI CV:      {new_range:.3f}  (natural archetype variation)")

    lighting_rose = (cdf["new_lighting_eui"] > cdf["old_lighting_eui"]).mean()
    print(f"  Fraction buildings where lighting EUI rose: {lighting_rose:.2%}")

    all_ozpf = (manifest[success_mask]["zoning_strategy"] == "one_zone_per_floor").all()
    print(f"  All affected buildings now one_zone_per_floor: {all_ozpf}")

    total_sims = len([d for d in SIM_DIR.iterdir() if d.is_dir()])
    sim_pass_rate = n_parsed / len(manifest[success_mask]) if len(manifest[success_mask]) > 0 else 0.0
    print(f"  SQL parse rate (proxy for sim pass): {sim_pass_rate:.1%}  ({n_parsed}/{len(manifest[success_mask])})")

    go = lighting_rose > 0.90 and sim_pass_rate >= 0.95 and all_ozpf
    print(f"\n  VERDICT: {'GO' if go else 'NO-GO'}")

    # Print per-building table for the report
    print("\n  Per-building table (sorted by archetype, levels):")
    print(f"  {'osm_id':<25} {'arch':<18} {'lv':>3} {'old_lit':>9} {'new_lit':>9} {'ratio':>7} {'exp':>5} {'r/e':>6}")
    for _, row in ratio_check.iterrows():
        print(f"  {row['osm_id']:<25} {row['archetype_id']:<18} {int(row['levels']):>3} "
              f"{row['old_lighting_eui']:>9.3f} {row['new_lighting_eui']:>9.3f} "
              f"{row['lighting_ratio']:>7.3f} {row['expected_ratio']:>5.1f} {row['ratio_vs_expected']:>6.3f}")


if __name__ == "__main__":
    main()
