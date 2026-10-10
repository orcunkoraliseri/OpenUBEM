from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import scripts.cluster.export_flat_counts_4j as flat
import scripts.cluster.harvest_eu11_district as hd
import scripts.cluster.harvest_eu11_merged as hm
import scripts.eu22.write_results_eu22 as wr

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "c07_madrid3"
SITE = "AT-VIE-RUDOLFSHEIM"
TAG = "win_2099-01-01"
STEMS = ["c0469f277749f93e", "c6e90803c98dba87", "a776387b1281ccea"]
EXPECTED_HEATING = {"c0469f277749f93e": 124317.93081, "c6e90803c98dba87": 123757.052872}
EXPECTED_EUI = {"c0469f277749f93e": 114.135776, "c6e90803c98dba87": 85.622905}


def _make_tree(root: Path, building_ids: list[str] | None = None) -> Path:
    tree = root / f"{SITE}_{TAG}"
    tree.mkdir(parents=True)
    for name in ("prepared_buildings.csv", "fleet.lst", "md5_2099-01-01.txt", "speed_jobs.txt", "summary.json", "left_out.csv"):
        shutil.copy2(FIXTURE / name, tree / name)
    shutil.copytree(FIXTURE / "idfs", tree / "idfs")
    if building_ids is not None:
        prepared = pd.read_csv(tree / "prepared_buildings.csv", dtype=str)
        prepared["building_id"] = building_ids
        prepared.to_csv(tree / "prepared_buildings.csv", index=False)
        left = pd.read_csv(tree / "left_out.csv", dtype=str)
        left["building_id"] = building_ids[2]
        left.to_csv(tree / "left_out.csv", index=False)
    return tree


def _harvest(monkeypatch, tmp_path: Path, out_src: Path, building_ids: list[str] | None = None):
    root = tmp_path / "EU-11"
    root.mkdir()
    tree = _make_tree(root, building_ids)
    monkeypatch.setattr(hd, "EVIDENCE_ROOT", root)
    monkeypatch.setattr(hd, "fetch_district_out", lambda district, work_base, tag=None: out_src)
    monkeypatch.setattr(hd, "fetch_sacct_elapsed", lambda job_id, with_state=False: (
        {i: (100 * i, "COMPLETED") for i in (1, 2, 3)} if with_state else {1: 100, 2: 200, 3: 300}))
    summary = hd.harvest_district(SITE, tmp_path / "work", TAG)
    return root, tree, summary


def test_new_sites_registered_and_four_site_tables_unchanged():
    assert len(hd.NEW_SITES) == 7
    assert sorted(hd.DISTRICT_JOBS) == [
        "ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2",
    ]
    assert hd._remote_fleet_dir(SITE, TAG) == f"/speed-scratch/o_iseri/fleets/EU22_{SITE}_{TAG}"
    assert hd._remote_fleet_dir("ES-MAD-BERRUGUETE", "win_2026-10-06") == (
        "/speed-scratch/o_iseri/fleets/EU11_ES-MAD-BERRUGUETE_win_2026-10-06"
    )


def test_harvest_fixture_gives_expected_manifest_rows(monkeypatch, tmp_path):
    root, tree, summary = _harvest(monkeypatch, tmp_path, FIXTURE / "out")
    manifest = pd.read_csv(tree / "at_vie_rudolfsheim_manifest.csv", dtype={"building_id": str})
    assert len(manifest) == 3
    assert sorted(manifest["dwellings_used"]) == [14, 18, 21]
    by_id = dict(zip(manifest["building_id"], manifest["heating_kwh"]))
    for stem, heating in EXPECTED_HEATING.items():
        bid = pd.read_csv(FIXTURE / "prepared_buildings.csv", dtype=str).set_index("stem").loc[stem, "building_id"]
        assert by_id[bid] == pytest.approx(heating, abs=1e-3)
    assert manifest["heating_kwh"].notna().all()
    assert (manifest["eplus_return_code"] == 0).all()
    assert summary["population_run"] == 3 and summary["population_success"] == 3
    assert summary["speed_job_id"] == [9999999]


def test_harvest_refuses_run_without_end_marker(monkeypatch, tmp_path):
    out = tmp_path / "out_copy"
    shutil.copytree(FIXTURE / "out", out)
    (out / STEMS[1] / "eplusout.end").write_text("EnergyPlus Terminated--Error(s) Detected.\n", encoding="utf-8")
    (out / STEMS[2] / "eplusout.end").unlink()
    root, tree, summary = _harvest(monkeypatch, tmp_path, out)
    manifest = pd.read_csv(tree / "at_vie_rudolfsheim_manifest.csv", dtype=str)
    ok = dict(zip(pd.read_csv(FIXTURE / "prepared_buildings.csv", dtype=str)["stem"], [True, False, False]))
    stem_of = dict(zip(pd.read_csv(FIXTURE / "prepared_buildings.csv", dtype=str)["building_id"], ok))
    assert {stem_of[b]: pd.notna(h) for b, h in zip(manifest["building_id"], manifest["heating_kwh"])} == ok
    assert summary["population_success"] == 1 and summary["population_failed_on_speed"] == 2


