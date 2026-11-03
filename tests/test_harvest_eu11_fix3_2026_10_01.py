import hashlib

import pandas as pd
import pytest

from scripts.cluster import harvest_eu11_district as hd
from scripts.cluster import harvest_eu11_merged as hm

DISTRICT = "FR-LYO-HAUTCOEURPENTES"
TAG = "fix_2026-10-01"


def _prepared(rows):
    return pd.DataFrame(
        [
            {
                "building_id": bid, "stem": stem, "archetype_id": "A", "building_type": "AB",
                "age_band": "X", "geometry_outcome": "G", "idf_sha256": f"prep_{stem}",
                "weather_sha256": "w", "construction_period_provenance": "", "floor_area_m2": "100",
            }
            for bid, stem in rows
        ]
    )


def _setup_district(tmp_path, monkeypatch, stems, shipped, t06f_stems):
    root = tmp_path
    dist = root / f"{DISTRICT}_{TAG}"
    dist.mkdir(parents=True)
    _prepared([(f"b{s}", s) for s in stems]).to_csv(dist / "prepared_buildings.csv", index=False)
    (dist / "fleet.lst").write_text("\n".join(stems) + "\n", encoding="utf-8")
    if shipped is not None:
        (dist / "shipped_t06f.lst").write_text("\n".join(shipped) + "\n", encoding="utf-8")
    t06f_idfs = root / f"{DISTRICT}_{TAG}_t06f" / "idfs"
    t06f_idfs.mkdir(parents=True)
    for s in t06f_stems:
        (t06f_idfs / f"{s}.idf").write_bytes(f"idf-{s}".encode())
    monkeypatch.setattr(hd, "EVIDENCE_ROOT", root)
    monkeypatch.setattr(hd, "fetch_district_out", lambda d, w, t=None: tmp_path / "sim_out")
    monkeypatch.setattr(hd, "fetch_sacct_elapsed", lambda j, with_state=False: {})
    return dist


def test_list_of_jobs_elapsed_override(monkeypatch):
    data = {
        1: {1: (10, "COMPLETED"), 2: (20, "FAILED"), 3: (30, "COMPLETED")},
        2: {2: (99, "COMPLETED"), 3: (77, "FAILED"), 4: (5, "FAILED")},
    }
    monkeypatch.setattr(hd, "fetch_sacct_elapsed", lambda j, with_state=False: data[j])
    assert hd._elapsed_for_jobs([1, 2]) == {1: 10, 2: 99, 3: 30, 4: 5}


def test_sha_from_t06f_idf_for_listed_stem(tmp_path, monkeypatch):
    _setup_district(tmp_path, monkeypatch, ["s1", "s2"], ["s1"], ["s1"])
    hd.harvest_district(DISTRICT, tmp_path, tag=TAG)
    m = pd.read_csv(tmp_path / f"{DISTRICT}_{TAG}" / "fr_lyo_hautcoeurpentes_manifest.csv", dtype=str)
    by = m.set_index("building_id")
    assert by.loc["bs1", "idf_sha256"] == hashlib.sha256(b"idf-s1").hexdigest()
    assert by.loc["bs1", "idf_variant"] == "t06f"
    assert list(m.columns)[-1] == "idf_variant"


def test_unlisted_stem_keeps_prepared_sha(tmp_path, monkeypatch):
    _setup_district(tmp_path, monkeypatch, ["s1", "s2"], ["s1"], ["s1"])
    hd.harvest_district(DISTRICT, tmp_path, tag=TAG)
    m = pd.read_csv(tmp_path / f"{DISTRICT}_{TAG}" / "fr_lyo_hautcoeurpentes_manifest.csv", dtype=str)
    by = m.set_index("building_id")
    assert by.loc["bs2", "idf_sha256"] == "prep_s2"
    assert by.loc["bs2", "idf_variant"] == "fix"


def test_shipped_stem_not_in_fleet_raises(tmp_path, monkeypatch):
    _setup_district(tmp_path, monkeypatch, ["s1", "s2"], ["s1", "ghost"], ["s1", "ghost"])
    with pytest.raises(ValueError):
        hd.harvest_district(DISTRICT, tmp_path, tag=TAG)


def test_tagged_jobs_registered():
    assert hd.TAGGED_DISTRICT_JOBS[("ES-MAD-BERRUGUETE", TAG)] == [1405556, 1405952, 1406517]
    assert hd.TAGGED_DISTRICT_JOBS[("IT-BOL-GALVANI2", TAG)] == [1405559, 1406674]
    assert isinstance(hd.TAGGED_DISTRICT_JOBS[("FR-LYO-HAUTCOEURPENTES", "fix_2026-09-29")], int)


