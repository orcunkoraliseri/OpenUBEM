"""Audit EU-04 geometry remedies after the ruled G1 + V1 implementation.

Measures native/translated layout equivalence and the bounded vertex-budget
simplification provenance.  The manifest remains unchanged.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.affinity import translate

from openubem.geometry.european_residential import (
    allocate_european_dwellings,
    generate_european_dwelling_layout,
)
from openubem.geometry.zoning import bounded_energyplus_footprint


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg"
S2_CENSUS = ROOT / "openubem/outputs/eu_evidence/EU-04/s2_scope_measurement.csv"
OUT = ROOT / "openubem/outputs/eu_evidence/EU-04"


def _layout_status(footprint, row: pd.Series) -> tuple[str, str]:
    allocation = allocate_european_dwellings(
        archetype_id=str(row["archetype_id"]),
        building_type=str(row["building_type"]),
        n_apartment=int(row["observed_dwellings"]),
        n_storey=int(row["observed_storeys"]),
        plate_area_m2=float(footprint.area),
    )
    layout = generate_european_dwelling_layout(
        footprint, requested_dwelling_count=allocation.units_per_floor
    )
    if layout.dwelling_layout_emitted:
        return "DWELLING_LAYOUT_EMITTED", ""
    return "FALLBACK_PENDING_LAYOUT", layout.fallback_reason or ""


def main() -> None:
    census = pd.read_csv(S2_CENSUS)
    census = census.loc[census["layout_ready"]].copy()
    manifest = gpd.read_file(MANIFEST)
    manifest["building_id"] = manifest["osm_id"].astype(str)
    rows = census.merge(manifest[["building_id", "geometry"]], on="building_id", validate="one_to_one")

    records: list[dict[str, object]] = []
    for _, row in rows.iterrows():
        footprint = row["geometry"]
        native_status, native_reason = _layout_status(footprint, row)
        exterior_vertices = len(footprint.exterior.coords) - 1 if footprint.geom_type == "Polygon" else None
        _, simplification = bounded_energyplus_footprint(footprint)
        translated_status, translated_reason = native_status, native_reason
        if footprint.geom_type == "Polygon":
            centroid = footprint.centroid
            local = translate(footprint, xoff=-centroid.x, yoff=-centroid.y)
            translated_status, translated_reason = _layout_status(local, row)
        records.append(
            {
                "building_id": row["building_id"],
                "building_type": row["building_type"],
                "year_built": row["year_built"],
                "native_layout_status": native_status,
                "native_layout_reason": native_reason,
                "centroid_translated_layout_status": translated_status,
                "centroid_translated_layout_reason": translated_reason,
                "status_changed_under_translation": native_status != translated_status or native_reason != translated_reason,
                "exterior_vertex_count": exterior_vertices,
                "exceeds_energyplus_idd_vertex_budget_approx_120": bool(exterior_vertices is not None and exterior_vertices > 120),
                **simplification,
            }
        )

    result = pd.DataFrame(records)
    OUT.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT / "s2_geometry_limits_diagnostic.csv", index=False)
    summary = {
        "input_rows": int(len(result)),
        "native_layout_emitted": int((result.native_layout_status == "DWELLING_LAYOUT_EMITTED").sum()),
        "centroid_translated_layout_emitted": int((result.centroid_translated_layout_status == "DWELLING_LAYOUT_EMITTED").sum()),
        "status_changed_under_translation": int(result.status_changed_under_translation.sum()),
        "native_reason_counts": result.native_layout_reason.value_counts().to_dict(),
        "centroid_translated_reason_counts": result.centroid_translated_layout_reason.value_counts().to_dict(),
        "vertex_budget_threshold_approx": 120,
        "rows_over_vertex_budget": int(result.exceeds_energyplus_idd_vertex_budget_approx_120.sum()),
        "max_exterior_vertex_count": int(result.exterior_vertex_count.max()),
        "rows_simplified_for_energyplus": int(result.geometry_simplified_for_energyplus.sum()),
        "max_simplification_delta_area_m2": float(result.geometry_simplification_delta_area_m2.max()),
        "max_simplification_hausdorff_m": float(result.geometry_simplification_hausdorff_m.max()),
        "interpretation": "Post-ruling G1+V1 audit. Native and centroid-translated layout statuses must agree; V1 simplification is measured with per-footprint area and Hausdorff error. No manifest was changed and no EnergyPlus run was made.",
    }
    (OUT / "s2_geometry_limits_diagnostic_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
