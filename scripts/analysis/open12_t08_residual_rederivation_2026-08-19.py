"""T08 (PLAN_twenty-items-2026-08-19.md) -- OPEN-12: re-derive the height_m residual on
run-4 (open48_refleet4) Stage-1 files, the fleet's current tracked-artifact-equivalent inputs.

Per cell: n buildings, n height_m absent / present, split present into "observed" (raw source,
not fused/imputed) vs "backfilled" (any imputation/fusion provenance token), cross-checked
against data_quality_flag's no_height token.
"""
import os
import csv

import geopandas as gpd

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
ROOT = os.path.join(os.environ["LOCALAPPDATA"], "Temp", "ubem_validation", "open48_refleet4")
OUT_CSV = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open12_t08_residual_rederivation_2026-08-19.csv"


def main():
    rows = []
    total = 0
    total_absent = 0
    total_backfilled = 0
    total_observed = 0
    total_flag_no_height = 0
    total_disagree = 0
    all_prov_values = set()

    for cell in CELLS:
        path = os.path.join(ROOT, cell, "01_buildings.gpkg")
        if not os.path.isfile(path):
            print(f"MISSING: {cell} -> {path}")
            continue
        g = gpd.read_file(path)
        n = len(g)
        absent = g["height_m"].isna()
        n_absent = int(absent.sum())

        prov = g["provenance_height_m"]
        all_prov_values.update(prov.dropna().unique().tolist())
        present = ~absent
        # "observed" = present with a raw-source provenance token (or empty/None provenance,
        # meaning it came straight from OSM and was never touched by any imputation tier);
        # "backfilled" = present with any non-raw provenance token (fusion/spatial/ml/
        # statistical/heuristic tier stamped it).
        raw_tokens = {None, "", "OSM_OBSERVED", "RAW_OSM"}
        is_raw = prov.isna() | prov.isin([t for t in raw_tokens if t is not None]) | (prov == "")
        n_observed = int((present & is_raw).sum())
        n_backfilled = int((present & ~is_raw).sum())

        flag = g["data_quality_flag"].astype(str)
        flag_no_height = flag.str.contains("no_height", na=False)
        n_flag_no_height = int(flag_no_height.sum())
        disagree = int((absent != flag_no_height).sum())

        pct_absent = round(100 * n_absent / n, 4) if n else 0.0
        rows.append({
            "cell": cell, "n": n, "n_absent": n_absent, "pct_absent": pct_absent,
            "n_observed": n_observed, "n_backfilled": n_backfilled,
            "n_flag_no_height": n_flag_no_height, "n_disagree_absent_vs_flag": disagree,
        })
        total += n
        total_absent += n_absent
        total_backfilled += n_backfilled
        total_observed += n_observed
        total_flag_no_height += n_flag_no_height
        total_disagree += disagree

    rows.append({
        "cell": "FLEET_TOTAL", "n": total, "n_absent": total_absent,
        "pct_absent": round(100 * total_absent / total, 4) if total else 0.0,
        "n_observed": total_observed, "n_backfilled": total_backfilled,
        "n_flag_no_height": total_flag_no_height,
        "n_disagree_absent_vs_flag": total_disagree,
    })

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("distinct provenance_height_m values fleet-wide:", sorted(all_prov_values))
    for r in rows:
        print(r)

    hundred_pct_cells = [r["cell"] for r in rows[:-1] if r["pct_absent"] == 100.0]
    print("\n100%-absent cells:", hundred_pct_cells)
    print("sum of buildings in 100%-absent cells:",
          sum(r["n"] for r in rows[:-1] if r["cell"] in hundred_pct_cells))


if __name__ == "__main__":
    main()
