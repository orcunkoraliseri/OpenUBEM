import re
from pathlib import Path

import pytest
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF

from openubem import config
from openubem.idf.pv import (
    MAX_GENERATORS_PER_LIST,
    _DISTRIBUTION_NAME,
    classify_roof_surfaces,
    inject_pv,
    strip_existing_pv,
)

try:
    IDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_TEMPLATE = str(
    Path(__file__).resolve().parents[1]
    / "openubem" / "idf" / "templates" / "commercial_base.idf"
)

_PROTOTYPE_WITH_PLACEHOLDER = Path(config.BASELINE_IDF_DIR) / "ASHRAE901_OfficeMedium_STD2022_Buffalo.idf"
_PROTOTYPE_WITHOUT_PLACEHOLDER = Path(config.BASELINE_IDF_DIR) / "ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf"

_FLAT_10X10 = [(0, 0, 3), (0, 10, 3), (10, 10, 3), (10, 0, 3)]
_FLAT_10X10_ADJACENT = [(10, 0, 3), (10, 10, 3), (20, 10, 3), (20, 0, 3)]
_PITCHED_10X10 = [(0, 0, 3), (0, 10, 5), (10, 10, 5), (10, 0, 3)]
_SMALL_ROOF = [(0, 0, 3), (0, 1, 3), (1, 1, 3), (1, 0, 3)]


def _fresh_idf():
    return IDF(_TEMPLATE)


def _add_roof(idf, name, coords, outside_boundary_condition="Outdoors"):
    surface = idf.newidfobject(
        "BUILDINGSURFACE:DETAILED",
        Name=name,
        Surface_Type="Roof",
        Outside_Boundary_Condition=outside_boundary_condition,
    )
    surface.setcoords(coords)
    return surface


class TestStripExistingPv:
    def test_placeholder_prototype_strips_all_named_classes(self):
        idf = IDF(str(_PROTOTYPE_WITH_PLACEHOLDER))
        counts = strip_existing_pv(idf)
        assert counts == {
            "GENERATOR:PVWATTS": 1,
            "ELECTRICLOADCENTER:GENERATORS": 1,
            "ELECTRICLOADCENTER:INVERTER:PVWATTS": 1,
            "ELECTRICLOADCENTER:DISTRIBUTION": 1,
        }
        for object_class in counts:
            assert len(idf.idfobjects[object_class]) == 0

    def test_pv_sch_left_in_place_after_strip(self):
        idf = IDF(str(_PROTOTYPE_WITH_PLACEHOLDER))
        strip_existing_pv(idf)
        schedule_names = {s.Name for s in idf.idfobjects["SCHEDULE:COMPACT"]}
        assert "PV_SCH" in schedule_names

    def test_no_dangling_references_after_strip(self):
        idf = IDF(str(_PROTOTYPE_WITH_PLACEHOLDER))
        removed_unique_names = {"PV_module", "PV_Generator", "PV_Inverter"}
        strip_existing_pv(idf)
        for object_list in idf.idfobjects.values():
            for obj in object_list:
                for field in obj.fieldnames[1:]:
                    value = getattr(obj, field, None)
                    assert value not in removed_unique_names

    def test_no_placeholder_prototype_is_noop(self):
        idf = IDF(str(_PROTOTYPE_WITHOUT_PLACEHOLDER))
        counts = strip_existing_pv(idf)
        assert all(count == 0 for count in counts.values())


