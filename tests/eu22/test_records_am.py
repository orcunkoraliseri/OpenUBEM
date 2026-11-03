from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "openubem" / "data" / "construction"
SPEC = DATA_DIR / "national_specs" / "am_spec.json"
PERIODS = ["AM.01", "AM.02", "AM.03", "AM.04", "AM.05"]
TYPES = ["SFH", "TH", "MFH", "AB"]
EXPECTED_INCREASES = {
    ("SFH", "u_wall_w_m2k", "AM.03", "AM.04"),
    ("TH", "u_wall_w_m2k", "AM.03", "AM.04"),
    ("MFH", "u_wall_w_m2k", "AM.03", "AM.04"),
    ("AB", "u_wall_w_m2k", "AM.03", "AM.04"),
    ("SFH", "u_roof_w_m2k", "AM.01", "AM.02"),
    ("MFH", "u_window_w_m2k", "AM.01", "AM.02"),
    ("AB", "u_window_w_m2k", "AM.01", "AM.02"),
}
ARMSTAT_HOA_PERIODS_YEREVAN = {"1950": 344, "1951-70": 1729, "1971-80": 1213, "1981-90": 1123, "1991-2000": 139, "2001-10": 91, "2011+": 82}
ARMSTAT_HOA_PERIODS_NOR_NORK = {"1950": 0, "1951-70": 268, "1971-80": 189, "1981-90": 164, "1991-2000": 32, "2001-10": 2, "2011+": 2}
ARMSTAT_HOA_MATERIAL_YEREVAN = {"stone": 2219, "panel": 2376, "monolithic": 126}
ARMSTAT_HOA_MATERIAL_NOR_NORK = {"stone": 205, "panel": 439, "monolithic": 13}


def _records(cc):
    return json.loads((DATA_DIR / f"tabula_archetypes_{cc.lower()}.json").read_text(encoding="utf-8"))["records"]


def _spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))


def _record(btype, period):
    matches = [r for r in _records("AM") if r["building_type"] == btype and r["construction_period"] == period]
    assert len(matches) == 1
    return matches[0]


def _share(record):
    geometry = record["geometry"]
    window = sum(geometry["a_window_components_m2"])
    wall = sum(geometry["a_wall_components_m2"])
    return window / (window + wall)


def test_record_count_and_ids():
    records = _records("AM")
    assert len(records) == 20
    assert {r["archetype_id"] for r in records} == {f"AM.N.{t}.{p[-2:]}.Gen.ReEx.001.001" for t in TYPES for p in PERIODS}
    assert {r["country_stock_code"] for r in records} == {"AM"}
    assert {r["survey_fold"] for r in records} == {"am"}


def test_key_set_equals_it():
    it_keys = set(_records("IT")[0])
    for record in _records("AM"):
        assert set(record) == it_keys


def test_periods_tile_for_every_type():
    spec = _spec()
    bounds = [(p["from"], p["to"], p["code"]) for p in spec["periods"]]
    assert [b[2] for b in bounds] == PERIODS
    assert bounds[0][0] == 0 and bounds[-1][1] == 9999
    for left, right in zip(bounds, bounds[1:]):
        assert right[0] == left[1] + 1
    for btype in TYPES:
        assert {e["period"] for e in spec["entries"] if e["building_type"] == btype} == set(PERIODS)
        assert {r["construction_period"] for r in _records("AM") if r["building_type"] == btype} == set(PERIODS)


def test_period_tuple_for_construction_sets():
    tuple_am = tuple((p["from"], p["to"], p["code"]) for p in _spec()["periods"])
    assert tuple_am == (
        (0, 1950, "AM.01"), (1951, 1970, "AM.02"), (1971, 1990, "AM.03"),
        (1991, 2015, "AM.04"), (2016, 9999, "AM.05"),
    )


