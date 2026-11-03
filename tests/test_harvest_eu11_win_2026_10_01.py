import pandas as pd
import pytest

from scripts.cluster import harvest_eu11_district as hd
from scripts.cluster import harvest_eu11_merged as hm

DISTRICT = "FR-LYO-HAUTCOEURPENTES"
SLUG = "fr_lyo_hautcoeurpentes"
WIN = "win_2026-10-01"


def _base_row(bid, source="merged_2026-09-08_carry", eui="50"):
    row = {c: "x" for c in hm.MANIFEST_COLUMNS}
    row.update({"building_id": bid, "eui_kwh_m2": eui, "eui_source": source})
    return row


def _win_row(bid, rc=0, heat="1000", area="100"):
    row = {c: "w" for c in hm.MANIFEST_COLUMNS}
    row.update({"building_id": bid, "eplus_return_code": str(rc), "heating_kwh": heat,
                "floor_area_m2": area, "eui_kwh_m2": str(float(heat) / float(area))})
    return row


def _setup(tmp_path, monkeypatch, base_ids, win_ids, undivided, win_manifest=None, nowin=None):
    root = tmp_path
    monkeypatch.setattr(hm, "EVIDENCE_ROOT", root)
    (root / f"{DISTRICT}_merged_2026-09-08").mkdir()
    pd.DataFrame([_base_row(b) for b in base_ids]).to_csv(
        root / f"{DISTRICT}_merged_2026-09-08" / f"{SLUG}_manifest.csv", index=False)
    wd = root / f"{DISTRICT}_{WIN}"
    wd.mkdir()
    stems = [f"s_{b}" for b in win_ids]
    pd.DataFrame([
        {"building_id": b, "stem": f"s_{b}", "archetype_id": "A", "building_type": "AB", "age_band": "X",
         "geometry_outcome": "G", "idf_sha256": f"prep_{b}", "weather_sha256": "wx",
         "construction_period_provenance": "", "floor_area_m2": "100"}
        for b in win_ids
    ]).to_csv(wd / "prepared_buildings.csv", index=False)
    (wd / "fleet.lst").write_text("\n".join(stems) + "\n", encoding="utf-8")
    pd.DataFrame([
        {"stem": f"s_{b}", "building_id": b, "window_m2": str(10 + i), "outdoor_wall_m2": "100",
         "share_achieved": "0.1", "fallback": "False", "source_tree": "tree"}
        for i, b in enumerate(win_ids)
    ]).to_csv(wd / "windows.csv", index=False)
    if win_manifest is not None:
        pd.DataFrame(win_manifest).to_csv(wd / f"{SLUG}_manifest.csv", index=False)
    if nowin is not None:
        nd = root / f"{DISTRICT}_merged_2026-10-01"
        nd.mkdir()
        pd.DataFrame(nowin).to_csv(nd / f"{SLUG}_manifest.csv", index=False)
    monkeypatch.setattr(hm, "_undivided_ids", lambda d: set(undivided))
    return wd


def test_win_counts_toy_base(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, ["u", "a", "b", "c", "f"], ["a", "b", "c", "f"], ["u"],
           win_manifest=[_win_row("a"), _win_row("b"), _win_row("c"), _win_row("f", rc=1)])
    m, counts = hm.build_merged_manifest(DISTRICT, True, merged_tag=WIN)
    assert counts == {WIN: 3, "win_failed": 1}
    assert len(m) == 4
    assert len(m.attrs["excluded_undivided"]) == 1
    assert m.loc[m["building_id"] == "f", "eui_source"].iloc[0] == "win_failed"
    assert m.loc[m["building_id"] == "a", "eui_source"].iloc[0] == WIN


