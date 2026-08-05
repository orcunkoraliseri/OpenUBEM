"""R06 condition (b) — fleet-scale count of buildings whose match_storeys()
status CHANGED under R10 (E-LA-36 residual-multiplier fix), split by archetype
and by old -> new status.

R06b DEVIATION (2026-08-04, executor): the original version of this script
(R06-part-1) read (osm_id, archetype_id, generation_status) from a LOCAL
03_manifest.parquet cached under a temp sweep-work dir. That local cache no
longer exists (12-cell local Step2/Step3 tmp dirs were cleaned after shipping
to the cluster — confirmed absent for all 12 cells before this run). Fixed by
substituting two sources already proven and used by t20_harvest_layout_assign.py
for the SAME T20 fleet, for the SAME purpose:
  - population/"generation succeeded" filter: the REMOTE fleet.lst (each
    cell's shipped build list) via read-only `ssh ... cat fleet.lst` --
    identical source the harvest script itself falls back to when no local
    manifest exists.
  - archetype_id per osm_id: PHASED_RESULTS/<cell>/05_results.gpkg (same file,
    same column, same priority order as t20_harvest_layout_assign.py's own
    build_cell_info()). 01_buildings.gpkg's own archetype_id column is empty
    (archetype is assigned during semantic enrichment, not present in the raw
    buildings fixture) -- checked directly before adopting this fallback.
  - num_floors per osm_id: unchanged from the original script --
    derive_num_floors() applied to 01_buildings.gpkg, the same function the
    real Step2 enrichment path uses to derive num_floors from raw building
    attributes (not a reimplementation of match_storeys() or any storey-
    matching logic -- only the population source changed, not the archetype/
    band-map/formula logic below, which is untouched from R06-part-1).

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

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd
from geomeppy import IDF as GeomIDF

from openubem.geometry import layout_assigner
from openubem.geometry.footprint import derive_num_floors
from openubem.idf.builder import _layout_assign_baseline_path

PHASED_RESULTS = (
    REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
)
OUTPUT_DIR = REPO / "openubem" / "outputs" / "comparisons"
OUTPUT_CSV = OUTPUT_DIR / "t20_r10_reach_change.csv"

REMOTE_HOST = "o_iseri@speed.encs.concordia.ca"
_REMOTE_FLEET_BASE = "/speed-scratch/o_iseri/fleets"
_FLEET_TAG = "t20"
_MODE = "layout_assign"

ALL_CELLS = [
    "nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
    "la_centre", "la_urban", "la_suburban", "la_rural",
    "austin_centre", "austin_urban", "austin_suburban", "austin_rural",
]


def _ssh(cmd: str, timeout: int = 60) -> str:
    r = subprocess.run(
        ["ssh", REMOTE_HOST, f"bash -lc '{cmd}'"],
        capture_output=True, text=True, timeout=timeout,
    )
    return r.stdout + r.stderr


def _remote_fleet_lst(cell: str) -> list[str]:
    """Read-only ssh cat of the shipped fleet.lst -- the same population
    source t20_harvest_layout_assign.py falls back to when no local
    Step2/Step3 manifest exists (see module docstring, R06b deviation)."""
    remote_dir = f"{_REMOTE_FLEET_BASE}/{_FLEET_TAG}_{cell}_{_MODE}"
    raw = _ssh(f"cat {remote_dir}/fleet.lst", timeout=30)
    return [s.strip() for s in raw.splitlines() if s.strip()]


def _load_archetype_map(cell: str) -> dict[str, str]:
    """osm_id -> archetype_id.

    R06b SECOND DEVIATION (2026-08-04, executor, found while hand-verifying
    this very map): the first version of this fix read archetype_id from
    PHASED_RESULTS/<cell>/05_results.gpkg -- the same source
    t20_harvest_layout_assign.py's build_cell_info() already uses for the
    T20 fleet's own published archetype_id column. That file is STALE: it
    predates this codebase's Hotel-archetype support. Proven directly on one
    of the 7 SLURM-FAILED buildings (way/965718400, nyc_rural): its retained
    (un-trimmed, because `set -e` aborted before cleanup) in.idf names
    `Building, HotelSmall` verbatim, but 05_results.gpkg's archetype_id for
    that same osm_id says "SmallOffice". Cross-checked fleet-wide: running
    the REAL, current `BuildingClassifier().classify()` (the exact code
    Step2 calls at generation time -- openubem/semantic/building_classifier.py,
    invoked identically to run_step2() in t20_layout_assign_full_sweep.py,
    not a reimplementation) against every cell's 01_buildings.gpkg finds
    41/8,160 (0.5%) buildings where 05_results.gpkg's archetype_id disagrees
    with the current classifier -- and all 41 are exactly the fleet's true
    LargeHotel (33) + SmallHotel (8) population, 100% of which 05_results.gpkg
    mislabels as an Office archetype. This is a pre-existing defect in the
    T17->T20 harvest lineage's own archetype_id column, not something this
    task introduces -- forwarded to the director as a new finding (see the
    R06 progress-log entry), not fixed retroactively in T17/T18/T19's already-
    published CSVs (out of scope here). Fixed HERE by using the real
    BuildingClassifier() output directly instead of the stale gpkg column.
    """
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier

    fixture_dir = PHASED_RESULTS / cell
    buildings_path = fixture_dir / "01_buildings.gpkg"
    if not buildings_path.exists():
        return {}
    gdf_raw = gpd.read_file(str(buildings_path))
    gdf_in = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_in["levels"] = gdf_in["levels"].astype("Int64")
    out = BuildingClassifier().classify(gdf_in)
    return dict(zip(out["osm_id"].astype(str), out["archetype_id"].astype(str)))


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
        if not buildings_path.exists():
            print(f"  SKIP {cell}: {buildings_path} not found", file=sys.stderr)
            continue
        fleet_stems = _remote_fleet_lst(cell)
        if not fleet_stems:
            print(f"  SKIP {cell}: empty/unreachable remote fleet.lst", file=sys.stderr)
            continue
        n_cells_ready += 1
        gdf = gpd.read_file(str(buildings_path))
        gdf["_num_floors"] = gdf.apply(derive_num_floors, axis=1)
        floors_by_osm = dict(zip(gdf["osm_id"].astype(str), gdf["_num_floors"]))
        arch_by_osm = _load_archetype_map(cell)

        pop_osm_ids = [stem.replace("_", "/", 1) for stem in fleet_stems]
        print(f"  {cell}: {len(pop_osm_ids)} layout_assign successes (remote fleet.lst)")

        for osm_id in pop_osm_ids:
            arch = arch_by_osm.get(osm_id, "")
            num_floors = floors_by_osm.get(osm_id)
            if num_floors is None:
                print(f"    [{cell}/{osm_id}] no matching raw-fixture row for num_floors -- skipped", file=sys.stderr)
                continue
            if not arch:
                print(f"    [{cell}/{osm_id}] no archetype_id in 05_results.gpkg -- skipped", file=sys.stderr)
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
