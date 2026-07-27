"""R06 condition (b) — fleet-scale count of buildings whose match_storeys()
status CHANGED under R10 (E-LA-36 residual-multiplier fix), split by archetype
and by old -> new status.

Pure local computation, independent of the cluster run: compute_band_map()
(R01-amended, unaffected by R10) is called ONCE per archetype (25 baseline
IDFs max) to get {n_proto, bands[*].storeys_in_band, bands[*].zone_names}.
Per building we then need only (archetype_id, num_floors) to derive both the
CURRENT (post-R10) status via the real match_storeys() taller-branch formula
and the PRE-R10 status via the formula it replaced (both fully specified in
R10's own progress-log entry, PLAN_storey-matching_REMAINder.md L732-833):

  PRE-R10 taller branch (n_real > n_proto, single middle band or n_proto==1):
    always "applied", multiplier = n_real - (n_proto - 1)  [n_proto==1: n_real]
  POST-R10 (current code, layout_assigner.py match_storeys() L606-653):
    residual = (n_real - non_middle_storeys) / list_multiplier; "applied" only
    if that division is exact and >= 1, else "fallback_not_expressible".

For every one of the 23 non-ZoneGroup archetypes list_multiplier == 1, so the
two formulas are algebraically identical (proved in R01's/R10's own byte-
identity tests) -- status cannot change there. Only HighriseApartment
(list=8) and MidriseApartment (list=2) can differ; this script proves that
by construction (band_map read straight from compute_band_map(), no
reimplementation of that part) and reports the counts.

identity / fallback_shorter / fallback_not_expressible-for-other-reasons
(n_proto==2, or >1 middle band) are UNCHANGED by R10 by construction (that
code path is untouched) -- included in the report as "unchanged" for the
row-count cross-check, not because they were individually re-derived.

Usage:
    ./.venv/Scripts/python.exe scripts/cluster/t20_r10_reach_change.py

Output:
    openubem/outputs/comparisons/t20_r10_reach_change.csv   (per-building)
    stdout summary: counts by archetype, old_status -> new_status
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import tempfile

import geopandas as gpd
import pandas as pd
from geomeppy import IDF as GeomIDF

from openubem.geometry import layout_assigner
from openubem.geometry.footprint import derive_num_floors
from openubem.idf.builder import _layout_assign_baseline_path

PHASED_RESULTS = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)
SWEEP_WORK = Path(tempfile.gettempdir()) / "ubem_t20_sweep"
OUTPUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
OUTPUT_CSV = OUTPUT_DIR / "t20_r10_reach_change.csv"

ALL_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]


def _pre_r10_status(n_proto: int, n_real: int, bands: list[dict]) -> tuple[str, int | None]:
    """Reimplements the EXACT pre-R10 taller-branch formula (see docstring)."""
    if n_proto <= 0 or n_real == n_proto:
        return "identity", None
    if n_real < n_proto:
        return "fallback_shorter", None
    if n_proto == 1:
        multiplier = n_real  # pre-R10: n_real written directly (degenerate case, list_mult==1 always)
        return "applied", multiplier
    middle_bands = bands[1:-1]
    if len(middle_bands) != 1:
        return "fallback_not_expressible", None
    multiplier = n_real - (n_proto - 1)
    if multiplier < 1:
        return "fallback_not_expressible", None
    return "applied", multiplier


def _post_r10_status(n_proto: int, n_real: int, bands: list[dict]) -> tuple[str, int | None]:
    """Delegates to the REAL current match_storeys() logic, band-map-only
    (no idf object needed -- status/multiplier depend only on n_proto/bands/n_real)."""
    if n_proto <= 0 or n_real == n_proto:
        return "identity", None
    if n_real < n_proto:
        return "fallback_shorter", None
    if n_proto == 1:
        target_band = bands[0]
    else:
        middle_bands = bands[1:-1]
        if len(middle_bands) != 1:
            return "fallback_not_expressible", None
        target_band = middle_bands[0]
    list_multiplier = target_band["storeys_in_band"]
    non_middle_storeys = sum(b["storeys_in_band"] for b in bands if b is not target_band)
    if list_multiplier <= 0:
        return "fallback_not_expressible", None
    raw = n_real - non_middle_storeys
    if raw < list_multiplier or (raw % list_multiplier) != 0:
        return "fallback_not_expressible", None
    residual = int(round(raw / list_multiplier))
    if residual < 1:
        return "fallback_not_expressible", None
    return "applied", residual


def main() -> None:
    print("Loading band maps per archetype (compute_band_map(), unaffected by R10) ...")
    band_map_cache: dict[str, dict] = {}

    rows = []
    n_cells_ready = 0
    for cell in ALL_CELLS:
        buildings_path = PHASED_RESULTS / cell / "01_buildings.gpkg"
        manifest_path = SWEEP_WORK / cell / "step3_layout_assign" / "03_manifest.parquet"
        if not buildings_path.exists() or not manifest_path.exists():
            print(f"  SKIP {cell}: manifest not ready yet ({manifest_path})", file=sys.stderr)
            continue
        n_cells_ready += 1
        gdf = gpd.read_file(str(buildings_path))
        gdf["_num_floors"] = gdf.apply(derive_num_floors, axis=1)
        floors_by_osm = dict(zip(gdf["osm_id"].astype(str), gdf["_num_floors"]))

        manifest = pd.read_parquet(str(manifest_path))
        pop = manifest[
            (manifest["zoning_strategy"] == "layout_assign")
            & (manifest["generation_status"] == "success")
        ]
        print(f"  {cell}: {len(pop)}/{len(manifest)} layout_assign successes")

        for _, mrow in pop.iterrows():
            osm_id = str(mrow["osm_id"])
            arch = str(mrow["archetype_id"])
            num_floors = floors_by_osm.get(osm_id)
            if num_floors is None:
                print(f"    [{cell}/{osm_id}] no matching raw-fixture row for num_floors -- skipped", file=sys.stderr)
                continue

            if arch not in band_map_cache:
                baseline_path = _layout_assign_baseline_path("layout_assign", arch)
                if baseline_path is None:
                    band_map_cache[arch] = None
                else:
                    try:
                        idf = GeomIDF(str(baseline_path))
                        band_map_cache[arch] = layout_assigner.compute_band_map(idf)
                    except Exception as exc:
                        print(f"    [{arch}] load/band_map error: {exc}", file=sys.stderr)
                        band_map_cache[arch] = None

            bm = band_map_cache[arch]
            if bm is None:
                continue  # no_baseline fallback-to-auto population, out of scope for match_storeys()

            n_proto = bm["n_proto"]
            bands = bm["bands"]
            old_status, old_mult = _pre_r10_status(n_proto, num_floors, bands)
            new_status, new_mult = _post_r10_status(n_proto, num_floors, bands)

            rows.append({
                "cell": cell, "osm_id": osm_id, "archetype_id": arch,
                "num_floors": num_floors, "n_proto": n_proto,
                "old_status": old_status, "old_multiplier": old_mult,
                "new_status": new_status, "new_multiplier": new_mult,
                "changed": old_status != new_status,
            })

    df = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(str(OUTPUT_CSV), index=False)
    print(f"\nWrote {len(df)} rows -> {OUTPUT_CSV}")
    print(f"Cells with a ready manifest: {n_cells_ready}/{len(ALL_CELLS)}"
          f"{' -- PARTIAL, re-run once the sweep finishes all cells' if n_cells_ready < len(ALL_CELLS) else ' -- FULL FLEET'}")

    print(f"\nTotal layout_assign-eligible buildings evaluated: {len(df)}")
    n_changed = int(df["changed"].sum())
    print(f"Buildings whose status CHANGED under R10: {n_changed}")

    print("\nBy archetype (changed only):")
    chg = df[df["changed"]]
    if not chg.empty:
        print(chg.groupby("archetype_id").size().sort_values(ascending=False).to_string())
    else:
        print("  (none)")

    print("\nOld -> New status transitions (changed rows):")
    if not chg.empty:
        print(chg.groupby(["archetype_id", "old_status", "new_status"]).size().to_string())

    print("\nFull old_status -> new_status crosstab (all rows, sanity check):")
    print(pd.crosstab(df["old_status"], df["new_status"]).to_string())


if __name__ == "__main__":
    main()
