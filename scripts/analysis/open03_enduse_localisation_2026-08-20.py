"""T01 of PLAN_four-board-items-2026-08-20.md -- AA7: end-use diff on the 4
from-scratch buildings where auto and layout_assign share bit-identical
internal loads (per open03_load_source_per_building.csv, lighting/equipment
ratio == 1.000). No EnergyPlus is run here -- everything is read from the two
arms' existing eplusout.sql.

auto arm end uses: extracted directly from
  C:\\Users\\o_iseri\\AppData\\Local\\Temp\\ubem_validation\\open48_refleet4\\<cell>\\sim_out\\<way>\\eplusout.sql
  (ABUPS "End Uses" table, TabularDataWithStrings, summed over fuel columns per RowName).
  This location is NOT under scratchpad/open03-untrimmed-sample -- that directory holds
  the layout_assign arm only ("sim" + "step3_layout_assign"), never an "auto" arm. The
  plan's §6 T01 text says both arms live under scratchpad/open03-untrimmed-sample; that is
  wrong for the auto arm. Reported as a plan-citation deviation, not acted on further.

layout_assign arm end uses: extracted the same way from
  scratchpad/open03-untrimmed-sample/<cell>/sim/<way>/eplusout.sql -- this IS the file §5
  cites for the layout_assign arm.

Per-building total EUI, for the mandatory control against
openubem/outputs/comparisons/open03_load_source_per_building.csv and the -23.61% pooled
gap in MEASUREMENT_open-03_load-elasticity.md's CP-2:
  - layout_assign: sum of the 7 ABUPS end uses / conditioned floor area (IVRS "Zone
    Summary", "Conditioned Total" row) -- reproduces Total_End_Uses_kwh_eui almost exactly
    (it is the same computation the elasticity script already used for scale=1.0).
  - auto: taken directly from the existing 05_results.csv total_eui_kwh_m2 (production's
    own meter-based EUI, computed by openubem/results/parser.py::_compute_eui), NOT
    re-derived from ABUPS -- because that is the number the -23.61% control figure and
    the per_building.csv ratios were themselves built from (open03_load_source_decomposition
    _2026-08-20.py's `pooled()` reads total_eui_kwh_m2 straight from that same csv). A
    from-sql ABUPS re-derivation of the auto total was tried first and came out ~1.0-1.1%
    HIGH on all 4 buildings versus the production total_eui_kwh_m2 -- traced to a defect,
    not a rounding artifact: see the DEFECT note below.

DEFECT FOUND (measured, not fixed -- forbidden by plan §2 rule 2 and this task's own
"Forbidden" line): openubem/results/parser.py's METER_QUERY (line ~41-53) lists
'WaterSystems:NaturalGas' and 'WaterSystems:Electricity' but never
'WaterSystems:DistrictHeating'. All 4 of these buildings' Water Systems end use is served
partly by a DistrictHeating meter (ABUPS "Water Systems"/"District Heating" = 0.72 GJ for
3 of the 4, non-zero for the 4th) that dhw_eui_kwh_m2 (parser.py:469-482) silently drops,
so total_eui_kwh_m2 undercounts delivered energy by ~1.0-1.1% for every building whose DHW
(or heating/cooling) is served by a district-heating/cooling meter not in that IN-list.
Confirmed by direct comparison of ABUPS Water Systems (all fuel columns) against
dhw_eui_kwh_m2 * floor_area for all 4 buildings, both arms, 8/8 show the same gap.

Lighting/equipment end uses are unaffected (electricity-only, both arms) -- this defect
does not touch the OPEN-03 "loads bit-identical" finding, only the auto-side total.

Read-only against openubem/. Writes only to openubem/outputs/comparisons/.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
AUTO_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet4")
LA_ROOT = REPO / "scratchpad" / "open03-untrimmed-sample"
PER_BUILDING_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open03_load_source_per_building.csv"
OUT_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open03_enduse_localisation.csv"
OUT_META_CSV = REPO / "openubem" / "outputs" / "comparisons" / "open03_enduse_localisation_geometry.csv"

GJ_TO_KWH = 277.7778

END_USES = [
    "Heating", "Cooling", "Interior Lighting", "Interior Equipment",
    "Fans", "Pumps", "Water Systems",
]

BUILDINGS = [
    ("austin_centre", "way/1008727470"),
    ("nyc_centre", "way/265424467"),
    ("nyc_suburban", "way/846412106"),
    ("nyc_urban", "way/241862488"),
]

_ZONE_SUMMARY_TOTAL_ROWS = {
    "Total", "Conditioned Total", "Unconditioned Total", "Not Part of Total",
}


def _safe(osm_id: str) -> str:
    return osm_id.replace("/", "_")


def auto_sql_path(cell: str, osm_id: str) -> Path:
    return AUTO_ROOT / cell / "sim_out" / _safe(osm_id) / "eplusout.sql"


def la_sql_path(cell: str, osm_id: str) -> Path:
    return LA_ROOT / cell / "sim" / _safe(osm_id) / "eplusout.sql"


def extract_end_uses(sql_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
    try:
        placeholders = ",".join("?" for _ in END_USES)
        q = f"""
            SELECT RowName, COALESCE(SUM(CAST(Value AS REAL)), 0.0)
            FROM TabularDataWithStrings
            WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
              AND TableName = 'End Uses'
              AND Units = 'GJ'
              AND RowName IN ({placeholders})
            GROUP BY RowName
        """
        eu_gj = dict(conn.execute(q, END_USES).fetchall())

        q2 = """
            SELECT COALESCE(SUM(CAST(Value AS REAL)), 0.0)
            FROM TabularDataWithStrings
            WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
              AND TableName = 'End Uses'
              AND Units = 'GJ'
              AND RowName = 'Total End Uses'
        """
        abups_total_gj = conn.execute(q2).fetchone()[0]

        q3 = """
            SELECT ColumnName, COALESCE(SUM(CAST(Value AS REAL)), 0.0)
            FROM TabularDataWithStrings
            WHERE ReportName = 'AnnualBuildingUtilityPerformanceSummary'
              AND TableName = 'End Uses'
              AND Units = 'GJ'
              AND RowName = 'Water Systems'
            GROUP BY ColumnName
        """
        water_by_fuel_gj = dict(conn.execute(q3).fetchall())
    finally:
        conn.close()

    out = {r: eu_gj.get(r, 0.0) * GJ_TO_KWH for r in END_USES}
    out["_abups_total_kwh"] = abups_total_gj * GJ_TO_KWH
    out["_water_systems_district_heating_kwh"] = (
        water_by_fuel_gj.get("District Heating", 0.0) * GJ_TO_KWH
    )
    return out


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def extract_geometry(sql_path: Path) -> dict:
    conn = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
    try:
        zs = conn.execute(
            """SELECT RowName, ColumnName, Value FROM TabularDataWithStrings
               WHERE ReportName='InputVerificationandResultsSummary'
                 AND TableName='Zone Summary'"""
        ).fetchall()

        vals: dict[tuple[str, str], float | None] = {}
        zone_names: set[str] = set()
        for row_name, col_name, value in zs:
            vals[(row_name, col_name)] = _num(value)
            if row_name not in _ZONE_SUMMARY_TOTAL_ROWS and col_name == "Area":
                zone_names.add(row_name)

        cond_area = vals.get(("Conditioned Total", "Area"))
        wall_above = vals.get(("Conditioned Total", "Above Ground Gross Wall Area")) or 0.0
        wall_below = vals.get(("Conditioned Total", "Underground Gross Wall Area")) or 0.0
        window_area = vals.get(("Conditioned Total", "Window Glass Area")) or 0.0
        wall_area = wall_above + wall_below
        wwr_pct = (100.0 * window_area / wall_area) if wall_area else None

        coil = conn.execute(
            """SELECT RowName, ColumnName, Value FROM TabularDataWithStrings
               WHERE ReportName='HVACSizingSummary' AND TableName='Coil Sizing Summary'
                 AND ColumnName IN ('Coil Type', 'Coil Final Gross Total Capacity')"""
        ).fetchall()
        coil_type: dict[str, str] = {}
        coil_cap: dict[str, float] = {}
        for row_name, col_name, value in coil:
            if col_name == "Coil Type":
                coil_type[row_name] = value
            else:
                coil_cap[row_name] = _num(value) or 0.0

        heating_w = sum(
            cap for name, cap in coil_cap.items()
            if "Heating" in (coil_type.get(name) or "")
        )
        cooling_w = sum(
            cap for name, cap in coil_cap.items()
            if "Cooling" in (coil_type.get(name) or "")
        )
    finally:
        conn.close()

    return {
        "conditioned_floor_area_m2": cond_area,
        "n_zones": len(zone_names),
        "exterior_wall_area_m2": wall_area,
        "window_area_m2": window_area,
        "wwr_pct": wwr_pct,
        "heating_capacity_kw": heating_w / 1000.0,
        "cooling_capacity_kw": cooling_w / 1000.0,
    }


def main() -> None:
    per_building = pd.read_csv(PER_BUILDING_CSV, dtype={"osm_id": str})
    per_building = per_building.set_index(["cell", "osm_id"])

    long_rows = []
    meta_rows = []
    control_rows = []

    for cell, osm_id in BUILDINGS:
        auto_path = auto_sql_path(cell, osm_id)
        la_path = la_sql_path(cell, osm_id)
        assert auto_path.exists(), f"missing auto sql: {auto_path}"
        assert la_path.exists(), f"missing layout_assign sql: {la_path}"

        auto_eu = extract_end_uses(auto_path)
        la_eu = extract_end_uses(la_path)
        auto_geo = extract_geometry(auto_path)
        la_geo = extract_geometry(la_path)

        pb_row = per_building.loc[(cell, osm_id)]
        official_auto_total_eui = float(pb_row["total_eui_kwh_m2"])
        official_la_total_eui = float(pb_row["Total_End_Uses_kwh_eui"])
        floor_area_auto = float(pb_row["floor_area_m2_auto"])

        auto_cond_area = auto_geo["conditioned_floor_area_m2"]
        la_cond_area = la_geo["conditioned_floor_area_m2"]

        auto_sql_total_kwh = sum(auto_eu[r] for r in END_USES)
        la_sql_total_kwh = sum(la_eu[r] for r in END_USES)
        auto_sql_eui = auto_sql_total_kwh / auto_cond_area
        la_sql_eui = la_sql_total_kwh / la_cond_area

        # control row: recomputed la eui (sql-based) vs official; auto eui taken from
        # production's own 05_results.csv total_eui_kwh_m2 (see module docstring).
        reproduced_ratio = official_la_total_eui / official_auto_total_eui
        recomputed_la_vs_official_pct = (
            100.0 * (la_sql_eui - official_la_total_eui) / official_la_total_eui
        )
        auto_sql_vs_official_pct = (
            100.0 * (auto_sql_eui - official_auto_total_eui) / official_auto_total_eui
        )

        control_rows.append({
            "cell": cell,
            "osm_id": osm_id,
            "official_auto_total_eui_kwh_m2": official_auto_total_eui,
            "official_la_total_eui_kwh_m2": official_la_total_eui,
            "official_reproduced_ratio_la_over_auto": round(reproduced_ratio, 4),
            "sql_recomputed_la_total_eui_kwh_m2": round(la_sql_eui, 4),
            "sql_recomputed_la_vs_official_pct": round(recomputed_la_vs_official_pct, 4),
            "sql_recomputed_auto_total_eui_kwh_m2": round(auto_sql_eui, 4),
            "sql_recomputed_auto_vs_official_total_eui_pct": round(auto_sql_vs_official_pct, 4),
            "auto_water_systems_district_heating_kwh": round(
                auto_eu["_water_systems_district_heating_kwh"], 3
            ),
            "la_water_systems_district_heating_kwh": round(
                la_eu["_water_systems_district_heating_kwh"], 3
            ),
            "reconcile_resid_pct_auto": round(
                100.0 * abs(auto_sql_total_kwh - auto_eu["_abups_total_kwh"])
                / auto_eu["_abups_total_kwh"], 4
            ) if auto_eu["_abups_total_kwh"] else None,
            "reconcile_resid_pct_la": round(
                100.0 * abs(la_sql_total_kwh - la_eu["_abups_total_kwh"])
                / la_eu["_abups_total_kwh"], 4
            ) if la_eu["_abups_total_kwh"] else None,
        })

        gap_official_kwh_m2 = official_la_total_eui - official_auto_total_eui

        for eu in END_USES:
            auto_kwh_m2 = auto_eu[eu] / auto_cond_area
            la_kwh_m2 = la_eu[eu] / la_cond_area
            diff_kwh_m2 = la_kwh_m2 - auto_kwh_m2
            share_of_gap_pct = (
                100.0 * diff_kwh_m2 / gap_official_kwh_m2 if gap_official_kwh_m2 else None
            )
            long_rows.append({
                "cell": cell,
                "osm_id": osm_id,
                "end_use": eu,
                "auto_kwh_m2": round(auto_kwh_m2, 4),
                "layout_assign_kwh_m2": round(la_kwh_m2, 4),
                "diff_kwh_m2_la_minus_auto": round(diff_kwh_m2, 4),
                "share_of_official_gap_pct": (
                    round(share_of_gap_pct, 2) if share_of_gap_pct is not None else None
                ),
            })

        for mode, geo in [("auto", auto_geo), ("layout_assign", la_geo)]:
            meta_rows.append({
                "cell": cell,
                "osm_id": osm_id,
                "mode": mode,
                **geo,
            })

    long_df = pd.DataFrame(long_rows)
    meta_df = pd.DataFrame(meta_rows)
    control_df = pd.DataFrame(control_rows)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    long_df.to_csv(OUT_CSV, index=False)
    meta_df.to_csv(OUT_META_CSV, index=False)

    print("=== per-building control ===")
    print(control_df.to_string(index=False))

    # pooled share-of-gap, area-weighted by floor_area_m2_auto (matches decomposition
    # script's pooled() weighting)
    weights = per_building.loc[[b for b in BUILDINGS]]["floor_area_m2_auto"]
    weights.index = pd.MultiIndex.from_tuples(BUILDINGS, names=["cell", "osm_id"])
    pooled_rows = []
    for eu in END_USES:
        sub = long_df[long_df["end_use"] == eu].set_index(["cell", "osm_id"])
        w = weights.loc[sub.index]
        pooled_diff = (sub["diff_kwh_m2_la_minus_auto"] * w).sum() / w.sum()
        pooled_rows.append({"end_use": eu, "pooled_diff_kwh_m2": round(pooled_diff, 4)})
    pooled_df = pd.DataFrame(pooled_rows)

    auto_pooled = (control_df["official_auto_total_eui_kwh_m2"]
                   * weights.loc[[(r["cell"], r["osm_id"]) for _, r in control_df.iterrows()]].values).sum() \
                  / weights.sum()
    la_pooled = (control_df["official_la_total_eui_kwh_m2"]
                 * weights.loc[[(r["cell"], r["osm_id"]) for _, r in control_df.iterrows()]].values).sum() \
                / weights.sum()
    pooled_gap_pct = 100.0 * (la_pooled - auto_pooled) / auto_pooled
    pooled_df["share_of_pooled_gap_pct"] = (
        pooled_df["pooled_diff_kwh_m2"] / (la_pooled - auto_pooled) * 100.0
    ).round(2)

    print("\n=== pooled (area-weighted by floor_area_m2_auto) end-use diff ===")
    print(pooled_df.to_string(index=False))
    print(f"\npooled auto EUI = {auto_pooled:.4f}  pooled la EUI = {la_pooled:.4f}  "
          f"pooled gap = {pooled_gap_pct:.4f}%  (target -23.61%)")

    print("\n=== geometry / zoning / envelope / HVAC sizing ===")
    print(meta_df.to_string(index=False))

    pooled_df.to_csv(OUT_CSV.with_name("open03_enduse_localisation_pooled.csv"), index=False)
    print(f"\nwrote {OUT_CSV}, {OUT_META_CSV}, "
          f"{OUT_CSV.with_name('open03_enduse_localisation_pooled.csv')}")


if __name__ == "__main__":
    main()
