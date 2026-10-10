from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from openubem.data.construction.tabula_registry import generate_country_registry, generate_fr_registry


ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "openubem" / "data" / "construction"
FIXTURE = Path(__file__).parent / "fixtures" / "calc_fixture_fr3.xlsx"
WORKBOOK = Path("C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ/Step8_docs/outputs_step8/raw/tabula-calculator.xlsx")


def _by_id(path: Path) -> dict:
    return {record["archetype_id"]: record for record in json.loads(path.read_text(encoding="utf-8"))["records"]}


def _assert_close(left, right):
    if isinstance(right, dict):
        assert left.keys() == right.keys()
        for key in right:
            _assert_close(left[key], right[key])
    elif isinstance(right, list):
        assert len(left) == len(right)
        for a, b in zip(left, right):
            _assert_close(a, b)
    elif isinstance(right, float):
        assert left == pytest.approx(right, rel=1e-12, abs=1e-12)
    else:
        assert left == right


def test_country_registry_on_fixture_equals_committed_fr_records(tmp_path):
    destination = generate_country_registry("FR", FIXTURE, tmp_path, expected_md5=None)
    generated = _by_id(destination)
    committed = _by_id(DATA_DIR / "tabula_archetypes_fr.json")
    fixture_sha = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert len(generated) == 3
    for archetype_id, record in generated.items():
        assert record.pop("source_workbook_sha256") == fixture_sha
        expected = dict(committed[archetype_id])
        expected.pop("source_workbook_sha256")
        _assert_close(record, expected)


def test_country_registry_rejects_wrong_md5(tmp_path):
    with pytest.raises(ValueError, match="Unexpected calculator workbook MD5"):
        generate_country_registry("FR", FIXTURE, tmp_path)


def test_country_registry_rejects_country_without_rows(tmp_path):
    with pytest.raises(ValueError, match="No Number_BuildingVariant"):
        generate_country_registry("AT", FIXTURE, tmp_path, expected_md5=None)


@pytest.mark.skipif(not WORKBOOK.exists(), reason="Pinned parent calculator workbook is unavailable")
def test_country_registry_fr_is_byte_identical_to_committed(tmp_path):
    destination = generate_country_registry("FR", WORKBOOK, tmp_path)
    assert destination.read_bytes() == (DATA_DIR / "tabula_archetypes_fr.json").read_bytes()


@pytest.mark.skipif(not WORKBOOK.exists(), reason="Pinned parent calculator workbook is unavailable")
@pytest.mark.parametrize("cc, rows", [("AT", 61), ("HU", 16)])
def test_country_registry_new_tabula_countries_row_counts(tmp_path, cc, rows):
    destination = generate_country_registry(cc, WORKBOOK, tmp_path)
    records = json.loads(destination.read_text(encoding="utf-8"))["records"]
    assert len(records) == rows
    assert all(record["survey_fold"] == cc.lower() for record in records)
    assert all(record["country_stock_code"] == cc for record in records)


@pytest.mark.skipif(not WORKBOOK.exists(), reason="Pinned parent calculator workbook is unavailable")
def test_generate_fr_registry_unchanged(tmp_path):
    generated = generate_fr_registry(WORKBOOK, tmp_path)
    committed = DATA_DIR / "tabula_archetypes_fr.json"
    assert hashlib.sha256(generated.read_bytes()).hexdigest() == hashlib.sha256(committed.read_bytes()).hexdigest()


from openubem.data.construction.national_records import build_records, rescale_transmission


IT_RECORDS = _by_id(DATA_DIR / "tabula_archetypes_it.json")
IT_KEYS = set(next(iter(IT_RECORDS.values())))
DONOR_A = "IT.MidClim.AB.01.Gen.ReEx.001.001"
DONOR_B = "IT.MidClim.SFH.02.Gen.ReEx.001.001"


def _spec(values_a, values_b=None, extra=None):
    spec = {
        "country": "FI",
        "fold": "fi",
        "donor_country": "IT",
        "periods": [{"code": "FI.01", "from": 0, "to": 1975}, {"code": "FI.02", "from": 1976, "to": 2010}],
        "entries": [
            {"building_type": "AB", "period": "FI.01", "donor_archetype_id": DONOR_A, "values": values_a},
            {"building_type": "SFH", "period": "FI.02", "donor_archetype_id": DONOR_B, "values": values_b or {}},
        ],
    }
    spec.update(extra or {})
    return spec


