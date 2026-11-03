from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.affinity import translate

from openubem.geometry.european_residential import (
    allocate_european_dwellings,
    generate_european_dwelling_layout,
)
from openubem.geometry.zoning import bounded_energyplus_footprint, build_zones


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg"
READINESS = ROOT / "openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness.csv"
SENSITIVE_IDS = {
    "BATIMENT0000000240877159_part0", "BATIMENT0000000240877179_part0",
    "BATIMENT0000000240879467_part0", "BATIMENT0000000240879979_part0",
    "BATIMENT0000000240880177_part0", "BATIMENT0000000240880393_part0",
    "BATIMENT0000000240881095_part0", "BATIMENT0000000240881134_part0",
    "BATIMENT0000000240881528_part0", "BATIMENT0000000240881532_part0",
}


def test_g1_translation_invariance_for_sensitive_ids():
    manifest = gpd.read_file(MANIFEST)
    manifest["building_id"] = manifest["osm_id"].astype(str)
    readiness = pd.read_csv(READINESS)
    rows = readiness[readiness.layout_ready & readiness.building_id.isin(SENSITIVE_IDS)].merge(
        manifest[["building_id", "geometry", "surplus_tags", "levels"]], on="building_id", validate="one_to_one"
    )
    assert set(rows.building_id) == SENSITIVE_IDS
    for _, row in rows.iterrows():
        allocation = allocate_european_dwellings(
            archetype_id=str(row.archetype_id), building_type=str(row.building_type),
                n_apartment=int(float(__import__("json").loads(row.surplus_tags)["nombre_de_logements"])),
            n_storey=int(row.levels), plate_area_m2=float(row.geometry.area),
        )
        native = generate_european_dwelling_layout(row.geometry, requested_dwelling_count=allocation.units_per_floor)
        shifted = translate(row.geometry, xoff=1_000_000.0, yoff=-2_000_000.0)
        moved = generate_european_dwelling_layout(shifted, requested_dwelling_count=allocation.units_per_floor)
        assert native.dwelling_layout_emitted and moved.dwelling_layout_emitted
        assert len(native.dwelling_polygons) == len(moved.dwelling_polygons)


def test_v1_simplifies_only_over_budget_ring_and_records_error():
    manifest = gpd.read_file(MANIFEST)
    footprint = manifest.loc[manifest.osm_id.astype(str) == "BATIMENT0000000240877527_part0", "geometry"].iloc[0]
    simplified, metadata = bounded_energyplus_footprint(footprint)
    assert len(footprint.exterior.coords) - 1 == 173
    assert len(simplified.exterior.coords) - 1 <= 120
    assert metadata["geometry_simplified_for_energyplus"] is True
    assert metadata["geometry_simplification_delta_area_m2"] >= 0.0
    assert metadata["geometry_simplification_hausdorff_m"] >= 0.0
    zones = build_zones("v1", footprint, "AB", 1, "one_zone_per_floor")
    assert zones[0]["geometry_simplified_for_energyplus"] is True
    assert len(zones[0]["coords_m"]) <= 120
