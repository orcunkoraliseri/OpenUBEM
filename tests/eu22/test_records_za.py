from __future__ import annotations

import json
from pathlib import Path

import pytest

from openubem.data.construction.national_records import ALLOWED_KEYS, build_records


ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "openubem" / "data" / "construction"
SPEC = DATA_DIR / "national_specs" / "za_spec.json"
TYPES = ("AB", "MFH", "SFH", "TH")
PERIODS = (("ZA.01", 0, 1950), ("ZA.02", 1951, 2011), ("ZA.03", 2012, 9999))
TABULA_PERIODS_ZA = ((0, 1950, "ZA.01"), (1951, 2011, "ZA.02"), (2012, 9999, "ZA.03"))


def _records(cc):
    return json.loads((DATA_DIR / f"tabula_archetypes_{cc.lower()}.json").read_text(encoding="utf-8"))["records"]


def _spec():
    return json.loads(SPEC.read_text(encoding="utf-8"))


def _share(record):
    g = record["geometry"]
    window = sum(g["a_window_components_m2"])
    wall = sum(g["a_wall_components_m2"])
    return window / (window + wall)


def test_record_count_and_ids():
    ids = {r["archetype_id"] for r in _records("ZA")}
    assert ids == {f"ZA.N.{t}.{p[0].split('.')[1]}.Gen.ReEx.001.001" for t in TYPES for p in PERIODS}


def test_key_set_equals_it():
    it_keys = set(_records("IT")[0])
    for record in _records("ZA"):
        assert set(record) == it_keys


def test_country_fold_and_attribution():
    for record in _records("ZA"):
        assert record["country_stock_code"] == "ZA"
        assert record["survey_fold"] == "za"
        assert "national sources per parameter_assumptions" in record["attribution"]
        assert any(a.startswith("ASSUMED:donor ES.ME.") for a in record["parameter_assumptions"])


def test_periods_tile_per_type():
    spec = _spec()
    spans = [(p["from"], p["to"]) for p in spec["periods"]]
    assert spans == [(a, b) for _, a, b in PERIODS]
    assert [p["code"] for p in spec["periods"]] == [c for c, _, _ in PERIODS]
    for (_, y1, y2), (_, z1, z2) in zip(PERIODS, PERIODS[1:]):
        assert z1 == y2 + 1
    assert PERIODS[0][1] == 0 and PERIODS[-1][2] == 9999
    assert tuple(TABULA_PERIODS_ZA) == tuple((a, b, c) for c, a, b in PERIODS)
    for t in TYPES:
        periods = sorted(r["construction_period"] for r in _records("ZA") if r["building_type"] == t)
        assert periods == [c for c, _, _ in PERIODS]


def test_u_values_do_not_increase_with_newer_period(capsys):
    by_type = {}
    for r in _records("ZA"):
        by_type.setdefault(r["building_type"], []).append(r)
    increases = []
    for t, items in by_type.items():
        items.sort(key=lambda r: r["construction_period"])
        for a, b in zip(items, items[1:]):
            for key in ("u_wall_w_m2k", "u_roof_w_m2k", "u_window_w_m2k"):
                if b[key] > a[key] + 1e-9:
                    increases.append((t, a["construction_period"], b["construction_period"], key, a[key], b[key]))
    print("U increases:", increases)
    assert increases == []


def test_window_share_in_range():
    for record in _records("ZA"):
        assert 0.05 <= _share(record) <= 0.55, (record["archetype_id"], _share(record))


def test_every_override_has_source_or_assumed():
    for entry in _spec()["entries"]:
        for key, item in entry["values"].items():
            assert key in ALLOWED_KEYS
            source = item["source"].strip()
            assert source
            assert source.startswith("ASSUMED:") or "NHBRC" in source or "SANS" in source


def test_regulated_values_are_sourced_not_assumed():
    for entry in _spec()["entries"]:
        if entry["period"] == "ZA.03":
            assert not entry["values"]["u_roof_w_m2k"]["source"].startswith("ASSUMED:")
            assert entry["values"]["u_roof_w_m2k"]["value"] == pytest.approx(1 / 3.7, abs=1e-4)
            assert not entry["values"]["u_wall_w_m2k"]["source"].startswith("ASSUMED:")


def test_overrides_land_in_records():
    by_id = {r["archetype_id"]: r for r in _records("ZA")}
    for entry in _spec()["entries"]:
        suffix = entry["period"].split(".")[1]
        record = by_id[f"ZA.N.{entry['building_type']}.{suffix}.Gen.ReEx.001.001"]
        assert record["u_wall_w_m2k"] == pytest.approx(entry["values"]["u_wall_w_m2k"]["value"], abs=1e-6)
        assert record["u_roof_w_m2k"] == pytest.approx(entry["values"]["u_roof_w_m2k"]["value"], abs=1e-6)
        assert record["u_window_w_m2k"] == pytest.approx(entry["values"]["u_window_w_m2k"]["value"], abs=1e-6)


def test_committed_records_equal_rebuild(tmp_path):
    out = build_records(SPEC, tmp_path / "tabula_archetypes_za.json")
    assert json.loads(out.read_text(encoding="utf-8")) == json.loads((DATA_DIR / "tabula_archetypes_za.json").read_text(encoding="utf-8"))


def test_print_table(capsys):
    rows = sorted(_records("ZA"), key=lambda r: (r["building_type"], r["construction_period"]))
    for r in rows:
        print(
            f"{r['building_type']:>3} {r['construction_period']} wall {r['u_wall_w_m2k']:.3f} roof {r['u_roof_w_m2k']:.3f} "
            f"window {r['u_window_w_m2k']:.2f} share {_share(r):.3f}"
        )
    assert len(rows) == 12
