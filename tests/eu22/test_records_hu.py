from __future__ import annotations

import hashlib
import json
import re
import statistics
from pathlib import Path

import pytest


ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "openubem" / "data" / "construction"
FIXTURE = Path(__file__).parent / "fixtures" / "tabula_period_years_at_hu.json"
WORKBOOK = Path("C:/Users/o_iseri/Desktop/GSSCanada/GSSCanada-main/4J_docs_occ/Step8_docs/outputs_step8/raw/tabula-calculator.xlsx")
PINNED_MD5 = "c99ddc9ffcb6dc0ae7391273d9619e37"
CC = "HU"
EXPECTED_COUNT = 16
KNOWN_GAPS = {}


def _records(cc):
    return json.loads((DATA_DIR / f"tabula_archetypes_{cc.lower()}.json").read_text(encoding="utf-8"))["records"]


def _years():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))[CC]


def _token_years():
    table = {}
    for archetype_id, (_, klass, y1, y2) in _years().items():
        if ".ReEx." in archetype_id:
            table[klass] = (y1, y2)
    return table


def _span(archetype_id):
    _, klass, y1, y2 = _years()[archetype_id]
    match = re.search(r"\.(\d\d)-(\d\d)\.", archetype_id)
    if not match:
        return y1, y2
    table = _token_years()
    return table[f"{CC}.{match.group(1)}"][0], table[f"{CC}.{match.group(2)}"][1]


def test_record_count():
    assert len(_records(CC)) == EXPECTED_COUNT


def test_key_set_equals_it():
    it_keys = set(_records("IT")[0])
    for record in _records(CC):
        assert set(record) == it_keys


def test_ids_match_period_fixture():
    assert {r["archetype_id"] for r in _records(CC)} == set(_years())


def test_period_codes_have_one_year_range_each():
    ranges = {}
    for archetype_id, (_, klass, y1, y2) in _years().items():
        if ".ReEx." in archetype_id:
            ranges.setdefault(klass, set()).add((y1, y2))
    assert all(len(v) == 1 for v in ranges.values()), ranges


def test_periods_do_not_overlap_and_tile_where_complete():
    groups = {}
    for archetype_id in _years():
        if ".ReEx." not in archetype_id:
            continue
        series, btype = archetype_id.split(".")[1], archetype_id.split(".")[2]
        groups.setdefault((series, btype), []).append(_span(archetype_id))
    gaps = {}
    for key, spans in groups.items():
        spans.sort()
        for (a1, a2), (b1, b2) in zip(spans, spans[1:]):
            assert b1 > a2, (key, "overlap", (a1, a2), (b1, b2))
            if b1 != a2 + 1:
                gaps.setdefault(f"{key[0]}.{key[1]}", []).append((a2 + 1, b1 - 1))
    assert {k: [list(g) for g in v] for k, v in gaps.items()} == {k: [list(g) for g in v] for k, v in KNOWN_GAPS.items()}


def test_national_series_start_at_zero_and_end_open():
    national = {}
    for archetype_id in _years():
        if archetype_id.startswith(f"{CC}.N.") and ".ReEx." in archetype_id:
            national.setdefault(archetype_id.split(".")[2], []).append(_span(archetype_id))
    for btype, spans in national.items():
        spans.sort()
        if btype in ("MFH", "SFH"):
            assert spans[0][0] == 0 and spans[-1][1] == 9999, btype


def test_window_share_in_range(capsys):
    shares = []
    for record in _records(CC):
        g = record["geometry"]
        window = sum(g["a_window_components_m2"])
        wall = sum(g["a_wall_components_m2"])
        assert window > 0 and wall > 0, record["archetype_id"]
        share = window / (window + wall)
        assert 0.05 <= share <= 0.50, (record["archetype_id"], share)
        shares.append(share)
    print(f"{CC} window share min {min(shares):.4f} median {statistics.median(shares):.4f} max {max(shares):.4f} n {len(shares)}")


def test_records_carry_pinned_md5():
    assert {r["source_workbook_md5"] for r in _records(CC)} == {PINNED_MD5}
    assert {r["country_stock_code"] for r in _records(CC)} == {CC}


@pytest.mark.skipif(not WORKBOOK.exists(), reason="pinned workbook not on this machine")
def test_workbook_md5():
    assert hashlib.md5(WORKBOOK.read_bytes()).hexdigest() == PINNED_MD5
