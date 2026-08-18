"""T06 (PLAN_open-49-and-open-01-2026-08-13.md) — regression tests for the OPEN-01
denominator swap: resolve_simulated_floor_area() and its wiring into parse_building().

Ruling 6: the EUI denominator is the multiplier-aware simulated area from eplusout.eio
(Sigma(Floor Area x Zone Multiplier x Zone List Multiplier) over zones with
Part of Total Building Area = Yes) when that file parses; footprint_area x num_floors
otherwise. Three cases, per the plan: .eio present and well-formed; .eio absent;
.eio present but malformed. Each case must assert the provenance value, not just
the number — a silent switch between two denominators is exactly the failure mode
this module exists to prevent (see openubem/results/parser.py fact 6/8 comments).
"""
from __future__ import annotations

import math
import shutil
from pathlib import Path

import pandas as pd
import pytest

from openubem.results.parser import parse_building, resolve_simulated_floor_area

GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden_sql"

_EIO_HEADER = (
    "! <Zone Information>,Zone Name,North Axis {deg},Origin X-Coordinate {m},"
    "Origin Y-Coordinate {m},Origin Z-Coordinate {m},Centroid X-Coordinate {m},"
    "Centroid Y-Coordinate {m},Centroid Z-Coordinate {m},Type,Zone Multiplier,"
    "Zone List Multiplier,Minimum X {m},Maximum X {m},Minimum Y {m},Maximum Y {m},"
    "Minimum Z {m},Maximum Z {m},Ceiling Height {m},Volume {m3},"
    "Zone Inside Convection Algorithm {Simple-Detailed-CeilingDiffuser-TrombeWall},"
    "Zone Outside Convection Algorithm {Simple-Detailed-Tarp-MoWitt-DOE-2-BLAST}, "
    "Floor Area {m2},Exterior Gross Wall Area {m2},Exterior Net Wall Area {m2},"
    "Exterior Window Area {m2}, Number of Surfaces, Number of SubSurfaces, "
    "Number of Shading SubSurfaces,  Part of Total Building Area\n"
)


def _well_formed_eio_text() -> str:
    """Two zones: one Zone Multiplier=2/Zone List Multiplier=3 counted (Part=Yes,
    Floor Area=100 -> contributes 100*2*3=600), one excluded (Part=No, Floor Area=50,
    contributes 0). area_multiplier_aware_m2 must come out to 600.0, not
    area_plain_m2 (150.0) and not footprint x num_floors.
    """
    included = (
        " Zone Information, INCLUDED ZONE,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1,2,3,"
        "0.0,10.0,0.0,10.0,0.0,3.0,3.0,300.0,TARP,TARP,100.0,90.0,70.0,18.0,6,2,0,Yes\n"
    )
    excluded = (
        " Zone Information, EXCLUDED ZONE,0.0,0.0,0.0,0.0,0.0,0.0,0.0,1,1,1,"
        "0.0,10.0,0.0,10.0,0.0,3.0,3.0,150.0,TARP,TARP,50.0,45.0,35.0,9.0,6,2,0,No\n"
    )
    return _EIO_HEADER + included + excluded


def _malformed_eio_text() -> str:
    """Header present, immediately EOF — parse_eio_zone_area() returns
    parse_status='header_found_zero_rows', area_multiplier_aware_m2=0.0."""
    return _EIO_HEADER


class TestResolveSimulatedFloorAreaThreeCases:
    """The three cases named in T06's How, at the resolve_simulated_floor_area() unit."""

    def test_eio_present_well_formed_uses_simulated_area(self, tmp_path):
        sql_path = tmp_path / "eplusout.sql"
        (tmp_path / "eplusout.eio").write_text(_well_formed_eio_text(), encoding="utf-8")

        floor_area, provenance = resolve_simulated_floor_area(sql_path, footprint_area=999.0, num_floors=5)

        assert provenance == "eio_simulated"
        assert math.isclose(floor_area, 600.0, rel_tol=1e-9), \
            f"expected multiplier-aware area 600.0 (100*2*3), got {floor_area}"
        # Sanity: this must differ from both the plain area and the fallback,
        # proving the multiplier-aware column (not area_plain_m2) is what's read.
        assert not math.isclose(floor_area, 150.0), "used area_plain_m2, not area_multiplier_aware_m2"
        assert not math.isclose(floor_area, 999.0 * 5), "used the fallback despite a well-formed .eio"

    def test_eio_absent_falls_back_no_exception(self, tmp_path):
        sql_path = tmp_path / "eplusout.sql"  # no eplusout.eio written alongside it
        try:
            floor_area, provenance = resolve_simulated_floor_area(sql_path, footprint_area=200.0, num_floors=3)
        except Exception as exc:  # pragma: no cover - the assertion below is the real check
            pytest.fail(f"resolve_simulated_floor_area raised on missing .eio: {exc!r}")

        assert provenance == "footprint_fallback"
        assert math.isclose(floor_area, 600.0, rel_tol=1e-9)

    def test_eio_present_malformed_falls_back(self, tmp_path):
        sql_path = tmp_path / "eplusout.sql"
        (tmp_path / "eplusout.eio").write_text(_malformed_eio_text(), encoding="utf-8")

        floor_area, provenance = resolve_simulated_floor_area(sql_path, footprint_area=50.0, num_floors=4)

        assert provenance == "footprint_fallback"
        assert math.isclose(floor_area, 200.0, rel_tol=1e-9)

    def test_sql_path_none_falls_back_no_exception(self):
        """No sql_path at all (e.g. a never-simulated building) must not raise."""
        floor_area, provenance = resolve_simulated_floor_area(None, footprint_area=10.0, num_floors=1)
        assert provenance == "footprint_fallback"
        assert math.isclose(floor_area, 10.0, rel_tol=1e-9)