class TestClassifyRoofSurfaces:
    def test_flat_surfaces_single_z_level_are_group_b(self):
        idf = _fresh_idf()
        _add_roof(idf, "roof1", _FLAT_10X10)
        _add_roof(idf, "roof2", _FLAT_10X10_ADJACENT)
        groups = classify_roof_surfaces(idf)
        assert len(groups["group_a"]) == 0
        assert len(groups["group_b"]) == 2
        assert len(groups["group_c"]) == 0

    def test_flat_surfaces_multi_z_level_are_group_c(self):
        idf = _fresh_idf()
        _add_roof(idf, "roof_low", _FLAT_10X10)
        elevated = [(x, y, z + 3) for x, y, z in _FLAT_10X10_ADJACENT]
        _add_roof(idf, "roof_high", elevated)
        groups = classify_roof_surfaces(idf)
        assert len(groups["group_b"]) == 0
        assert len(groups["group_c"]) == 2

    def test_pitched_surface_is_group_a(self):
        idf = _fresh_idf()
        _add_roof(idf, "pitched", _PITCHED_10X10)
        groups = classify_roof_surfaces(idf)
        assert len(groups["group_a"]) == 1
        assert groups["group_a"][0].Name == "pitched"

    def test_non_outdoors_boundary_condition_never_qualifies(self):
        idf = _fresh_idf()
        _add_roof(idf, "interior_roof", _FLAT_10X10, outside_boundary_condition="Surface")
        groups = classify_roof_surfaces(idf)
        assert groups["group_a"] == []
        assert groups["group_b"] == []
        assert groups["group_c"] == []
        assert groups["skipped_boundary_condition"] == 1

    def test_below_minimum_area_is_skipped(self):
        idf = _fresh_idf()
        _add_roof(idf, "tiny_roof", _SMALL_ROOF)
        groups = classify_roof_surfaces(idf)
        assert groups["group_a"] == []
        assert groups["group_b"] == []
        assert groups["skipped_min_area"] == 1


