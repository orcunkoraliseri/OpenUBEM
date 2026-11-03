"""Phase C combined-resim pilot driver.

Regenerates IDFs fresh (so both the zoning multi-floor fix and the OQ-2 DOE schedule
digitization are baked in together) for the identical 47-building la_urban subset used
by the zoning-only pilot.  Outputs to runtime/phasec_pilot/ (new dir).
Do NOT touch runtime/zoning_pilot/ -- it is the old-schedule baseline.

Plan reference: docs/implementation/phaseC_combinedResim/PLAN_phaseC-combined-resim.md
Tasks: P1.T01, P1.T02.
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

PILOT_DIR     = REPO / "runtime" / "phasec_pilot"
IDF_DIR       = PILOT_DIR / "idfs"
SIM_DIR       = PILOT_DIR / "sim_out"
RESULTS_CSV   = PILOT_DIR / "phasec_pilot_results.csv"

ZONING_PILOT_RESULTS = REPO / "runtime" / "zoning_pilot" / "pilot_results.csv"
R7_PATH       = REPO / "docs" / "validations" / "overAll" / "results" / "r7_service_loads.csv"
GDF_PATH      = REPO / "runtime" / "ubem_validation" / "cases" / "la_urban" / "01_buildings.gpkg"
CZ_PATH       = REPO / "runtime" / "ubem_validation" / "cases" / "la_urban" / "02a_climate_epw.parquet"
EPW_PATH      = (
    REPO / "runtime" / "ubem_validation" / "cases" / "la_urban"
    / "weather" / "weather"
    / "USA_CA_Los.Angeles.Downtown-USC.Campus.722874_TMYx.2011-2025.epw"
)
EP_EXE = Path(r"C:\EnergyPlusV23-1-0\energyplus.exe")
EP_IDD = EP_EXE.parent / "Energy+.idd"

PILOT_ARCHETYPES = {"MidriseApartment", "MediumOffice", "SmallOffice", "RetailStandalone"}
LEVELS_TIERS     = [2, 3, 4, 5, 6, 7]
PER_LEVEL_CAPS   = {"MidriseApartment": 4, "MediumOffice": 3, "SmallOffice": 3, "RetailStandalone": 3}


# ---------------------------------------------------------------------------
# Subset selection -- identical logic to pilot_complete_run.py
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Step 2: enrich semantics (picks up new doe_schedules.json automatically)
# ---------------------------------------------------------------------------

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
    cz_map   = dict(zip(climate_sidecar["osm_id"], climate_sidecar["climate_zone"]))
    prov_map = dict(zip(climate_sidecar["osm_id"], climate_sidecar["provenance_climate_zone"]))
    gdf_26["climate_zone"] = pd.Categorical(
        gdf_26["osm_id"].map(cz_map), categories=list(_CLIMATE_ZONE_VOCAB)
    )
    gdf_26["epw_path"] = str(EPW_PATH)
    gdf_26["provenance_climate_zone"] = pd.Categorical(
        gdf_26["osm_id"].map(prov_map), categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )
    gdf_57, schedule_library = enrich_semantics(gdf_26)
    return gdf_57, schedule_library


# ---------------------------------------------------------------------------
# EnergyPlus local runner (unchanged from template)
# ---------------------------------------------------------------------------

def run_energyplus_local(idf_path: Path, epw: Path, work_dir: Path) -> bool:
    work_dir.mkdir(parents=True, exist_ok=True)
    idd_dest = work_dir / "Energy+.idd"
    if not idd_dest.exists():
        shutil.copy2(EP_IDD, idd_dest)
    cmd = [str(EP_EXE), "-w", str(epw), "-d", str(work_dir), "-x", "-r", str(idf_path)]
    result = subprocess.run(cmd, capture_output=True, timeout=600, cwd=str(work_dir))
    end_file = work_dir / "eplusout.end"
    if not end_file.exists():
        return False
    return "EnergyPlus Completed Successfully" in end_file.read_text(errors="replace")


# ---------------------------------------------------------------------------
# SQL parse -> EUI  (/ footprint*levels, DESIGN SS300, unchanged)
# ---------------------------------------------------------------------------

def parse_sql_eui(sql_path: Path, osm_id: str, footprint: float, num_floors: int) -> dict | None:
    J_TO_KWH = 1.0 / 3.6e6
    floor_area = footprint * num_floors
    mapping = {
        "Zone Ideal Loads Zone Total Heating Energy": "heating_eui_kwh_m2",
        "Zone Ideal Loads Zone Total Cooling Energy": "cooling_eui_kwh_m2",
        "Zone Lights Electricity Energy":              "lighting_eui_kwh_m2",
        "Zone Electric Equipment Electricity Energy":  "equipment_eui_kwh_m2",
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
        print(f"  SQL error {osm_id}: {e}")
        return None
    if not rows:
        return None
    totals = {name: val * J_TO_KWH for name, val in rows}
    out = {}
    for ep_var, col in mapping.items():
        out[col] = totals.get(ep_var, 0.0) / floor_area if floor_area > 0 else 0.0
    out["total_eui_kwh_m2"] = sum(out.values())
    return out


# ---------------------------------------------------------------------------
# IDF spot-check: verify apartment lighting schedule peak and zoning
# ---------------------------------------------------------------------------

def spot_check_idf(idf_path: Path, oid: str, expected_levels: int) -> dict:
    """Return dict with 'lighting_peak', 'zone_count', 'pass'.

    IDF zone name format: 'ZONE,\\n    <osm_id>_F{i}_whole,'  (lowercase 'whole')
    Lighting schedule block name: 'Lighting_Schedule_MidriseApartment'
    """
    import re
    text = idf_path.read_text(errors="replace")

    # Count zones named *_F{i}_whole (lowercase, zoning fix signature)
    zone_names = re.findall(r"ZONE,\s*\n\s*([^\n,]+_F\d+_whole)", text, re.IGNORECASE)
    zone_count = len(zone_names)

    # Find the peak value in the MidriseApartment Lighting schedule compact block.
    # Format: "Until: HH:MM, <value>,"  -- the value field after the comma.
    # Extract all "Until:" lines within the Lighting_Schedule_MidriseApartment block.
    lighting_peak = None
    in_block = False
    for line in text.splitlines():
        if "Lighting_Schedule_MidriseApartment" in line:
            in_block = True
            continue
        if in_block:
            # End of block: another SCHEDULE:COMPACT header or blank + object keyword
            if line.strip() == "" and lighting_peak is not None:
                pass  # blank lines within block are ok
            if "SCHEDULE:COMPACT" in line.upper() and "Lighting_Schedule_MidriseApartment" not in line:
                break
            # Parse "Until: HH:MM, <value>"
            m = re.search(r"Until:\s*\d+:\d+,\s*([\d.]+)", line)
            if m:
                val = float(m.group(1))
                lighting_peak = max(lighting_peak or 0.0, val)

    passed = (zone_count == expected_levels) and (lighting_peak is not None and lighting_peak < 0.30)
    return {
        "lighting_peak": lighting_peak,
        "zone_count": zone_count,
        "expected_zones": expected_levels,
        "pass": passed,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 72)
    print("PHASE C COMBINED PILOT: zoning fix + OQ-2 DOE schedules")
    print("=" * 72)

    assert EPW_PATH.exists(), f"EPW not found: {EPW_PATH}"
    assert EP_EXE.exists(),   f"EnergyPlus not found: {EP_EXE}"
    assert ZONING_PILOT_RESULTS.exists(), f"Zoning-only baseline not found: {ZONING_PILOT_RESULTS}"

    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    IDF_DIR.mkdir(parents=True, exist_ok=True)
    SIM_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # [1] Load inputs and select same 47-building subset
    # -----------------------------------------------------------------------
    print("\n[1] Loading inputs and selecting pilot subset ...")
    r7      = pd.read_csv(R7_PATH)
    raw_gdf = gpd.read_file(str(GDF_PATH))
    pilot_r7 = select_pilot(r7)
    print(f"  Pilot subset: {len(pilot_r7)} buildings")
    arch_counts = pilot_r7["archetype_id"].value_counts().to_dict()
    print(f"  By archetype: {arch_counts}")
    pilot_r7.to_csv(PILOT_DIR / "pilot_subset_definition.csv", index=False)

    # -----------------------------------------------------------------------
    # [2] Step 2 -- re-run enrich_semantics to pick up new doe_schedules.json
    # -----------------------------------------------------------------------
    print("\n[2] Running Step 2 (enrich_semantics) -- picks up new DOE schedules ...")
    pilot_oids = list(pilot_r7["osm_id"].astype(str))
    gdf_57, schedule_library = run_step2_for_pilot(pilot_oids, raw_gdf)
    print(f"  Enriched rows: {len(gdf_57)}")

    enrich_map = {str(r["osm_id"]): r for _, r in gdf_57.iterrows()}

    # -----------------------------------------------------------------------
    # [3] Step 3 -- build IDFs fresh via run_step3 (bakes zoning fix + new schedules)
    # -----------------------------------------------------------------------
    manifest_path = PILOT_DIR / "03_idf_manifest.parquet"
    if manifest_path.exists():
        print(f"\n[3] Manifest already exists -- reusing IDFs from prior run ({manifest_path})")
        manifest_df = pd.read_parquet(str(manifest_path))
    else:
        print(f"\n[3] Building IDFs fresh into {PILOT_DIR} via run_step3 ...")
        from openubem.idf.builder import run_step3
        manifest_df = run_step3(gdf_57, schedule_library, PILOT_DIR, n_jobs=1)

    n_idf_ok = (manifest_df["generation_status"].isin(["success", "fallback_bbox"])).sum()
    print(f"  IDF generation: {n_idf_ok}/{len(gdf_57)} success/fallback_bbox")
    print(f"  Status counts: {manifest_df['generation_status'].value_counts().to_dict()}")

    # Spot-check: first MidriseApartment with levels>1 that built successfully
    apt_success = manifest_df[
        (manifest_df["archetype_id"] == "MidriseApartment")
        & (manifest_df["generation_status"].isin(["success", "fallback_bbox"]))
        & (manifest_df["idf_path"] != "")
    ]
    if len(apt_success) == 0:
        print("ERROR: No successful MidriseApartment IDFs for spot-check. Halting.")
        sys.exit(1)

    spot_row = apt_success.iloc[0]
    spot_oid = str(spot_row["osm_id"])
    spot_idf_path = Path(str(spot_row["idf_path"]))

    # Get expected levels from enriched row
    spot_enriched = enrich_map.get(spot_oid)
    if spot_enriched is not None:
        lv_raw = spot_enriched["levels"]
        expected_lvs = int(lv_raw) if not pd.isna(lv_raw) else int(spot_row.get("num_zones", 2))
    else:
        expected_lvs = int(spot_row.get("num_zones", 2))

    spot = spot_check_idf(spot_idf_path, spot_oid, expected_lvs)
    print(f"\n  *** IDF SPOT-CHECK on {spot_oid} (MidriseApartment, expected_levels={expected_lvs}) ***")
    print(f"      zone_count in IDF = {spot['zone_count']} (expected {expected_lvs})")
    print(f"      apartment lighting schedule peak in IDF = {spot['lighting_peak']}")
    print(f"      PASS={spot['pass']}")
    if not spot["pass"]:
        print("  *** STOP: IDF spot-check FAILED.")
        print(f"      zone_count={spot['zone_count']} vs expected {expected_lvs}")
        print(f"      lighting_peak={spot['lighting_peak']} (expect < 0.30 for new DOE schedules)")
        print("      Rebuild is NOT picking up the fixed schedules or zoning. Halting.")
        sys.exit(1)
    print("  Spot-check PASSED.\n")

    if n_idf_ok == 0:
        print("ERROR: No IDFs generated. Halting.")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # [4] Simulate all buildings with local EnergyPlus 23.1
    # -----------------------------------------------------------------------
    success_manifest = manifest_df[manifest_df["generation_status"].isin(["success", "fallback_bbox"])]
    print(f"\n[4] Simulating {len(success_manifest)} buildings with EnergyPlus 23.1 ...")
    n_sim_ok = 0
    n_sim_skip = 0
    for i, (_, mrow) in enumerate(success_manifest.iterrows()):
        oid      = str(mrow["osm_id"])
        idf_path = Path(str(mrow["idf_path"]))
        safe_oid = oid.replace("/", "_").replace(":", "_").replace(" ", "_")
        work_dir = SIM_DIR / safe_oid
        # Resume: skip buildings whose sim already succeeded
        end_file = work_dir / "eplusout.end"
        if end_file.exists() and "EnergyPlus Completed Successfully" in end_file.read_text(errors="replace"):
            n_sim_ok += 1
            n_sim_skip += 1
            print(f"  [{i+1}/{len(success_manifest)}] {oid} ... SKIP (already done)")
            continue
        print(f"  [{i+1}/{len(success_manifest)}] {oid} ...", end=" ", flush=True)
        ok = run_energyplus_local(idf_path, EPW_PATH, work_dir)
        if ok:
            n_sim_ok += 1
            print("OK")
        else:
            print("FAIL")
            end_f = work_dir / "eplusout.end"
            if end_f.exists():
                print(f"    end: {end_f.read_text()[:300]}")

    print(f"\n  Sim pass: {n_sim_ok}/{len(success_manifest)} (skipped already-done: {n_sim_skip})")

    # -----------------------------------------------------------------------
    # [5] Parse SQL -> EUI
    # -----------------------------------------------------------------------
    print(f"\n[5] Parsing SQL for all {len(success_manifest)} buildings ...")
    z_pilot  = pd.read_csv(ZONING_PILOT_RESULTS)
    z_map    = {str(r["osm_id"]): r for _, r in z_pilot.iterrows()}

    rows_out = []
    n_parsed = 0
    n_missing_sql = 0

    for _, mrow in success_manifest.iterrows():
        oid      = str(mrow["osm_id"])
        safe_oid = oid.replace("/", "_").replace(":", "_").replace(" ", "_")
        sql_path = SIM_DIR / safe_oid / "eplusout.sql"

        r7_rows = pilot_r7[pilot_r7["osm_id"].astype(str) == oid]
        if len(r7_rows) == 0:
            continue
        r7_r = r7_rows.iloc[0]

        enriched_row = enrich_map.get(oid)
        if enriched_row is not None:
            footprint = float(enriched_row["footprint_area_m2"])
            lv_raw    = enriched_row["levels"]
            levels    = int(r7_r["levels"]) if pd.isna(lv_raw) else int(lv_raw)
            archetype = str(enriched_row["archetype_id"])
        else:
            footprint = float(r7_r["footprint_area_m2"])
            levels    = int(r7_r["levels"])
            archetype = str(r7_r["archetype_id"])

        if not sql_path.exists():
            n_missing_sql += 1
            continue

        combined_eui = parse_sql_eui(sql_path, oid, footprint, levels)
        if combined_eui is None:
            n_missing_sql += 1
            continue

        z_row = z_map.get(oid)
        rows_out.append({
            "osm_id":            oid,
            "archetype_id":      archetype,
            "levels":            levels,
            "footprint_area_m2": footprint,
            # old = r7 (single_zone + synthetic schedules)
            "old_lighting_eui":   float(r7_r["lighting_eui_kwh_m2"]),
            "old_equipment_eui":  float(r7_r["equipment_eui_kwh_m2"]),
            "old_heating_eui":    float(r7_r["heating_eui_kwh_m2"]),
            "old_cooling_eui":    float(r7_r["cooling_eui_kwh_m2"]),
            "old_total_eui":      float(r7_r["total_eui_kwh_m2"]),
            # zoning_only = zoning pilot new_* columns
            "zoning_lighting_eui":  float(z_row["new_lighting_eui"])  if z_row is not None else float("nan"),
            "zoning_equipment_eui": float(z_row["new_equipment_eui"]) if z_row is not None else float("nan"),
            "zoning_heating_eui":   float(z_row["new_heating_eui"])   if z_row is not None else float("nan"),
            "zoning_cooling_eui":   float(z_row["new_cooling_eui"])   if z_row is not None else float("nan"),
            "zoning_total_eui":     float(z_row["new_total_eui"])     if z_row is not None else float("nan"),
            # combined = this resim
            "combined_lighting_eui":  combined_eui["lighting_eui_kwh_m2"],
            "combined_equipment_eui": combined_eui["equipment_eui_kwh_m2"],
            "combined_heating_eui":   combined_eui["heating_eui_kwh_m2"],
            "combined_cooling_eui":   combined_eui["cooling_eui_kwh_m2"],
            "combined_total_eui":     combined_eui["total_eui_kwh_m2"],
        })
        n_parsed += 1

    print(f"  Parsed: {n_parsed}, missing SQL: {n_missing_sql}")

    if len(rows_out) == 0:
        print("ERROR: zero parsed rows. Halting.")
        sys.exit(1)

    cdf = pd.DataFrame(rows_out)
    cdf.to_csv(str(RESULTS_CSV), index=False)
    print(f"  Saved: {RESULTS_CSV}")

    # -----------------------------------------------------------------------
    # [6] Summary stats
    # -----------------------------------------------------------------------
    print("\n[6] Three-way comparison -- per-archetype medians:")
    header = f"  {'Archetype':<20} {'n':>3}  {'old_lit':>8} {'zone_lit':>9} {'comb_lit':>9}  {'old_eq':>8} {'zone_eq':>8} {'comb_eq':>8}  {'old_tot':>8} {'zone_tot':>9} {'comb_tot':>9}"
    sep    = f"  {'-'*20} {'-'*3}  {'-'*8} {'-'*9} {'-'*9}  {'-'*8} {'-'*8} {'-'*8}  {'-'*8} {'-'*9} {'-'*9}"
    print(header)
    print(sep)
    for arch in sorted(cdf["archetype_id"].unique()):
        sub = cdf[cdf["archetype_id"] == arch]
        n   = len(sub)
        m   = sub.median(numeric_only=True)
        print(f"  {arch:<20} {n:>3}  "
              f"{m['old_lighting_eui']:>8.2f} {m['zoning_lighting_eui']:>9.2f} {m['combined_lighting_eui']:>9.2f}  "
              f"{m['old_equipment_eui']:>8.2f} {m['zoning_equipment_eui']:>8.2f} {m['combined_equipment_eui']:>8.2f}  "
              f"{m['old_total_eui']:>8.2f} {m['zoning_total_eui']:>9.2f} {m['combined_total_eui']:>9.2f}")

    print("\n[7] Lighting EUI floor-count independence (combined -- zoning fix intact):")
    print(f"  {'Archetype':<20} {'levels':>6} {'n':>3} {'med_comb_lit':>13} {'std':>8}")
    for (arch, lv), row in cdf.groupby(["archetype_id", "levels"])["combined_lighting_eui"].agg(["median","std","count"]).iterrows():
        print(f"  {arch:<20} {lv:>6} {int(row['count']):>3} {row['median']:>13.3f} {row['std']:>8.4f}")

    # Four confirmations
    apt_sub = cdf[cdf["archetype_id"] == "MidriseApartment"]
    apt_med_comb_lit  = apt_sub["combined_lighting_eui"].median()
    apt_med_zone_lit  = apt_sub["zoning_lighting_eui"].median()
    apt_med_comb_tot  = apt_sub["combined_total_eui"].median()
    apt_med_comb_eq   = apt_sub["combined_equipment_eui"].median()
    apt_med_zone_eq   = apt_sub["zoning_equipment_eui"].median()

    lit_std_within = cdf.groupby(["archetype_id","levels"])["combined_lighting_eui"].std().max()

    print("\n[8] Four confirmations (P1.T02):")
    print(f"  (a) MidriseApartment combined lighting median = {apt_med_comb_lit:.3f} kWh/m2")
    print(f"      (expect ~4 kWh/m2; zoning-only was {apt_med_zone_lit:.2f})")
    print(f"  (b) Max combined_lighting std within archetype*level = {lit_std_within:.4f}")
    print(f"      (0 = perfectly floor-count-independent; zoning fix intact if near 0)")
    print(f"  (c) MidriseApartment combined equipment median = {apt_med_comb_eq:.3f} kWh/m2")
    print(f"      (zoning-only was {apt_med_zone_eq:.3f}; expect ~unchanged)")
    print(f"  (d) MidriseApartment combined TOTAL median = {apt_med_comb_tot:.2f} kWh/m2")
    print(f"      V17 measured band ~ 116 kWh/m2")
    below = apt_med_comb_tot < 116.0
    print(f"      Result: {'BELOW' if below else 'ABOVE'} the V17 ~116 band")

    print("\n[9] Pass rates:")
    print(f"  IDF generation:  {n_idf_ok}/{len(gdf_57)}")
    print(f"  Sim success:     {n_sim_ok}/{len(success_manifest)}")
    print(f"  SQL parse:       {n_parsed}/{len(success_manifest)}")

    print("\nPhase C pilot COMPLETE. HALTING for manager audit per P1 checkpoint (SS6).")
    print("Do NOT start P2 fan-out without manager/user go.")


if __name__ == "__main__":
    main()
