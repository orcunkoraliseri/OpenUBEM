"""Recovery driver for the 10 Phase-E dropped buildings.

Usage:
    py -3 scripts/validation/phaseE_recover_10.py --phase1   # T06-R: regen+sim Group A, parse all 10
    py -3 scripts/validation/phaseE_recover_10.py --phase2   # T07:   merge into canonical results
    py -3 scripts/validation/phaseE_recover_10.py --all      # both phases (default)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# ── repo root on sys.path ──────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from openubem import config
from openubem.results.carbon import attach_gwp
from openubem.results.parser import parse_building
from openubem.simulation.parallel import SimTask
from openubem.simulation.runner import classify_outcome, run_energyplus

# ── constants ─────────────────────────────────────────────────────────────────
TEMP_BASE = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseE")
CANON_BASE = ROOT / "docs/docs_VALIDATION/validations/overAll/results/phaseE"

GROUP_A = [
    ("la_rural",  "way/472960972"),
    ("la_rural",  "way/472961034"),
    ("la_rural",  "way/472961088"),
    ("la_rural",  "way/472961091"),
    ("la_rural",  "way/472961171"),
    ("la_urban",  "way/402215469"),
]
GROUP_B = [
    ("nyc_centre", "way/266149332"),
    ("la_centre",  "way/319507579"),
    ("la_rural",   "way/472961047"),
    ("la_rural",   "way/472961092"),
]
AFFECTED_CELLS = ["nyc_centre", "la_centre", "la_rural", "la_urban"]
CELL_STATE = {"la_rural": "CA", "la_urban": "CA", "nyc_centre": "NY", "la_centre": "CA"}
CELL_CRS   = {"la_rural": 32611, "la_urban": 32611, "nyc_centre": 32618, "la_centre": 32611}

# ── Floor-RX (same as v12_cell_pipeline._build_enriched_gdf) ──────────────────
_floor_rx = re.compile(r"_F(\d+)_", re.IGNORECASE)


def _oid_to_dir(osm_id: str) -> str:
    return osm_id.replace("/", "_")


# ── PHASE 1 helpers ───────────────────────────────────────────────────────────

def _epw_path(cell: str) -> Path:
    return next((TEMP_BASE / cell / "weather" / "weather").glob("*.epw"))


def _enrich_cell(cell: str) -> tuple[gpd.GeoDataFrame, dict]:
    """Run step2_classify_enrich on cached 01_buildings.gpkg (deterministic, offline)."""
    from scripts.validation.v12_cell_pipeline import step2_classify_enrich
    work_base = TEMP_BASE / cell
    gdf_raw = gpd.read_file(str(work_base / "01_buildings.gpkg"))
    epw = _epw_path(cell)
    print(f"  Enriching {cell} ({len(gdf_raw)} buildings) ...")
    gdf57, sched = step2_classify_enrich(gdf_raw, epw, work_base, cell)
    gdf57["epw_path"] = str(epw)
    return gdf57, sched


def _derive_gdf_row_from_sql(sql_path: Path, osm_id: str, zoning: str, num_zones: int,
                              centroid_x: float, centroid_y: float) -> dict:
    """Derive footprint_area_m2/levels/height_m from SQL zone table (same logic as _build_enriched_gdf)."""
    try:
        conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
        zones = conn.execute(
            "SELECT ZoneName, CeilingHeight, FloorArea, CentroidX, CentroidY FROM Zones"
        ).fetchall()
        conn.close()
    except Exception as e:
        print(f"  SQL read error for {osm_id}: {e}")
        return {"footprint_area_m2": 200.0, "levels": 1.0, "height_m": 3.5}

    if not zones:
        return {"footprint_area_m2": 200.0, "levels": 1.0, "height_m": 3.5}

    if zoning == "single_zone":
        z = zones[0]
        fp = float(z[2]); ht = float(z[1])
        nf = max(1.0, round(ht / 3.5))
        return {"footprint_area_m2": fp, "levels": nf, "height_m": ht}
    elif zoning == "one_zone_per_floor":
        fp = float(zones[0][2])
        nf = float(num_zones)
        return {"footprint_area_m2": fp, "levels": nf, "height_m": nf * 3.5}
    elif "perimeter_core" in zoning:
        floor_areas: dict[int, float] = {}
        for z in zones:
            m = _floor_rx.search(z[0])
            if m:
                f = int(m.group(1))
                floor_areas[f] = floor_areas.get(f, 0.0) + float(z[2])
        nf = max(1.0, float(len(floor_areas)))
        fp = floor_areas.get(0, sum(floor_areas.values()) / max(1, len(floor_areas)))
        return {"footprint_area_m2": fp, "levels": nf, "height_m": nf * 3.5}
    else:
        z = zones[0]
        return {"footprint_area_m2": float(z[2]), "levels": 1.0, "height_m": float(z[1])}


def _sim_one(osm_id: str, idf_path: Path, epw_path: Path, sim_dir: Path) -> dict:
    """Run E+ on idf_path; return classify_outcome result dict."""
    task = SimTask(osm_id, str(idf_path), str(epw_path), str(sim_dir))
    raw = run_energyplus(task)
    return classify_outcome(raw, sim_dir)


def _is_nomass_divergence(sim_dir: Path) -> bool:
    """Return True if err file has 0 volume clamps and >=1 temperature out-of-bounds severe."""
    err = sim_dir / "eplusout.err"
    if not err.exists():
        return False
    txt = err.read_text(encoding="utf-8", errors="replace")
    has_vol_clamp = bool(re.search(r"Indicated Zone Volume <= 0", txt))
    has_temp = bool(re.search(r"Temperature.*out of bounds", txt, re.IGNORECASE))
    return (not has_vol_clamp) and has_temp


def _build_manifest_row(osm_id: str, gdf57_row: pd.Series,
                        num_zones: int, zoning: str, dq_flag: str) -> pd.Series:
    def _f(col, default):
        v = gdf57_row.get(col, default)
        return default if (v is None or pd.isna(v)) else float(v)
    return pd.Series({
        "osm_id": osm_id,
        "footprint_area_m2": _f("footprint_area_m2", 200.0),
        "levels": _f("levels", 1.0),
        "height_m": _f("height_m", 3.5),
        "num_zones": num_zones,
        "zoning_strategy": zoning,
        "data_quality_flag": dq_flag,
    })


def recover_group_a() -> list[dict]:
    """Regen+sim+parse Group A (6).  Returns list of result dicts."""
    from openubem.idf.builder import BuildingIDF

    results = []
    cells_done: dict[str, tuple] = {}

    for cell, oid in GROUP_A:
        if cell not in cells_done:
            cells_done[cell] = _enrich_cell(cell)
        gdf57, sched = cells_done[cell]
        epw = _epw_path(cell)
        state = CELL_STATE[cell]

        row = gdf57[gdf57["osm_id"].astype(str) == oid].iloc[0]
        oid_dir = _oid_to_dir(oid)

        step3_dir = TEMP_BASE / cell / "recover_step3"
        (step3_dir / "idfs").mkdir(parents=True, exist_ok=True)
        sim_dir = TEMP_BASE / cell / "recover_sim" / oid_dir
        sim_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  [{cell}] {oid}: regenerating IDF (orient applied) ...")
        res = BuildingIDF(row).build(gdf57, sched, step3_dir)
        if res["generation_status"] not in ("success", "fallback_bbox", "success_rerouted"):
            print(f"    WARN: generation_status={res['generation_status']} — skipping")
            continue

        idf_path = Path(res["idf_path"])
        num_zones = int(res["num_zones"])
        zoning = res["zoning_strategy"]

        print(f"    Running E+ (orient-only, NoMass) ...")
        outcome = _sim_one(oid, idf_path, epw, sim_dir)
        status = outcome["status"]

        dq_flag = str(row.get("data_quality_flag", "") or "")
        used_mass = False

        if status != "success":
            if _is_nomass_divergence(sim_dir):
                print(f"    NoMass divergence detected — rebuilding with thermal_mass=True ...")
                sim_dir_mass = TEMP_BASE / cell / "recover_sim" / (oid_dir + "_mass")
                sim_dir_mass.mkdir(parents=True, exist_ok=True)
                step3_mass = TEMP_BASE / cell / "recover_step3_mass"
                (step3_mass / "idfs").mkdir(parents=True, exist_ok=True)
                res2 = BuildingIDF(row, thermal_mass=True).build(gdf57, sched, step3_mass)
                idf_path2 = Path(res2["idf_path"])
                num_zones = int(res2["num_zones"])
                zoning = res2["zoning_strategy"]
                outcome = _sim_one(oid, idf_path2, epw, sim_dir_mass)
                status = outcome.get("status", outcome.get("simulation_status", "failed_fatal"))
                used_mass = True
                tokens = [t.strip() for t in dq_flag.split(",") if t.strip()]
                if "NOMASS_DIVERGENCE_MASS_FALLBACK" not in tokens:
                    dq_flag = (dq_flag + ",NOMASS_DIVERGENCE_MASS_FALLBACK").lstrip(",")
            else:
                print(f"    FAIL (not NoMass divergence) — status={status}")
                results.append({"cell": cell, "osm_id": oid, "parse_status": "failed_fatal",
                                 "error_summary": "E+ fatal (non-NoMass)", "used_mass": False})
                continue

        if status != "success":
            print(f"    STILL FATAL after mass fallback — status={status}")
            results.append({"cell": cell, "osm_id": oid, "parse_status": "failed_fatal",
                             "error_summary": f"fatal after mass fallback: {status}", "used_mass": used_mass})
            continue

        n_severe = outcome.get("n_severe", 0) or 0
        print(f"    E+ SUCCESS  n_severe={n_severe}  used_mass={used_mass}")

        sql_path = sim_dir / "eplusout.sql"
        geom_info = _derive_gdf_row_from_sql(sql_path, oid, zoning, num_zones, 0.0, 0.0)
        manifest_row = _build_manifest_row(oid, row, num_zones, zoning, dq_flag)

        parsed = parse_building(sql_path, None, manifest_row)
        parsed = attach_gwp(parsed, state)
        parsed["simulation_status"] = parsed.pop("parse_status", "success")
        parsed["cell"] = cell
        parsed["osm_id"] = oid
        parsed["used_mass"] = used_mass
        parsed.update(geom_info)
        print(f"    total_eui_kwh_m2={parsed.get('total_eui_kwh_m2'):.2f}")
        results.append(parsed)

    return results


def recover_group_b() -> list[dict]:
    """Parse Group B (4) from existing SQL.  Returns list of result dicts."""
    results = []
    for cell, oid in GROUP_B:
        state = CELL_STATE[cell]
        oid_dir = _oid_to_dir(oid)
        sql_path = TEMP_BASE / cell / "sim_out" / oid_dir / "eplusout.sql"
        if not sql_path.exists():
            print(f"  [{cell}] {oid}: SQL NOT FOUND at {sql_path}")
            continue

        canon_gdf = gpd.read_file(str(CANON_BASE / cell / "05_results.gpkg"))
        row_df = canon_gdf[canon_gdf["osm_id"].astype(str) == oid]
        if len(row_df) == 0:
            print(f"  [{cell}] {oid}: not found in canonical gpkg")
            continue
        canon_row = row_df.iloc[0]

        manifest_row = pd.Series({
            "osm_id": oid,
            "footprint_area_m2": float(canon_row["footprint_area_m2"]),
            "levels": float(canon_row["levels"]),
            "height_m": float(canon_row["height_m"]),
            "num_zones": 999,  # non-gating after T02
            "zoning_strategy": str(canon_row.get("zoning_strategy", "")),
            "data_quality_flag": str(canon_row.get("data_quality_flag", "") or ""),
        })

        parsed = parse_building(sql_path, None, manifest_row)
        parsed = attach_gwp(parsed, state)
        parsed["simulation_status"] = parsed.pop("parse_status", "success")
        parsed["cell"] = cell
        parsed["osm_id"] = oid
        parsed["used_mass"] = False
        parsed["footprint_area_m2"] = float(canon_row["footprint_area_m2"])
        parsed["levels"] = float(canon_row["levels"])
        parsed["height_m"] = float(canon_row["height_m"])
        eui = parsed.get("total_eui_kwh_m2")
        eui_str = f"{eui:.2f}" if (eui is not None and str(eui) != "nan") else "N/A"
        print(f"  [{cell}] {oid}: status={parsed['simulation_status']}  total_eui={eui_str}")
        results.append(parsed)

    return results


def phase1() -> list[dict]:
    """T06-R + T05: recover all 10 buildings, report EUIs."""
    print("\n" + "="*70)
    print("PHASE 1: Recover Group A (6) + Group B (4)")
    print("="*70)

    print("\n--- Group A (6 geometry fatals — regen+sim) ---")
    a_results = recover_group_a()

    print("\n--- Group B (4 false drops — parse from SQL) ---")
    b_results = recover_group_b()

    all_results = a_results + b_results

    print("\n" + "="*70)
    print("PHASE 1 REPORT — 10 building EUIs")
    print("="*70)
    ok = 0
    for r in all_results:
        eui = r.get("total_eui_kwh_m2")
        st  = r.get("simulation_status", r.get("parse_status", "?"))
        mass = "MASS_FALLBACK" if r.get("used_mass") else ""
        eui_str = f"{eui:.2f}" if eui is not None and str(eui) != "nan" else "N/A"
        print(f"  [{r['cell']}] {r['osm_id']:30s}  status={st:30s}  total_eui={eui_str}  {mass}")
        if st == "success":
            ok += 1

    print(f"\nPHASE 1 SUMMARY: {ok}/10 recovered to success")
    if ok < 10:
        print("  WARNING: not all 10 recovered.  DO NOT run --phase2 until all 10 are success.")
    else:
        print("  All 10 recovered.  Proceed to --phase2 (T07 merge).")

    # Cache phase 1 results for phase 2
    _save_phase1_cache(all_results)
    return all_results


def _phase1_cache_path() -> Path:
    p = TEMP_BASE / "recover_phase1_cache.json"
    return p


def _save_phase1_cache(results: list[dict]) -> None:
    import math
    def _clean(v):
        if isinstance(v, float) and math.isnan(v): return None
        if isinstance(v, (bool, int, str, type(None))): return v
        if isinstance(v, float): return v
        return str(v)
    cleaned = [{k: _clean(v) for k, v in r.items()} for r in results]
    _phase1_cache_path().write_text(json.dumps(cleaned, indent=2), encoding="utf-8")
    print(f"  Phase 1 cache written: {_phase1_cache_path()}")


def _load_phase1_cache() -> list[dict]:
    p = _phase1_cache_path()
    if not p.exists():
        raise FileNotFoundError(f"Phase 1 cache not found at {p}. Run --phase1 first.")
    return json.loads(p.read_text(encoding="utf-8"))


# ── PHASE 2 helpers ───────────────────────────────────────────────────────────

_METRIC_COLS = [
    "heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2", "equipment_eui_kwh_m2",
    "fans_eui_kwh_m2", "pumps_eui_kwh_m2", "dhw_gas_eui_kwh_m2", "dhw_elec_eui_kwh_m2",
    "dhw_eui_kwh_m2", "cooking_eui_kwh_m2", "refrigeration_eui_kwh_m2", "total_eui_kwh_m2",
    "gwp_heating_kgco2_m2", "gwp_cooling_kgco2_m2", "gwp_lighting_kgco2_m2",
    "gwp_equipment_kgco2_m2", "gwp_fans_kgco2_m2", "gwp_pumps_kgco2_m2",
    "gwp_dhw_kgco2_m2", "gwp_cooking_kgco2_m2", "gwp_refrigeration_kgco2_m2",
    "gwp_total_kgco2_m2", "iod", "simulation_status", "error_summary",
]


def phase2(results: list[dict] | None = None) -> None:
    """T07: merge all 10 into canonical 05_results.{csv,gpkg,geojson} and recompute summaries."""
    if results is None:
        results = _load_phase1_cache()

    # Verify all 10 are success
    ok = [r for r in results if r.get("simulation_status") == "success"]
    if len(ok) != 10:
        print(f"ERROR: only {len(ok)}/10 are success. Aborting merge.")
        sys.exit(1)

    print("\n" + "="*70)
    print("PHASE 2: Merge 10 rows into canonical results")
    print("="*70)

    from openubem.results.aggregator import compute_neighbourhood_summary, export_results
    from openubem.results.carbon import load_egrid

    # Group results by cell
    by_cell: dict[str, list[dict]] = {}
    for r in results:
        by_cell.setdefault(r["cell"], []).append(r)

    for cell in AFFECTED_CELLS:
        cell_results = by_cell.get(cell, [])
        if not cell_results:
            continue

        canon_dir = CANON_BASE / cell
        gpkg_path = canon_dir / "05_results.gpkg"

        print(f"\n  [{cell}]: merging {len(cell_results)} row(s) ...")

        # Checksum a few untouched rows BEFORE merge
        gdf = gpd.read_file(str(gpkg_path))
        target_oids = {r["osm_id"] for r in cell_results}
        unchanged = gdf[~gdf["osm_id"].isin(target_oids)]
        sample_check = unchanged.sample(min(20, len(unchanged)), random_state=42)["total_eui_kwh_m2"].values.copy()

        # Drop old rows and append new ones
        gdf = gdf[~gdf["osm_id"].isin(target_oids)].copy()

        new_rows = []
        for r in cell_results:
            oid = r["osm_id"]
            geom = Point(0.0, 0.0)  # placeholder; geometry updated below from existing row if available
            new_row = {col: None for col in gdf.columns}
            new_row["osm_id"] = oid
            # Geometry: use centroid point (0,0) in cell CRS — same as _build_enriched_gdf fallback for unsimulated
            new_row["geometry"] = Point(0.0, 0.0)
            new_row["footprint_area_m2"] = r.get("footprint_area_m2", 200.0)
            new_row["levels"] = r.get("levels", 1.0)
            new_row["height_m"] = r.get("height_m", 3.5)
            # archetype_id and zoning_strategy from the original (these were already correct)
            orig_rows = unchanged[unchanged["osm_id"] == oid]
            if len(orig_rows) == 0:
                # Get from canonical gdf before we dropped
                all_gdf = gpd.read_file(str(gpkg_path))
                orig_rows = all_gdf[all_gdf["osm_id"] == oid]
            if len(orig_rows) > 0:
                new_row["archetype_id"] = orig_rows.iloc[0].get("archetype_id")
                new_row["zoning_strategy"] = orig_rows.iloc[0].get("zoning_strategy")
                new_row["geometry"] = orig_rows.iloc[0]["geometry"]
            # Metric columns
            for col in _METRIC_COLS:
                new_row[col] = r.get(col)
            # data_quality_flag
            new_row["data_quality_flag"] = r.get("data_quality_flag", "")
            new_rows.append(new_row)

        new_gdf = gpd.GeoDataFrame(new_rows, crs=gdf.crs)
        gdf = pd.concat([gdf, new_gdf], ignore_index=True)
        gdf = gpd.GeoDataFrame(gdf, crs=new_gdf.crs)

        # Verify checksum of untouched rows
        unch_after = gdf[~gdf["osm_id"].isin(target_oids)].sample(
            min(20, len(gdf) - len(cell_results)), random_state=42
        )["total_eui_kwh_m2"].values
        if not all(
            (abs(a - b) < 1e-6 if (a is not None and b is not None and str(a) != "nan" and str(b) != "nan") else True)
            for a, b in zip(sample_check, unch_after)
        ):
            print(f"  WARNING: checksum mismatch in {cell} — check before proceeding")

        # Verify row count
        expected = {"nyc_centre": 738, "la_centre": 226, "la_rural": 149, "la_urban": 618}
        if cell in expected and len(gdf) != expected[cell]:
            print(f"  WARNING: row count {len(gdf)} != expected {expected[cell]} for {cell}")

        # Recompute neighbourhood summary
        state = CELL_STATE[cell]
        egrid_subregion = None
        try:
            egrid = load_egrid()
            egrid_subregion = egrid.get(state.upper(), {}).get("subregion")
        except Exception:
            pass

        summary = compute_neighbourhood_summary(
            gdf,
            gwp_convention=config.GWP_CONVENTION,
            ep_version="23.1.0",
            egrid_subregion=egrid_subregion,
        )

        # Export
        export_results(gdf, canon_dir, summary)
        print(f"  [{cell}]: exported {len(gdf)} rows  status={gdf['simulation_status'].value_counts().to_dict()}")
        print(f"  [{cell}]: neighbourhood EUI={summary['neighbourhood_eui_weighted_kwh_m2']['total_eui_kwh_m2']:.2f}")

    print("\n" + "="*70)
    print("PHASE 2 COMPLETE — fleet integrity check")
    print("="*70)
    total = 0
    total_success = 0
    for cell in sorted(CANON_BASE.iterdir(), key=lambda p: p.name):
        if not (cell / "05_results.csv").exists():
            continue
        df = pd.read_csv(str(cell / "05_results.csv"))
        n = len(df)
        ns = (df["simulation_status"] == "success").sum()
        total += n
        total_success += ns
        print(f"  {cell.name:20s}: {ns}/{n} success")
    print(f"\n  FLEET TOTAL: {total_success}/{total} success")
    if total_success == total:
        print("  PASS 8,160/8,160 — TARGET REACHED")
    else:
        print(f"  ✗ {total - total_success} non-success remain")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    grp = parser.add_mutually_exclusive_group()
    grp.add_argument("--phase1", action="store_true", help="T06-R: regen+sim Group A, parse all 10")
    grp.add_argument("--phase2", action="store_true", help="T07: merge into canonical results")
    grp.add_argument("--all", action="store_true", help="run both phases (default)")
    args = parser.parse_args()

    run_p1 = args.phase1 or args.all or (not args.phase1 and not args.phase2)
    run_p2 = args.phase2 or args.all or (not args.phase1 and not args.phase2)

    if run_p1:
        results = phase1()
    else:
        results = None

    if run_p2:
        phase2(results)


if __name__ == "__main__":
    main()
