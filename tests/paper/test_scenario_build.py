import csv
import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "paper" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sb = _load("scenario_build")
rc = _load("retrofit_check")

REAL_SMALL_OFFICE = (ROOT / "docs" / "validations" / "overAll" / "evidence" / "open48_runs" / "open07_ab_sim"
                     / "nyc_rural" / "way_965718402" / "B_SmallOffice_as_recorded_in_t19.idf")
REAL_WAREHOUSE = (ROOT / "docs" / "validations" / "overAll" / "evidence" / "open48_runs" / "run2_refleet"
                  / "la_urban" / "way_402215469" / "way_402215469.idf")

THERMOSTATS = (
    ("HVACTEMPLATE:THERMOSTAT", "Heating_Setpoint_Schedule_Name"),
    ("THERMOSTATSETPOINT:DUALSETPOINT", "Heating_Setpoint_Temperature_Schedule_Name"),
)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _heating_deltas(src, out):
    from openubem.scenarios import measures as m

    a = sb.load_idf(Path(src))
    b = sb.load_idf(Path(out))
    deltas = set()
    for key, field in THERMOSTATS:
        for ta, tb in zip(a.idfobjects[key], b.idfobjects[key]):
            name_a, name_b = getattr(ta, field), getattr(tb, field)
            if name_a == name_b:
                continue
            ea = m._parse_compact_value_entries(m._find_compact_schedule(a, name_a))
            eb = m._parse_compact_value_entries(m._find_compact_schedule(b, name_b))
            for x, y in zip(ea, eb):
                if x["value"] != y["value"]:
                    deltas.add(round(x["value"] - y["value"], 4))
    return deltas


def _status_row(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    return rows[0]


@pytest.fixture(scope="module")
def builder_idf(tmp_path_factory):
    d = tmp_path_factory.mktemp("synthetic")
    idf = rc._make_idf("SmallOffice")
    path = d / "relation_1.idf"
    path.write_text(idf.idfstr(), encoding="utf-8")
    return path


def test_setback_cell_changes_the_builder_thermostat_by_0_0556_k(builder_idf, tmp_path):
    before = _sha(builder_idf)
    out = tmp_path / "in.idf"
    status = tmp_path / "status.csv"
    row = sb.build(builder_idf, "SmallOffice", "setback", out, status)
    assert _sha(builder_idf) == before
    assert row["changed"] == 1 and row["agree"] == 1
    s = _status_row(status)
    assert s["setback_outcome"] == "applied" and s["cell"] == "setback" and s["stem"] == "relation_1"
    assert s["lighting_outcome"] == "" and s["infiltration_outcome"] == ""
    assert _heating_deltas(builder_idf, out) == {0.0556}


def test_lighting_only_on_out_of_scope_archetype_is_unchanged(builder_idf, tmp_path):
    out = tmp_path / "in.idf"
    status = tmp_path / "status.csv"
    row = sb.build(builder_idf, "Warehouse", "lighting", out, status)
    s = _status_row(status)
    assert s["lighting_outcome"] == "not_in_scope"
    assert row["changed"] == 0 and row["agree"] == 1


def test_baseline_is_not_a_buildable_cell(builder_idf, tmp_path):
    with pytest.raises(SystemExit):
        sb.build(builder_idf, "SmallOffice", "baseline", tmp_path / "in.idf", tmp_path / "status.csv")


def test_seven_cells_and_status_appends(builder_idf, tmp_path):
    assert len(sb.measure_cells()) == 7
    status = tmp_path / "status.csv"
    sb.build(builder_idf, "SmallOffice", "setback", tmp_path / "a.idf", status)
    sb.build(builder_idf, "SmallOffice", "setback", tmp_path / "b.idf", status)
    with open(status, newline="", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 2


@pytest.mark.skipif(not REAL_SMALL_OFFICE.exists(), reason="no local builder-made U.S. IDF")
def test_real_doe_vintage_small_office_setback_is_0_0056_k_and_input_untouched(tmp_path):
    before = _sha(REAL_SMALL_OFFICE)
    out = tmp_path / "in.idf"
    row = sb.build(REAL_SMALL_OFFICE, "SmallOffice", "setback", out, tmp_path / "status.csv")
    assert _sha(REAL_SMALL_OFFICE) == before
    assert row["changed"] == 1 and row["agree"] == 1
    assert _heating_deltas(REAL_SMALL_OFFICE, out) == {0.0056}


@pytest.mark.skipif(not REAL_SMALL_OFFICE.exists(), reason="no local builder-made U.S. IDF")
def test_real_us_small_office_lighting_and_combined_cell(tmp_path):
    r1 = sb.build(REAL_SMALL_OFFICE, "SmallOffice", "lighting", tmp_path / "l.idf", tmp_path / "l.csv")
    assert r1["lighting_outcome"] == "applied" and r1["changed"] == 1
    r2 = sb.build(REAL_SMALL_OFFICE, "SmallOffice", "lighting+setback", tmp_path / "ls.idf", tmp_path / "ls.csv")
    assert r2["lighting_outcome"] == "applied" and r2["setback_outcome"] == "applied" and r2["changed"] == 1


@pytest.mark.skipif(not REAL_WAREHOUSE.exists(), reason="no local builder-made U.S. IDF")
def test_real_us_warehouse_setback_is_already_compliant_so_unchanged(tmp_path):
    out = tmp_path / "in.idf"
    row = sb.build(REAL_WAREHOUSE, "Warehouse", "setback", out, tmp_path / "status.csv")
    assert row["setback_outcome"] == "unchanged"
    assert row["changed"] == 0 and row["agree"] == 1


GOLDEN_SQL = ROOT / "tests" / "fixtures" / "golden_sql" / "r1_single_zone.sql"


@pytest.mark.skipif(not GOLDEN_SQL.exists(), reason="no local golden .sql")
def test_parse_writes_one_row_with_the_t01_columns(tmp_path):
    import shutil

    import pandas as pd

    shutil.copy(GOLDEN_SQL, tmp_path / "eplusout.sql")
    (tmp_path / "eplusout.end").write_text("EnergyPlus Completed Successfully-- 0 Warning; 0 Severe Errors", encoding="utf-8")
    row_csv = tmp_path / "row.csv"
    parsed = sb.parse_one(tmp_path / "eplusout.sql", "way/1", 100.0, "", row_csv)
    assert parsed["parse_status"] == "success" and parsed["completed"] == 1
    r = pd.read_csv(row_csv)
    assert len(r) == 1
    for col in ("total_eui_kwh_m2", "dhw_district_eui_kwh_m2", "dhw_eui_kwh_m2", "heating_eui_kwh_m2",
                "floor_area_m2", "total_kwh", "completed"):
        assert col in r.columns
    assert r.loc[0, "total_kwh"] > 0
    assert not [c for c in r.columns if c.startswith("gwp_")]


@pytest.mark.skipif(not GOLDEN_SQL.exists(), reason="no local golden .sql")
def test_parse_without_end_file_is_not_completed(tmp_path):
    import shutil

    shutil.copy(GOLDEN_SQL, tmp_path / "eplusout.sql")
    parsed = sb.parse_one(tmp_path / "eplusout.sql", "way/1", 100.0, "", tmp_path / "row.csv")
    assert parsed["completed"] == 0
