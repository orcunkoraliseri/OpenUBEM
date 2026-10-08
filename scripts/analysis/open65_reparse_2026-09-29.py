from __future__ import annotations

import json
import os
import sqlite3
import sys
import warnings
from multiprocessing import Pool
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import numpy as np
import pandas as pd

from openubem.results.carbon import compute_gwp
from openubem.results.parser import check_building_integrity, parse_building

OUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
ADOPTED_CSV = OUT_DIR / "t08_restated_fleet_eui_2026-09-10.csv"
OUT_CSV = OUT_DIR / "open65_reparse_fleet_eui_2026-09-29.csv"
OUT_JSON = OUT_DIR / "open65_reparse_summary_2026-09-29.json"
FETCH_BASE = Path(os.environ["TEMP"]) / "ubem_validation" / "open65_reparse_2026-09-29"
EVIDENCE = REPO / "evidence" / "open48_refleet"
STATE_OF = {"nyc": "NY", "la": "CA", "austin": "TX"}
KWH_PER_GJ = 1e6 / 3600.0
RECON_TOL = 0.005

DH_COLS = [
    "cooling_district_eui_kwh_m2", "heating_district_eui_kwh_m2", "fans_district_eui_kwh_m2",
    "pumps_district_eui_kwh_m2", "refrigeration_district_eui_kwh_m2",
    "lighting_district_eui_kwh_m2", "equipment_district_eui_kwh_m2",
    "dhw_district_eui_kwh_m2", "exterior_lighting_eui_kwh_m2",
    "exterior_equipment_eui_kwh_m2", "heat_rejection_eui_kwh_m2",
    "humidification_eui_kwh_m2", "heat_recovery_eui_kwh_m2", "generators_eui_kwh_m2",
]

ABUPS_TO_OURS = {
    "Heating": ["heating_eui_kwh_m2"],
    "Cooling": ["cooling_eui_kwh_m2"],
    "Interior Lighting": ["lighting_eui_kwh_m2"],
    "Interior Equipment": ["equipment_eui_kwh_m2", "cooking_eui_kwh_m2", "elevators_eui_kwh_m2"],
    "Exterior Lighting": ["exterior_lighting_eui_kwh_m2"],
    "Exterior Equipment": ["exterior_equipment_eui_kwh_m2"],
    "Fans": ["fans_eui_kwh_m2"],
    "Pumps": ["pumps_eui_kwh_m2"],
    "Heat Rejection": ["heat_rejection_eui_kwh_m2"],
    "Humidification": ["humidification_eui_kwh_m2"],
    "Heat Recovery": ["heat_recovery_eui_kwh_m2"],
    "Water Systems": ["dhw_eui_kwh_m2"],
    "Refrigeration": ["refrigeration_eui_kwh_m2"],
    "Generators": ["generators_eui_kwh_m2"],
}

_CELL_CACHE: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}


def _cell_inputs(cell: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    if cell not in _CELL_CACHE:
        d = EVIDENCE / cell
        man = pd.read_parquet(d / "step3" / "03_idf_manifest.parquet").set_index("osm_id")
        bld = gpd.read_file(str(d / "01_buildings.gpkg"))[["osm_id", "footprint_area_m2", "levels", "height_m"]]
        _CELL_CACHE[cell] = (man, bld.set_index("osm_id"))
    return _CELL_CACHE[cell]


def _abups(sql_path: Path) -> tuple[float | None, dict[str, float]]:
    site_kwh = None
    per_use: dict[str, float] = {}
    with sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True) as conn:
        r = conn.execute(
            "SELECT Value FROM TabularDataWithStrings WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' "
            "AND TableName='Site and Source Energy' AND RowName='Total Site Energy' "
            "AND ColumnName='Total Energy'"
        ).fetchone()
        if r and str(r[0]).strip():
            site_kwh = float(r[0]) * KWH_PER_GJ
        rows = conn.execute(
            "SELECT RowName, ColumnName, Value FROM TabularDataWithStrings "
            "WHERE ReportName='AnnualBuildingUtilityPerformanceSummary' AND TableName='End Uses' "
            "AND Units='GJ'"
        ).fetchall()
    for row_name, _col, val in rows:
        if row_name in ABUPS_TO_OURS:
            try:
                per_use[row_name] = per_use.get(row_name, 0.0) + float(val) * KWH_PER_GJ
            except (TypeError, ValueError):
                pass
    return site_kwh, per_use


