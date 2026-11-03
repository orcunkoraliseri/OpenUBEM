import csv
import importlib.util
import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "eu_flat_spread.py"
_spec = importlib.util.spec_from_file_location("eu_flat_spread", _P)
m = importlib.util.module_from_spec(_spec)
sys.modules["eu_flat_spread"] = m
_spec.loader.exec_module(m)

REAL_SQL = (
    Path(__file__).resolve().parents[2]
    / "openubem" / "outputs" / "eu_evidence" / "EU-11" / "division_residual_2026-09-29"
    / "scratch" / "ep" / "02f186e541967f24" / "eplusout.sql"
)


def make_sql(path, zones, hours=3, warmup_hours=1, frequency="Hourly", variable=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE Zones (ZoneIndex INTEGER, ZoneName TEXT, Multiplier REAL, ListMultiplier REAL, FloorArea REAL);"
        "CREATE TABLE Time (TimeIndex INTEGER, WarmupFlag INTEGER);"
        "CREATE TABLE ReportDataDictionary (ReportDataDictionaryIndex INTEGER, KeyValue TEXT, Name TEXT, ReportingFrequency TEXT);"
        "CREATE TABLE ReportData (ReportDataIndex INTEGER, TimeIndex INTEGER, ReportDataDictionaryIndex INTEGER, Value REAL);"
    )
    total = hours + warmup_hours
    for t in range(1, total + 1):
        conn.execute("INSERT INTO Time VALUES (?, ?)", (t, 1 if t <= warmup_hours else 0))
    name = variable or m.HEATING_VARIABLE
    rid = 0
    for i, (zone, area, mult, joules) in enumerate(zones, start=1):
        conn.execute("INSERT INTO Zones VALUES (?, ?, ?, 1.0, ?)", (i, zone, mult, area))
        conn.execute(
            "INSERT INTO ReportDataDictionary VALUES (?, ?, ?, ?)",
            (i, zone.upper() + m.IDEAL_SUFFIX, name, frequency),
        )
        for t in range(1, total + 1):
            rid += 1
            conn.execute("INSERT INTO ReportData VALUES (?, ?, ?, ?)", (rid, t, i, 9.9e9 if t <= warmup_hours else joules))
    conn.commit()
    conn.close()


KWH = 3.6e6


def test_variable_and_frequency_pinned():
    assert m.HEATING_VARIABLE == "Zone Ideal Loads Zone Total Heating Energy"
    assert m.HEATING_FREQUENCY == "Hourly"


def test_parse_zone_name():
    assert m.parse_zone_name("02F186E541967F24_F3_DWELLING_12") == (3, 12)
    assert m.parse_zone_name("CORE") == (None, None)


def test_read_zones_synthetic_multiplier_and_warmup(tmp_path):
    sql = tmp_path / "out" / "abc" / "eplusout.sql"
    make_sql(sql, [("ABC_F0_DWELLING_0", 50.0, 1.0, 2 * KWH), ("ABC_F1_DWELLING_0", 40.0, 2.0, 1 * KWH)])
    rows = m.read_zones(sql, "S", "abc")
    assert [r["zone"] for r in rows] == ["ABC_F0_DWELLING_0", "ABC_F1_DWELLING_0"]
    assert rows[0]["heating_kwh"] == pytest.approx(2.0 * 3)
    assert rows[1]["heating_kwh"] == pytest.approx(1.0 * 3 * 2)
    assert rows[1]["floor_area_m2"] == pytest.approx(80.0)
    assert (rows[1]["floor"], rows[1]["dwelling"]) == (1, 0)


def test_read_zones_wrong_frequency_raises(tmp_path):
    sql = tmp_path / "e.sql"
    make_sql(sql, [("A_F0_DWELLING_0", 10.0, 1.0, KWH)], frequency="RunPeriod")
    with pytest.raises(ValueError):
        m.read_zones(sql, "S", "a")


@pytest.mark.skipif(not REAL_SQL.exists(), reason="no local EnergyPlus .sql with ideal loads")
def test_read_zones_real_sql_sum_equals_independent_query():
    rows = m.read_zones(REAL_SQL, "T", "02f186e541967f24")
    assert len(rows) == 40
    assert all(r["floor"] is not None for r in rows)
    conn = sqlite3.connect(f"file:{REAL_SQL.as_posix()}?mode=ro", uri=True)
    joules = conn.execute(
        "SELECT SUM(r.Value) FROM ReportData r JOIN ReportDataDictionary d "
        "ON r.ReportDataDictionaryIndex = d.ReportDataDictionaryIndex JOIN Time t ON r.TimeIndex = t.TimeIndex "
        "WHERE d.Name = 'Zone Ideal Loads Zone Total Heating Energy' AND d.ReportingFrequency = 'Hourly' "
        "AND (t.WarmupFlag IS NULL OR t.WarmupFlag = 0)"
    ).fetchone()[0]
    area = conn.execute("SELECT SUM(FloorArea) FROM Zones").fetchone()[0]
    conn.close()
    total = sum(r["heating_kwh"] for r in rows)
    assert total > 0
    assert abs(total - joules / 3.6e6) / total < 1e-9
    assert sum(r["floor_area_m2"] for r in rows) == pytest.approx(area)


