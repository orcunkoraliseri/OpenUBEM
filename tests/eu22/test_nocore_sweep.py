from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
EV = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
FIX = EV / "division_fix_2026-10-10"
SEED = 20261010
SITES = ["FI-HEL-KALLIO", "AT-VIE-RUDOLFSHEIM", "HU-BUD-ERZSEBETVAROS"]
SWITCHES = ("OPENUBEM_NOCORE_SWEEP", "OPENUBEM_NOCORE_SWEEP_S", "OPENUBEM_NOCORE_KMINUS1")

import scripts.run_eu_s2_district_campaign as camp  # noqa: E402
import openubem.geometry.european_nocore as E  # noqa: E402


def _env(**extra):
    env = {k: v for k, v in os.environ.items() if k not in SWITCHES}
    env.update(extra)
    return env


def _scratch():
    base = FIX / "scratch"
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(dir=base))


def _prepare_and_emit(site, ids, out, env):
    ids_csv = out / "ids.csv"
    pd.DataFrame({"building_id": ids}).to_csv(ids_csv, index=False)
    tree = out / "tree"
    r = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", str(ROOT / "scripts" / "run_eu_s2_district_campaign.py"), "--district", site, "--only-ids", str(ids_csv), "--out", str(tree)],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr[-400:]
    r = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-m", "scripts.emit_eu11_layout_sidecars", "--district", site,
         "--evidence-root", f"{site}={tree}", "--population-manifest", f"{site}={tree / 'prepared_buildings.csv'}"],
        cwd=ROOT, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr[-400:]
    return tree


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@pytest.mark.slow
@pytest.mark.parametrize("site", SITES)
def test_switches_off_idf_and_sidecar_identical_to_2026_10_09(site):
    dw = EV / f"{site}_dw_2026-10-09"
    classes = pd.read_csv(EV / f"{site}_win_2026-10-09" / "division_classes.csv", dtype=str)
    ids = sorted(classes[(classes["cls"] == "OK") & ~classes["building_id"].str.contains("_part")]["building_id"])
    pick = random.Random(SEED).sample(ids, 20)
    out = _scratch()
    try:
        tree = _prepare_and_emit(site, pick, out, _env())
        new = pd.read_csv(tree / "prepared_buildings.csv", dtype=str).set_index("building_id")
        old = pd.read_csv(dw / "prepared_buildings.csv", dtype=str).set_index("building_id")
        assert len(new) == 20
        assert "dwellings_removed" not in new.columns
        assert (new["idf_sha256"] == old["idf_sha256"].reindex(new.index)).all()
        for stem in new["stem"]:
            assert _sha(tree / "idfs" / f"{stem}.idf") == _sha(dw / "idfs" / f"{stem}.idf")
        for bid in pick:
            assert _sha(tree / "layouts" / f"{bid}.json") == _sha(dw / "layouts" / f"{bid}.json")
    finally:
        shutil.rmtree(out, ignore_errors=True)


def _fastest_recovered_vienna(n):
    d = pd.read_csv(EV / "vienna_division_2026-10-09" / "t02_dryrun.csv")
    d = d[(d["lever"] == "L1") & (d["recovered"] == 1) & (d["floors_changed"] > 0)].sort_values("seconds")
    return list(d["building_id"].head(n))