class TestParseBuildingFloorAreaProvenance:
    """End-to-end: parse_building() must surface floor_area_m2/floor_area_provenance
    and the EUI columns must actually be divided by the simulated area, not silently
    still by footprint x num_floors."""

    def _manifest_row(self, footprint_m2: float, num_floors: int) -> pd.Series:
        # osm_id must match the golden fixture's zone-name encoding (way/R1) or the
        # I2 foreign-osm_id guard aborts the run before EUI is even computed.
        return pd.Series({
            "osm_id": "way/R1",
            "footprint_area_m2": footprint_m2,
            "levels": float(num_floors),
            "height_m": float("nan"),
            "num_zones": 1,
            "data_quality_flag": "",
        })

    def test_well_formed_eio_changes_eui_denominator(self, tmp_path):
        sql_path = tmp_path / "eplusout.sql"
        shutil.copyfile(GOLDEN_DIR / "r1_single_zone.sql", sql_path)
        # footprint x num_floors would be 196*2=392; force the simulated area to a
        # deliberately different value (600) so a silent fallback would be caught.
        (tmp_path / "eplusout.eio").write_text(_well_formed_eio_text(), encoding="utf-8")

        row = self._manifest_row(footprint_m2=196.0, num_floors=2)
        result = parse_building(sql_path, None, row)

        assert result["floor_area_provenance"] == "eio_simulated"
        assert math.isclose(result["floor_area_m2"], 600.0, rel_tol=1e-9)

        # Cross-check: re-run with the .eio absent (fallback) and confirm the EUI
        # columns scale by exactly footprint_area_fallback / eio_area, proving the
        # denominator actually changed the reported EUI, not just the metadata column.
        (tmp_path / "eplusout.eio").unlink()
        result_fallback = parse_building(sql_path, None, row)
        assert result_fallback["floor_area_provenance"] == "footprint_fallback"
        assert math.isclose(result_fallback["floor_area_m2"], 392.0, rel_tol=1e-9)

        # eui = kwh / area, so eui scales inversely with the area used as denominator.
        ratio = result["floor_area_m2"] / result_fallback["floor_area_m2"]
        for col in ("heating_eui_kwh_m2", "cooling_eui_kwh_m2", "lighting_eui_kwh_m2", "total_eui_kwh_m2"):
            assert math.isclose(result_fallback[col], result[col] * ratio, rel_tol=1e-6), (
                f"{col} did not scale with the denominator: eio={result[col]}, "
                f"fallback={result_fallback[col]}, expected ratio {ratio}"
            )

    def test_eio_absent_provenance_on_real_golden_fixture(self):
        """Golden fixtures directory has no eplusout.eio siblings (by design — those
        are standalone .sql copies, not full run directories), so every existing
        golden-SQL test exercises the fallback path. Pin that explicitly here."""
        row = self._manifest_row(footprint_m2=196.0, num_floors=2)
        result = parse_building(GOLDEN_DIR / "r1_single_zone.sql", None, row)
        assert result["floor_area_provenance"] == "footprint_fallback"
        assert math.isclose(result["floor_area_m2"], 392.0, rel_tol=1e-9)

    def test_failed_parse_still_reports_provenance(self):
        """Even a failed_parse row carries floor_area_m2/floor_area_provenance —
        resolved before the parse attempt, per parse_building()'s ordering."""
        row = self._manifest_row(footprint_m2=100.0, num_floors=1)
        result = parse_building(GOLDEN_DIR / "nonexistent.sql", None, row)
        assert result["parse_status"] == "failed_parse"
        assert result["floor_area_provenance"] == "footprint_fallback"
        assert math.isclose(result["floor_area_m2"], 100.0, rel_tol=1e-9)
