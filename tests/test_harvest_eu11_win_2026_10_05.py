import hashlib

import pandas as pd
import pytest

from scripts.cluster import export_flat_counts_4j as ex
from scripts.cluster import harvest_eu11_district as hd
from scripts.cluster import harvest_eu11_merged as hm

DISTRICT = "GB-LDN-STDUNSTANS"
SLUG = "gb_ldn_stdunstans"
WIN5 = "win_2026-10-05"
DWELL = "ZONE,\n    {s}_F0_dwelling_0,    !- Name\n    0;\n"
PLAIN = "ZONE,\n    {s}_F0_zone,    !- Name\n    0;\n"


def _tree(tmp_path, monkeypatch, stems, fleet, plain=(), bad_md5=None):
    wd = tmp_path / f"{DISTRICT}_{WIN5}"
    (wd / "idfs").mkdir(parents=True)
    md5 = []
    for s in stems:
        data = (PLAIN if s in plain else DWELL).format(s=s).encode()
        (wd / "idfs" / f"{s}.idf").write_bytes(data)
        md5.append(f"{hashlib.md5(data).hexdigest()}  {s}.idf")
    if bad_md5:
        md5 = [ln.replace(ln.split()[0], "0" * 32) if bad_md5 in ln else ln for ln in md5]
    (wd / "md5_2026-10-05.txt").write_text("\n".join(md5) + "\n", encoding="utf-8")
    (wd / "fleet.lst").write_text("\n".join(fleet) + "\n", encoding="utf-8")
    pd.DataFrame([
        {"building_id": f"b_{s}", "stem": s, "archetype_id": "A", "building_type": "AB", "age_band": "X",
         "geometry_outcome": "G", "idf_sha256": "stale", "weather_sha256": "wx",
         "construction_period_provenance": "", "floor_area_m2": "100",
         "dwellings_used": "3", "dwellings_source": "observed"}
        for s in stems
    ]).to_csv(wd / "prepared_buildings.csv", index=False)
    (wd / "speed_jobs.txt").write_text("1410433 oom_resubmit_32G idx=5\n\n1410500\n", encoding="utf-8")
    monkeypatch.setattr(hd, "EVIDENCE_ROOT", tmp_path)
    monkeypatch.setattr(hm, "EVIDENCE_ROOT", tmp_path)
    monkeypatch.setattr(hd, "fetch_district_out", lambda d, w, t=None: tmp_path / "sim_out")
    seen = {}

    def fake(ids):
        seen["ids"] = ids
        return {1: 11, 2: 22, 3: 33}

    monkeypatch.setattr(hd, "_elapsed_for_jobs", fake)
    return wd, seen


def test_universe_is_idfs_not_fleet_lst(tmp_path, monkeypatch):
    wd, seen = _tree(tmp_path, monkeypatch, ["a", "b", "c", "d", "e"], ["a", "b", "c"])
    hd.harvest_district(DISTRICT, tmp_path, tag=WIN5)
    m = pd.read_csv(wd / f"{SLUG}_manifest.csv", dtype=str).set_index("building_id")
    assert len(m) == 5
    assert m.loc["b_a", "run_seconds"] == "11"
    assert pd.isna(m.loc["b_d", "run_seconds"])
    assert m.loc["b_a", "idf_sha256"] == hashlib.sha256((wd / "idfs" / "a.idf").read_bytes()).hexdigest()
    assert m.loc["b_a", "dwellings_used"] == "3" and m.loc["b_a", "dwellings_source"] == "observed"


def test_speed_jobs_first_token_only(tmp_path, monkeypatch):
    _, seen = _tree(tmp_path, monkeypatch, ["a", "b", "c", "d", "e"], ["a", "b", "c"])
    hd.harvest_district(DISTRICT, tmp_path, tag=WIN5)
    assert seen["ids"] == [1410433, 1410500]


def test_md5_mismatch_raises(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch, ["a", "b", "c"], ["a", "b", "c"], bad_md5="b.idf")
    with pytest.raises(ValueError, match="md5 mismatch"):
        hd.harvest_district(DISTRICT, tmp_path, tag=WIN5)


def test_stem_without_dwelling_zone_listed(tmp_path, monkeypatch):
    wd, _ = _tree(tmp_path, monkeypatch, ["a", "b", "c"], ["a", "b", "c"], plain=("b",))
    assert hm._stems_without_dwelling_zone(wd / "idfs") == ["b"]
    old = tmp_path / "division_residual_2026-09-29"
    old.mkdir()
    pd.DataFrame([{"district": DISTRICT, "building_id": "b_old", "stem": "old", "geometry_outcome": "G",
                   "storeys": "2", "gross_area_m2": "10", "fleet_index": ""}]).to_csv(
        old / "undivided_excluded_2026-10-01.csv", index=False)
    df = hm.build_undivided_win5(DISTRICT)
    assert sorted(df["building_id"]) == ["b_b", "b_old"]
    assert list(df.columns) == hm.UNDIVIDED_CSV_COLUMNS