def _class_of_one(site, bid, rules, sd, env):
    out = _scratch()
    try:
        tree = _prepare_and_emit(site, [bid], out, env)
        j = json.loads((tree / "layouts" / f"{bid}.json").read_text(encoding="utf-8"))
        return sd._sidecar_home({}, j, {}, rules)["cls"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


@pytest.mark.slow
def test_sweep_on_five_vienna_homes_score_ok_or_v3():
    from concurrent.futures import ThreadPoolExecutor

    site = "AT-VIE-RUDOLFSHEIM"
    pick = _fastest_recovered_vienna(5)
    spec = importlib.util.spec_from_file_location("score_division", ROOT / "scripts" / "eu22" / "score_division.py")
    sd = importlib.util.module_from_spec(spec)
    sys.modules["score_division"] = sd
    spec.loader.exec_module(sd)
    rules = sd._rules("final")
    env = _env(OPENUBEM_NOCORE_SWEEP="1", OPENUBEM_NOCORE_SWEEP_S="600")
    with ThreadPoolExecutor(max_workers=5) as pool:
        got = list(pool.map(lambda b: _class_of_one(site, b, rules, sd, env), pick))
    classes = dict(zip(pick, got))
    good = [b for b, c in classes.items() if c in ("OK", "V3_divided_wrapped_flat")]
    print(classes)
    assert len(good) >= 4, classes


def test_sweep_pass_is_inert_with_switch_off(monkeypatch):
    monkeypatch.delenv("OPENUBEM_NOCORE_SWEEP", raising=False)
    poly = box(0, 0, 30, 12)
    flats = [box(0, 0, 10, 12), box(10, 0, 30, 12)]
    base = E._score_cut(poly, flats, 2)
    out_flats, out_base = E._sweep_pass(poly, flats, 2, base)
    assert out_flats is flats and out_base is base


def test_sweep_pass_zero_budget_keeps_todays_result(monkeypatch):
    monkeypatch.setenv("OPENUBEM_NOCORE_SWEEP", "1")
    monkeypatch.setenv("OPENUBEM_NOCORE_SWEEP_S", "0")
    poly = box(0, 0, 60, 4)
    flats = [box(0, 0, 3, 4), box(3, 0, 60, 4)]
    base = E._score_cut(poly, flats, 2)
    assert not all(base["checks"][c]["pass"] for c in E._GATED_CHECKS + ("C12",))
    out_flats, out_base = E._sweep_pass(poly, flats, 2, base)
    assert out_flats is flats and out_base is base


@dataclass(frozen=True)
class _Fa:
    storey_index: int
    dwelling_count: int


@dataclass
class _Alloc:
    floor_allocations: tuple


@dataclass
class _Layout:
    dwelling_layout_emitted: bool = True
    fallback_reason: str | None = None
    fallback_reason_by_storey: tuple = ()


def _patch(monkeypatch, bad_counts):
    calls = []

    def storey(footprint, *, dwelling_count, **kw):
        calls.append(dwelling_count)
        if dwelling_count in bad_counts:
            return _Layout(True, "NOCORE_BEST_EFFORT_C6")
        return _Layout(True, None)

    def building(footprint, *, floor_allocations, **kw):
        reasons = tuple("NOCORE_BEST_EFFORT_C6" if fa.dwelling_count in bad_counts else None for fa in floor_allocations)
        return _Layout(True, None, reasons)

    monkeypatch.setattr(camp, "generate_european_nocore_storey_layout", storey)
    monkeypatch.setattr(camp, "generate_european_building_dwelling_layout", building)
    monkeypatch.setattr(camp, "replace", lambda fa, **kw: _Fa(fa.storey_index, kw["dwelling_count"]))
    return calls


def test_kminus1_refuses_on_observed_count(monkeypatch):
    monkeypatch.setenv("OPENUBEM_NOCORE_KMINUS1", "1")
    calls = _patch(monkeypatch, bad_counts={8})
    alloc = _Alloc((_Fa(0, 8), _Fa(1, 8)))
    for source in ("observed", "observed_split", "single", "archetype_default"):
        layout, removed = camp._layout_with_kminus1(box(0, 0, 1, 1), alloc, source)
        assert removed == 0 and layout.fallback_reason_by_storey == ("NOCORE_BEST_EFFORT_C6",) * 2
    assert calls == []


def test_kminus1_off_by_default(monkeypatch):
    monkeypatch.delenv("OPENUBEM_NOCORE_KMINUS1", raising=False)
    calls = _patch(monkeypatch, bad_counts={8})
    layout, removed = camp._layout_with_kminus1(box(0, 0, 1, 1), _Alloc((_Fa(0, 8),)), "area_imputed")
    assert removed == 0 and calls == []


def test_kminus1_removes_one_flat_per_failing_floor_when_imputed(monkeypatch):
    monkeypatch.setenv("OPENUBEM_NOCORE_KMINUS1", "1")
    calls = _patch(monkeypatch, bad_counts={8})
    alloc = _Alloc((_Fa(0, 8), _Fa(1, 8), _Fa(2, 6)))
    layout, removed = camp._layout_with_kminus1(box(0, 0, 1, 1), alloc, "area_imputed")
    assert removed == 2
    assert not any(layout.fallback_reason_by_storey)
    assert sorted(set(calls)) == [6, 7, 8]


def test_kminus1_keeps_floor_when_one_less_also_fails(monkeypatch):
    monkeypatch.setenv("OPENUBEM_NOCORE_KMINUS1", "1")
    _patch(monkeypatch, bad_counts={8, 7})
    layout, removed = camp._layout_with_kminus1(box(0, 0, 1, 1), _Alloc((_Fa(0, 8),)), "area_imputed")
    assert removed == 0
