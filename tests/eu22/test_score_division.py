from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import Polygon

from scripts.eu22 import score_division as sd

ROOT = Path(__file__).resolve().parents[2]
FIX = Path(__file__).parent / "fixtures" / "c05_madrid2"
SITE = "ES-MAD-BERRUGUETE"
TREE_1006 = SITE + "_win_2026-10-06"
BASELINE = ROOT / "openubem/outputs/eu_evidence/EU-11/rulebook_2026-09-30/baseline_1006.csv"
DRIFT = ROOT / "openubem/outputs/eu_evidence/EU-11/rulebook_2026-09-30/drift_1006.csv"


def _fixture_tree(tmp_path):
    root = tmp_path / "ev"
    tdir = root / (SITE + "_win_2099-01-01")
    shutil.copytree(FIX / "idfs", tdir / "idfs")
    shutil.copy2(FIX / "prepared_buildings.csv", tdir / "prepared_buildings.csv")
    return root, tdir.name


def test_fixture_homes_get_the_baseline_class_and_files_are_written(tmp_path):
    root, tree = _fixture_tree(tmp_path)
    out = sd.score(SITE, tree, 1, root, tmp_path / "o", "defaults")
    got = pd.read_csv(tmp_path / "o" / "division_classes.csv", dtype=str).set_index("building_id")
    base = pd.read_csv(BASELINE, dtype=str).set_index("building_id")
    assert list(pd.read_csv(tmp_path / "o" / "division_classes.csv").columns) == sd.COLUMNS
    assert set(got.class_source) == {"IDF_ONLY"}
    assert out["homes"] == 2
    for bid in got.index:
        assert got.loc[bid, "cls"] == base.loc[bid, "cls"]
    left = pd.read_csv(tmp_path / "o" / "left_out.csv", dtype=str)
    assert set(left.cls).isdisjoint(sd.KEEP_CLASSES)
    assert len(left) == int((~got.cls.isin(sd.KEEP_CLASSES)).sum())


def test_scorer_leaves_the_tree_alone(tmp_path):
    root, tree = _fixture_tree(tmp_path)
    tdir = root / tree
    before = sorted(p.name for p in tdir.rglob("*"))
    sd.score(SITE, tree, 1, root, tmp_path / "o", "final")
    assert sorted(p.name for p in tdir.rglob("*")) == before


def test_final_ruleset_is_the_frozen_value_and_defaults_are_the_old_one():
    assert sd._rules("final") == {"max_flat_aspect": 5.0, "min_spread": 0.25, "flat_area_cap_m2": None}
    assert sd._rules("defaults") == {"max_flat_aspect": 2.5, "min_spread": 0.5, "flat_area_cap_m2": None}
    sd._rules("final")


def test_spike_remover_drops_a_zero_width_tooth_and_keeps_corners():
    ring = [(0, 0), (10, 0), (10, 5), (5, 5), (5.002, 8), (5, 5), (0, 5), (0, 0)]
    kept = sd._drop_spikes(ring)
    assert (5.002, 8) not in kept
    assert {(0, 0), (10, 0), (10, 5), (0, 5)} <= set(kept)
    assert Polygon(kept).area == pytest.approx(50.0)


def test_raw_polygon_of_one_surface_is_not_cleaned():
    tooth = Polygon([(0, 0), (6, 0), (6, 4), (1.2, 0.4), (0, 4)])
    assert len(sd._raw_polygon([tooth]).exterior.coords) == len(tooth.exterior.coords)


FIX33 = Path(__file__).parent / "fixtures" / "c06b_madrid33"


def _tree33(tmp_path):
    root = tmp_path / "ev"
    tdir = root / (SITE + "_dw_2099-01-01")
    (tdir / "idfs").mkdir(parents=True)
    shutil.copytree(FIX33 / "layouts", tdir / "layouts")
    shutil.copy2(FIX33 / "prepared_buildings.csv", tdir / "prepared_buildings.csv")
    return root, tdir.name


