"""EU-18a T01: the IDF plan reader proved against eppy on a spanning sample."""
from __future__ import annotations

from pathlib import Path

import pytest
from shapely.geometry import Polygon

from scripts.eu_idf_plan_reader import (
    UnrecognizedZoneNameError,
    classify_zone_name,
    district_paths,
    load_prepared_buildings,
    read_building_plan,
)
from scripts.run_eu_s2_district_campaign import DISTRICTS

PER_DISTRICT_BOX = 2
PER_DISTRICT_CORED = 3


def _select_sample_stems() -> list[tuple[str, str, str]]:
    """Return ``(district, building_id, stem)`` — up to 2 box-only and 3
    ruled buildings per district, chosen by first-in-CSV-order among
    candidates the reader itself classifies (an independent eppy oracle
    checks the reader's own output below, so using the reader to pick a
    spanning sample does not weaken the test)."""
    from scripts.eu_idf_plan_reader import read_district

    sample: list[tuple[str, str, str]] = []
    for district in sorted(DISTRICTS):
        plans = read_district(district)
        box = [p for p in plans if not p.is_ruled()][:PER_DISTRICT_BOX]
        cored = [p for p in plans if p.has_unconditioned_core()][:PER_DISTRICT_CORED]
        chosen = box + cored
        for plan in chosen:
            sample.append((district, plan.building_id, plan.stem))
    return sample


SAMPLE = _select_sample_stems()


def test_sample_spans_four_districts_and_three_kinds():
    districts = {row[0] for row in SAMPLE}
    assert districts == set(DISTRICTS)
    assert len(SAMPLE) == 20, SAMPLE


def _eppy_zone_areas(idf_path: Path) -> dict[str, float]:
    from eppy.modeleditor import IDF, IDDAlreadySetError

    from openubem.config import ENERGYPLUS_IDD_PATH

    try:
        IDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except IDDAlreadySetError:
        pass
    idf = IDF(str(idf_path))
    zone_names = {z.Name for z in idf.idfobjects["ZONE"]}
    areas: dict[str, float] = {name: 0.0 for name in zone_names}
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if surface.Surface_Type.strip().lower() != "floor":
            continue
        ring = [(x, y) for x, y, _z in surface.coords]
        areas[surface.Zone_Name] = areas.get(surface.Zone_Name, 0.0) + Polygon(ring).area
    return {"zone_names": zone_names, "areas": areas}


@pytest.mark.parametrize("district,building_id,stem", SAMPLE)
def test_reader_matches_eppy(district, building_id, stem):
    root = district_paths(district)
    idf_path = root / "idfs" / f"{stem}.idf"
    prepared = load_prepared_buildings(district)
    geometry_outcome = prepared.loc[prepared["building_id"] == building_id, "geometry_outcome"].iloc[0]

    plan = read_building_plan(
        idf_path,
        stem=stem,
        building_id=building_id,
        district=district,
        geometry_outcome=geometry_outcome,
    )

    oracle = _eppy_zone_areas(idf_path)
    assert set(plan.zone_names) == oracle["zone_names"]

    for zone in plan.zones:
        expected = oracle["areas"][zone.name]
        assert expected > 0.0
        relative_error = abs(zone.area_m2 - expected) / expected
        assert relative_error < 1e-6, (zone.name, zone.area_m2, expected, relative_error)


def test_unknown_zone_name_pattern_raises():
    with pytest.raises(UnrecognizedZoneNameError):
        classify_zone_name("abc123_weirdname_not_taxonomy")


def test_unknown_zone_name_pattern_via_synthetic_idf(tmp_path):
    synthetic = tmp_path / "synthetic.idf"
    synthetic.write_text(
        "ZONE,\n"
        "    deadbeef00000001_weirdname,    !- Name\n"
        "    0,                        !- Direction of Relative North\n"
        "    0,                        !- X Origin\n"
        "    0,                        !- Y Origin\n"
        "    0,                        !- Z Origin\n"
        "    1,                        !- Type\n"
        "    1,                        !- Multiplier\n"
        "    autocalculate,            !- Ceiling Height\n"
        "    100,                      !- Volume\n"
        "    autocalculate,            !- Floor Area\n"
        "    ,                         !- Zone Inside Convection Algorithm\n"
        "    ,                         !- Zone Outside Convection Algorithm\n"
        "    Yes;                      !- Part of Total Floor Area\n"
        "\n"
        "BUILDINGSURFACE:DETAILED,\n"
        "    Block deadbeef Storey 0 Floor 0001,    !- Name\n"
        "    floor,                    !- Surface Type\n"
        "    EU_floor_Construction,    !- Construction Name\n"
        "    deadbeef00000001_weirdname,    !- Zone Name\n"
        "    ,                         !- Space Name\n"
        "    ground,                   !- Outside Boundary Condition\n"
        "    ,                         !- Outside Boundary Condition Object\n"
        "    NoSun,                    !- Sun Exposure\n"
        "    NoWind,                   !- Wind Exposure\n"
        "    autocalculate,            !- View Factor to Ground\n"
        "    autocalculate,            !- Number of Vertices\n"
        "    0,                        !- Vertex 1 Xcoordinate\n"
        "    0,                        !- Vertex 1 Ycoordinate\n"
        "    0,                        !- Vertex 1 Zcoordinate\n"
        "    10,                       !- Vertex 2 Xcoordinate\n"
        "    0,                        !- Vertex 2 Ycoordinate\n"
        "    0,                        !- Vertex 2 Zcoordinate\n"
        "    10,                       !- Vertex 3 Xcoordinate\n"
        "    10,                       !- Vertex 3 Ycoordinate\n"
        "    0,                        !- Vertex 3 Zcoordinate\n"
        "    0,                        !- Vertex 4 Xcoordinate\n"
        "    10,                       !- Vertex 4 Ycoordinate\n"
        "    0;                        !- Vertex 4 Zcoordinate\n",
        encoding="utf-8",
    )
    with pytest.raises(UnrecognizedZoneNameError):
        read_building_plan(
            synthetic,
            stem="deadbeef00000001",
            building_id="synthetic/1",
            district="ES-MAD-BERRUGUETE",
            geometry_outcome="FALLBACK_PENDING_LAYOUT",
        )