def test_four_site_parse_task_keeps_err_only_gate(tmp_path):
    out = tmp_path / "o"
    shutil.copytree(FIXTURE / "out" / STEMS[0], out)
    (out / "eplusout.end").unlink()
    assert pd.notna(hd.parse_task(out)["heating_kwh"])
    assert pd.isna(hd.parse_task(out, require_end=True)["heating_kwh"])


def test_new_site_needs_win_tag(monkeypatch, tmp_path):
    with pytest.raises(ValueError):
        hd.harvest_district(SITE, tmp_path, "fix_2026-10-01")
    with pytest.raises(ValueError):
        hd.harvest_district(SITE, tmp_path, None)


def test_write_results_drops_left_out_and_computes_eui(monkeypatch, tmp_path):
    root, tree, summary = _harvest(monkeypatch, tmp_path, FIXTURE / "out")
    result = wr.build_results(SITE, TAG, root)
    per_home = result["per_home"]
    assert len(per_home) == 3 - 1
    assert result["left_out_in_manifest"] == 1
    assert per_home["has_result"].all()
    for _, r in per_home.iterrows():
        assert r["eui_heating_kwh_m2"] == pytest.approx(r["heating_kwh"] / r["floor_area_m2"], abs=1e-6)
    prepared = pd.read_csv(FIXTURE / "prepared_buildings.csv", dtype=str).set_index("building_id")
    for _, r in per_home.iterrows():
        stem = prepared.loc[r["building_id"], "stem"]
        assert r["eui_heating_kwh_m2"] == pytest.approx(EXPECTED_EUI[stem], abs=1e-5)
    row = result["summary_row"]
    assert row["homes"] == 2 and row["homes_with_result"] == 2
    assert row["eui_heating_kwh_m2"] == pytest.approx(
        per_home["heating_kwh"].sum() / per_home["floor_area_m2"].sum(), abs=1e-5
    )
    paths = wr.write_results(result, tmp_path / "results")
    assert [p.name for p in paths] == [
        f"EU22_results_{SITE}_2099-01-01_per_home.csv",
        f"EU22_results_{SITE}_2099-01-01_per_home.json",
        f"EU22_results_{SITE}_2099-01-01_summary.csv",
        f"EU22_results_{SITE}_2099-01-01_summary.json",
    ]
    back = pd.read_csv(paths[0])
    live = pd.read_csv(REPO / "docs/docs_ACTIVE/europeanLocations/results/EU11_results_2026-10-08_per_home.csv")
    assert list(back.columns) == list(live.columns)
    assert len(json.loads(paths[1].read_text(encoding="utf-8"))) == 2
    summary_json = json.loads(paths[3].read_text(encoding="utf-8"))
    assert summary_json["districts"][SITE]["homes"] == 2
    assert summary_json["left_out_not_correctly_divided"] == 1
    assert list(pd.read_csv(paths[2]).columns) == list(
        pd.read_csv(REPO / "docs/docs_ACTIVE/europeanLocations/results/EU11_results_2026-10-08_summary.csv").columns
    )


def test_write_results_lists_failed_run_with_reason(monkeypatch, tmp_path):
    out = tmp_path / "out_copy"
    shutil.copytree(FIXTURE / "out", out)
    (out / STEMS[1] / "eplusout.end").write_text("EnergyPlus Terminated--Error(s) Detected.\n", encoding="utf-8")
    root, tree, summary = _harvest(monkeypatch, tmp_path, out)
    result = wr.build_results(SITE, TAG, root)
    per_home = result["per_home"]
    assert len(per_home) == 2 and int(per_home["has_result"].sum()) == 1
    assert len(result["failed"]) == 1 and result["failed"][0]["reason"].startswith("rc=")
    assert result["summary_row"]["homes_with_result"] == 1


