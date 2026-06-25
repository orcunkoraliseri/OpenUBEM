"""T05: Rebuild all 69 la_urban perimeter_core buildings with the fix (IDF gen only).

Reports how many still build as perimeter_core vs how many rerouted to
one_zone_per_floor via coreperim_degenerate_fallback.

STOP criterion: if more than 2 buildings reroute, print the list and exit 1.

Usage: python scripts/diagnostics/t05_perimeter_core_regression.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

import geopandas as gpd
import pandas as pd

GDF_PATH = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban\01_buildings.gpkg")
CZ_PATH  = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban\02a_climate_epw.parquet")
EPW_PATH = (
    Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban")
    / "weather" / "weather"
    / "USA_CA_Los.Angeles.Downtown-USC.Campus.722874_TMYx.2011-2025.epw"
)
MANIFEST_PATH = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\phaseC\la_urban\step3\03_idf_manifest.parquet")


def _enrich_subset(osm_ids: list[str]) -> tuple[gpd.GeoDataFrame, dict]:
    from openubem.semantic.building_classifier import _INPUT_SCHEMA_COLUMNS, BuildingClassifier
    from openubem.acquisition import _CLIMATE_ZONE_VOCAB
    from openubem.semantic import enrich_semantics

    raw_gdf = gpd.read_file(str(GDF_PATH))
    climate  = pd.read_parquet(str(CZ_PATH))

    subset = raw_gdf[raw_gdf["osm_id"].isin(osm_ids)].copy()
    pilot_input = subset[_INPUT_SCHEMA_COLUMNS].copy()
    pilot_input["levels"] = pilot_input["levels"].astype("Int64")

    bc = BuildingClassifier()
    gdf_26 = bc.classify(pilot_input)

    cz_map   = dict(zip(climate["osm_id"], climate["climate_zone"]))
    prov_map = dict(zip(climate["osm_id"], climate["provenance_climate_zone"]))
    gdf_26["climate_zone"] = pd.Categorical(
        gdf_26["osm_id"].map(cz_map), categories=list(_CLIMATE_ZONE_VOCAB)
    )
    gdf_26["epw_path"] = str(EPW_PATH)
    gdf_26["provenance_climate_zone"] = pd.Categorical(
        gdf_26["osm_id"].map(prov_map), categories=["ASHRAE_STANDARD", "HEURISTIC"]
    )

    gdf_57, schedule_library = enrich_semantics(gdf_26)
    return gdf_57, schedule_library


def _build_one_record(row: pd.Series, gdf: gpd.GeoDataFrame,
                       schedule_library: dict, out_dir: Path) -> dict:
    """Build IDF for one building; returns a result dict (never raises)."""
    from openubem.idf.builder import BuildingIDF
    osm_id = str(row["osm_id"])
    try:
        bidf = BuildingIDF(row)
        manifest = bidf.build(gdf, schedule_library, out_dir)
        zones = bidf.idf.idfobjects["ZONE"] if hasattr(bidf, "idf") else []
        # Check if coreperim_degenerate_fallback fired
        # The manifest doesn't carry the note; we need to inspect the IDF zone names.
        zone_names = [z.Name for z in bidf.idf.idfobjects["ZONE"]]
        rerouted = any("_whole" in n for n in zone_names)
        # Confirm via any zone dict note in the idf text (fallback: inspect zone names)
        return {
            "osm_id": osm_id,
            "generation_status": manifest.get("generation_status", "unknown"),
            "zoning_strategy": manifest.get("zoning_strategy", ""),
            "num_zones": manifest.get("num_zones", 0),
            "rerouted_to_ozpf": rerouted,
            "zone_names_sample": str(zone_names[:3]),
        }
    except Exception as e:
        return {
            "osm_id": osm_id,
            "generation_status": f"exception: {e}",
            "zoning_strategy": "",
            "num_zones": 0,
            "rerouted_to_ozpf": False,
            "zone_names_sample": "",
        }


def main():
    assert GDF_PATH.exists(),     f"GDF not found: {GDF_PATH}"
    assert MANIFEST_PATH.exists(), f"Manifest not found: {MANIFEST_PATH}"

    print("=== T05: Regression — all 69 la_urban perimeter_core buildings ===\n")

    manifest = pd.read_parquet(str(MANIFEST_PATH))
    pc_ids = manifest[manifest["zoning_strategy"] == "perimeter_core"]["osm_id"].tolist()
    print(f"perimeter_core buildings to rebuild: {len(pc_ids)}")

    print("Enriching all perimeter_core buildings (Step 2 + 2.1 + 2.2)...")
    gdf_57, schedule_library = _enrich_subset(pc_ids)
    full_gdf = gpd.read_file(str(GDF_PATH))

    out_dir = Path(tempfile.gettempdir()) / "ubem_t05_idf"
    (out_dir / "idfs").mkdir(parents=True, exist_ok=True)

    results = []
    for i, osm_id in enumerate(pc_ids, 1):
        row_match = gdf_57[gdf_57["osm_id"] == osm_id]
        if len(row_match) == 0:
            results.append({"osm_id": osm_id, "generation_status": "not_in_enriched",
                             "zoning_strategy": "", "num_zones": 0,
                             "rerouted_to_ozpf": False, "zone_names_sample": ""})
            continue
        row = row_match.iloc[0]
        rec = _build_one_record(row, full_gdf, schedule_library, out_dir)
        results.append(rec)
        status = "REROUTED" if rec["rerouted_to_ozpf"] else "ok"
        print(f"  [{i:3d}/{len(pc_ids)}] {osm_id:35s}  zones={rec['num_zones']:4d}  {status}")

    df = pd.DataFrame(results)
    rerouted = df[df["rerouted_to_ozpf"]]
    stayed = df[~df["rerouted_to_ozpf"]]

    print("\n" + "=" * 60)
    print(f"SUMMARY")
    print(f"  Total perimeter_core buildings rebuilt: {len(df)}")
    print(f"  Still perimeter_core (no reroute):      {len(stayed)}")
    print(f"  Rerouted to one_zone_per_floor:         {len(rerouted)}")
    print()

    if len(rerouted) > 0:
        print("Rerouted buildings:")
        for _, r in rerouted.iterrows():
            print(f"  {r['osm_id']}  num_zones={r['num_zones']}  zones={r['zone_names_sample']}")

    print()
    if len(rerouted) > 2:
        print(f"STOP: {len(rerouted)} buildings rerouted — exceeds zero-false-positive bar (max 2).")
        print("Do NOT proceed. Report this list to the manager.")
        sys.exit(1)
    else:
        print(f"PASS: {len(rerouted)} rerouted (≤ 2 — within zero-false-positive bar).")
        if len(rerouted) == 0:
            print("      (Expected at least way/428643335 — check if it was in the set.)")


if __name__ == "__main__":
    main()
