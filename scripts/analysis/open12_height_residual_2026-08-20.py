"""OPEN-12 T04 -- name the third 100%-residual cell and lock the replacement figures.

Plan: docs/docs_ACTIVE/openings/implemenation/previous/PLAN_five-items-2026-08-20-late.md, T04.

`extra/MEASUREMENT_open-12_height-residual-retrace.md` (T05 of an earlier plan) already
established that the register's original 36.4% / 19.2% only reproduce on a gitignored,
never-committed UTCI-arc scratch dataset, and that the fleet's own tracked Stage-1 inputs read
100.00% / 100.00% for `nyc_rural` / `austin_rural`, with a third cell -- `nyc_suburban`, used as
a control in that task -- also at 100.0000% but never formally named as the third cell in the
register. That prior task read four cells (the two named ones plus `nyc_suburban` and
`austin_centre` as controls) off `docs/docs_VALIDATION/validations/overAll/results/phaseE/`.

This task reads all 12 cells off the currently-adopted run-4 corpus
(`evidence/open48_refleet4/<cell>/01_buildings.gpkg`), which is the corpus every other task in
this plan (T01-T03) uses, and checks whether `04_simulation_manifest.parquet` carries a resolved
height_m value anywhere (it does not, in any cell checked -- it is a run-status manifest:
idf_path/work_dir/sql_path/status/..., no height field).

No fix, no code change, no simulation. Diagnosis only.

Emits openubem/outputs/comparisons/open12_height_residual.csv: one row per cell.
"""

from __future__ import annotations

import csv
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROOT = REPO_ROOT / "evidence" / "open48_refleet4"

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

OUTPUT_CSV = REPO_ROOT / "openubem" / "outputs" / "comparisons" / "open12_height_residual.csv"


def manifest_has_resolved_height(cell: str) -> bool:
    path = EVIDENCE_ROOT / cell / "04_simulation_manifest.parquet"
    df = pd.read_parquet(path)
    return any("height" in c.lower() for c in df.columns)


def main() -> None:
    rows = []
    for cell in CELLS:
        gpkg_path = EVIDENCE_ROOT / cell / "01_buildings.gpkg"
        gdf = gpd.read_file(gpkg_path, columns=["osm_id", "height_m", "provenance_height_m"])
        n = len(gdf)
        n_missing = int(gdf["height_m"].isna().sum())
        prov_counts = gdf["provenance_height_m"].value_counts(dropna=False).to_dict()
        n_osm_observed = int(prov_counts.get("OSM_OBSERVED", 0))
        n_osm_missing = int(prov_counts.get("OSM_MISSING", 0))
        n_other_provenance = n - n_osm_observed - n_osm_missing
        manifest_resolved = manifest_has_resolved_height(cell)
        n_filled_by_manifest = 0
        residual_pct = round(100.0 * n_missing / n, 4) if n else float("nan")
        rows.append({
            "cell": cell,
            "n_buildings": n,
            "n_missing_height_m_source": n_missing,
            "n_osm_observed": n_osm_observed,
            "n_osm_missing_provenance": n_osm_missing,
            "n_other_provenance": n_other_provenance,
            "manifest_carries_resolved_height": manifest_resolved,
            "n_filled_by_manifest_mechanism": n_filled_by_manifest,
            "residual_share_pct": residual_pct,
            "at_100pct": n_missing == n,
        })

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    total_n = sum(r["n_buildings"] for r in rows)
    total_missing = sum(r["n_missing_height_m_source"] for r in rows)
    cells_at_100 = [r["cell"] for r in rows if r["at_100pct"]]

    print(f"Wrote {OUTPUT_CSV} ({len(rows)} rows)")
    print("C9 -- sum of per-cell n:", total_n)
    print("Fleet-wide n missing height_m at source (sum of per-cell n_missing):", total_missing)
    print("C10 -- cells at 100% missing:", cells_at_100)
    for r in rows:
        print(f"  {r['cell']:16s} n={r['n_buildings']:5d} missing={r['n_missing_height_m_source']:5d} "
              f"residual={r['residual_share_pct']:8.4f}% manifest_resolved={r['manifest_carries_resolved_height']}")


if __name__ == "__main__":
    main()
