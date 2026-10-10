from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "openubem" / "data" / "construction"
SPEC = DATA_DIR / "national_specs" / "ca_spec.json"
TYPES = ("SFH", "TH", "MFH", "AB")
PERIODS = ("CA.01", "CA.02", "CA.03", "CA.04", "CA.05", "CA.06")
EXPECTED_RANGES = ((0, 1945), (1946, 1960), (1961, 1977), (1978, 1983), (1984, 2011), (2012, 9999))
BASE_OVERRIDES = {
    "u_wall_w_m2k", "u_roof_w_m2k", "u_floor_w_m2k", "u_window_w_m2k", "wwr",
}
SERIES_FIELDS = ("u_wall_w_m2k", "u_roof_w_m2k", "u_floor_w_m2k", "u_window_w_m2k")


def _spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))


def _records(cc):
    return json.loads((DATA_DIR / f"tabula_archetypes_{cc.lower()}.json").read_text(encoding="utf-8"))["records"]


def _by_type_period():
    return {(r["building_type"], r["construction_period"]): r for r in _records("CA")}


def _expected_keys(entry):
    keys = set(BASE_OVERRIDES)
    if entry["building_type"] in ("MFH", "AB"):
        keys.add("mean_flat_area_m2")
    if entry["period"] != "CA.06":
        keys.add("n_air_infiltration_h_1")
    return keys


def test_record_count_and_types():
    records = _records("CA")
    assert len(records) == len(TYPES) * len(PERIODS)
    assert {r["building_type"] for r in records} == set(TYPES)
    assert set(_by_type_period()) == {(t, p) for t in TYPES for p in PERIODS}


def test_key_set_equals_it():
    it_keys = set(_records("IT")[0])
    for record in _records("CA"):
        assert set(record) == it_keys


def test_identity_fields():
    for record in _records("CA"):
        assert record["country_stock_code"] == "CA"
        assert record["survey_fold"] == "ca"
        assert record["archetype_id"].startswith("CA.N.")
        assert "national sources per parameter_assumptions" in record["attribution"]
        assert any(a.startswith("ASSUMED:donor SE.N.") for a in record["parameter_assumptions"])


def test_periods_tile_without_gap_or_overlap():
    periods = _spec()["periods"]
    assert tuple(p["code"] for p in periods) == PERIODS
    assert tuple((p["from"], p["to"]) for p in periods) == EXPECTED_RANGES
    for (_, previous_to), (next_from, _) in zip(EXPECTED_RANGES, EXPECTED_RANGES[1:]):
        assert next_from == previous_to + 1
    for btype in TYPES:
        entries = [e["period"] for e in _spec()["entries"] if e["building_type"] == btype]
        assert tuple(entries) == PERIODS


def test_donor_pairing_is_recorded_and_from_se():
    for entry in _spec()["entries"]:
        assert entry["donor_archetype_id"].startswith("SE.N.")
        expected_type = "SFH" if entry["building_type"] in ("SFH", "TH") else "MFH"
        assert entry["donor_archetype_id"].split(".")[2] == expected_type


def test_every_spec_value_has_source_or_assumed():
    for entry in _spec()["entries"]:
        assert set(entry["values"]) == _expected_keys(entry), (entry["building_type"], entry["period"])
        for key, item in entry["values"].items():
            source = item.get("source", "")
            assert isinstance(source, str) and len(source) > 10, (entry["building_type"], entry["period"], key)
            assert (
                source.startswith("ASSUMED:")
                or source.startswith("MEASURED:")
                or "p." in source
                or "pp." in source
            ), (entry["period"], key, source)


def test_u_values_do_not_increase_with_newer_periods(capsys):
    by = _by_type_period()
    increases = []
    for btype in TYPES:
        for field in SERIES_FIELDS:
            series = [by[(btype, p)][field] for p in PERIODS]
            for older, newer, p_old, p_new in zip(series, series[1:], PERIODS, PERIODS[1:]):
                if newer > older + 1e-9:
                    increases.append((btype, field, p_old, p_new, older, newer))
    print(f"U-value increases between consecutive periods: {increases if increases else 'none'}")
    assert increases == []


