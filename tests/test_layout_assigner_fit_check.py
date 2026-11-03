"""T9 -- prototype-vs-plot fit check unit tests (plan §6 E02,
PLAN_techtransfer-block2-2026-09-17.md)."""

from pathlib import Path

import pytest
import shapely
from shapely import affinity
from eppy.modeleditor import IDDAlreadySetError
from geomeppy import IDF as GeomIDF

from openubem import config
from openubem.geometry import layout_assigner

try:
    GeomIDF.setiddname(str(config.ENERGYPLUS_IDD_PATH))
except IDDAlreadySetError:
    pass

_BASELINE_AREA = 200.0


def _blank_template_path() -> Path:
    return Path(__file__).resolve().parent.parent / "openubem" / "idf" / "templates" / "residential_base.idf"


@pytest.fixture(scope="module")
def proto_idf_path(tmp_path_factory):
    idf = GeomIDF(str(_blank_template_path()))
    idf.add_block(name="Proto", coordinates=[(0, 0), (20, 0), (20, 10), (0, 10)], height=3.0, num_stories=1)
    out_dir = tmp_path_factory.mktemp("fit_check")
    out_path = out_dir / "synthetic_proto.idf"
    idf.saveas(str(out_path))
    return out_path


class _FakeRegistry:
    def __init__(self, idf_path, area):
        self._idf_path = idf_path
        self._area = area

    def get_baseline_idf(self, archetype_id):
        return self._idf_path

    def get_baseline_area(self, archetype_id):
        return self._area


def _patch_registry(monkeypatch, proto_idf_path):
    monkeypatch.setattr(
        layout_assigner, "get_registry", lambda: _FakeRegistry(proto_idf_path, _BASELINE_AREA)
    )


def _fit_check_via_applied_scale(footprint_poly, proto_idf_path, num_floors=1):
    real_area = footprint_poly.area * num_floors
    scaling = layout_assigner.calculate_scaling_factor(real_area, _BASELINE_AREA)
    return layout_assigner._fit_check(footprint_poly, proto_idf_path, scaling["planar_scale_factor"])


def test_raw_prototype_xy_extent_reads_synthetic_proto(proto_idf_path):
    extent = layout_assigner._raw_prototype_xy_extent(proto_idf_path)
    assert extent == pytest.approx((20.0, 10.0))


def test_comfortable_footprint_gives_no_reason(monkeypatch, proto_idf_path):
    _patch_registry(monkeypatch, proto_idf_path)
    l_shape = shapely.box(0, 0, 45, 45).difference(shapely.box(5, 5, 45, 45))
    assert l_shape.area == pytest.approx(425.0)

    reason, overflow = _fit_check_via_applied_scale(l_shape, proto_idf_path)

    assert reason is None
    assert overflow < 0


def test_narrow_footprint_raises_flag_with_positive_overflow(monkeypatch, proto_idf_path):
    _patch_registry(monkeypatch, proto_idf_path)
    narrow = shapely.box(0, 0, 60, 5)

    reason, overflow = _fit_check_via_applied_scale(narrow, proto_idf_path)

    assert reason == layout_assigner.PROTOTYPE_EXTENT_EXCEEDS_FOOTPRINT
    assert overflow == pytest.approx(7.2474, abs=1e-3)


def test_exact_half_metre_overflow_does_not_trigger(monkeypatch, proto_idf_path):
    _patch_registry(monkeypatch, proto_idf_path)
    y_side = 9.5
    x_side = _BASELINE_AREA / y_side
    footprint = shapely.box(0, 0, x_side, y_side)

    reason, overflow = _fit_check_via_applied_scale(footprint, proto_idf_path)

    assert reason is None
    assert overflow == pytest.approx(0.5, abs=1e-6)


def test_no_baseline_path_sets_both_keys_none():
    poly = shapely.box(0, 0, 10, 10)
    meta = layout_assigner.assign_baseline_layout("osm_d", poly, "Courthouse", num_floors=3)

    assert meta["no_baseline"] is True
    assert meta["fit_check_reason"] is None
    assert meta["fit_overflow_m"] is None


def test_rotated_footprint_judged_on_rotated_rectangle_not_bbox(monkeypatch, proto_idf_path):
    _patch_registry(monkeypatch, proto_idf_path)
    narrow = shapely.box(0, 0, 60, 5)
    rotated = affinity.rotate(narrow, 35, origin="centroid")

    axis_aligned_reason, axis_aligned_overflow = _fit_check_via_applied_scale(narrow, proto_idf_path)
    rotated_reason, rotated_overflow = _fit_check_via_applied_scale(rotated, proto_idf_path)

    assert rotated_reason == layout_assigner.PROTOTYPE_EXTENT_EXCEEDS_FOOTPRINT
    assert rotated_overflow == pytest.approx(axis_aligned_overflow, abs=1e-6)

    minx, miny, maxx, maxy = rotated.bounds
    bbox_dims = sorted([maxx - minx, maxy - miny], reverse=True)
    assert bbox_dims[0] != pytest.approx(60.0, abs=1e-3)