def test_building_spread_top_vs_middle():
    z = pd.DataFrame([
        ("S", "b", "B_F0_DWELLING_0", 0, 0, 100.0, 1000.0),
        ("S", "b", "B_F1_DWELLING_0", 1, 0, 100.0, 500.0),
        ("S", "b", "B_F2_DWELLING_0", 2, 0, 100.0, 700.0),
        ("S", "b", "B_F2_DWELLING_1", 2, 1, 100.0, 900.0),
    ], columns=m.ZONE_COLUMNS)
    s = m.building_spread(z).iloc[0]
    assert s["n_flats"] == 4
    assert s["heating_kwh"] == pytest.approx(3100.0)
    assert s["flat_eui_min"] == pytest.approx(5.0) and s["flat_eui_max"] == pytest.approx(10.0)
    assert s["spread_kwh_m2"] == pytest.approx(5.0)
    assert s["top_floor_eui_mean"] == pytest.approx(8.0)
    assert s["middle_floor_eui_mean"] == pytest.approx(5.0)
    assert s["top_minus_middle_kwh_m2"] == pytest.approx(3.0)


def test_building_spread_two_floors_has_no_middle():
    z = pd.DataFrame([
        ("S", "b", "B_F0_DWELLING_0", 0, 0, 100.0, 1000.0),
        ("S", "b", "B_F1_DWELLING_0", 1, 0, 100.0, 500.0),
    ], columns=m.ZONE_COLUMNS)
    s = m.building_spread(z).iloc[0]
    assert pd.isna(s["middle_floor_eui_mean"]) and s["n_floors"] == 2


def test_case_list_and_array_size(tmp_path):
    out = tmp_path / "cases.csv"
    assert m.write_case_list(out) == 10
    rows = list(csv.DictReader(out.open(encoding="utf-8")))
    assert list(rows[0].keys()) == ["site", "folder", "n_sql", "internal_only"]
    assert sum(int(r["n_sql"]) for r in rows) == 7820
    assert [r["site"] for r in rows if r["internal_only"] == "1"] == ["ZA-CPT-WOODSTOCK"]
    assert m.array_size(100) == 84
    assert m.n_chunks(1179, 100) == 12 and m.n_chunks(500, 100) == 5


def test_chunks_cover_every_stem_once(tmp_path):
    folder = tmp_path / "fleet"
    stems = [f"s{i:03d}" for i in range(7)]
    for s in stems:
        make_sql(folder / "out" / s / "eplusout.sql", [(f"{s.upper()}_F0_DWELLING_0", 10.0, 1.0, KWH)])
    seen = []
    for k in range(m.n_chunks(7, 3)):
        part = tmp_path / "parts" / f"p{k}.csv"
        done, bad = m.run_chunk(folder, "S", k, 3, part)
        assert bad == 0
        seen += pd.read_csv(part)["stem"].tolist()
    assert seen == stems


def test_chunk_records_bad_sql(tmp_path):
    folder = tmp_path / "fleet"
    make_sql(folder / "out" / "good" / "eplusout.sql", [("G_F0_DWELLING_0", 10.0, 1.0, KWH)])
    make_sql(folder / "out" / "nohvac" / "eplusout.sql", [("N_F0_DWELLING_0", 10.0, 1.0, KWH)], variable="Zone Lights Electricity Energy")
    part = tmp_path / "part.csv"
    done, bad = m.run_chunk(folder, "S", 0, 10, part)
    assert (done, bad) == (1, 1)
    assert pd.read_csv(tmp_path / "part_bad.csv")["stem"].tolist() == ["nohvac"]


def test_merge_matches_reference_within_tenth_of_percent(tmp_path, monkeypatch):
    tree = tmp_path / "tree"
    tree.mkdir()
    pd.DataFrame({"building_id": ["osm/1", "osm/2"], "stem": ["aaa", "bbb"]}).to_csv(tree / "prepared_buildings.csv", index=False)
    per_home = tmp_path / "per_home.csv"
    pd.DataFrame({
        "district": ["S", "S"], "building_id": ["osm/1", "osm/2"], "floor_area_m2": [200.0, 100.0],
        "heating_kwh": [9.0, 99.0], "has_result": [True, True], "tag": ["win_t", "win_t"],
    }).to_csv(per_home, index=False)

    class FakeSite(m.Site):
        @property
        def tree(self):
            return tree

    monkeypatch.setattr(m, "SITES", [FakeSite("S", "EU22", "t", 2, False, per_home)])
    parts = tmp_path / "parts"
    parts.mkdir()
    make_sql(tmp_path / "a.sql", [("AAA_F0_DWELLING_0", 100.0, 1.0, 1 * KWH), ("AAA_F1_DWELLING_0", 100.0, 1.0, 2 * KWH)])
    make_sql(tmp_path / "b.sql", [("BBB_F0_DWELLING_0", 100.0, 1.0, 40 * KWH)])
    rows = m.read_zones(tmp_path / "a.sql", "S", "aaa") + m.read_zones(tmp_path / "b.sql", "S", "bbb")
    pd.DataFrame(rows).to_csv(parts / "S__chunk000.csv", index=False)
    spread, check = m.merge_parts(parts)
    by = spread.set_index("stem")
    assert by.loc["aaa", "heating_check"] == "pass"
    assert by.loc["bbb", "heating_check"] == "fail"
    assert by.loc["aaa", "building_id"] == "osm/1"
    assert int(check.loc[0, "passed"]) == 1 and int(check.loc[0, "failed"]) == 1