def test_window_share_in_range(capsys):
    shares = []
    for record in _records("CA"):
        g = record["geometry"]
        window = sum(g["a_window_components_m2"])
        wall = sum(g["a_wall_components_m2"])
        assert window > 0 and wall > 0, record["archetype_id"]
        share = window / (window + wall)
        assert 0.05 <= share <= 0.50, (record["archetype_id"], share)
        shares.append(share)
    print(f"CA window share min {min(shares):.4f} max {max(shares):.4f} n {len(shares)}")


def test_record_values_equal_spec_values():
    by = _by_type_period()
    for entry in _spec()["entries"]:
        record = by[(entry["building_type"], entry["period"])]
        values = entry["values"]
        for field in SERIES_FIELDS:
            assert record[field] == pytest.approx(values[field]["value"], abs=1e-9), (entry["period"], field)
        g = record["geometry"]
        window = sum(g["a_window_components_m2"])
        wall = sum(g["a_wall_components_m2"])
        assert window / (window + wall) == pytest.approx(values["wwr"]["value"], abs=1e-9)
        if "n_air_infiltration_h_1" in values:
            assert record["n_air_infiltration_h_1"] == values["n_air_infiltration_h_1"]["value"]
        if "mean_flat_area_m2" in values:
            flat = g["a_c_ref_m2"] / record["n_apartment"]
            assert flat == pytest.approx(values["mean_flat_area_m2"]["value"], rel=1e-9)


def test_donor_fields_not_overridden_stay_copied():
    for entry in _spec()["entries"]:
        if entry["period"] != "CA.06":
            continue
        record = _by_type_period()[(entry["building_type"], "CA.06")]
        assert any("n_air_infiltration_h_1" in a for a in record["parameter_assumptions"] if a.startswith("ASSUMED:donor"))


def test_transmission_follows_the_new_u_values():
    for record in _records("CA"):
        g = record["geometry"]
        parts = record["h_transmission_components_w_k"]
        u = record["u_components_w_m2k"]["window"]
        for index in range(2):
            area = g["a_window_components_m2"][index]
            if area > 0:
                part = parts[f"window_{index + 1}"]
                fallback = f"RATIO_FALLBACK: window_{index + 1}" in record["parameter_assumptions"]
                assert part > 0, record["archetype_id"]
                assert fallback or part <= area * u[index] * (1 + 1e-9), record["archetype_id"]
        assert record["h_transmission_w_m2k"] == pytest.approx(sum(parts.values()) / g["a_c_ref_m2"], rel=1e-9)


def test_transmission_total_falls_from_oldest_to_newest():
    by = _by_type_period()
    for btype in TYPES:
        assert by[(btype, "CA.06")]["h_transmission_w_m2k"] < by[(btype, "CA.01")]["h_transmission_w_m2k"], btype


def test_ratio_fallback_slots_are_listed(capsys):
    valid = {f"RATIO_FALLBACK: {slot}" for slot in ("wall_1", "wall_2", "wall_3", "roof_1", "roof_2", "floor_1", "floor_2", "window_1", "window_2")}
    total = 0
    for record in _records("CA"):
        found = [a for a in record["parameter_assumptions"] if a.startswith("RATIO_FALLBACK")]
        assert set(found) <= valid, record["archetype_id"]
        total += len(found)
    print(f"ratio-fallback slots over the 24 CA records: {total}")


def test_print_type_period_table_and_period_tuple(capsys):
    by = _by_type_period()
    lines = ["type period  U_wall U_roof U_floor U_window share  H_tr  n_air  flat_m2"]
    for btype in TYPES:
        for p in PERIODS:
            r = by[(btype, p)]
            g = r["geometry"]
            window = sum(g["a_window_components_m2"])
            wall = sum(g["a_wall_components_m2"])
            lines.append(
                f"{btype:4s} {p}  {r['u_wall_w_m2k']:.3f}  {r['u_roof_w_m2k']:.3f}  {r['u_floor_w_m2k']:.3f}  "
                f"{r['u_window_w_m2k']:.2f}     {window / (window + wall):.3f}  {r['h_transmission_w_m2k']:.3f}  "
                f"{r['n_air_infiltration_h_1']:.3f}  {g['a_c_ref_m2'] / r['n_apartment']:.1f}"
            )
    print("\n".join(lines))
    periods = _spec()["periods"]
    print("_TABULA_PERIODS['CA'] = (" + ", ".join(f'({p["from"]}, {p["to"]}, "{p["code"]}")' for p in periods) + ")")