def test_write_results_refuses_four_sites_and_missing_left_out(tmp_path):
    with pytest.raises(ValueError):
        wr.build_results("ES-MAD-BERRUGUETE", "win_2026-10-06", tmp_path)
    (tmp_path / f"{SITE}_{TAG}").mkdir()
    (tmp_path / f"{SITE}_{TAG}" / "at_vie_rudolfsheim_manifest.csv").write_text("building_id\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        wr.build_results(SITE, TAG, tmp_path)


def test_flat_counts_new_site_sum_equals_dwellings_of_divided_homes(monkeypatch, tmp_path):
    root, tree, summary = _harvest(monkeypatch, tmp_path, FIXTURE / "out")
    prepared = pd.read_csv(tree / "prepared_buildings.csv", dtype=str)
    pd.DataFrame({
        "building_id": prepared["building_id"],
        "old_count": prepared["dwellings_used"],
        "new_count": prepared["dwellings_used"],
        "dwellings_source": prepared["dwellings_source"],
    }).to_csv(tree / "dwelling_counts_2099-01-01.csv", index=False)
    b3d = tmp_path / "3D" / f"eu_{SITE}_data"
    b3d.mkdir(parents=True)
    rows = [{"building_id": b, "class": "residential"} for b in prepared["building_id"]]
    rows.append({"building_id": "way/999", "class": "excluded"})
    rows.append({"building_id": "way/998", "class": "residential"})
    pd.DataFrame(rows).to_csv(b3d / "buildings.csv", index=False)
    monkeypatch.setattr(hm, "EVIDENCE_ROOT", root)
    monkeypatch.setattr(flat, "BUILDINGS_ROOT", tmp_path / "3D")
    df = flat.build_flat_counts(SITE, TAG)
    assert df["status"].value_counts().to_dict() == {
        "simulated": 2, "undivided_excluded": 1, "not_residential": 1, "no_model": 1,
    }
    sim = df[df["status"] == "simulated"]
    assert sim["new_count"].astype(int).sum() == 18 + 14
    with pytest.raises(ValueError):
        flat.build_flat_counts(SITE, "fix_2026-10-01")


def test_four_site_flat_counts_still_reject_other_tags():
    with pytest.raises(ValueError):
        flat.build_flat_counts("ES-MAD-BERRUGUETE", flat.WIN5_TAG)
    with pytest.raises(ValueError):
        flat.build_flat_counts("GB-LDN-STDUNSTANS", "fix_2026-10-01")


def _vienna_ids(n: int) -> list[str]:
    import geopandas as gpd
    from scripts.run_eu_s2_district_campaign import _records, impute_from_neighbours
    from openubem.semantic.new_country_rules import new_country_rows

    gdf = gpd.read_file(REPO / "openubem/outputs/eu02" / SITE / "02_residential_manifest.gpkg")
    rows, _ = new_country_rows(SITE, gdf, _records("AT"))
    return [str(r["building_id"]) for r in rows[:n]]


def test_viewer_new_site_smoke_and_four_site_default(monkeypatch, tmp_path):
    import scripts.generate_eu_3d_viewers as gen

    ids = _vienna_ids(3)
    root, tree, summary = _harvest(monkeypatch, tmp_path, FIXTURE / "out", ids)
    result = wr.build_results(SITE, TAG, root)
    results_dir = tmp_path / "results"
    wr.write_results(result, results_dir)
    monkeypatch.setattr(gen, "EU11_ROOT", root)
    out3d, mirror = tmp_path / "3D", tmp_path / "mirror"
    gen.build_district(SITE, TAG, out3d, mirror, results_dir)
    viewer = out3d / f"eu_{SITE}_viewer.html"
    html = viewer.read_text(encoding="utf-8")
    i1 = html.find('<script type="application/json" id="scene">') + len('<script type="application/json" id="scene">')
    scene = json.loads(html[i1:html.find("</script>", i1)])
    by_id = {b["id"]: b for b in scene["buildings"]}
    sim = [b for b in scene["buildings"] if b.get("ss") == "simulated"]
    left = [b for b in scene["buildings"] if b.get("ud") == 1]
    assert scene["sim_counts"]["simulated"] == len(sim) == 2 == len(result["per_home"])
    assert scene["sim_counts"]["undivided"] == len(left) == 1
    assert left[0]["eui"] is None and all(b["eui"] is not None for b in sim)
    assert scene["licence"].startswith("CC BY 4.0")
    assert re.findall(r"eplus|severe|fatal|weather|epw|job.?id", html, re.IGNORECASE) == []
    assert (mirror / f"eu_{SITE}_viewer.html").read_bytes() == viewer.read_bytes()
    sources = json.loads((out3d / f"eu_{SITE}_data" / "sources.json").read_text(encoding="utf-8"))
    assert any(p.endswith("left_out.csv") for p in sources["generated_from"])
    assert (mirror / f"eu_{SITE}_data" / "buildings.csv").exists()
    assert gen.FOUR_SITES == (
        "ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2",
    )
    with pytest.raises(ValueError):
        gen.build_district(SITE, None, out3d, mirror, results_dir)


def test_sidecars_new_site_smoke(monkeypatch, tmp_path):
    import scripts.emit_eu11_layout_sidecars as em

    ids = _vienna_ids(3)
    root, tree, summary = _harvest(monkeypatch, tmp_path, FIXTURE / "out", ids)
    stats = em.emit_layouts_for_district(SITE, evidence_root=tree)
    assert stats["population_simulated"] == 3
    pop = pd.read_csv(tree / "sidecar_population.csv", dtype=str)
    assert len(pop) == 2
    files = list((tree / "layouts").rglob("*.json"))
    assert len(files) == 2
    first = json.loads(files[0].read_text(encoding="utf-8"))
    assert first["dwellings_total"] in (18, 14)
    manifest_before = pd.read_csv(tree / "at_vie_rudolfsheim_manifest.csv", dtype=str)
    assert "layout_json" not in manifest_before.columns
    assert em.FOUR_SITES == (
        "ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2",
    )
