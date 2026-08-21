"""OPEN-60 (T03): lighting/equipment EUI must scale by zone multiplier x zone list
multiplier, matching the multiplier-aware floor-area denominator already produced by
resolve_simulated_floor_area(). See docs/docs_ACTIVE/openings/extra/FIX_open-60_multiplier-eui.md
and PLAN_rulings-and-fixes-2026-08-21.md T03.

Scope: openubem/results/parser.py — parse_eio_zone_multipliers() (new) and _compute_eui()'s
zone_multipliers parameter (new, optional, default-off). Does not touch resolve_simulated_floor_area()
or parse_eio_zone_area() (verbatim-pinned to the audit script).
"""
from pathlib import Path

import pandas as pd
import pytest

from openubem.results.parser import _compute_eui, parse_eio_zone_multipliers

_EIO_HEADER = (
    "! <Zone Information>,Zone Name,North Axis {deg},Origin X-Coordinate {m},"
    "Origin Y-Coordinate {m},Origin Z-Coordinate {m},Centroid X-Coordinate {m},"
    "Centroid Y-Coordinate {m},Centroid Z-Coordinate {m},Type,Zone Multiplier,"
    "Zone List Multiplier,Minimum X {m},Maximum X {m},Minimum Y {m},Maximum Y {m},"
    "Minimum Z {m},Maximum Z {m},Ceiling Height {m},Volume {m3},Zone Inside Convection "
    "Algorithm {Simple-Detailed-CeilingDiffuser-TrombeWall},Zone Outside Convection "
    "Algorithm {Simple-Detailed-Tarp-MoWitt-DOE-2-BLAST}, Floor Area {m2},"
    "Exterior Gross Wall Area {m2},Exterior Net Wall Area {m2},Exterior Window Area {m2},"
    " Number of Surfaces, Number of SubSurfaces, Number of Shading SubSurfaces,"
    "  Part of Total Building Area\n"
)


def _eio_zone_row(name: str, zone_mult: int, zone_list_mult: int, floor_area: float = 100.0) -> str:
    return (
        f" Zone Information, {name},0.0,0.00,0.00,0.00,1.0,1.0,1.0,1,"
        f"{zone_mult},{zone_list_mult},0.00,10.0,0.00,10.0,0.00,3.0,3.0,300.0,"
        f"TARP,TARP,{floor_area},0.00,0.00,0.00,4,0,0,Yes\n"
    )


def _write_eio(tmp_path: Path, rows: list[str]) -> Path:
    eio_path = tmp_path / "eplusout.eio"
    with open(eio_path, "w", encoding="utf-8") as f:
        f.write(_EIO_HEADER)
        for row in rows:
            f.write(row)
        f.write(" ! next block\n")
    return eio_path


def _make_row(footprint=100.0, num_floors=1):
    return pd.Series({
        "footprint_area_m2": footprint,
        "levels": num_floors,
        "height_m": num_floors * 3.5,
        "num_floors_override": None,
    })


def _make_two_zone_hourly_df(zone_a_kwh: float, zone_b_kwh: float) -> pd.DataFrame:
    records = []
    for zone, total_kwh in (("WAY/1_F0_WHOLE", zone_a_kwh), ("WAY/1_F1_WHOLE", zone_b_kwh)):
        per_hour = total_kwh / 8760.0
        for h in range(8760):
            records.append({"key_value": zone, "variable_name": "Zone Lights Electricity Energy",
                             "units": "kWh", "Month": 1, "Day": 1, "Hour": h % 24 + 1,
                             "value": per_hour})
            records.append({"key_value": zone, "variable_name": "Zone Electric Equipment Electricity Energy",
                             "units": "kWh", "Month": 1, "Day": 1, "Hour": h % 24 + 1,
                             "value": per_hour})
    return pd.DataFrame(records)


class TestParseEioZoneMultipliers:
    def test_reads_multiplier_times_list_multiplier(self, tmp_path):
        eio_path = _write_eio(tmp_path, [
            _eio_zone_row("WAY/1_F0_WHOLE", zone_mult=1, zone_list_mult=1),
            _eio_zone_row("WAY/1_F1_WHOLE", zone_mult=5, zone_list_mult=2),
        ])
        result = parse_eio_zone_multipliers(eio_path)
        assert result["WAY/1_F0_WHOLE"] == 1.0
        assert result["WAY/1_F1_WHOLE"] == 10.0

    def test_missing_file_returns_empty_dict(self, tmp_path):
        assert parse_eio_zone_multipliers(tmp_path / "nope.eio") == {}

    def test_no_zone_information_block_returns_empty_dict(self, tmp_path):
        eio_path = tmp_path / "eplusout.eio"
        eio_path.write_text("nothing here\n", encoding="utf-8")
        assert parse_eio_zone_multipliers(eio_path) == {}


class TestComputeEuiZoneMultiplierAware:
    def test_multiplier_5_zone_contributes_5x(self):
        row = _make_row(footprint=100.0, num_floors=1)
        df = _make_two_zone_hourly_df(zone_a_kwh=100.0, zone_b_kwh=100.0)
        zone_multipliers = {"WAY/1_F0_WHOLE": 1.0, "WAY/1_F1_WHOLE": 5.0}

        eui, _, missing = _compute_eui(
            df, row, "", floor_area=100.0, zone_multipliers=zone_multipliers,
        )
        assert missing is None
        # 100 kWh (mult 1) + 100 kWh x 5 (mult 5) = 600 kWh over 100 m2
        assert eui["lighting_eui_kwh_m2"] == pytest.approx(6.0)
        assert eui["equipment_eui_kwh_m2"] == pytest.approx(6.0)

    def test_unmapped_zone_defaults_to_multiplier_1(self):
        row = _make_row(footprint=100.0, num_floors=1)
        df = _make_two_zone_hourly_df(zone_a_kwh=100.0, zone_b_kwh=100.0)
        zone_multipliers = {"WAY/1_F0_WHOLE": 1.0}  # F1 zone absent from map

        eui, _, missing = _compute_eui(
            df, row, "", floor_area=100.0, zone_multipliers=zone_multipliers,
        )
        assert missing is None
        assert eui["lighting_eui_kwh_m2"] == pytest.approx(2.0)

    def test_omitted_zone_multipliers_is_bit_identical_to_pre_open60(self):
        row = _make_row(footprint=100.0, num_floors=1)
        df = _make_two_zone_hourly_df(zone_a_kwh=100.0, zone_b_kwh=100.0)

        eui_none, _, _ = _compute_eui(df, row, "", floor_area=100.0, zone_multipliers=None)
        eui_omitted, _, _ = _compute_eui(df, row, "", floor_area=100.0)
        eui_empty, _, _ = _compute_eui(df, row, "", floor_area=100.0, zone_multipliers={})

        assert eui_none["lighting_eui_kwh_m2"] == eui_omitted["lighting_eui_kwh_m2"] == eui_empty["lighting_eui_kwh_m2"]
        assert eui_none["lighting_eui_kwh_m2"] == pytest.approx(2.0)
