"""FINDING 206 regression test: circulation polygon must reach the EU-11 sidecar.

Scope: ``scripts/emit_eu11_layout_sidecars.py`` serializes
``storey_layout.circulation_polygon`` (present for ruled schemes) into a
``"circulation"`` key on each floor dict, ``None`` when the scheme
deliberately combines away the corridor shape (``l_shape_decomposition``, per
the pinned decision in
``docs/docs_ACTIVE/europeanLocations/implementation/PLAN_eu-circulation-viewer-2026-08-30.md``
section 3).

Reference: ``docs/docs_ACTIVE/europeanLocations/debugs/docs/
INVESTIGATION_viewer-circulation-not-drawn_2026-08-30.md`` section 1.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

RULED_GRID_SIDECAR = (
    ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / "ES-MAD-BERRUGUETE"
    / "layouts" / "way" / "388485191.json"
)
# EU-15 T04 finding: way/420409335 (the original fixture) no longer
# succeeds via l_shape_decomposition at all -- retiring the strip cutter as
# a success path revealed its wing combine was already failing
# (L_SHAPE_DECOMPOSITION_FAILED); it only "passed" pre-T04 via a wing that
# was itself served by the (then-mislabelled) strip cutter. Replaced with a
# real building whose every floor still emits via l_shape_decomposition
# post-T04/T05 (see docs/docs_EXPLANATION/OpenUBEM_debug_References.md,
# "European locations EU-15").
L_SHAPE_SIDECAR = (
    ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / "ES-MAD-BERRUGUETE"
    / "layouts" / "way" / "288461989.json"
)


@pytest.mark.skipif(not RULED_GRID_SIDECAR.exists(), reason="EU-11 side-cars not present in this environment")
def test_ruled_grid_building_carries_non_empty_circulation_ring_per_floor():
    data = json.loads(RULED_GRID_SIDECAR.read_text(encoding="utf-8"))
    assert data.get("scheme", "").startswith("ruled_grid_")
    assert data["floors"], "expected at least one floor"
    for floor in data["floors"]:
        circulation = floor.get("circulation")
        assert circulation is not None, floor.get("storey_index")
        assert len(circulation) >= 3, floor.get("storey_index")


@pytest.mark.skipif(not L_SHAPE_SIDECAR.exists(), reason="EU-11 side-cars not present in this environment")
def test_l_shape_decomposition_building_carries_null_circulation_per_floor():
    data = json.loads(L_SHAPE_SIDECAR.read_text(encoding="utf-8"))
    assert data.get("scheme") == "l_shape_decomposition"
    assert data["floors"], "expected at least one floor"
    for floor in data["floors"]:
        assert floor.get("circulation") is None, floor.get("storey_index")