def _build(tmp_path, spec):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    out = build_records(spec_path, tmp_path / "out")
    return _by_id(out)


def _share(record):
    g = record["geometry"]
    window = sum(g["a_window_components_m2"])
    return window / (window + sum(g["a_wall_components_m2"]))


def test_spec_overrides_equal_spec_and_rest_equals_donor(tmp_path):
    values_a = {
        "u_window_w_m2k": {"value": 2.8, "source": "ASSUMED: test"},
        "g_gl_window": {"value": 0.6, "source": "doc p1"},
        "n_air_infiltration_h_1": {"value": 0.3, "source": "doc p2"},
        "mean_flat_area_m2": {"value": 50.0, "source": "doc p3"},
        "u_wall_w_m2k": {"value": 0.81, "source": "doc table 1"},
    }
    values_b = {"u_roof_w_m2k": {"value": 0.25, "source": "doc table 2"}, "delta_u_tb_w_m2k": {"value": 0.05, "source": "doc t3"}}
    built = _build(tmp_path, _spec(values_a, values_b))
    assert set(built) == {"FI.N.AB.01.Gen.ReEx.001.001", "FI.N.SFH.02.Gen.ReEx.001.001"}
    a = built["FI.N.AB.01.Gen.ReEx.001.001"]
    donor = IT_RECORDS[DONOR_A]
    assert set(a) == IT_KEYS
    assert a["u_window_w_m2k"] == pytest.approx(2.8, abs=1e-12)
    assert a["u_wall_w_m2k"] == pytest.approx(0.81, abs=1e-12)
    assert a["g_gl_window"] == 0.6
    assert a["n_air_infiltration_h_1"] == 0.3
    assert a["n_apartment"] == pytest.approx(donor["geometry"]["a_c_ref_m2"] / 50.0)
    untouched = [
        "boundary_condition", "c_m_wh_m2k", "f_red_htr1", "f_red_htr4", "f_red_temp", "geometry",
        "h_ventilation_w_m2k", "n_air_use_h_1", "phi_int_w_m2", "q_w_nd_kwh_m2a", "theta_i_c",
        "transmission_b_factors", "u_floor_w_m2k", "u_roof_w_m2k", "delta_u_tb_w_m2k", "g_gl_n_window_2",
        "source_workbook_md5", "source_workbook_sha256", "source_sheet",
    ]
    for key in untouched:
        assert a[key] == donor[key], key
    assert a["h_transmission_components_w_k"]["door_1"] == donor["h_transmission_components_w_k"]["door_1"]
    assert a["h_transmission_components_w_k"]["roof_1"] == donor["h_transmission_components_w_k"]["roof_1"]
    assert any(item.startswith(f"ASSUMED:donor {DONOR_A}") for item in a["parameter_assumptions"])
    assert a["survey_fold"] == "fi" and a["country_stock_code"] == "FI" and a["construction_period"] == "FI.01"
    b = built["FI.N.SFH.02.Gen.ReEx.001.001"]
    assert b["u_roof_w_m2k"] == pytest.approx(0.25, abs=1e-12)
    assert b["delta_u_tb_w_m2k"] == 0.05


def test_wwr_rescale_keeps_sum_and_hits_share(tmp_path):
    built = _build(tmp_path, _spec({"wwr": {"value": 0.18, "source": "doc p9"}}))
    a = built["FI.N.AB.01.Gen.ReEx.001.001"]
    donor = IT_RECORDS[DONOR_A]
    g, gd = a["geometry"], donor["geometry"]
    assert _share(a) == pytest.approx(0.18, abs=1e-9)
    assert sum(g["a_window_components_m2"]) + sum(g["a_wall_components_m2"]) == pytest.approx(
        sum(gd["a_window_components_m2"]) + sum(gd["a_wall_components_m2"]), abs=1e-9
    )
    assert sum(g["a_window_by_orientation_m2"].values()) == pytest.approx(sum(g["a_window_components_m2"]), abs=1e-9)
    ratio = [x / y for x, y in zip(g["a_wall_components_m2"], gd["a_wall_components_m2"]) if y > 0]
    assert max(ratio) - min(ratio) < 1e-9


