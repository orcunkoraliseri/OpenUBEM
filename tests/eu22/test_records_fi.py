from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "openubem" / "data" / "construction"
SPEC = DATA_DIR / "national_specs" / "fi_spec.json"
TYPES = ("SFH", "TH", "MFH", "AB")
PERIODS = ("FI.01", "FI.02", "FI.03", "FI.04", "FI.05", "FI.06", "FI.07")
EXPECTED_RANGES = ((0, 1975), (1976, 1977), (1978, 1984), (1985, 2002), (2003, 2007), (2008, 2009), (2010, 9999))
OVERRIDES = (
    "u_wall_w_m2k", "u_roof_w_m2k", "u_floor_w_m2k", "u_window_w_m2k",
    "g_gl_window", "delta_u_tb_w_m2k", "n_air_infiltration_h_1", "mean_flat_area_m2",
)


def _spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))


def _records(cc):
    return json.loads((DATA_DIR / f"tabula_archetypes_{cc.lower()}.json").read_text(encoding="utf-8"))["records"]


def _by_type_period():
    return {(r["building_type"], r["construction_period"]): r for r in _records("FI")}


def test_record_count_and_types():
    records = _records("FI")
    assert len(records) == len(TYPES) * len(PERIODS)
    assert {r["building_type"] for r in records} == set(TYPES)
    assert set(_by_type_period()) == {(t, p) for t in TYPES for p in PERIODS}


def test_key_set_equals_it():
    it_keys = set(_records("IT")[0])
    for record in _records("FI"):
        assert set(record) == it_keys


def test_identity_fields():
    for record in _records("FI"):
        assert record["country_stock_code"] == "FI"
        assert record["survey_fold"] == "fi"
        assert record["archetype_id"].startswith("FI.N.")
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


def test_every_spec_value_has_source_or_assumed():
    for entry in _spec()["entries"]:
        assert set(entry["values"]) == set(OVERRIDES)
        for key, item in entry["values"].items():
            source = item.get("source", "")
            assert isinstance(source, str) and len(source) > 10, (entry["building_type"], entry["period"], key)
            assert source.startswith("ASSUMED:") or "p." in source or "Statistics Finland" in source, (entry["period"], key, source)


def test_u_values_do_not_increase_with_newer_periods(capsys):
    by = _by_type_period()
    increases = []
    for btype in TYPES:
        for field in ("u_wall_w_m2k", "u_roof_w_m2k", "u_floor_w_m2k", "u_window_w_m2k"):
            series = [by[(btype, p)][field] for p in PERIODS]
            for older, newer, p_old, p_new in zip(series, series[1:], PERIODS, PERIODS[1:]):
                if newer > older + 1e-9:
                    increases.append((btype, field, p_old, p_new, older, newer))
    print(f"U-value increases between consecutive periods: {increases if increases else 'none'}")
    assert increases == []


def test_window_share_in_range(capsys):
    shares = []
    for record in _records("FI"):
        g = record["geometry"]
        window = sum(g["a_window_components_m2"])
        wall = sum(g["a_wall_components_m2"])
        assert window > 0 and wall > 0, record["archetype_id"]
        share = window / (window + wall)
        assert 0.05 <= share <= 0.50, (record["archetype_id"], share)
        shares.append(share)
    print(f"FI window share min {min(shares):.4f} max {max(shares):.4f} n {len(shares)}")


def test_record_u_values_equal_spec_values():
    by = _by_type_period()
    for entry in _spec()["entries"]:
        record = by[(entry["building_type"], entry["period"])]
        for field in ("u_wall_w_m2k", "u_roof_w_m2k", "u_floor_w_m2k", "u_window_w_m2k"):
            assert record[field] == pytest.approx(entry["values"][field]["value"], abs=1e-9), (entry["period"], field)
        assert record["g_gl_window"] == entry["values"]["g_gl_window"]["value"]
        assert record["n_air_infiltration_h_1"] == entry["values"]["n_air_infiltration_h_1"]["value"]
        assert record["delta_u_tb_w_m2k"] == pytest.approx(entry["values"]["delta_u_tb_w_m2k"]["value"], abs=1e-12)
        flat = record["geometry"]["a_c_ref_m2"] / record["n_apartment"]
        assert flat == pytest.approx(entry["values"]["mean_flat_area_m2"]["value"], rel=1e-9)


def test_transmission_follows_the_new_u_values():
    for record in _records("FI"):
        g = record["geometry"]
        parts = record["h_transmission_components_w_k"]
        u = record["u_components_w_m2k"]["window"]
        for index in range(2):
            area = g["a_window_components_m2"][index]
            if area > 0:
                assert parts[f"window_{index + 1}"] == pytest.approx(area * u[index], rel=1e-9), record["archetype_id"]
        assert record["h_transmission_w_m2k"] == pytest.approx(sum(parts.values()) / g["a_c_ref_m2"], rel=1e-9)


def test_transmission_total_falls_from_oldest_to_newest(capsys):
    by = _by_type_period()
    for btype in TYPES:
        first = by[(btype, "FI.01")]["h_transmission_w_m2k"]
        last = by[(btype, "FI.07")]["h_transmission_w_m2k"]
        assert last < first, btype


def test_no_ratio_fallback_slots():
    for record in _records("FI"):
        assert not [a for a in record["parameter_assumptions"] if a.startswith("RATIO_FALLBACK")], record["archetype_id"]


def test_print_type_period_table_and_period_tuple(capsys):
    by = _by_type_period()
    lines = ["type period  U_wall U_roof U_floor U_window share  H_tr"]
    for btype in TYPES:
        for p in PERIODS:
            r = by[(btype, p)]
            g = r["geometry"]
            window = sum(g["a_window_components_m2"])
            wall = sum(g["a_wall_components_m2"])
            lines.append(
                f"{btype:4s} {p}  {r['u_wall_w_m2k']:.3f}  {r['u_roof_w_m2k']:.3f}  {r['u_floor_w_m2k']:.3f}  "
                f"{r['u_window_w_m2k']:.2f}     {window / (window + wall):.3f}  {r['h_transmission_w_m2k']:.3f}"
            )
    print("\n".join(lines))
    periods = _spec()["periods"]
    print("_TABULA_PERIODS['FI'] = (" + ", ".join(f'({p["from"]}, {p["to"]}, "{p["code"]}")' for p in periods) + ")")