def test_failed_row_has_na_results(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, ["a", "f"], ["a", "f"], [], win_manifest=[_win_row("a")])
    m, counts = hm.build_merged_manifest(DISTRICT, True, merged_tag=WIN)
    f = m[m["building_id"] == "f"].iloc[0]
    assert counts == {WIN: 1, "win_failed": 1}
    assert f["eui_source"] == "win_failed"
    assert pd.isna(f["eui_kwh_m2"]) and pd.isna(f["heating_kwh"])
    assert f["idf_sha256"] == "prep_f"
    s = hm.build_summary(DISTRICT, m, counts)
    assert s["n_win_failed"] == 1 and s["win_failed_ids"] == ["f"]
    assert s["pooled_eui_kwh_m2"] == 10.0


def test_dry_no_manifest_all_failed(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, ["u", "a", "b"], ["a", "b"], ["u"])
    m, counts = hm.build_merged_manifest(DISTRICT, True, merged_tag=WIN)
    assert counts == {WIN: 0, "win_failed": 2}
    assert m["eui_kwh_m2"].isna().all()


def test_not_in_win_ids_raises(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, ["a", "orphan"], ["a"], [])
    with pytest.raises(ValueError):
        hm.build_merged_manifest(DISTRICT, True, merged_tag=WIN)


def test_windows_columns_joined_by_stem(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch, ["a", "b"], ["a", "b"], [], win_manifest=[_win_row("a"), _win_row("b")])
    m, _ = hm.build_merged_manifest(DISTRICT, True, merged_tag=WIN)
    by = m.set_index("building_id")
    assert by.loc["a", "window_m2"] == "10"
    assert by.loc["b", "window_m2"] == "11"
    assert by.loc["b", "source_tree"] == "tree"
    assert by.loc["a", "eui_0908"] == "50"
    assert by.loc["a", "eui_source_0908"] == "merged_2026-09-08_carry"


def test_eui_nowin_only_from_fix_rows(tmp_path, monkeypatch):
    nowin = [
        _base_row("a", source="fix_2026-10-01", eui="40"),
        _base_row("b", source="merged_2026-09-08_carry", eui="41"),
    ]
    _setup(tmp_path, monkeypatch, ["a", "b", "c"], ["a", "b", "c"], [],
           win_manifest=[_win_row("a"), _win_row("b"), _win_row("c")], nowin=nowin)
    m, _ = hm.build_merged_manifest(DISTRICT, True, merged_tag=WIN)
    by = m.set_index("building_id")
    assert float(by.loc["a", "eui_nowin"]) == 40.0
    assert pd.isna(by.loc["b", "eui_nowin"])
    assert pd.isna(by.loc["c", "eui_nowin"])


def _district_dir(tmp_path, monkeypatch):
    dist = tmp_path / f"{DISTRICT}_{WIN}"
    dist.mkdir()
    pd.DataFrame([{
        "building_id": "ba", "stem": "sa", "archetype_id": "A", "building_type": "AB", "age_band": "X",
        "geometry_outcome": "G", "idf_sha256": "p", "weather_sha256": "w", "construction_period_provenance": "",
        "floor_area_m2": "100",
    }]).to_csv(dist / "prepared_buildings.csv", index=False)
    (dist / "fleet.lst").write_text("sa\n", encoding="utf-8")
    monkeypatch.setattr(hd, "EVIDENCE_ROOT", tmp_path)
    monkeypatch.setattr(hd, "fetch_district_out", lambda d, w, t=None: tmp_path / "sim_out")
    seen = {}

    def fake(ids):
        seen["ids"] = ids
        return {}

    monkeypatch.setattr(hd, "_elapsed_for_jobs", fake)
    return dist, seen


def test_speed_jobs_file_is_read(tmp_path, monkeypatch):
    dist, seen = _district_dir(tmp_path, monkeypatch)
    (dist / "speed_jobs.txt").write_text("111\n222\n", encoding="utf-8")
    hd.harvest_district(DISTRICT, tmp_path, tag=WIN)
    assert seen["ids"] == [111, 222]


def test_missing_speed_jobs_raises(tmp_path, monkeypatch):
    _district_dir(tmp_path, monkeypatch)
    with pytest.raises(FileNotFoundError):
        hd.harvest_district(DISTRICT, tmp_path, tag=WIN)