def test_fix3_branch_source_counts(tmp_path, monkeypatch):
    root = tmp_path
    base_dir = root / f"{DISTRICT}_merged_2026-09-08"
    base_dir.mkdir(parents=True)
    ids = ["b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8"]
    base = pd.DataFrame({c: "x" for c in hm.MANIFEST_COLUMNS}, index=range(8))
    base["building_id"] = ids
    base["eui_source"] = ["recut_2026-09-08"] * 3 + ["pending_resimulation"] + ["recut_2026-09-08"] * 2 + ["pending_resimulation"] * 2
    base.to_csv(base_dir / "fr_lyo_hautcoeurpentes_manifest.csv", index=False)

    fix_dir = root / f"{DISTRICT}_{TAG}"
    fix_dir.mkdir()
    _prepared([("b1", "s1"), ("b2", "s2"), ("b3", "s3"), ("b4", "s4"), ("b7", "s7"), ("b8", "s8")]).to_csv(
        fix_dir / "prepared_buildings.csv", index=False
    )
    (fix_dir / "fleet.lst").write_text("s1\ns2\ns7\ns8\n", encoding="utf-8")
    fix_manifest = pd.DataFrame({c: "y" for c in hm.MANIFEST_COLUMNS}, index=range(3))
    fix_manifest["building_id"] = ["b1", "b2", "b7"]
    fix_manifest["eplus_return_code"] = ["0", "1", "0"]
    fix_manifest["idf_variant"] = ["t06f", "fix", "t06f"]
    fix_manifest.to_csv(fix_dir / "fr_lyo_hautcoeurpentes_manifest.csv", index=False)

    csv_dir = root / "division_residual_2026-09-29"
    csv_dir.mkdir()
    pd.DataFrame({"district": [], "building_id": []}).to_csv(csv_dir / "undivided_excluded_2026-10-01.csv", index=False)
    monkeypatch.setattr(hm, "EVIDENCE_ROOT", root)
    manifest, counts = hm.build_merged_manifest(DISTRICT, True, merged_tag="2026-10-01")
    assert counts == {
        TAG: 2, "fix3_failed_carry": 1, "merged_2026-09-08_carry": 3, "pending_resimulation": 2,
    }
    assert len(manifest) == 8
    by = manifest.set_index("building_id")
    assert by.loc["b1", "idf_variant"] == "t06f"
    assert by.loc["b7", "eui_source"] == TAG
    assert by.loc["b8", "eui_source"] == "pending_resimulation"
    assert pd.isna(by.loc["b3", "idf_variant"])
    summary = hm.build_summary(DISTRICT, manifest, counts)
    assert summary["fix_failed_ids"] == ["b2"]
    assert summary["held_back_finding280"] == []


def test_t06g_listed_stem_takes_precedence_over_t06f_and_unknown_stem_raises(tmp_path, monkeypatch):
    dist = _setup_district(tmp_path, monkeypatch, ["s1", "s2", "s3"], ["s1", "s2"], ["s1", "s2"])
    g_idfs = tmp_path / f"{DISTRICT}_{TAG}_t06g" / "idfs"
    g_idfs.mkdir(parents=True)
    (g_idfs / "s1.idf").write_bytes(b"idf-g-s1")
    (dist / "shipped_t06g.lst").write_text("s1\n", encoding="utf-8")
    hd.harvest_district(DISTRICT, tmp_path, tag=TAG)
    by = pd.read_csv(dist / "fr_lyo_hautcoeurpentes_manifest.csv", dtype=str).set_index("building_id")
    assert by.loc["bs1", "idf_variant"] == "t06g"
    assert by.loc["bs1", "idf_sha256"] == hashlib.sha256(b"idf-g-s1").hexdigest()
    assert by.loc["bs2", "idf_variant"] == "t06f"
    assert by.loc["bs3", "idf_variant"] == "fix"
    (dist / "shipped_t06g.lst").write_text("s1\nghost\n", encoding="utf-8")
    with pytest.raises(ValueError):
        hd.harvest_district(DISTRICT, tmp_path, tag=TAG)


def test_undivided_homes_dropped_and_excluded(tmp_path, monkeypatch):
    root = tmp_path
    base_dir = root / f"{DISTRICT}_merged_2026-09-08"
    base_dir.mkdir(parents=True)
    ids = ["b1", "b2", "b3", "b4"]
    base = pd.DataFrame({c: "x" for c in hm.MANIFEST_COLUMNS}, index=range(4))
    base["building_id"] = ids
    base["eui_source"] = "recut_2026-09-08"
    base.to_csv(base_dir / "fr_lyo_hautcoeurpentes_manifest.csv", index=False)

    fix_dir = root / f"{DISTRICT}_{TAG}"
    fix_dir.mkdir()
    _prepared([("b1", "s1"), ("b2", "s2")]).to_csv(fix_dir / "prepared_buildings.csv", index=False)
    (fix_dir / "fleet.lst").write_text("s1\ns2\n", encoding="utf-8")
    fix_manifest = pd.DataFrame({c: "y" for c in hm.MANIFEST_COLUMNS}, index=range(2))
    fix_manifest["building_id"] = ["b1", "b2"]
    fix_manifest["eplus_return_code"] = ["0", "0"]
    fix_manifest["idf_variant"] = ["t06f", "fix"]
    fix_manifest.to_csv(fix_dir / "fr_lyo_hautcoeurpentes_manifest.csv", index=False)

    csv_dir = root / "division_residual_2026-09-29"
    csv_dir.mkdir()
    pd.DataFrame(
        {"district": [DISTRICT, DISTRICT, "ES-MAD-BERRUGUETE"], "building_id": ["b1", "b3", "b2"]}
    ).to_csv(csv_dir / "undivided_excluded_2026-10-01.csv", index=False)

    monkeypatch.setattr(hm, "EVIDENCE_ROOT", root)
    manifest, counts = hm.build_merged_manifest(DISTRICT, True, merged_tag="2026-10-01")
    assert sorted(manifest["building_id"]) == ["b2", "b4"]
    assert counts == {TAG: 1, "fix3_failed_carry": 0, "merged_2026-09-08_carry": 1, "pending_resimulation": 0}
    excluded = manifest.attrs["excluded_undivided"]
    assert sorted(excluded["building_id"]) == ["b1", "b3"]
    assert set(excluded["blocker"]) == {"UNDIVIDED_NOT_SIMULATED_D-EU-139"}
    assert hm.build_summary(DISTRICT, manifest, counts)["n_excluded_undivided"] == 2
