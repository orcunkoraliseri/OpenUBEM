"""T03 -- OPEN-56 / OPEN-01: does the Zone.Volume anomaly reach the EUI denominator?

Fleet-wide census: EnergyPlus's own simulated floor area (multiplier-aware "Total
Building Area", derived from each building's eplusout.eio) vs the declared
denominator footprint_area_m2 x levels from each cell's 01_buildings.gpkg.

Also a targeted, level-independent recheck of nyc_centre/relation_3566904's
baseline-vs-treated Total Building Area shift (157,115 -> 37,551 m2, ~/4.18),
read directly from the surviving OPEN-56 A/B work directory
(%TEMP%/open56_fleet_cost/nyc_centre__relation_3566904), cross-validated against
the same number as EnergyPlus itself reports it (eplusout.sql "Building Area" /
"Total Building Area" / "Area"), independent of the eio-based re-derivation.

Read-only. No cluster access. No production code touched. No .sql file is copied
anywhere -- both .sql reads here are local, in place, for verification only.

Run: ./.venv/Scripts/python.exe scripts/analysis/open56_denominator_census_2026-08-19.py
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

RUN3_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\open48_refleet3")
AB_WORKDIR = Path(r"C:\Users\o_iseri\AppData\Local\Temp\open56_fleet_cost\nyc_centre__relation_3566904")

OUT_DIR = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons")
PER_BUILDING_CSV = OUT_DIR / "open56_denominator_census_2026-08-19.csv"
CELL_SUMMARY_CSV = OUT_DIR / "open56_denominator_census_cellsummary_2026-08-19.csv"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

HEADER_MARKER = "! <Zone Information>"
DATA_PREFIX = " Zone Information,"
FIELD_FLOOR_AREA = "Floor Area {m2}"
FIELD_ZONE_MULT = "Zone Multiplier"
FIELD_ZONE_LIST_MULT = "Zone List Multiplier"
FIELD_PART_OF_TOTAL = "Part of Total Building Area"


def parse_eio_zone_area(path: Path) -> dict:
    """Stream one .eio file, header-name-mapped. Multiplier-aware Total Building
    Area = sum(Floor Area * Zone Multiplier * Zone List Multiplier) over zones
    flagged 'Part of Total Building Area' == Yes. Same method as
    scripts/analysis/e02_t04_floor_area_audit.py:parse_eio_zone_area."""
    header_idx = None
    n_zones = 0
    area_plain = 0.0
    area_mult = 0.0
    max_zm = 0.0
    max_zlm = 0.0
    n_excluded = 0
    n_row_errors = 0
    saw_header = False
    in_block = False

    try:
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
            for line in f:
                if not saw_header:
                    if line.startswith(HEADER_MARKER):
                        raw = next(csv.reader([line]))
                        names = [c.strip() for c in raw]
                        header_idx = {name: i for i, name in enumerate(names)}
                        saw_header = True
                    continue
                if line.startswith(DATA_PREFIX):
                    in_block = True
                    n_zones += 1
                    try:
                        row = next(csv.reader([line]))
                        floor_area = float(row[header_idx[FIELD_FLOOR_AREA]])
                        zm = float(row[header_idx[FIELD_ZONE_MULT]])
                        zlm = float(row[header_idx[FIELD_ZONE_LIST_MULT]])
                        part = row[header_idx[FIELD_PART_OF_TOTAL]].strip()
                    except (KeyError, ValueError, IndexError):
                        n_row_errors += 1
                        continue
                    if zm > max_zm:
                        max_zm = zm
                    if zlm > max_zlm:
                        max_zlm = zlm
                    if part == "Yes":
                        area_plain += floor_area
                        area_mult += floor_area * zm * zlm
                    else:
                        n_excluded += 1
                elif in_block:
                    break
    except OSError as e:
        return dict(
            n_zones=0, area_plain_m2=0.0, area_multiplier_aware_m2=0.0,
            max_zone_multiplier=0, max_zone_list_multiplier=0,
            n_zones_excluded_not_in_total_area=0,
            parse_status=f"file_error:{e}",
        )

    if not saw_header:
        status = "no_zone_information_header"
    elif n_zones == 0:
        status = "header_found_zero_rows"
    elif n_row_errors > 0:
        status = f"ok_with_{n_row_errors}_row_errors"
    else:
        status = "ok"

    return dict(
        n_zones=n_zones,
        area_plain_m2=area_plain,
        area_multiplier_aware_m2=area_mult,
        max_zone_multiplier=int(round(max_zm)),
        max_zone_list_multiplier=int(round(max_zlm)),
        n_zones_excluded_not_in_total_area=n_excluded,
        parse_status=status,
    )


def read_sql_total_building_area(sql_path: Path):
    if not sql_path.exists():
        return None
    try:
        con = sqlite3.connect(str(sql_path))
        q = ("SELECT Value FROM TabularDataWithStrings WHERE TableName=? "
             "AND RowName=? AND ColumnName=?")
        r = con.execute(q, ("Building Area", "Total Building Area", "Area")).fetchone()
        con.close()
        return float(r[0]) if r else None
    except Exception as exc:  # noqa: BLE001
        print(f"  [sql-read-error] {sql_path}: {exc}", file=sys.stderr)
        return None


def stem_to_osm_id(stem: str) -> str:
    # '_partN' suffixed stems (e.g. relation_17953040_part0) are pre-split
    # geometries: 01_buildings.gpkg already carries them as separate osm_id
    # rows ('relation/17953040_part0'), each with its own footprint_area_m2.
    # Do NOT merge them back -- only the first underscore (type/id separator)
    # is a slash.
    return stem.replace("_", "/", 1)


def cell_available(cell: str) -> bool:
    sim_out = RUN3_ROOT / cell / "sim_out"
    if not sim_out.is_dir():
        return False
    return any(sim_out.glob("*/eplusout.eio"))


def census_one_cell(cell: str, rows_out: list, reconcile: dict) -> None:
    gpkg_path = RUN3_ROOT / cell / "01_buildings.gpkg"
    idfs_dir = RUN3_ROOT / cell / "step3" / "idfs"
    sim_out = RUN3_ROOT / cell / "sim_out"

    gdf = gpd.read_file(gpkg_path)
    n_gpkg = len(gdf)
    decl = gdf.set_index("osm_id")[["footprint_area_m2", "levels", "underground"]]

    n_idf = sum(1 for _ in idfs_dir.glob("*.idf")) if idfs_dir.is_dir() else 0
    sim_stems = sorted(p.name for p in sim_out.iterdir() if p.is_dir())
    n_sim = len(sim_stems)

    # group multi-part stems (e.g. relation_X_part0/part1) by base osm_id --
    # exactly 2 such stems fleet-wide (both in nyc_urban), summed to one row.
    per_osm_agg: dict = {}
    for stem in sim_stems:
        eio_path = sim_out / stem / "eplusout.eio"
        parsed = parse_eio_zone_area(eio_path)
        osm_id = stem_to_osm_id(stem)
        if osm_id not in per_osm_agg:
            per_osm_agg[osm_id] = dict(
                n_zones=0, area_plain_m2=0.0, area_multiplier_aware_m2=0.0,
                max_zone_multiplier=0, max_zone_list_multiplier=0,
                n_zones_excluded_not_in_total_area=0, parse_status_list=[],
                n_parts=0,
            )
        agg = per_osm_agg[osm_id]
        agg["n_zones"] += parsed["n_zones"]
        agg["area_plain_m2"] += parsed["area_plain_m2"]
        agg["area_multiplier_aware_m2"] += parsed["area_multiplier_aware_m2"]
        agg["max_zone_multiplier"] = max(agg["max_zone_multiplier"], parsed["max_zone_multiplier"])
        agg["max_zone_list_multiplier"] = max(agg["max_zone_list_multiplier"], parsed["max_zone_list_multiplier"])
        agg["n_zones_excluded_not_in_total_area"] += parsed["n_zones_excluded_not_in_total_area"]
        agg["parse_status_list"].append(parsed["parse_status"])
        agg["n_parts"] += 1

    n_osm_sim = len(per_osm_agg)
    osm_ids_sim = set(per_osm_agg.keys())
    osm_ids_gpkg = set(decl.index)
    sim_not_in_gpkg = osm_ids_sim - osm_ids_gpkg
    gpkg_not_in_sim = osm_ids_gpkg - osm_ids_sim

    reconcile[cell] = dict(
        n_gpkg=n_gpkg, n_idf=n_idf, n_sim_dirs=n_sim, n_osm_after_part_merge=n_osm_sim,
        n_sim_not_in_gpkg=len(sim_not_in_gpkg), n_gpkg_not_in_sim=len(gpkg_not_in_sim),
        sample_sim_not_in_gpkg=sorted(sim_not_in_gpkg)[:5],
        sample_gpkg_not_in_sim=sorted(gpkg_not_in_sim)[:5],
    )

    for osm_id, agg in per_osm_agg.items():
        footprint = levels = underground = None
        if osm_id in decl.index:
            footprint = decl.loc[osm_id, "footprint_area_m2"]
            levels = decl.loc[osm_id, "levels"]
            underground = decl.loc[osm_id, "underground"]
            if hasattr(footprint, "iloc"):
                footprint = footprint.iloc[0]
                levels = levels.iloc[0]
                underground = underground.iloc[0]
        declared_area = None
        ratio = None
        if footprint is not None and pd.notna(footprint) and levels is not None and pd.notna(levels):
            declared_area = float(footprint) * float(levels)
            if declared_area > 0:
                ratio = agg["area_multiplier_aware_m2"] / declared_area

        status_list = agg["parse_status_list"]
        parse_status = status_list[0] if len(status_list) == 1 else "|".join(sorted(set(status_list)))

        rows_out.append(dict(
            cell=cell, osm_id=osm_id, n_parts=agg["n_parts"],
            footprint_area_m2=footprint, levels=levels, underground=underground,
            declared_area_m2=declared_area,
            n_zones=agg["n_zones"],
            area_plain_m2=round(agg["area_plain_m2"], 3),
            area_multiplier_aware_m2=round(agg["area_multiplier_aware_m2"], 3),
            max_zone_multiplier=agg["max_zone_multiplier"],
            max_zone_list_multiplier=agg["max_zone_list_multiplier"],
            n_zones_excluded_not_in_total_area=agg["n_zones_excluded_not_in_total_area"],
            ratio=ratio,
            parse_status=parse_status,
        ))


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    available_cells = [c for c in CELLS if cell_available(c)]
    unavailable_cells = [c for c in CELLS if c not in available_cells]
    print(f"[T03] cells with sim_out present locally: {len(available_cells)}/{len(CELLS)}", file=sys.stderr)
    print(f"[T03] available: {available_cells}", file=sys.stderr)
    print(f"[T03] UNAVAILABLE (no sim_out / zero .eio on disk, excluded from census): {unavailable_cells}", file=sys.stderr)

    rows: list = []
    reconcile: dict = {}
    for cell in available_cells:
        census_one_cell(cell, rows, reconcile)

    df = pd.DataFrame(rows)
    df.to_csv(PER_BUILDING_CSV, index=False)
    print(f"[T03] wrote {PER_BUILDING_CSV} ({len(df)} rows)", file=sys.stderr)

    print("\n[T03] row-count reconciliation per cell (idf / sim_out dirs / after part-merge / gpkg):", file=sys.stderr)
    recon_rows = []
    for cell, r in reconcile.items():
        print(f"  {cell}: idf={r['n_idf']} sim_dirs={r['n_sim_dirs']} "
              f"osm_after_merge={r['n_osm_after_part_merge']} gpkg={r['n_gpkg']} "
              f"sim_not_in_gpkg={r['n_sim_not_in_gpkg']} gpkg_not_in_sim={r['n_gpkg_not_in_sim']}",
              file=sys.stderr)
        if r["n_sim_not_in_gpkg"] or r["n_gpkg_not_in_sim"]:
            print(f"    sample sim_not_in_gpkg: {r['sample_sim_not_in_gpkg']}", file=sys.stderr)
            print(f"    sample gpkg_not_in_sim: {r['sample_gpkg_not_in_sim']}", file=sys.stderr)
        recon_rows.append(dict(cell=cell, **r))
    pd.DataFrame(recon_rows).drop(columns=["sample_sim_not_in_gpkg", "sample_gpkg_not_in_sim"]).to_csv(
        CELL_SUMMARY_CSV, index=False
    )
    print(f"[T03] wrote {CELL_SUMMARY_CSV}", file=sys.stderr)

    # ---- control: levels == 1, no multiplier -> ratio should be ~1.0 -------
    ctrl = df[(df["levels"] == 1.0) & (df["max_zone_multiplier"] <= 1) &
              (df["max_zone_list_multiplier"] <= 1) & df["ratio"].notna()]
    print(f"\n[T03] CONTROL levels==1 & no multiplier: n={len(ctrl)}", file=sys.stderr)
    if len(ctrl):
        print(f"  ratio median={ctrl['ratio'].median():.4f} mean={ctrl['ratio'].mean():.4f} "
              f"p10={ctrl['ratio'].quantile(0.10):.4f} p90={ctrl['ratio'].quantile(0.90):.4f}",
              file=sys.stderr)
        outside = ctrl[(ctrl["ratio"] < 0.9) | (ctrl["ratio"] > 1.1)]
        print(f"  outside +/-10%% of 1.0: {len(outside)} / {len(ctrl)}", file=sys.stderr)
        if len(outside):
            print(outside[["cell", "osm_id", "footprint_area_m2", "declared_area_m2",
                            "area_multiplier_aware_m2", "ratio", "n_zones",
                            "n_zones_excluded_not_in_total_area"]].to_string(index=False),
                  file=sys.stderr)
    else:
        print("  CONTROL EMPTY -- cannot validate the join. Treat all downstream ratios as unverified.",
              file=sys.stderr)

    # ---- ratio distribution, pooled and per cell -----------------------
    have_ratio = df[df["ratio"].notna()].copy()
    n_no_declared = len(df) - len(have_ratio)
    print(f"\n[T03] buildings with a usable declared_area (footprint & levels present): "
          f"{len(have_ratio)} / {len(df)} ({n_no_declared} dropped for missing footprint/levels)",
          file=sys.stderr)

    print("\n[T03] ratio distribution (sim / declared), pooled:", file=sys.stderr)
    print(f"  median={have_ratio['ratio'].median():.4f}  "
          f"IQR=[{have_ratio['ratio'].quantile(0.25):.4f}, {have_ratio['ratio'].quantile(0.75):.4f}]",
          file=sys.stderr)
    outside_10 = have_ratio[(have_ratio["ratio"] < 0.9) | (have_ratio["ratio"] > 1.1)]
    print(f"  outside +/-10%%: {len(outside_10)} / {len(have_ratio)} "
          f"({100 * len(outside_10) / len(have_ratio):.2f}%%)", file=sys.stderr)

    print("\n[T03] ratio distribution per cell:", file=sys.stderr)
    for cell, g in have_ratio.groupby("cell"):
        out10 = g[(g["ratio"] < 0.9) | (g["ratio"] > 1.1)]
        print(f"  {cell}: n={len(g)} median={g['ratio'].median():.4f} "
              f"IQR=[{g['ratio'].quantile(0.25):.4f}, {g['ratio'].quantile(0.75):.4f}] "
              f"outside+/-10%%={len(out10)}", file=sys.stderr)

    # ---- outlier / anomaly separation: near-4.18 pattern with vs without a multiplier
    print("\n[T03] outliers outside +/-10%%, multiplier explanation split:", file=sys.stderr)
    outside_10 = outside_10.copy()
    outside_10["has_multiplier"] = (outside_10["max_zone_multiplier"] > 1) | (outside_10["max_zone_list_multiplier"] > 1)
    outside_10["near_4p18_low"] = (outside_10["ratio"] > (1 / 4.18) * 0.85) & (outside_10["ratio"] < (1 / 4.18) * 1.15)
    n_benign = int(outside_10["has_multiplier"].sum())
    n_unexplained = int((~outside_10["has_multiplier"]).sum())
    n_near_4p18_unexplained = int((outside_10["near_4p18_low"] & ~outside_10["has_multiplier"]).sum())
    print(f"  total outliers: {len(outside_10)}", file=sys.stderr)
    print(f"  benign (carries a multiplier > 1): {n_benign}", file=sys.stderr)
    print(f"  UNEXPLAINED (no multiplier): {n_unexplained}", file=sys.stderr)
    print(f"  of those, near the 1/4.18 ratio specifically: {n_near_4p18_unexplained}", file=sys.stderr)
    if n_unexplained:
        cols = ["cell", "osm_id", "footprint_area_m2", "levels", "declared_area_m2",
                "area_multiplier_aware_m2", "ratio", "n_zones", "max_zone_multiplier",
                "max_zone_list_multiplier", "n_zones_excluded_not_in_total_area", "parse_status"]
        print(outside_10.loc[~outside_10["has_multiplier"], cols].to_string(index=False), file=sys.stderr)

    outside_10.to_csv(OUT_DIR / "open56_denominator_census_outliers_2026-08-19.csv", index=False)

    # ---- targeted recheck: nyc_centre / relation_3566904, both arms --------
    print("\n[T03] targeted recheck: nyc_centre/relation_3566904 (OPEN-56 A/B work dir)", file=sys.stderr)
    if not AB_WORKDIR.is_dir():
        print(f"  STOP: {AB_WORKDIR} not present on disk -- cannot recheck.", file=sys.stderr)
    else:
        base_out = AB_WORKDIR / "base_out"
        treat_out = AB_WORKDIR / "treat_out"
        base_eio = parse_eio_zone_area(base_out / "eplusout.eio")
        treat_eio = parse_eio_zone_area(treat_out / "eplusout.eio")
        base_sql = read_sql_total_building_area(base_out / "eplusout.sql")
        treat_sql = read_sql_total_building_area(treat_out / "eplusout.sql")
        print(f"  eio-derived (multiplier-aware) Total Building Area: "
              f"baseline={base_eio['area_multiplier_aware_m2']:.1f} m2  "
              f"treated={treat_eio['area_multiplier_aware_m2']:.1f} m2", file=sys.stderr)
        print(f"  sql-reported ('Building Area'/'Total Building Area'/'Area'): "
              f"baseline={base_sql}  treated={treat_sql}", file=sys.stderr)
        if base_sql and treat_sql:
            print(f"  ratio baseline/treated = {base_sql / treat_sql:.4f} "
                  f"(overnight pass reported 157115/37551 = {157115/37551:.4f})", file=sys.stderr)
        if base_sql:
            eio_vs_sql = base_eio["area_multiplier_aware_m2"] / base_sql
            print(f"  cross-check baseline: eio-derived / sql-reported = {eio_vs_sql:.6f} "
                  f"(should be ~1.0 if the two methods agree)", file=sys.stderr)
        if treat_sql:
            eio_vs_sql_t = treat_eio["area_multiplier_aware_m2"] / treat_sql
            print(f"  cross-check treated:  eio-derived / sql-reported = {eio_vs_sql_t:.6f}", file=sys.stderr)

    print("\nDONE", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
