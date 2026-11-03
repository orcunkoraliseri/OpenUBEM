import glob
import hashlib
import json
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import pytest
from shapely.geometry import Polygon, box

import openubem.geometry.european_nocore as E

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "openubem/outputs/eu_evidence/EU-11/rulebook_2026-09-30"
BENCH_GLOB = str(ROOT / "openubem/outputs/eu_evidence/EU-21/rules_tests/test_0[1-5]_nocore.json")
PRE_EDIT_BENCH_HASH = "b3f9f0a329456a903df2148ec8070d47ae91cf3b1e590df646085969092104aa"
DISTRICTS = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]


def _bench_plates():
    out = []
    for f in sorted(glob.glob(BENCH_GLOB)):
        for p in json.load(open(f, encoding="utf-8"))["plates"]:
            out.append((p["footprint"], p["drawn_per_floor"]))
    return out


def _plate_hash(args):
    footprint, k = args
    _, flats, _, verdict = E.cut_storey_nocore(Polygon(footprint[0], footprint[1:]), k)
    h = hashlib.sha256()
    h.update(verdict.encode())
    for w in sorted(f.wkb_hex for f in flats):
        h.update(w.encode())
    return h.hexdigest()


@pytest.mark.skip(reason="retired 2026-10-07: defaults now ruled values (CP-1); bench not re-run (owner: no full scans)")
def test_a_defaults_bench_hash_unchanged():
    plates = _bench_plates()
    assert len(plates) == 550
    assert E.NOCORE_RULESET == E.NOCORE_RULESET_DEFAULTS
    with Pool(8) as pool:
        hashes = pool.map(_plate_hash, plates, chunksize=5)
    assert hashlib.sha256("".join(hashes).encode()).hexdigest() == PRE_EDIT_BENCH_HASH


@pytest.mark.skip(reason="retired 2026-10-06: 09-08 fixture; superseded by T11 gate (a), PLAN_eu-rulebook-change-2026-09-30.md")
def test_b_defaults_prepare_hashes_equal_pre_edit_reference(tmp_path):
    ref = pd.read_csv(EVIDENCE / "t03_pre_edit_hashes.csv", dtype=str)
    assert len(ref) == 100
    procs = []
    for d in DISTRICTS:
        ids = tmp_path / f"ids_{d}.csv"
        ref[ref.district == d][["building_id"]].to_csv(ids, index=False)
        procs.append(subprocess.Popen(
            [sys.executable, str(ROOT / "scripts/run_eu_s2_district_campaign.py"), "--district", d,
             "--out", str(tmp_path / f"out_{d}"), "--only-ids", str(ids)],
            cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ))
    assert [p.wait() for p in procs] == [0, 0, 0, 0]
    same = 0
    for d in DISTRICTS:
        new = pd.read_csv(tmp_path / f"out_{d}/prepared_buildings.csv", dtype=str)[["building_id", "idf_sha256"]]
        m = ref[ref.district == d].merge(new, on="building_id", how="left", suffixes=("_ref", "_new"))
        same += int((m.idf_sha256_ref == m.idf_sha256_new).sum())
    assert same == 100


def test_c_relaxed_aspect_keeps_plate_that_passes_today():
    plate = box(0, 0, 30, 10)
    with E.nocore_ruleset(**E.NOCORE_RULESET_DEFAULTS):
        base = E.cut_storey_nocore(plate, 3)
    with E.nocore_ruleset(max_flat_aspect=3.0):
        relaxed = E.cut_storey_nocore(plate, 3)
    assert base[3] == "PASS"
    assert [f.wkb_hex for f in relaxed[1]] == [f.wkb_hex for f in base[1]]
    assert relaxed[3] == "PASS"


def test_d_relaxed_aspect_passes_plate_failing_only_c11():
    plate = box(0, 0, 42, 5)
    with E.nocore_ruleset(**E.NOCORE_RULESET_DEFAULTS):
        _, _, checks, verdict = E.cut_storey_nocore(plate, 3)
    assert verdict == "FAIL" and not checks["C11"]["pass"]
    with E.nocore_ruleset(max_flat_aspect=3.0):
        _, _, checks, verdict = E.cut_storey_nocore(plate, 3)
    assert verdict == "PASS" and checks["C11"]["pass"]
    assert E.NOCORE_RULESET == {"max_flat_aspect": E.MAX_FLAT_ASPECT, "min_spread": E.MIN_SPREAD, "flat_area_cap_m2": None}


