"""Real acquired-footprint GEO-04 pre-layout feasibility tests."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pytest
from shapely import affinity
from shapely.geometry import MultiPolygon, Polygon, box

from openubem.geometry.european_residential import (
    audit_real_footprint_manifest,
    assess_european_floor_layout_feasibility,
    generate_external_unconditioned_core,
    generate_european_dwelling_layout,
    write_real_footprint_feasibility_census,
)


REPO_ROOT = Path(__file__).parent.parent
MANIFEST_ROOT = REPO_ROOT / "openubem" / "outputs" / "eu02"
SITE_IDS = (
    "ES-MAD-BERRUGUETE",
    "FR-LYO-HAUTCOEURPENTES",
    "GB-LDN-STDUNSTANS",
    "IT-BOL-GALVANI2",
)


def _write_manifest(path: Path, geometries, *, crs: str = "EPSG:32630") -> None:
    gpd.GeoDataFrame(
        {"osm_id": [f"building-{index}" for index in range(len(geometries))]},
        geometry=geometries,
        crs=crs,
    ).to_file(path, layer="buildings", driver="GPKG")


def test_real_manifest_census_records_topology_without_claiming_a_layout(tmp_path):
    manifest = tmp_path / "02_residential_manifest.gpkg"
    courtyard = Polygon(
        shell=((0, 0), (12, 0), (12, 12), (0, 12)),
        holes=(((4, 4), (8, 4), (8, 8), (4, 8)),),
    )
    l_shape = Polygon(((20, 0), (32, 0), (32, 4), (28, 4), (28, 8), (20, 8)))
    _write_manifest(manifest, [box(0, 20, 30, 27.99), courtyard, l_shape])

    rows, audit = audit_real_footprint_manifest(manifest, neighbourhood_id="EU-TEST")

    assert list(rows["building_id"]) == ["building-0", "building-1", "building-2"]
    assert audit.neighbourhood_id == "EU-TEST"
    assert audit.footprint_count == 3
    assert audit.narrow_fallback_count == 1
    assert audit.courtyard_count == 1
    assert audit.non_convex_count >= 2
    narrow = rows.loc[rows["fallback_required"]].iloc[0]
    assert narrow["fallback_reason"] == "NARROW_FOOTPRINT_LT_8M"
    assert narrow["layout_status"] == "FALLBACK_ONE_ZONE_PER_FLOOR"
    assert not rows["dwelling_layout_emitted"].any()


def test_real_manifest_census_rejects_geographic_coordinates(tmp_path):
    manifest = tmp_path / "02_residential_manifest.gpkg"
    _write_manifest(manifest, [box(-0.1, 51.5, -0.09, 51.51)], crs="EPSG:4326")

    with pytest.raises(ValueError, match="projected CRS"):
        audit_real_footprint_manifest(manifest)


def test_all_four_audited_eu02_manifests_are_nonempty_and_deterministic(tmp_path):
    first_rows, first_audits = write_real_footprint_feasibility_census(MANIFEST_ROOT, tmp_path / "first")
    second_rows, second_audits = write_real_footprint_feasibility_census(MANIFEST_ROOT, tmp_path / "second")

    assert {audit.neighbourhood_id for audit in first_audits} == set(SITE_IDS)
    assert all(audit.footprint_count > 0 for audit in first_audits)
    assert all(audit.projected_crs.startswith("EPSG:32") for audit in first_audits)
    assert all(audit.dwelling_layout_emitted_count == 0 for audit in first_audits)
    assert first_rows.to_dict(orient="records") == second_rows.to_dict(orient="records")
    assert [audit.source_sha256 for audit in first_audits] == [audit.source_sha256 for audit in second_audits]
    assert (tmp_path / "first" / "real_footprint_feasibility.csv").is_file()
    assert (tmp_path / "first" / "real_footprint_feasibility_summary.json").is_file()


def test_real_layout_generator_partitions_a_rotated_convex_footprint_without_a_core():
    footprint = affinity.rotate(box(0.0, 0.0, 30.0, 12.0), 31.0, origin="centroid")

    layout = generate_european_dwelling_layout(footprint, requested_dwelling_count=3)

    assert layout.dwelling_layout_emitted
    assert layout.status == "DWELLING_LAYOUT_EMITTED"
    assert layout.fallback_reason is None
    assert len(layout.dwelling_polygons) == 3
    assert layout.partition_audit is not None and layout.partition_audit.passed
    assert all(length >= 2.5 for length in layout.facade_contact_lengths_m)
    assert not layout.unconditioned_core_emitted


@pytest.mark.parametrize(
    ("footprint", "expected_reason"),
    [
        (box(0.0, 0.0, 30.0, 7.99), "NARROW_FOOTPRINT_LT_8M"),
        (
            Polygon(
                shell=((0, 0), (12, 0), (12, 12), (0, 12)),
                holes=(((4, 4), (8, 4), (8, 8), (4, 8)),),
            ),
            "COURTYARD_TOPOLOGY_UNSUPPORTED",
        ),
        (Polygon(((0, 0), (12, 0), (12, 4), (8, 4), (8, 8), (0, 8))), "NON_CONVEX_TOPOLOGY_UNSUPPORTED"),
    ],
)
def test_real_layout_generator_fails_closed_for_unsupported_topology(footprint, expected_reason):
    layout = generate_european_dwelling_layout(footprint, requested_dwelling_count=2)

    assert not layout.dwelling_layout_emitted
    assert not layout.dwelling_polygons
    assert layout.fallback_reason == expected_reason


def test_real_layout_generator_does_not_infer_dwellings_for_live_manifest_geometry():
    manifest = MANIFEST_ROOT / "ES-MAD-BERRUGUETE" / "02_residential_manifest.gpkg"
    gdf = gpd.read_file(manifest)
    footprint = next(
        geometry
        for geometry in gdf.geometry
        if not geometry.interiors
        and geometry.equals(geometry.convex_hull)
        and not assess_european_floor_layout_feasibility(
            geometry, requested_dwelling_count=1
        ).fallback_required
    )

    layout = generate_european_dwelling_layout(footprint, requested_dwelling_count=1)

    assert layout.requested_dwelling_count == 1
    assert layout.dwelling_layout_emitted
    assert len(layout.dwelling_polygons) == 1


def test_real_layout_generator_rejects_non_polygon_inputs_before_partitioning():
    with pytest.raises(ValueError, match="must be a Polygon"):
        generate_european_dwelling_layout(
            MultiPolygon([box(0.0, 0.0, 12.0, 12.0), box(20.0, 0.0, 32.0, 12.0)]),
            requested_dwelling_count=2,
        )


def test_external_core_is_area_faithful_non_overlapping_and_rotation_invariant():
    plate = affinity.rotate(box(0.0, 0.0, 20.0, 10.0), 31.0, origin="centroid")

    core = generate_external_unconditioned_core(plate, requested_area_m2=12.0)

    assert core.emitted
    assert core.fallback_reason is None
    assert core.emitted_area_m2 == pytest.approx(12.0)
    assert core.overlap_area_m2 == pytest.approx(0.0)
    assert core.shared_boundary_length_m == pytest.approx(20.0, abs=1e-5)
    assert core.core_polygon is not None


def test_external_core_fails_closed_for_non_rectangular_conditioned_plate():
    non_rectangular = Polygon(((0, 0), (12, 0), (12, 4), (8, 4), (8, 8), (0, 8)))

    core = generate_external_unconditioned_core(non_rectangular, requested_area_m2=4.8)

    assert not core.emitted
    assert core.core_polygon is None
    assert core.fallback_reason == "NON_RECTANGULAR_CONDITIONED_PLATE_UNSUPPORTED"
