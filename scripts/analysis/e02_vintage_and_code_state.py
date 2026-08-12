"""T03 -- Vintage persistence (OPEN-30) and the one-code-state demonstration (OPEN-01c).

(a) Reads the persisted `vintage_standard` column from all 60 E02 03_manifest.parquet
files and reports its value distribution fleet-wide, per cell and per mode. Does not
call resolve_vintage() or re-derive vintage in any way -- this is provenance, not
reconstruction (register RULING D). Cross-checks la_rural's persisted vintage against
year_built in that cell's raw 01_buildings.gpkg, independently of the manifest join.

(b) Assembles local evidence bearing on whether all five modes came from one code
state: the two e02_generation_summary__*.json files, the manifest column schema
across all 60 files, IDF/manifest mtimes per (cell, mode), and the two e02_run*.log
files. States what this evidence does and does not prove.

Plan: docs/docs_ACTIVE/openings/implemenation/PLAN_e02-audit-and-closure.md, T03.
"""

import csv
import json
import os
import time
from pathlib import Path

import geopandas as gpd
import pandas as pd

FLEET_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_fleet")
PHASED_RESULTS = Path(
    r"C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_VALIDATION\validations\overAll\results\phaseE"
)
FIVE_MODE_DIR = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_five_mode")

OUT_DIR = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons")
OUT_VINTAGE = OUT_DIR / "open30_vintage_distribution.csv"
OUT_CODESTATE = OUT_DIR / "open01c_code_state_evidence.csv"
OUT_LARURAL_CROSSCHECK = OUT_DIR / "open30_la_rural_year_built_crosscheck.csv"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
MODES = ["auto", "building", "floor", "fast_zone", "layout_assign"]

GEN_SUMMARY_FILES = {
    "batch_4cells_austin_centre": FLEET_ROOT / "e02_generation_summary__batch_4cells_austin_centre.json",
    "la_urban_la_suburban_la_rural": FLEET_ROOT / "e02_generation_summary__la_urban_la_suburban_la_rural.json",
}


def load_manifest(cell, mode):
    mp = FLEET_ROOT / cell / f"step3_{mode}" / "03_manifest.parquet"
    if not mp.exists():
        return None, mp
    return pd.read_parquet(mp), mp


def part_a_vintage_distribution():
    rows = []
    frames = []
    n_manifests_read = 0
    total_rows = 0

    for cell in CELLS:
        for mode in MODES:
            df, mp = load_manifest(cell, mode)
            if df is None:
                rows.append({
                    "scope": "mode_cell", "cell": cell, "mode": mode,
                    "vintage_standard": "MANIFEST_MISSING", "n": 0,
                    "n_rows_in_scope": 0, "pct_within_scope": 0.0,
                })
                continue
            n_manifests_read += 1
            total_rows += len(df)
            vc = df["vintage_standard"].fillna("<NULL>").value_counts()
            n_scope = len(df)
            for val, n in vc.items():
                rows.append({
                    "scope": "mode_cell", "cell": cell, "mode": mode,
                    "vintage_standard": val, "n": int(n),
                    "n_rows_in_scope": n_scope,
                    "pct_within_scope": round(100.0 * n / n_scope, 4) if n_scope else 0.0,
                })
            frames.append(df.assign(_cell=cell, _mode=mode))

    all_df = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    # per-cell (all 5 modes pooled)
    for cell in CELLS:
        sub = all_df[all_df["_cell"] == cell]
        n_scope = len(sub)
        vc = sub["vintage_standard"].fillna("<NULL>").value_counts()
        for val, n in vc.items():
            rows.append({
                "scope": "cell", "cell": cell, "mode": "ALL",
                "vintage_standard": val, "n": int(n),
                "n_rows_in_scope": n_scope,
                "pct_within_scope": round(100.0 * n / n_scope, 4) if n_scope else 0.0,
            })

    # per-mode (all 12 cells pooled)
    for mode in MODES:
        sub = all_df[all_df["_mode"] == mode]
        n_scope = len(sub)
        vc = sub["vintage_standard"].fillna("<NULL>").value_counts()
        for val, n in vc.items():
            rows.append({
                "scope": "mode", "cell": "ALL", "mode": mode,
                "vintage_standard": val, "n": int(n),
                "n_rows_in_scope": n_scope,
                "pct_within_scope": round(100.0 * n / n_scope, 4) if n_scope else 0.0,
            })

    # fleet-wide
    n_scope = len(all_df)
    vc = all_df["vintage_standard"].fillna("<NULL>").value_counts() if n_scope else pd.Series(dtype=int)
    for val, n in vc.items():
        rows.append({
            "scope": "fleet", "cell": "ALL", "mode": "ALL",
            "vintage_standard": val, "n": int(n),
            "n_rows_in_scope": n_scope,
            "pct_within_scope": round(100.0 * n / n_scope, 4) if n_scope else 0.0,
        })

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_VINTAGE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "scope", "cell", "mode", "vintage_standard", "n",
            "n_rows_in_scope", "pct_within_scope",
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    n_distinct_fleet = vc.shape[0]
    largest_share = round(100.0 * vc.max() / n_scope, 4) if n_scope else 0.0
    largest_value = vc.idxmax() if n_scope else None

    print("=== OPEN-30 vintage distribution ===")
    print(f"manifests read: {n_manifests_read} / 60")
    print(f"fleet-wide rows: {n_scope} (expected 40,800)")
    print(f"fleet-wide distinct vintage_standard values: {n_distinct_fleet}")
    print(f"fleet-wide value counts:\n{vc}")
    print(f"largest value: {largest_value}  share: {largest_share}%")

    return all_df, {
        "n_manifests_read": n_manifests_read,
        "fleet_n_rows": n_scope,
        "n_distinct": n_distinct_fleet,
        "largest_value": largest_value,
        "largest_share_pct": largest_share,
        "value_counts": vc,
    }