def test_unknown_key_and_missing_source_raise(tmp_path):
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(_spec({"u_door_w_m2k": {"value": 1.0, "source": "x"}})), encoding="utf-8")
    with pytest.raises(ValueError, match="not allowed"):
        build_records(spec_path, tmp_path / "o1")
    spec_path.write_text(json.dumps(_spec({"u_wall_w_m2k": {"value": 1.0}})), encoding="utf-8")
    with pytest.raises(ValueError, match="neither a source nor an ASSUMED"):
        build_records(spec_path, tmp_path / "o2")
    spec_path.write_text(json.dumps(_spec({"u_wall_w_m2k": {"value": 1.0, "source": ""}})), encoding="utf-8")
    with pytest.raises(ValueError, match="neither a source nor an ASSUMED"):
        build_records(spec_path, tmp_path / "o3")


def _all_registry_records():
    records = []
    for cc in ("it", "es", "gb", "fr"):
        records.extend(json.loads((DATA_DIR / f"tabula_archetypes_{cc}.json").read_text(encoding="utf-8"))["records"])
    return records


def _slot_u(record):
    out = {}
    for slot, group, position in __import__("openubem.data.construction.national_records", fromlist=["_slots"])._slots():
        out[slot] = record["u_components_w_m2k"][group][position]
    return out


def test_unchanged_u_values_give_identical_parts():
    import copy

    worst = 0.0
    for record in _all_registry_records():
        clone = copy.deepcopy(record)
        rescale_transmission(clone, _slot_u(record))
        for slot, value in record["h_transmission_components_w_k"].items():
            worst = max(worst, abs(clone["h_transmission_components_w_k"][slot] - value))
    assert worst < 1e-9


def test_hand_value_on_fr_wall_3():
    import copy

    record = next(r for r in _all_registry_records() if r["archetype_id"] == "FR.N.SFH.01.Gen.ReEx.001.001")
    clone = copy.deepcopy(record)
    rescale_transmission(clone, {"wall_3": 0.5})
    area, b, u0, h0 = 11.1, 1.0, 1.9, record["h_transmission_components_w_k"]["wall_3"]
    resistance = b * area / h0 - 1.0 / u0
    assert resistance == pytest.approx(0.3, abs=1e-6)
    expected = b * area / (1.0 / 0.5 + resistance)
    assert clone["h_transmission_components_w_k"]["wall_3"] == pytest.approx(expected, abs=1e-9)
    assert clone["h_transmission_components_w_k"]["wall_2"] == record["h_transmission_components_w_k"]["wall_2"]


def test_count_ratio_fallback_slots_when_u_halved(capsys):
    import copy

    fallback_slots = 0
    total_records = 0
    for record in _all_registry_records():
        clone = copy.deepcopy(record)
        halved = {slot: 0.5 * u for slot, u in _slot_u(record).items()}
        fallback_slots += len(rescale_transmission(clone, halved))
        total_records += 1
    with capsys.disabled():
        print(f"\nTEST8 ratio-fallback slots at U1 = 0.5*U0: {fallback_slots} over {total_records} records")
    assert total_records == 142
    assert fallback_slots >= 0


def test_build_records_wall_override_rescales_parts_from_donor_u(tmp_path):
    donor = IT_RECORDS[DONOR_A]
    u1 = 0.5 * donor["u_wall_w_m2k"]
    built = _build(tmp_path, _spec({"u_wall_w_m2k": {"value": u1, "source": "ASSUMED: test"}}))
    record = built["FI.N.AB.01.Gen.ReEx.001.001"]
    checked = 0
    for index in range(1, 4):
        slot = f"wall_{index}"
        area = donor["geometry"]["a_wall_components_m2"][index - 1]
        h0 = donor["h_transmission_components_w_k"][slot]
        if area == 0.0 or h0 == 0.0:
            continue
        u0 = donor["u_components_w_m2k"]["wall"][index - 1]
        b = donor["transmission_b_factors"][slot]
        resistance = b * area / h0 - 1.0 / u0
        expected = b * area / (1.0 / u1 + resistance)
        assert record["h_transmission_components_w_k"][slot] == pytest.approx(expected, abs=1e-9)
        assert record["u_components_w_m2k"]["wall"][index - 1] == pytest.approx(u1, abs=1e-12)
        checked += 1
    assert checked >= 1
    assert record["h_transmission_w_m2k"] != donor["h_transmission_w_m2k"]
    assert record["h_transmission_components_w_k"]["roof_1"] == donor["h_transmission_components_w_k"]["roof_1"]