def _work(args: tuple[str, str, str, str, str]) -> dict:
    stem, osm_id, cell, city, archetype = args
    sql = FETCH_BASE / cell / stem / "eplusout.sql"
    out: dict = {"stem": stem, "osm_id": osm_id, "cell": cell, "city": city, "archetype_id": archetype}
    try:
        man, bld = _cell_inputs(cell)
        m = man.loc[osm_id]
        b = bld.loc[osm_id]
        levels = b["levels"]
        row = pd.Series({
            "osm_id": osm_id,
            "num_zones": int(m["num_zones"]),
            "data_quality_flag": m["data_quality_flag"],
            "resolution_mode": m["resolution_mode"],
            "archetype_id": m["archetype_id"],
            "footprint_area_m2": float(b["footprint_area_m2"]),
            "levels": None if pd.isna(levels) else levels,
            "height_m": b["height_m"],
        })
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = parse_building(sql, None, row)
            out.update({k: v for k, v in p.items() if not k.startswith("gwp_") and k != "osm_id"})
            if p["parse_status"] == "success":
                gw = compute_gwp(p, STATE_OF[cell.split("_")[0]])
                out.update(gw)
                fa = p["floor_area_m2"]
                out["total_kwh"] = p["total_eui_kwh_m2"] * fa
                out["dh_kwh"] = sum(p[c] for c in DH_COLS) * fa
                out["gwp_total_kgco2"] = gw["gwp_total_kgco2_m2"] * fa
            integ = check_building_integrity(sql)
            out["abups_ok"] = integ["abups_ok"]
        site_kwh, per_use = _abups(sql)
        out["abups_site_kwh"] = site_kwh
        if p["parse_status"] == "success" and site_kwh:
            gap = out["total_kwh"] - site_kwh
            out["recon_gap_pct"] = 100.0 * gap / site_kwh
            worst, worst_v = "", 0.0
            for use, cols in ABUPS_TO_OURS.items():
                ours = sum(p.get(c, 0.0) or 0.0 for c in cols) * p["floor_area_m2"]
                d = ours - per_use.get(use, 0.0)
                if abs(d) > abs(worst_v):
                    worst, worst_v = use, d
            out["recon_end_use"] = worst
            out["recon_end_use_gap_kwh"] = worst_v
    except Exception as exc:
        out["parse_status"] = out.get("parse_status", "worker_error")
        out["error_summary"] = f"{type(exc).__name__}: {exc}"[:300]
    return out


def main() -> int:
    ad = pd.read_csv(ADOPTED_CSV)
    jobs = [(r.stem, r.osm_id, r.cell, r.city, r.archetype_id) for r in ad.itertuples()]
    missing = [j[0] for j in jobs if not (FETCH_BASE / j[2] / j[0] / "eplusout.sql").exists()]
    print(f"jobs={len(jobs)} missing_sql={len(missing)}", flush=True)
    if missing:
        print("STOP: missing sql", missing[:5])
        return 2
    with Pool(10) as pool:
        rows = []
        for i, r in enumerate(pool.imap_unordered(_work, jobs, chunksize=20)):
            rows.append(r)
            if (i + 1) % 1000 == 0:
                print(f"  parsed {i + 1}", flush=True)
    new = pd.DataFrame(rows).set_index("stem")
    ad = ad.set_index("stem")
    df = new.join(
        ad[["floor_area_m2", "total_kwh", "total_eui_kwh_m2", "gwp_total_kgco2"]].add_prefix("adopted_"),
        how="left",
    ).reset_index()
    df["area_matches_adopted"] = np.isclose(df["floor_area_m2"], df["adopted_floor_area_m2"], rtol=1e-9, atol=1e-6)
    df.to_csv(OUT_CSV, index=False)

    ok = df[df["parse_status"] == "success"]
    n = int(len(ok))
    pooled = ok["total_kwh"].sum() / ok["floor_area_m2"].sum()
    pooled_nodh = (ok["total_kwh"] - ok["dh_kwh"]).sum() / ok["floor_area_m2"].sum()
    adopted_pooled = ok["adopted_total_kwh"].sum() / ok["adopted_floor_area_m2"].sum()
    carbon_t = float(ok["gwp_total_kgco2"].sum()) / 1000.0
    adopted_carbon_t = float(ok["adopted_gwp_total_kgco2"].sum()) / 1000.0
    arch = ok.groupby("archetype_id").apply(
        lambda g: pd.Series({
            "n": len(g),
            "candidate_eui": g["total_kwh"].sum() / g["floor_area_m2"].sum(),
            "adopted_eui": g["adopted_total_kwh"].sum() / g["adopted_floor_area_m2"].sum(),
        }),
        include_groups=False,
    )
    arch["delta"] = arch["candidate_eui"] - arch["adopted_eui"]
    fail = df[df["abups_ok"] == False]  # noqa: E712
    recon = ok[ok["recon_gap_pct"].abs() > RECON_TOL * 100]
    summary = {
        "date": "2026-09-29",
        "status": "CANDIDATE - not adopted; adoption is CP-1, user only",
        "n_jobs": int(len(df)),
        "n_parse_success": n,
        "parse_status_counts": df["parse_status"].value_counts().to_dict(),
        "candidate_pooled_eui_kwh_m2": round(float(pooled), 4),
        "candidate_carbon_total_tonnes_co2e": round(carbon_t, 2),
        "adopted_pooled_eui_kwh_m2": 153.9501,
        "adopted_pooled_eui_recomputed_same_population": round(float(adopted_pooled), 4),
        "adopted_carbon_total_tonnes_co2e": 881743.09,
        "adopted_carbon_recomputed_same_population": round(adopted_carbon_t, 2),
        "delta_eui_kwh_m2": round(float(pooled - adopted_pooled), 4),
        "delta_carbon_tonnes": round(carbon_t - adopted_carbon_t, 2),
        "test_a_area_equals_t08_count": int(df["area_matches_adopted"].sum()),
        "test_b_pooled_eui_district_zeroed": round(float(pooled_nodh), 4),
        "test_b_target": 153.9501,
        "abups_ok_fail_count": int(len(fail)),
        "abups_ok_fail_stems": fail["stem"].tolist(),
        "abups_ok_none_count": int(df["abups_ok"].isna().sum()),
        "recon_gap_gt_0p5pct_count": int(len(recon)),
        "recon_gap_end_use_counts": recon["recon_end_use"].value_counts().to_dict(),
        "floor_area_provenance_counts": df["floor_area_provenance"].value_counts().to_dict(),
        "district_heat_buildings": int((ok["dh_kwh"] > 0).sum()),
        "per_archetype": {k: {c: round(float(v), 4) for c, v in r.items()} for k, r in arch.iterrows()},
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("per_archetype", "abups_ok_fail_stems")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