def test_export_maps_five_statuses(tmp_path, monkeypatch):
    wd = tmp_path / f"{DISTRICT}_{WIN5}"
    wd.mkdir()
    pd.DataFrame([
        {"building_id": b, "old_count": "1", "new_count": "2", "dwellings_source": "observed"}
        for b in ["s", "f", "u"]
    ]).to_csv(wd / "dwelling_counts_2026-10-05.csv", index=False)
    md = tmp_path / f"{DISTRICT}_merged_{WIN5}"
    md.mkdir()
    pd.DataFrame([{"building_id": "s", "eui_source": WIN5}, {"building_id": "f", "eui_source": "win_failed"}]
                 ).to_csv(md / f"{SLUG}_manifest.csv", index=False)
    div = tmp_path / "division_residual_2026-09-29"
    div.mkdir()
    pd.DataFrame([{"district": DISTRICT, "building_id": "u"}]).to_csv(
        div / "undivided_excluded_2026-10-05.csv", index=False)
    bd = tmp_path / "3D" / f"eu_{DISTRICT}_data"
    bd.mkdir(parents=True)
    pd.DataFrame([{"building_id": b, "class": c} for b, c in
                  [("s", "residential"), ("f", "residential"), ("u", "residential"),
                   ("n", "excluded"), ("m", "residential")]]).to_csv(bd / "buildings.csv", index=False)
    monkeypatch.setattr(hm, "EVIDENCE_ROOT", tmp_path)
    monkeypatch.setattr(ex, "BUILDINGS_ROOT", tmp_path / "3D")
    df = ex.build_flat_counts(DISTRICT).set_index("building_id")
    assert df["status"].to_dict() == {
        "s": "simulated", "f": "run_failed", "u": "undivided_excluded",
        "n": "not_residential", "m": "no_model",
    }
    assert df.loc["s", "new_count"] == "2"
    assert df.loc["n", "old_count"] == "" or pd.isna(df.loc["n", "old_count"])


def test_export_refuses_es_and_fr():
    for d in ("ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES"):
        with pytest.raises(ValueError):
            ex.build_flat_counts(d)


def test_win6_tag_reads_its_own_md5_and_exports(tmp_path, monkeypatch):
    wd, _ = _tree(tmp_path, monkeypatch, ["a", "b"], ["a", "b"])
    wd6 = tmp_path / f"{DISTRICT}_win_2026-10-06"
    wd.rename(wd6)
    (wd6 / "md5_2026-10-05.txt").rename(wd6 / "md5_2026-10-06.txt")
    hd.harvest_district(DISTRICT, tmp_path, tag="win_2026-10-06")
    m = pd.read_csv(wd6 / f"{SLUG}_manifest.csv", dtype=str)
    assert len(m) == 2 and "dwellings_used" in m.columns
    assert hm.WIN6_TAG in hm.WIN_TAGS and ex.WIN6_TAG == "win_2026-10-06"
    with pytest.raises(ValueError):
        ex.build_flat_counts(DISTRICT, "win_2026-10-01")


def test_win6_drops_geometry_fault_stem_with_reason(tmp_path, monkeypatch):
    wd, _ = _tree(tmp_path, monkeypatch, ["a", "b", "c"], ["a", "b", "c"])
    wd6 = tmp_path / f"{DISTRICT}_win_2026-10-06"
    wd.rename(wd6)
    pd.DataFrame([{"stem": s} for s in "abc"]).to_csv(wd6 / "windows.csv", index=False)
    ev = tmp_path / "division_residual_2026-09-29"
    ev.mkdir()
    pd.DataFrame(columns=hm.UNDIVIDED_CSV_COLUMNS).to_csv(ev / "undivided_excluded_2026-10-05.csv", index=False)
    pd.DataFrame([{"district": DISTRICT, "building_id": "b_b", "stem": "b",
                   "reason": hm.GEOMETRY_FAULT_REASON}]).to_csv(
        ev / "geometry_fault_excluded_2026-10-06.csv", index=False)
    base = pd.DataFrame({"building_id": ["b_a", "b_b", "b_c"]})
    monkeypatch.setattr(hm, "_load_manifest", lambda d, t: base if t == hm.BASE_MERGED_TAG else None)
    manifest, counts = hm.build_merged_manifest(DISTRICT, True, merged_tag="win_2026-10-06")
    assert sorted(manifest["building_id"]) == ["b_a", "b_c"]
    exc = manifest.attrs["excluded_undivided"]
    assert exc["building_id"].tolist() == ["b_b"] and exc["blocker"].tolist() == ["GEOMETRY_FAULT_FINDING_291"]
    assert hm.GEOMETRY_FAULT_REASON == "GEOMETRY_FAULT_FINDING_291"
    summary = hm.build_summary(DISTRICT, manifest, counts)
    assert summary["n_excluded_geometry_fault"] == 1
    assert summary["n_excluded_undivided"] == 0