def part_a_la_rural_crosscheck(all_df):
    gpkg_path = PHASED_RESULTS / "la_rural" / "01_buildings.gpkg"
    gdf = gpd.read_file(str(gpkg_path))
    year_built = gdf[["osm_id", "year_built"]].drop_duplicates(subset="osm_id")

    rows = []
    verdict_rows = []
    for mode in MODES:
        sub = all_df[(all_df["_cell"] == "la_rural") & (all_df["_mode"] == mode)]
        if sub.empty:
            continue
        merged = sub.merge(year_built, on="osm_id", how="left")
        for vintage_val, grp in merged.groupby(merged["vintage_standard"].fillna("<NULL>")):
            yb = grp["year_built"].dropna()
            rows.append({
                "mode": mode,
                "vintage_standard": vintage_val,
                "n_buildings": len(grp),
                "year_built_min": int(yb.min()) if len(yb) else None,
                "year_built_max": int(yb.max()) if len(yb) else None,
                "n_year_built_missing": int(grp["year_built"].isna().sum()),
            })
        is_2007 = merged["vintage_standard"] == "90.1-2007"
        is_pre1980 = merged["vintage_standard"] == "DOERefPre1980"
        yb_2007_known = merged.loc[is_2007, "year_built"].dropna()
        yb_pre1980_known = merged.loc[is_pre1980, "year_built"].dropna()

        n_2007 = int(is_2007.sum())
        n_2007_missing_yb = int(merged.loc[is_2007, "year_built"].isna().sum())
        n_2007_known_in_range = int(((yb_2007_known >= 2005) & (yb_2007_known <= 2007)).sum())

        n_pre1980 = int(is_pre1980.sum())
        n_pre1980_missing_yb = int(merged.loc[is_pre1980, "year_built"].isna().sum())
        n_pre1980_known_in_range = int(((yb_pre1980_known >= 1920) & (yb_pre1980_known <= 1979)).sum())

        verdict_rows.append({
            "mode": mode,
            "n_90.1-2007": n_2007,
            "n_90.1-2007_missing_year_built": n_2007_missing_yb,
            "n_90.1-2007_known_in_range_2005_2007": n_2007_known_in_range,
            "n_DOERefPre1980": n_pre1980,
            "n_DOERefPre1980_missing_year_built": n_pre1980_missing_yb,
            "n_DOERefPre1980_known_in_range_1920_1979": n_pre1980_known_in_range,
            "reproduces_R07_zero_crossover": bool(
                n_2007_known_in_range == (n_2007 - n_2007_missing_yb)
                and n_pre1980_known_in_range == (n_pre1980 - n_pre1980_missing_yb)
            ),
        })

    with open(OUT_LARURAL_CROSSCHECK, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "mode", "vintage_standard", "n_buildings",
            "year_built_min", "year_built_max", "n_year_built_missing",
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print("\n=== la_rural cross-check (all 5 modes) ===")
    for v in verdict_rows:
        print(v)

    return verdict_rows


def part_b_code_state_evidence():
    gen_summaries = {}
    for key, path in GEN_SUMMARY_FILES.items():
        if path.exists():
            gen_summaries[key] = json.load(open(path, encoding="utf-8"))

    covered_pairs = set()
    for key, d in gen_summaries.items():
        for arr_key, stats in d.get("manifest_stats", {}).items():
            covered_pairs.add((stats["cell"], stats["mode"]))

    rows = []
    for cell in CELLS:
        for mode in MODES:
            df, mp = load_manifest(cell, mode)
            idf_dir = FLEET_ROOT / cell / f"step3_{mode}" / "idfs"

            manifest_mtime = None
            n_manifest_cols = None
            has_vintage_col = None
            if mp.exists():
                manifest_mtime = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(os.stat(mp).st_mtime)
                )
            if df is not None:
                n_manifest_cols = len(df.columns)
                has_vintage_col = "vintage_standard" in df.columns

            idf_mtimes = []
            n_idfs = 0
            if idf_dir.exists():
                with os.scandir(idf_dir) as it:
                    for entry in it:
                        if entry.is_file():
                            n_idfs += 1
                            idf_mtimes.append(entry.stat().st_mtime)

            idf_dir_mtime_min = (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(min(idf_mtimes)))
                if idf_mtimes else None
            )
            idf_dir_mtime_max = (
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(max(idf_mtimes)))
                if idf_mtimes else None
            )

            rows.append({
                "cell": cell,
                "mode": mode,
                "manifest_mtime": manifest_mtime,
                "n_manifest_cols": n_manifest_cols,
                "has_vintage_col": has_vintage_col,
                "idf_dir_mtime_min": idf_dir_mtime_min,
                "idf_dir_mtime_max": idf_dir_mtime_max,
                "n_idfs": n_idfs,
                "covered_by_generation_summary_json": (cell, mode) in covered_pairs,
            })

    with open(OUT_CODESTATE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "cell", "mode", "manifest_mtime", "n_manifest_cols", "has_vintage_col",
            "idf_dir_mtime_min", "idf_dir_mtime_max", "n_idfs",
            "covered_by_generation_summary_json",
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    schemas = set()
    for cell in CELLS:
        for mode in MODES:
            df, _ = load_manifest(cell, mode)
            if df is not None:
                schemas.add(tuple(df.columns))
    n_distinct_schemas = len(schemas)

    all_mtimes_manifest = [
        os.stat(FLEET_ROOT / c / f"step3_{m}" / "03_manifest.parquet").st_mtime
        for c in CELLS for m in MODES
        if (FLEET_ROOT / c / f"step3_{m}" / "03_manifest.parquet").exists()
    ]
    span_seconds = max(all_mtimes_manifest) - min(all_mtimes_manifest) if all_mtimes_manifest else None

    print("\n=== OPEN-01(c) code-state evidence ===")
    print(f"distinct manifest schemas across 60 files: {n_distinct_schemas}")
    if all_mtimes_manifest:
        print(f"manifest mtime span: {time.ctime(min(all_mtimes_manifest))} .. "
              f"{time.ctime(max(all_mtimes_manifest))}  ({span_seconds:.0f} s)")
    print(f"(cell, mode) pairs covered by a generation_summary JSON: {len(covered_pairs)} / 60")
    print(f"cells with NO generation_summary JSON coverage at all: "
          f"{sorted(set(CELLS) - {c for c, m in covered_pairs})}")

    return {
        "n_distinct_schemas": n_distinct_schemas,
        "mtime_span_seconds": span_seconds,
        "n_pairs_covered_by_json": len(covered_pairs),
        "covered_pairs": covered_pairs,
    }


def part_b_run_logs():
    print("\n=== e02_run*.log inspection ===")
    for name in ["e02_run.log", "e02_run_2.log"]:
        p = FIVE_MODE_DIR / name
        if not p.exists():
            print(f"{name}: NOT FOUND")
            continue
        txt = p.read_bytes().decode("utf-8", errors="replace")
        cells_seen = sorted(set(
            line.split("CELL:")[1].split("(")[0].strip()
            for line in txt.splitlines() if "CELL:" in line
        ))
        has_memoryerror = "MemoryError" in txt
        has_traceback = "Traceback" in txt
        print(f"{name}: size={p.stat().st_size}B mtime={time.ctime(p.stat().st_mtime)} "
              f"cells_referenced={cells_seen} MemoryError={has_memoryerror} "
              f"Traceback={has_traceback}")


def main():
    all_df, vintage_summary = part_a_vintage_distribution()
    crosscheck = part_a_la_rural_crosscheck(all_df)
    codestate_summary = part_b_code_state_evidence()
    part_b_run_logs()

    print("\n=== SUMMARY ===")
    print(vintage_summary)
    print(crosscheck)
    print(codestate_summary)


if __name__ == "__main__":
    main()