def test_33_madrid_homes_from_layout_sidecars_equal_baseline(tmp_path):
    root, tree = _tree33(tmp_path)
    out = sd.score(SITE, tree, 4, root, tmp_path / "o", "defaults", layout_tree=tree)
    got = pd.read_csv(tmp_path / "o" / "division_classes.csv", dtype=str)
    base = pd.read_csv(BASELINE, dtype=str)
    base = base[base.district == SITE]
    m = got.merge(base, on="building_id", suffixes=("", "_b"))
    assert len(m) == out["homes"] == 33
    assert out["idf_fallback"] == 0
    assert set(got.class_source) == {"LAYOUT_SIDECAR"}
    bad = m[m.cls != m.cls_b]
    assert bad.empty, list(bad.building_id)


def test_missing_sidecar_falls_back_to_idf_and_is_counted(tmp_path):
    root, tree = _fixture_tree(tmp_path)
    (root / "empty").mkdir()
    out = sd.score(SITE, tree, 1, root, tmp_path / "o", "defaults", layout_tree="empty")
    got = pd.read_csv(tmp_path / "o" / "division_classes.csv", dtype=str)
    assert out["idf_fallback"] == out["homes"] == 2
    assert set(got.class_source) == {"IDF_FALLBACK"}
    base = pd.read_csv(BASELINE, dtype=str).set_index("building_id")
    for _, r in got.iterrows():
        assert r.cls == base.loc[r.building_id, "cls"]


def test_columns_are_the_baseline_columns_plus_class_source():
    assert sd.COLUMNS[:22] == list(pd.read_csv(BASELINE, nrows=0).columns)
    assert sd.COLUMNS[22:] == ["class_source"]


EV11 = ROOT / "openubem/outputs/eu_evidence/EU-11"
VIE = "AT-VIE-RUDOLFSHEIM"
ZA = "ZA-CPT-WOODSTOCK"


def _tag_only_vienna_ids():
    d = pd.read_csv(EV11 / "vienna_division_2026-10-09" / "t02_dryrun.csv")
    return set(d[d["note"].fillna("") == "no_failing_floor_tag_only"]["building_id"])


@pytest.mark.slow
@pytest.mark.parametrize("site", [ZA, VIE])
def test_floors_decide_off_is_byte_identical_to_the_2026_10_09_scores(site, tmp_path):
    tree, layouts = f"{site}_win_2026-10-09", f"{site}_dw_2026-10-09"
    sd.score(site, tree, 2, EV11, tmp_path / "o", "final", layout_tree=layouts)
    for name in ("division_classes.csv", "left_out.csv"):
        assert (tmp_path / "o" / name).read_bytes() == (EV11 / tree / name).read_bytes()


@pytest.mark.slow
def test_floors_decide_on_moves_exactly_the_11_tag_only_vienna_homes(tmp_path):
    tree, layouts = f"{VIE}_win_2026-10-09", f"{VIE}_dw_2026-10-09"
    sd.score(VIE, tree, 2, EV11, tmp_path / "o", "final", layout_tree=layouts, floors_decide=True)
    off = pd.read_csv(EV11 / tree / "division_classes.csv", dtype=str).fillna("").set_index("building_id")
    on = pd.read_csv(tmp_path / "o" / "division_classes.csv", dtype=str).fillna("").set_index("building_id")
    moved = set(off.index[off["cls"] != on["cls"].reindex(off.index)])
    assert moved == _tag_only_vienna_ids() and len(moved) == 11
    assert set(on.loc[list(moved), "cls"]) <= {"OK", "V3_divided_wrapped_flat"}
    rest = off.drop(index=list(moved))
    assert rest.equals(on.loc[rest.index])


def test_floors_decide_flag_reaches_divided_result(monkeypatch):
    seen = []
    monkeypatch.setattr(sd, "_divided_result", lambda spans, storeys, rules, best_effort=None: seen.append(best_effort) or {"cls": "OK"})
    monkeypatch.setattr(sd, "_sidecar_storeys", lambda j: ([1], [[Polygon([(0, 0), (1, 0), (1, 1)])]]))
    j = {"geometry_outcome": "DWELLING_LAYOUT_EMITTED_BEST_EFFORT"}
    sd._sidecar_home({}, j, {}, {"min_spread": 0.25})
    sd._sidecar_home({}, j, {}, {"min_spread": 0.25}, floors_decide=True)
    assert seen == [True, None]
