"""Acceptance tests for the EU-04 S2 physics-complete campaign runner (T02)
and the T03 EU-08 campaign-cell manifests emitted from its real outputs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from openubem.acquisition.european_weather import sha256_file
from openubem.idf.surfaces import find_mismatched_interzone_pairs
from openubem.validation.european_campaign import dependency_digest, dependency_fingerprints
from scripts.run_eu_s2_campaign import (
    CAMPAIGN_MANIFEST_PATH,
    REGISTRY_PATH,
    RUN_ROOT,
    WEATHER_PATH,
    _has_near_duplicate_vertex_surfaces,
    build_geometry_for_row,
    build_idf_for_building,
    load_fr_record,
    load_frozen_sample,
    load_manifest_native,
    validate_mapping_ready,
    verify_census_sha256,
    verify_weather_checksum,
)

CELL_MANIFEST_DIR = Path(__file__).parents[1] / "openubem/outputs/eu_evidence/EU-08/s2_cell_manifests"
REQUIRED_MANIFEST_KEYS = (
    "schema_version", "cell_id", "archetype_id", "country_stock_code",
    "fold", "sensitivity_f", "schedule_source_sha256", "schedule_emitted_sha256",
    "idf_sha256", "weather_sha256", "openubem_version", "openubem_git_commit",
    "energyplus_version", "energyplus_build_hash", "platform", "created_utc", "status",
)


def _load_cell_manifests() -> list[dict[str, object]]:
    paths = sorted(CELL_MANIFEST_DIR.glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in paths]


def test_frozen_sample_has_31_rows_with_ruled_quotas_and_census_sha256():
    sample = load_frozen_sample()
    assert len(sample) == 31
    assert sample["building_type"].value_counts().to_dict() == {
        "AB": 8, "MFH": 8, "TH": 8, "SFH": 7,
    }
    recorded = verify_census_sha256()
    assert len(recorded) == 64


def test_validate_mapping_ready_accepts_the_frozen_sample():
    sample = load_frozen_sample()
    validate_mapping_ready(sample)


def test_validate_mapping_ready_rejects_a_non_ready_row():
    sample = load_frozen_sample().copy()
    sample.loc[sample.index[0], "mapping_status"] = "NOT_READY"
    with pytest.raises(ValueError, match="MAPPED_LAYOUT_READY"):
        validate_mapping_ready(sample)


def test_verify_weather_checksum_matches_registry():
    digest = verify_weather_checksum()
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    fr_target = next(entry for entry in registry["targets"] if entry["fold"] == "fr")
    assert digest == fr_target["sha256"]


def test_verify_weather_checksum_raises_on_registry_mismatch(tmp_path):
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    for entry in registry["targets"]:
        if entry["fold"] == "fr":
            entry["sha256"] = "0" * 64
    tampered = tmp_path / "weather_registry.json"
    tampered.write_text(json.dumps(registry), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        verify_weather_checksum(WEATHER_PATH, tampered)


def test_single_building_dry_run_emits_non_smoke_construction_and_external_schedule(tmp_path):
    sample = load_frozen_sample()
    manifest = load_manifest_native()
    row = sample.loc[sample["building_id"] == "BATIMENT0000000240879449_part0"].iloc[0]
    record = load_fr_record(row["archetype_id"])
    zones, geometry_outcome = build_geometry_for_row(row, manifest)
    assert geometry_outcome == "DWELLING_LAYOUT_EMITTED"
    assert len(zones) >= 1

    idf_path = build_idf_for_building(row, record, zones, tmp_path)
    idf_text = idf_path.read_text(encoding="utf-8")
    assert "Smoke" not in idf_text

    from geomeppy import IDF
    from eppy.modeleditor import IDDAlreadySetError
    from openubem.config import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    idf = IDF(str(idf_path))

    zone_names = {zone.Name for zone in idf.idfobjects["ZONE"]}
    assert zone_names == {zone["name"] for zone in zones}

    construction_names = {c.Name for c in idf.idfobjects["CONSTRUCTION"]}
    assert "Smoke" not in "".join(construction_names)
    assert {"EU_wall_Construction", "EU_roof_Construction", "EU_floor_Construction"} <= construction_names

    schedule_files = idf.idfobjects["SCHEDULE:FILE"]
    assert len(schedule_files) == len(zones)

    other_equipment = idf.idfobjects["OTHEREQUIPMENT"]
    legacy_gain_names = {f"EU_InternalGains_{zone['name']}" for zone in zones}
    assert not (legacy_gain_names & {obj.Name for obj in other_equipment})


def test_runner_refuses_when_a_row_is_not_mapped_layout_ready():
    sample = load_frozen_sample().copy()
    sample.loc[sample.index[0], "mapping_status"] = "NOT_READY"
    with pytest.raises(ValueError, match="MAPPED_LAYOUT_READY"):
        validate_mapping_ready(sample)


def test_t03_exactly_31_cell_manifests_emitted():
    manifests = _load_cell_manifests()
    assert len(manifests) == 31


def test_t03_all_cell_ids_unique_and_schema_version_pinned():
    manifests = _load_cell_manifests()
    cell_ids = [str(manifest["cell_id"]) for manifest in manifests]
    assert len(set(cell_ids)) == 31
    assert all(str(manifest["schema_version"]) == "step8-cell-manifest/1.0" for manifest in manifests)
    assert all(str(manifest["cell_id"]).endswith("__f000") for manifest in manifests)


def test_t03_required_keys_present_and_non_null():
    manifests = _load_cell_manifests()
    for manifest in manifests:
        for key in REQUIRED_MANIFEST_KEYS:
            assert key in manifest, f"missing key {key!r} in {manifest.get('cell_id')}"
            assert manifest[key] not in (None, ""), f"null/empty {key!r} in {manifest.get('cell_id')}"


def test_t03_only_f000_cells_are_present_no_synthesized_f_levels():
    manifests = _load_cell_manifests()
    assert all(float(manifest["sensitivity_f"]) == 0.0 for manifest in manifests)


def test_t03_shas_are_measured_from_disk_not_copied_between_manifests():
    manifests = {str(manifest["building_id"]): manifest for manifest in _load_cell_manifests()}
    with CAMPAIGN_MANIFEST_PATH.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 31
    for row in rows:
        manifest = manifests[row["building_id"]]
        idf_path = RUN_ROOT / row["building_id"] / f"{row['building_id']}.idf"
        assert manifest["idf_sha256"] == sha256_file(idf_path)
        assert manifest["weather_sha256"] == sha256_file(WEATHER_PATH)
        gain_files = sorted((RUN_ROOT / row["building_id"]).glob("*_gain.csv"))
        assert gain_files
        assert manifest["schedule_emitted_sha256"] == sha256_file(gain_files[0])


def test_t03_dependency_digest_reproduces_over_unchanged_inputs_and_reacts_to_epw(tmp_path):
    with CAMPAIGN_MANIFEST_PATH.open(encoding="utf-8", newline="") as stream:
        row = next(iter(csv.DictReader(stream)))
    building_id = row["building_id"]
    run_dir = RUN_ROOT / building_id
    idf_path = run_dir / f"{building_id}.idf"
    gain_path = sorted(run_dir.glob("*_gain.csv"))[0]

    kwargs = dict(
        idf_path=idf_path,
        schedule_path=gain_path,
        weather_path=WEATHER_PATH,
        energyplus_build="EnergyPlus 23.1.0-87ed9199d4",
        adapter_config={"sensitivity_f": 0.0, "cell_id": row["archetype_id"]},
        source_commit="4a9fce2+dirty",
    )
    first = dependency_digest(**kwargs)
    second = dependency_digest(**kwargs)
    assert first == second

    fingerprints = dependency_fingerprints(**kwargs)
    assert fingerprints["weather_sha256"] == sha256_file(WEATHER_PATH)

    tampered_epw = tmp_path / "tampered.epw"
    tampered_epw.write_bytes(WEATHER_PATH.read_bytes() + b"\n! tamper\n")
    changed = dependency_digest(**{**kwargs, "weather_path": tampered_epw})
    assert changed != first


def test_t03_cell_ids_disambiguate_buildings_sharing_one_tabula_archetype():
    with CAMPAIGN_MANIFEST_PATH.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    archetypes = [row["archetype_id"] for row in rows]
    assert len(set(archetypes)) < len(rows)
    manifests = _load_cell_manifests()
    for manifest in manifests:
        assert str(manifest["building_id"]) in str(manifest["cell_id"])


class _MockSurface:
    def __init__(self, name: str, coords: list[tuple], obc: str = "Outdoors", obc_obj: str = ""):
        self.Name = name
        self.coords = coords
        self.Outside_Boundary_Condition = obc
        self.Outside_Boundary_Condition_Object = obc_obj


class _MockIDF:
    def __init__(self, surfaces: list[_MockSurface]):
        self.idfobjects = {"BUILDINGSURFACE:DETAILED": surfaces}


def test_near_duplicate_partnerless_collinear_surface_not_at_risk():
    """T02 Case 1: A surface with no interzone partner (e.g. Ground, Outdoors)
    carrying a collinear vertex triple must not set near_duplicate or at_risk."""
    # Rectangle with vertex 3 collinear along top edge (10, 10) -> (5, 10) -> (0, 10)
    collinear_coords = [
        (0.0, 0.0, 0.0),
        (10.0, 0.0, 0.0),
        (10.0, 10.0, 0.0),
        (5.0, 10.0, 0.0),  # angle = 180.0 deg
        (0.0, 10.0, 0.0),
    ]
    ground_surf = _MockSurface("GROUND_FLOOR", collinear_coords, obc="Ground", obc_obj="")
    idf = _MockIDF([ground_surf])

    # Partner-less: default interzone_only=True ignores it
    assert not _has_near_duplicate_vertex_surfaces(idf)
    # Legacy check without interzone filter would have flagged it
    assert _has_near_duplicate_vertex_surfaces(idf, interzone_only=False)

    mismatched = bool(find_mismatched_interzone_pairs(idf))
    near_dup = _has_near_duplicate_vertex_surfaces(idf)
    at_risk = mismatched or near_dup
    assert not at_risk


def test_near_duplicate_interzone_paired_collinear_surface_identical_coords_at_risk():
    """T02 Case 2: Interzone-paired collinear surface with identical coordinates
    (replicates T04 stem 8cdf349a99934f0d shape: 9-vertex ring, vertex 7 interior angle
    180.000000°, mirrored partner with matching coordinates). Must set at_risk = True."""
    coords_a = [
        (440376.908803735, 4479372.27754849, 3.0),
        (440382.868151124, 4479380.640902955, 3.0),
        (440376.090350857, 4479385.470425332, 3.0),
        (440371.918850262, 4479379.616110756, 3.0),
        (440373.952001537, 4479378.167385778, 3.0),
        (440373.952001537, 4479378.167385777, 3.0),
        (440373.952001537, 4479378.167385777, 3.0),
        (440373.92547985, 4479378.130165048, 3.0),  # vertex 7: collinear 180.0 deg
        (440372.164176842, 4479375.658339467, 3.0),
    ]
    coords_b = [
        (440382.868151124, 4479380.640902955, 3.0),
        (440376.908803735, 4479372.27754849, 3.0),
        (440372.164176842, 4479375.658339467, 3.0),
        (440373.92547985, 4479378.130165048, 3.0),
        (440373.952001537, 4479378.167385777, 3.0),
        (440373.952001537, 4479378.167385777, 3.0),
        (440373.952001537, 4479378.167385778, 3.0),
        (440371.918850262, 4479379.616110756, 3.0),
        (440376.090350857, 4479385.470425332, 3.0),
    ]
    ceiling = _MockSurface("BLOCK_CEILING", coords_a, obc="Surface", obc_obj="BLOCK_FLOOR")
    floor = _MockSurface("BLOCK_FLOOR", coords_b, obc="Surface", obc_obj="BLOCK_CEILING")
    idf = _MockIDF([ceiling, floor])

    # Vertex counts match so find_mismatched_interzone_pairs is empty
    assert not find_mismatched_interzone_pairs(idf)
    # But collinear defect on paired surface sets near_duplicate and at_risk
    assert _has_near_duplicate_vertex_surfaces(idf)
    at_risk = bool(find_mismatched_interzone_pairs(idf)) or _has_near_duplicate_vertex_surfaces(idf)
    assert at_risk is True


def test_near_duplicate_interzone_paired_asymmetric_coords_at_risk():
    """T02 Case 3: Interzone-paired defect with asymmetric coordinates (stem e21bec78b937acf5
    proximity-case shape: near-duplicate vertices < 0.005 m apart on one side of pair).
    Must set at_risk = True."""
    coords_asym_a = [
        (0.0, 0.0, 3.0),
        (10.0, 0.0, 3.0),
        (10.0, 10.0, 3.0),
        (0.0004, 10.0, 3.0),  # 0.0004 m from next vertex (< 0.005 m)
        (0.0, 10.0, 3.0),
    ]
    coords_asym_b = [
        (0.0, 10.0, 3.0),
        (10.0, 10.0, 3.0),
        (10.0, 0.0, 3.0),
        (0.0, 0.0, 3.0),
        (0.0, 5.0, 3.0),
    ]
    ceiling = _MockSurface("ASYM_CEILING", coords_asym_a, obc="Surface", obc_obj="ASYM_FLOOR")
    floor = _MockSurface("ASYM_FLOOR", coords_asym_b, obc="Surface", obc_obj="ASYM_CEILING")
    idf = _MockIDF([ceiling, floor])

    assert _has_near_duplicate_vertex_surfaces(idf)
    at_risk = bool(find_mismatched_interzone_pairs(idf)) or _has_near_duplicate_vertex_surfaces(idf)
    assert at_risk is True