DRIVER = ROOT / "scripts/analysis/eu_rulebook_dryrun_2026-09-30.py"
_RUNNER = (
    "import importlib.util, sys\n"
    "sp = importlib.util.spec_from_file_location('drv', sys.argv[1])\n"
    "m = importlib.util.module_from_spec(sp)\n"
    "sp.loader.exec_module(m)\n"
    "m.OUT = sys.argv[2]\n"
    "m._set_ref('1006')\n"
    "m.worker(sys.argv[3], 'GB-LDN-STDUNSTANS', sys.argv[4], sys.argv[5])\n"
)


def _driver():
    import importlib.util
    sp = importlib.util.spec_from_file_location("drv_test", DRIVER)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def test_e_s1_guard_keeps_ok_and_s1_homes_at_defaults(tmp_path):
    ids = tmp_path / "ids.csv"
    pd.DataFrame({"building_id": ["way/393505346", "way/328226230"]}).to_csv(ids, index=False)
    out_dir = tmp_path / "ev"
    out_dir.mkdir()
    pd.DataFrame({
        "district": ["GB-LDN-STDUNSTANS"] * 2,
        "building_id": ["way/393505346", "way/328226230"],
        "stem": ["", ""],
        "cls": ["OK", "S1_one_flat_per_floor_by_data"],
        "zones": ["0", "0"],
        "k_max": ["", ""],
    }).to_csv(out_dir / "baseline_1006.csv", index=False)
    for run in ("R0", "RALL_G"):
        r = subprocess.run([sys.executable, "-c", _RUNNER, str(DRIVER), str(out_dir) + "/", run, str(ids), str(tmp_path / f"o_{run}")],
                           cwd=ROOT, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr[-2000:]
    r0 = pd.read_csv(out_dir / "scratch/dryrun_1006/part_R0_GB-LDN-STDUNSTANS.csv", dtype=str).set_index("building_id")
    g = pd.read_csv(out_dir / "scratch/dryrun_1006/part_RALL_G_GB-LDN-STDUNSTANS.csv", dtype=str).set_index("building_id")
    assert len(r0) == 2 and len(g) == 2
    for bid in r0.index:
        assert r0.loc[bid, "idf_sha256"] == g.loc[bid, "idf_sha256"]


def _idf(zones):
    t = ""
    for name, w in zones:
        t += f"ZONE,\n    {name},    !- Name\n    0;    !- Direction of Relative North\n\n"
        x = [(0, 0), (w, 0), (w, 10), (0, 10)]
        t += "BUILDINGSURFACE:DETAILED,\n    f_" + name + ",    !- Name\n    Floor,    !- Surface Type\n    c,    !- Construction Name\n"
        t += f"    {name},    !- Zone Name\n    ,    !- Space Name\n    Ground,    !- Outside Boundary Condition\n    ,    !- Outside Boundary Condition Object\n"
        t += "    NoSun,    !- Sun Exposure\n    NoWind,    !- Wind Exposure\n    ,    !- View Factor to Ground\n    4,    !- Number of Vertices\n"
        for i, (a, b) in enumerate(x):
            t += f"    {a},    !- X\n    {b},    !- Y\n    0{';' if i == 3 else ','}    !- Z\n"
        t += "\n"
    return t


def test_f_moved_1006_reason_on_hand_made_pair(tmp_path):
    m = _driver()
    ref = tmp_path / "ref.idf"
    ref.write_text(_idf([("s_F0_dwelling_0", 5.0), ("s_F0_dwelling_1", 5.0)]))
    same = tmp_path / "same.idf"
    same.write_text(_idf([("s_F0_dwelling_0", 5.0), ("s_F0_dwelling_1", 5.0)]))
    bigger = tmp_path / "bigger.idf"
    bigger.write_text(_idf([("s_F0_dwelling_0", 5.03), ("s_F0_dwelling_1", 5.0)]))
    renamed = tmp_path / "renamed.idf"
    renamed.write_text(_idf([("s_F0_dwelling_0", 5.0), ("s_F0_dwelling_9", 5.0)]))
    zr = m._zone_map(str(ref))
    assert sorted(zr) == ["s_F0_dwelling_0", "s_F0_dwelling_1"]
    assert m._moved_1006_reason(m._zone_map(str(same)), zr) == ""
    assert m._moved_1006_reason(m._zone_map(str(bigger)), zr) == "zone_area"
    assert m._moved_1006_reason(m._zone_map(str(renamed)), zr) == "zone_names"


def _guard():
    import openubem.geometry.european_residential as R
    return R._nocore_cut_with_guard, R._nocore_cut_and_improve


def _flat_pairs(res):
    return [f.wkb_hex for f in res[1]], res[0].wkb_hex


def test_g_guard_default_ruleset_equals_default_cut():
    guard, cut = _guard()
    plate = box(0, 0, 22, 4)
    with E.nocore_ruleset(**E.NOCORE_RULESET_DEFAULTS):
        got = guard(plate, 2)
    exp = cut(plate, 2) + (2,)
    assert _flat_pairs(got) == _flat_pairs(exp)
    assert got[2] == exp[2] and got[3] == exp[3] and got[4] == exp[4]


def test_h_guard_relaxed_aspect_judges_kept_cut_by_relaxed_rules():
    guard, cut = _guard()
    plate = box(0, 0, 22, 4)
    base = cut(plate, 2)
    assert base[3] == "FAIL" and not base[2]["C11"]["pass"]
    assert all(base[2][c]["pass"] for c in base[2] if isinstance(base[2][c], dict) and c != "C11")
    with E.nocore_ruleset(max_flat_aspect=3.0):
        got = guard(plate, 2)
    assert _flat_pairs(got) == _flat_pairs(base)
    assert got[2]["C11"]["pass"] is True
    assert got[3] == "PASS"


def test_i_rescore_cut_default_matches_cut_own_checks():
    _, cut = _guard()
    plate = box(0, 0, 22, 4)
    base = cut(plate, 2)
    rec = E.rescore_cut(base[0], base[1], 2)
    flags = lambda ch: {c: ch[c]["pass"] for c in ch if isinstance(ch[c], dict) and "pass" in ch[c]}
    assert flags(rec["checks"]) == flags(base[2])
    assert rec["verdict"] == base[3]


def _dryrun_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("dryrun_t12c", str(ROOT / "scripts/analysis/eu_rulebook_dryrun_2026-09-30.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_j_home_cap_timer_interrupts_and_disarm_holds():
    import threading
    import time
    D = _dryrun_module()
    D.HOME_CAP_S = 1
    D._ORIG["timeouts"] = []
    t0 = time.time()
    D._arm(("r", "d", "s"), threading.get_ident())
    with pytest.raises(D.HomeTimeout):
        while time.time() - t0 < 10:
            sum(range(1000))
    assert time.time() - t0 < 3
    assert D._ORIG["timeouts"] == [("r", "d", "s")]
    D._arm(("r", "d", "s2"), threading.get_ident())
    D._disarm()
    t0 = time.time()
    while time.time() - t0 < 2:
        sum(range(1000))
    assert D._ORIG["timeouts"] == [("r", "d", "s")]


def test_k_relaxed_set_holds_madrid_stems_not_osm_ids(tmp_path):
    D = _dryrun_module()
    D._set_ref("1006")
    bl = pd.read_csv(EVIDENCE / "baseline_1006.csv", dtype=str)
    mad = bl[bl.district == "ES-MAD-BERRUGUETE"]
    ids = tmp_path / "ids.csv"
    mad[mad.cls == "V1_divided_shape_rule_broken"].head(1)[["building_id"]].to_csv(ids, index=False)
    try:
        D.worker("R1_30", "ES-MAD-BERRUGUETE", str(ids), str(tmp_path / "out"))
    except Exception:
        pass
    rel = D._ORIG["relaxed_ids"]
    want = mad[mad.cls.isin(D.UNRESOLVED)]
    assert len(rel) == len(want) == 86
    assert want.stem.iloc[0] in rel
    assert not any("/" in x for x in rel)

def _tail_plate():
    from shapely.ops import unary_union
    plate = box(0, 0, 20, 6)
    a = unary_union([box(0, 0, 10, 6), box(10, 2, 13, 3)])
    b = plate.difference(a)
    return plate, a, b


def test_l_repair_slivers_removes_cut_tail_keeps_coverage_and_count():
    plate, a, b = _tail_plate()
    assert E.pinch_area(a, plate) > 2.0
    out = E.repair_slivers(plate, [a, b])
    assert len(out) == 2
    assert all(E.pinch_area(f, plate) == 0.0 for f in out)
    assert abs(sum(f.area for f in out) - plate.area) < 1e-6
    assert abs(out[0].area - 60.0) < 1e-6 and abs(out[1].area - 60.0) < 1e-6


def test_m_repair_slivers_is_identity_without_sliver():
    plate = box(0, 0, 22, 8)
    flats = [box(0, 0, 11, 8), box(11, 0, 22, 8)]
    out = E.repair_slivers(plate, flats)
    assert [f.wkb_hex for f in out] == [f.wkb_hex for f in flats]
