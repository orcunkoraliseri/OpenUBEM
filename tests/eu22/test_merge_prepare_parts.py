from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
_spec = importlib.util.spec_from_file_location("merge_prepare_parts", ROOT / "scripts" / "eu22" / "merge_prepare_parts.py")
mp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mp)

EXCL_HEAD = "building_id,blocker\n"


def make_part(base, name, ids, excluded=(), census=None, weather=b"WX", extra_summary=None, prepared=None):
    part = base / name
    (part / "idfs").mkdir(parents=True)
    (part / "schedules").mkdir()
    (part / "weather").mkdir()
    for i in ids:
        (part / "idfs" / f"{i}.idf").write_text(f"idf {i}\n")
        (part / "schedules" / f"{i}.csv").write_text(f"sch {i}\n")
    (part / "weather" / "w.epw").write_bytes(weather)
    (part / "prepared_buildings.csv").write_text("building_id,x\n" + "".join(f"{i},1\n" for i in ids))
    (part / "x_manifest.csv").write_text("building_id,m\n" + "".join(f"{i},2\n" for i in ids))
    (part / "fleet.lst").write_text("".join(f"idfs/{i}.idf\n" for i in ids))
    (part / "excluded_buildings.csv").write_text(EXCL_HEAD + "".join(f"{b},{k}\n" for b, k in excluded))
    summary = {"district": "D", "population_prepared": len(ids), "blocker_exclusions": {}}
    if census is not None:
        summary["context_height_fallback_census"] = census
    summary.update(extra_summary or {})
    (part / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return part


def test_join_basic(tmp_path):
    p1 = make_part(tmp_path, "p1", ["b1", "b2"], excluded=[("e1", "k1"), ("e2", "k2")], census={"a": 1, "c": 2})
    p2 = make_part(tmp_path, "p2", ["b3"], excluded=[("e1", "k1"), ("e2", "k2"), ("e3", "k1")], census={"a": 3, "b": 4})
    out = tmp_path / "out"
    merged = mp.merge([p1, p2], out)
    assert merged["population_prepared"] == 3
    assert merged["context_height_fallback_census"] == {"a": 4, "b": 4, "c": 2}
    assert list(merged["context_height_fallback_census"]) == ["a", "b", "c"]
    assert merged["blocker_exclusions"] == {"k1": 2, "k2": 1}
    assert (out / "excluded_buildings.csv").read_text() == EXCL_HEAD + "e1,k1\ne2,k2\ne3,k1\n"
    assert (out / "prepared_buildings.csv").read_text() == "building_id,x\nb1,1\nb2,1\nb3,1\n"
    assert (out / "x_manifest.csv").read_text() == "building_id,m\nb1,2\nb2,2\nb3,2\n"
    assert (out / "fleet.lst").read_text() == "idfs/b1.idf\nidfs/b2.idf\nidfs/b3.idf\n"
    assert sorted(e.name for e in (out / "idfs").iterdir()) == ["b1.idf", "b2.idf", "b3.idf"]
    assert (out / "summary.json").read_text() == json.dumps(merged, indent=2, sort_keys=True) + "\n"


def test_duplicate_name_error(tmp_path):
    p1 = make_part(tmp_path, "p1", ["b1"])
    p2 = make_part(tmp_path, "p2", ["b1"])
    with pytest.raises(mp.MergeError, match="in two parts"):
        mp.merge([p1, p2], tmp_path / "out")


def test_weather_mismatch_error(tmp_path):
    p1 = make_part(tmp_path, "p1", ["b1"])
    p2 = make_part(tmp_path, "p2", ["b2"], weather=b"OTHER")
    with pytest.raises(mp.MergeError, match="weather differs"):
        mp.merge([p1, p2], tmp_path / "out")


def test_output_exists_error(tmp_path):
    p1 = make_part(tmp_path, "p1", ["b1"])
    (tmp_path / "out").mkdir()
    with pytest.raises(mp.MergeError, match="already exists"):
        mp.merge([p1], tmp_path / "out")


def test_summary_key_differs_error(tmp_path):
    p1 = make_part(tmp_path, "p1", ["b1"], extra_summary={"k": 1})
    p2 = make_part(tmp_path, "p2", ["b2"], extra_summary={"k": 2})
    with pytest.raises(mp.MergeError, match="key differs across parts: k"):
        mp.merge([p1, p2], tmp_path / "out")


def test_census_differing_is_summed_not_error(tmp_path):
    p1 = make_part(tmp_path, "p1", ["b1"], census={"z": 1})
    p2 = make_part(tmp_path, "p2", ["b2"], census={"y": 2, "z": 5})
    merged = mp.merge([p1, p2], tmp_path / "out")
    assert merged["context_height_fallback_census"] == {"y": 2, "z": 6}


def test_unexpected_file_error(tmp_path):
    p1 = make_part(tmp_path, "p1", ["b1"])
    (p1 / "stray.txt").write_text("x")
    with pytest.raises(mp.MergeError, match="stray.txt"):
        mp.merge([p1], tmp_path / "out")


def test_parts_untouched(tmp_path):
    p1 = make_part(tmp_path, "p1", ["b1"])
    p2 = make_part(tmp_path, "p2", ["b2"])
    before = {f.relative_to(tmp_path): f.read_bytes() for p in (p1, p2) for f in p.rglob("*") if f.is_file()}
    mp.merge([p1, p2], tmp_path / "out")
    after = {f.relative_to(tmp_path): f.read_bytes() for p in (p1, p2) for f in p.rglob("*") if f.is_file()}
    assert before == after
