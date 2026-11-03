"""D-EU-01/D-EU-04 dwelling allocation tests (GEO-07 foundation)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from openubem.geometry.european_residential import (
    CORE_FRACTION_OF_PLATE,
    allocate_european_dwellings,
    derive_european_plate_area,
)


DATA_DIR = Path(__file__).parent.parent / "openubem" / "data" / "construction"


def _records() -> list[dict]:
    records: list[dict] = []
    for country in ("es", "gb", "it", "fr"):
        records.extend(json.loads((DATA_DIR / "tabula_archetypes_{}.json".format(country)).read_text(encoding="utf-8"))["records"])
    return records


def _allocation(record: dict):
    geometry = record["geometry"]
    return allocate_european_dwellings(
        archetype_id=record["archetype_id"],
        building_type=record["building_type"],
        n_apartment=record["n_apartment"],
        n_storey=geometry["n_storey"],
        plate_area_m2=derive_european_plate_area(
            conditioned_reference_area_m2=geometry["a_c_ref_m2"],
            n_storey=geometry["n_storey"],
        ),
    )


def test_every_registry_record_has_exact_deterministic_dwelling_allocation():
    for record in _records():
        allocation = _allocation(record)
        expected_dwellings = int(float(record["n_apartment"]) + 0.5)
        expected_storeys = int(float(record["geometry"]["n_storey"]) + 0.5)
        assert allocation.dwelling_count == expected_dwellings
        assert allocation.storey_count == expected_storeys
        assert len(allocation.floor_allocations) == expected_storeys
        assert sum(floor.dwelling_count for floor in allocation.floor_allocations) == expected_dwellings
        assert allocation.units_per_floor == max(floor.dwelling_count for floor in allocation.floor_allocations)
        plate_area = derive_european_plate_area(
            conditioned_reference_area_m2=record["geometry"]["a_c_ref_m2"],
            n_storey=record["geometry"]["n_storey"],
        )
        assert all(floor.conditioned_area_m2 == pytest.approx(plate_area) for floor in allocation.floor_allocations)
        assert sum(floor.conditioned_area_m2 for floor in allocation.floor_allocations) == pytest.approx(
            float(record["geometry"]["a_c_ref_m2"])
        )


def test_gb_syav_synthetic_average_storeys_and_dwellings_round_half_up():
    """Verify D-EU-04 / Option A half-up rounding for the three GB AB SyAv rows."""
    syav_records = {
        r["archetype_id"]: r for r in _records() if "AB" in r["archetype_id"] and "SyAv" in r["archetype_id"]
    }
    assert len(syav_records) == 3

    # 1. GB.ENG.AB.01: n_apt=6.57 -> 7, n_storey=2.96 -> 3 => [3, 2, 2]
    r1 = syav_records["GB.ENG.AB.01.ApartmentBuildings.SyAv.001.001"]
    a1 = _allocation(r1)
    assert a1.dwelling_count == 7
    assert a1.storey_count == 3
    assert [f.dwelling_count for f in a1.floor_allocations] == [3, 2, 2]
    assert sum(f.conditioned_area_m2 for f in a1.floor_allocations) == pytest.approx(r1["geometry"]["a_c_ref_m2"])
    assert a1.has_unconditioned_core  # 7/3 = 2.33 >= 2.0

    # 2. GB.ENG.AB.02-03: n_apt=13.64 -> 14, n_storey=3.65 -> 4 => [4, 4, 3, 3]
    r2 = syav_records["GB.ENG.AB.02-03.ApartmentBuildings.SyAv.002.001"]
    a2 = _allocation(r2)
    assert a2.dwelling_count == 14
    assert a2.storey_count == 4
    assert [f.dwelling_count for f in a2.floor_allocations] == [4, 4, 3, 3]
    assert sum(f.conditioned_area_m2 for f in a2.floor_allocations) == pytest.approx(r2["geometry"]["a_c_ref_m2"])
    assert a2.has_unconditioned_core  # 14/4 = 3.5 >= 2.0

    # 3. GB.ENG.AB.04-08: n_apt=17.21 -> 17, n_storey=3.75 -> 4 => [5, 4, 4, 4]
    r3 = syav_records["GB.ENG.AB.04-08.ApartmentBuildings.SyAv.005.001"]
    a3 = _allocation(r3)
    assert a3.dwelling_count == 17
    assert a3.storey_count == 4
    assert [f.dwelling_count for f in a3.floor_allocations] == [5, 4, 4, 4]
    assert sum(f.conditioned_area_m2 for f in a3.floor_allocations) == pytest.approx(r3["geometry"]["a_c_ref_m2"])
    assert a3.has_unconditioned_core  # 17/4 = 4.25 >= 2.0


def test_non_integer_apartment_count_uses_half_up_and_first_storey_remainder_rule():
    allocation = allocate_european_dwellings(
        archetype_id="GB.TEST.AB.SyAv",
        building_type="AB",
        n_apartment=6.57,
        n_storey=4,
        plate_area_m2=100.0,
    )
    assert allocation.dwelling_count == 7
    assert [floor.dwelling_count for floor in allocation.floor_allocations] == [2, 2, 2, 1]
    assert allocation.units_per_floor == 2


def test_core_is_external_to_conditioned_tabula_plate_only_at_ruled_density():
    multi = allocate_european_dwellings(
        archetype_id="ES.TEST.MFH", building_type="MFH", n_apartment=6, n_storey=3, plate_area_m2=200.0,
    )
    single = allocate_european_dwellings(
        archetype_id="FR.TEST.MFH", building_type="MFH", n_apartment=1, n_storey=1, plate_area_m2=497.2,
    )
    assert multi.has_unconditioned_core
    assert all(floor.conditioned_area_m2 == 200.0 for floor in multi.floor_allocations)
    assert all(floor.unconditioned_core_area_m2 == pytest.approx(200.0 * CORE_FRACTION_OF_PLATE) for floor in multi.floor_allocations)
    assert not single.has_unconditioned_core
    assert single.floor_allocations[0].unconditioned_core_area_m2 == 0.0


def test_allocation_rejects_non_residential_or_nonpositive_inputs():
    with pytest.raises(ValueError, match="building_type"):
        allocate_european_dwellings(archetype_id="x", building_type="Office", n_apartment=1, n_storey=1, plate_area_m2=1)
    with pytest.raises(ValueError, match="n_storey"):
        allocate_european_dwellings(archetype_id="x", building_type="SFH", n_apartment=1, n_storey=0, plate_area_m2=1)
    with pytest.raises(ValueError, match="n_storey"):
        allocate_european_dwellings(archetype_id="x", building_type="SFH", n_apartment=1, n_storey=-2.5, plate_area_m2=1)
    with pytest.raises(ValueError, match="n_apartment"):
        allocate_european_dwellings(archetype_id="x", building_type="SFH", n_apartment=0, n_storey=1, plate_area_m2=1)