def test_donors_are_bg_and_paired_by_overlap():
    donor_period = {"BG.01": (1900, 1918), "BG.02": (1919, 1929), "BG.03": (1930, 1959), "BG.04": (1960, 1998), "BG.05": (1999, 2008), "BG.06": (2009, 2100)}
    spec = _spec()
    for entry in spec["entries"]:
        assert entry["donor_archetype_id"].startswith(f"BG.N.{entry['building_type']}.")
        period = next(p for p in spec["periods"] if p["code"] == entry["period"])
        low, high = max(period["from"], 1900), min(period["to"], 2100)
        code = ".".join(entry["donor_archetype_id"].split(".")[3:4])
        donor_code = f"BG.{code}"
        overlap = max(0, min(high, donor_period[donor_code][1]) - max(low, donor_period[donor_code][0]) + 1)
        best = max(max(0, min(high, hi) - max(low, lo) + 1) for lo, hi in donor_period.values())
        if entry["building_type"] != "TH" or entry["period"] != "AM.01":
            assert overlap == best, entry["donor_archetype_id"]
    for record in _records("AM"):
        assert any(a.startswith("ASSUMED:donor BG.N.") for a in record["parameter_assumptions"])


def test_armstat_transcription_totals():
    assert sum(ARMSTAT_HOA_PERIODS_YEREVAN.values()) == 4721
    assert sum(ARMSTAT_HOA_MATERIAL_YEREVAN.values()) == 4721
    assert sum(ARMSTAT_HOA_PERIODS_NOR_NORK.values()) == 657
    assert sum(ARMSTAT_HOA_MATERIAL_NOR_NORK.values()) == 657
    assert round(2234659 / 34417, 2) == 64.93


def test_wall_values_follow_period_material_rule():
    expected = {"AM.01": 0.874, "AM.02": 0.874, "AM.03": 0.633, "AM.04": 0.874, "AM.05": 0.56}
    assert round(1 / 1.144, 3) == 0.874 and round(1 / 1.58, 3) == 0.633
    for btype in TYPES:
        for period, value in expected.items():
            assert _record(btype, period)["u_wall_w_m2k"] == pytest.approx(value, abs=1e-9)
    for btype in TYPES:
        assert _record(btype, "AM.05")["u_floor_w_m2k"] == pytest.approx(0.42, abs=1e-9)


def test_mean_flat_area_for_multi_apartment_types():
    for btype in ("MFH", "AB"):
        for period in PERIODS:
            record = _record(btype, period)
            assert record["n_apartment"] == pytest.approx(record["geometry"]["a_c_ref_m2"] / 64.93, rel=1e-9)
    for btype in ("SFH", "TH"):
        for period in PERIODS:
            assert _record(btype, period)["n_apartment"] == 1.0


def test_u_values_decrease_or_stay_equal_except_explained():
    increases = set()
    for btype in TYPES:
        for quantity in ("u_wall_w_m2k", "u_roof_w_m2k", "u_window_w_m2k"):
            for left, right in zip(PERIODS, PERIODS[1:]):
                if _record(btype, right)[quantity] > _record(btype, left)[quantity] + 1e-9:
                    increases.add((btype, quantity, left, right))
    print("increases:", sorted(increases))
    assert increases == EXPECTED_INCREASES


def test_window_share_range():
    for record in _records("AM"):
        assert 0.05 <= _share(record) <= 0.50, record["archetype_id"]


def test_every_value_has_source_or_assumed():
    spec = _spec()
    for entry in spec["entries"]:
        for key, item in entry["values"].items():
            assert item["source"].strip(), (entry["building_type"], entry["period"], key)
    for record in _records("AM"):
        notes = record["parameter_assumptions"]
        assert any(n.startswith("u_wall_w_m2k = ") and (("ASSUMED:" in n) or ("RACN 24-01-2016" in n)) for n in notes)
        assert any(n.startswith("ASSUMED:donor ") for n in notes)
        assert "national sources per parameter_assumptions" in record["attribution"]


def test_print_table(capsys):
    with capsys.disabled():
        print()
        print("type period U_wall U_roof U_floor U_window share n_flat")
        for btype in TYPES:
            for period in PERIODS:
                r = _record(btype, period)
                print(
                    btype, period, round(r["u_wall_w_m2k"], 3), round(r["u_roof_w_m2k"], 3),
                    round(r["u_floor_w_m2k"], 3), round(r["u_window_w_m2k"], 3), round(_share(r), 3),
                    round(r["n_apartment"], 1),
                )
        fallbacks = sum(1 for r in _records("AM") for n in r["parameter_assumptions"] if n.startswith("RATIO_FALLBACK"))
        print("ratio-fallback slots:", fallbacks)