class TestInjectPv:
    def test_two_flat_roofs_create_two_generators_and_one_distribution(self):
        idf = _fresh_idf()
        _add_roof(idf, "roof1", _FLAT_10X10)
        _add_roof(idf, "roof2", _FLAT_10X10_ADJACENT)
        summary = inject_pv(idf, enabled=True)
        assert len(idf.idfobjects["GENERATOR:PVWATTS"]) == 2
        assert len(idf.idfobjects["ELECTRICLOADCENTER:DISTRIBUTION"]) == 1
        assert summary["n_generators"] == 2

    def test_idempotent_calling_twice_matches_calling_once(self):
        idf = _fresh_idf()
        _add_roof(idf, "roof1", _FLAT_10X10)
        _add_roof(idf, "roof2", _FLAT_10X10_ADJACENT)
        inject_pv(idf, enabled=True)
        once = idf.idfstr()
        inject_pv(idf, enabled=True)
        twice = idf.idfstr()
        assert once == twice

    def test_disabled_adds_no_object_but_returns_populated_summary(self):
        idf = _fresh_idf()
        _add_roof(idf, "roof1", _FLAT_10X10)
        before = idf.idfstr()
        summary = inject_pv(idf, enabled=False)
        after = idf.idfstr()
        assert before == after
        assert len(idf.idfobjects["GENERATOR:PVWATTS"]) == 0
        assert summary["n_generators"] == 1
        assert summary["total_dc_capacity_w"] > 0

    def test_non_outdoors_roof_never_injected(self):
        idf = _fresh_idf()
        _add_roof(idf, "interior_roof", _FLAT_10X10, outside_boundary_condition="Surface")
        summary = inject_pv(idf, enabled=True)
        assert summary["n_generators"] == 0
        assert len(idf.idfobjects["GENERATOR:PVWATTS"]) == 0

    def test_surface_below_minimum_area_skipped(self):
        idf = _fresh_idf()
        _add_roof(idf, "tiny_roof", _SMALL_ROOF)
        summary = inject_pv(idf, enabled=True)
        assert summary["n_generators"] == 0
        assert summary["skipped_min_area"] == 1

    def test_pitched_roof_produces_photovoltaic_not_pvwatts(self):
        idf = _fresh_idf()
        _add_roof(idf, "pitched", _PITCHED_10X10)
        summary = inject_pv(idf, enabled=True)
        assert len(idf.idfobjects["GENERATOR:PHOTOVOLTAIC"]) == 1
        assert len(idf.idfobjects["PHOTOVOLTAICPERFORMANCE:SIMPLE"]) == 1
        assert len(idf.idfobjects["GENERATOR:PVWATTS"]) == 0
        assert summary["n_pitched_generators"] == 1

    def test_mixed_pitched_and_flat_produce_both_and_one_distribution(self):
        idf = _fresh_idf()
        _add_roof(idf, "pitched", _PITCHED_10X10)
        _add_roof(idf, "flat", _FLAT_10X10_ADJACENT)
        summary = inject_pv(idf, enabled=True)
        assert len(idf.idfobjects["GENERATOR:PHOTOVOLTAIC"]) == 1
        assert len(idf.idfobjects["GENERATOR:PVWATTS"]) == 1
        assert len(idf.idfobjects["ELECTRICLOADCENTER:DISTRIBUTION"]) == 1
        assert summary["n_generators"] == 2

    def test_no_generator_cap_32_roofs_yield_32_generators(self):
        idf = _fresh_idf()
        for i in range(32):
            offset = i * 20
            coords = [
                (offset, 0, 3),
                (offset, 10, 3),
                (offset + 10, 10, 3),
                (offset + 10, 0, 3),
            ]
            _add_roof(idf, f"roof{i}", coords)
        summary = inject_pv(idf, enabled=True)
        assert len(idf.idfobjects["GENERATOR:PVWATTS"]) == 32
        assert len(idf.idfobjects["ELECTRICLOADCENTER:DISTRIBUTION"]) == 2
        assert summary["n_generators"] == 32
        assert summary["n_generator_lists"] == 2

    def test_generator_count_exceeding_cap_splits_into_multiple_lists(self):
        idf = _fresh_idf()
        n_roofs = MAX_GENERATORS_PER_LIST + 5
        for i in range(n_roofs):
            offset = i * 20
            coords = [
                (offset, 0, 3),
                (offset, 10, 3),
                (offset + 10, 10, 3),
                (offset + 10, 0, 3),
            ]
            _add_roof(idf, f"roof{i}", coords)
        summary = inject_pv(idf, enabled=True)

        generator_lists = idf.idfobjects["ELECTRICLOADCENTER:GENERATORS"]
        distributions = idf.idfobjects["ELECTRICLOADCENTER:DISTRIBUTION"]
        inverters = idf.idfobjects["ELECTRICLOADCENTER:INVERTER:PVWATTS"]
        assert len(generator_lists) == 2
        assert len(distributions) == 2
        assert len(inverters) == 2
        assert {obj.Name for obj in generator_lists} == {
            "OpenUBEM_PV_Generators_1",
            "OpenUBEM_PV_Generators_2",
        }
        assert {obj.Name for obj in distributions} == {
            "OpenUBEM_PV_Distribution_1",
            "OpenUBEM_PV_Distribution_2",
        }
        assert {obj.Generator_List_Name for obj in distributions} == {
            "OpenUBEM_PV_Generators_1",
            "OpenUBEM_PV_Generators_2",
        }
        assert summary["n_generators"] == n_roofs
        assert summary["n_generator_lists"] == 2
        assert len(idf.idfobjects["GENERATOR:PVWATTS"]) == n_roofs

        text = idf.idfstr()
        blocks = re.findall(r"ELECTRICLOADCENTER:GENERATORS,(.*?);", text, re.DOTALL)
        assert len(blocks) == 2
        block_sizes = sorted(len(re.findall(r"!- Generator \d+ Name", b)) for b in blocks)
        assert block_sizes == [5, MAX_GENERATORS_PER_LIST]
        assert sum(block_sizes) == n_roofs

    def test_inject_strips_placeholder_chain_and_leaves_single_openubem_distribution(self):
        idf = IDF(str(_PROTOTYPE_WITH_PLACEHOLDER))
        summary = inject_pv(idf, enabled=True)
        distributions = idf.idfobjects["ELECTRICLOADCENTER:DISTRIBUTION"]
        assert len(distributions) == 1
        assert distributions[0].Name == _DISTRIBUTION_NAME
        assert summary["stripped"]["ELECTRICLOADCENTER:DISTRIBUTION"] == 1

    def test_disabled_leaves_placeholder_chain_fully_intact(self):
        idf = IDF(str(_PROTOTYPE_WITH_PLACEHOLDER))
        before = idf.idfstr()
        summary = inject_pv(idf, enabled=False)
        after = idf.idfstr()
        assert before == after
        assert "stripped" not in summary
        distributions = idf.idfobjects["ELECTRICLOADCENTER:DISTRIBUTION"]
        assert len(distributions) == 1
        assert distributions[0].Name != _DISTRIBUTION_NAME
