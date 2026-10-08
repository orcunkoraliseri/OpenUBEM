from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("eu_model_integrity", ROOT / "scripts" / "eu21" / "13_model_integrity.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)

W = 10.0
H = 3.0


def _verts(pts):
    lines = []
    for i, (x, y, z) in enumerate(pts, 1):
        end = ";" if i == len(pts) else ","
        lines.append(f"    {x},{y},{z}{end}")
    return "\n".join(lines)


def _surface(name, stype, zone, bc, pts, obj="", sun="SunExposed"):
    return (
        f"BUILDINGSURFACE:DETAILED,\n    {name},\n    {stype},\n    C,\n    {zone},\n    ,\n    {bc},\n    {obj},\n"
        f"    {sun},\n    WindExposed,\n    autocalculate,\n    autocalculate,\n{_verts(pts)}\n"
    )


def _window(name, parent, pts):
    return (
        f"FENESTRATIONSURFACE:DETAILED,\n    {name},\n    Window,\n    WC,\n    {parent},\n    ,\n    autocalculate,\n    ,\n"
        f"    1,\n    autocalculate,\n{_verts(pts)}\n"
    )


def make_idf(storeys=2, share=0.2, zone_height=H, plate_scale=None, flats=None):
    plate_scale = plate_scale or {}
    parts = ["Version,23.1;\n"]
    for i in range(storeys):
        z0 = i * H
        z1 = z0 + zone_height
        w = W * plate_scale.get(i, 1.0)
        zone = f"S_F{i}_dwelling_0"
        parts.append(
            f"ZONE,\n    {zone},\n    0,\n    0,\n    0,\n    0,\n    1,\n    1,\n    autocalculate,\n    {w * W * zone_height},\n"
            f"    autocalculate,\n    ,\n    ,\n    Yes;\n"
        )
        floor_bc, floor_obj = ("ground", "") if i == 0 else ("surface", f"S_F{i - 1}_ceil")
        parts.append(_surface(f"S_F{i}_floor", "floor", zone, floor_bc, [(0, 0, z0), (0, W, z0), (w, W, z0), (w, 0, z0)], floor_obj, "NoSun"))
        if i == storeys - 1:
            parts.append(_surface(f"S_F{i}_roof", "roof", zone, "outdoors", [(0, 0, z1), (w, 0, z1), (w, W, z1), (0, W, z1)]))
        else:
            parts.append(_surface(f"S_F{i}_ceil", "ceiling", zone, "surface", [(0, 0, z1), (w, 0, z1), (w, W, z1), (0, W, z1)], f"S_F{i + 1}_floor", "NoSun"))
        sides = [
            ((0, 0), (w, 0)),
            ((w, 0), (w, W)),
            ((w, W), (0, W)),
            ((0, W), (0, 0)),
        ]
        for k, ((xa, ya), (xb, yb)) in enumerate(sides):
            nm = f"S_F{i}_wall{k}"
            parts.append(_surface(nm, "wall", zone, "outdoors", [(xa, ya, z1), (xa, ya, z0), (xb, yb, z0), (xb, yb, z1)]))
            length = ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5
            area = length * zone_height
            ws = share * area
            hgt = zone_height * 0.5
            wl = ws / hgt
            fx = (xb - xa) / length
            fy = (yb - ya) / length
            cx, cy = (xa + xb) / 2, (ya + yb) / 2
            a = (cx - fx * wl / 2, cy - fy * wl / 2)
            b = (cx + fx * wl / 2, cy + fy * wl / 2)
            z_lo = z0 + zone_height * 0.25
            z_hi = z_lo + hgt
            parts.append(_window(f"{nm}_Win", nm, [(a[0], a[1], z_hi), (a[0], a[1], z_lo), (b[0], b[1], z_lo), (b[0], b[1], z_hi)]))
    return "\n".join(parts)


def ctx(storeys=2, plate=W * W, share_target=0.2, prepared=None, dwellings=1, levels=None):
    return {
        "stem": "abc",
        "building_id": "way/1",
        "country": "ES",
        "storey_count": storeys,
        "levels_data": storeys if levels is None else levels,
        "footprint_area_m2": plate,
        "prepared_floor_area_m2": plate * storeys if prepared is None else prepared,
        "dwellings_used": dwellings,
        "archetype_id": "ES.ME.AB.01.Gen.ReEx.001.001",
        "building_type": "AB",
        "divided": True,
        "share_target": share_target,
        "shifted": False,
        "offset": None,
        "area_0908": plate * storeys,
    }


def run(text, c):
    return MOD.evaluate(MOD.parse_idf(text), c)


def test_passing_model_passes_every_implemented_check():
    r = run(make_idf(), ctx())
    for k in ("I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I11", "I13"):
        assert r[f"{k}_pass"] is True, (k, r[f"{k}_value"])
    assert r["I10_pass"] == ""
    assert r["storey_source"] == "levels"
    assert r["storeys_idf"] == 2
    assert r["floor_area_idf_m2"] == pytest.approx(200.0)
    assert r["I4_value"] == pytest.approx(6.0)


def test_missing_storey_fails_i1():
    r = run(make_idf(storeys=1), ctx(storeys=2))
    assert r["I1_pass"] is False
    assert r["I1_value"] == 1
    assert r["I3_pass"] is False


def test_tall_zone_fails_i5():
    r = run(make_idf(storeys=1, zone_height=6.0), ctx(storeys=1))
    assert r["I5_pass"] is False
    assert r["I5_value"] == 1
    assert r["I4_pass"] is False


def test_window_share_off_by_five_percent_fails_i9():
    r = run(make_idf(share=0.25), ctx(share_target=0.20))
    assert r["I9_pass"] is False
    assert r["I9_value"] == pytest.approx(0.25, abs=1e-6)
    ok = run(make_idf(share=0.21), ctx(share_target=0.20))
    assert ok["I9_pass"] is True


def test_ten_percent_floor_loss_fails_i2_and_i7():
    r = run(make_idf(plate_scale={1: 0.9}), ctx())
    assert r["I2_pass"] is False
    assert r["I2_value"] == pytest.approx(0.1)
    assert r["I7_pass"] is False
    assert r["I7_value"] == pytest.approx(0.05, abs=1e-6)


def test_dwelling_count_mismatch_fails_i8():
    r = run(make_idf(), ctx(dwellings=3))
    assert r["I8_pass"] is False


def test_no_outdoor_wall_is_named_exception():
    r = run(make_idf(), ctx())
    r["outdoor_wall_m2"] = 0.0
    assert "finding283_no_outdoor_wall" in MOD.named_reasons("abc", r)
    assert MOD.named_reasons("97d478bc56840531", {"outdoor_wall_m2": 5.0}) == "zero_floor_flat;core_rule"


def test_cross_vintage_reason_codes():
    c = ctx()
    c["area_0908"] = 100.0
    assert run(make_idf(), c)["I13_reason"] == "up_class_09-08_short"
    c["area_0908"] = 400.0
    c["n_deleted"] = 2
    assert run(make_idf(), c)["I13_reason"] == "sliver_drop"
    c["n_deleted"] = 0
    r = run(make_idf(), c)
    assert r["I13_reason"] == "UNEXPLAINED" and r["I13_pass"] is False
    c["stem"] = "bb4d3f44d4fbe5b1"
    assert run(make_idf(), c)["I13_reason"] == "core_rule"


def test_position_checks():
    c = ctx()
    c["shifted"] = True
    c["offset"] = (1000.0, 2000.0)
    c["ref_centroid_abs"] = (1005.0, 2005.0)
    assert run(make_idf(), c)["I11_pass"] is True
    c["ref_centroid_abs"] = (1020.0, 2005.0)
    assert run(make_idf(), c)["I11_pass"] is False
    c2 = ctx()
    c2["offset"] = (1.0, 1.0)
    assert run(make_idf(), c2)["I11_pass"] is False


def test_ground_dev_catches_missing_ground_part():
    text = make_idf(plate_scale={0: 0.9})
    r = run(text, ctx())
    assert r["I6_pass"] is False or r["I2_pass"] is False


def _block_idf(covered_adiabatic=False, lower_block=False):
    text = make_idf(storeys=2)
    if covered_adiabatic:
        old = (
            "BUILDINGSURFACE:DETAILED,\n    S_F0_ceil,\n    ceiling,\n    C,\n    S_F0_dwelling_0,\n    ,\n    surface,\n    S_F1_floor,"
        )
        assert old in text
        text = text.replace(
            old,
            "BUILDINGSURFACE:DETAILED,\n    S_F0_ceil,\n    roof,\n    C,\n    S_F0_dwelling_0,\n    ,\n    adiabatic,\n    ,",
        )
    if lower_block:
        z = "B_F0_dwelling_0"
        text += (
            f"ZONE,\n    {z},\n    0,\n    0,\n    0,\n    0,\n    1,\n    1,\n    autocalculate,\n    {W * W * H},\n    autocalculate,\n    ,\n    ,\n    Yes;\n"
            + _surface("B_floor", "floor", z, "ground", [(W, 0, 0), (W, W, 0), (2 * W, W, 0), (2 * W, 0, 0)], "", "NoSun")
            + _surface("B_roof", "roof", z, "adiabatic", [(W, 0, H), (2 * W, 0, H), (2 * W, W, H), (W, W, H)])
            + _surface("B_wall", "wall", z, "outdoors", [(2 * W, 0, H), (2 * W, 0, 0), (2 * W, W, 0), (2 * W, W, H)])
        )
    return text


def test_reference_follows_levels_not_storey_count():
    c = ctx(storeys=1, levels=2)
    r = run(make_idf(storeys=2), c)
    assert r["storey_source"] == "levels"
    assert r["storeys_ref"] == 2
    assert r["I1_pass"] is True
    assert r["I3_pass"] is True
    assert r["I4_pass"] is True
    assert r["I1_info_vs_storey_count"] is False


def test_unreproduced_storey_rule_fails_i1_with_reason():
    c = ctx(storeys=2, levels=float("nan"))
    r = run(make_idf(storeys=2), c)
    assert r["storey_source"] == "storey_rule_unreproduced"
    assert r["I1_pass"] is False
    assert r["I3_pass"] == "" and r["I4_pass"] == ""
    assert "storey_rule_unreproduced" in MOD.named_reasons("abc", r)


def test_it_reference_from_measured_height():
    c = ctx(storeys=2, levels=float("nan"))
    c["country"] = "IT"
    c["height_m"] = 6.2
    c["height_source"] = "measured (c_a944ctc_edifici_pl)"
    r = run(make_idf(storeys=2), c)
    assert r["storey_source"] == "ctc_height" and r["I1_pass"] is True


def test_adiabatic_roof_of_lower_block_passes_i6():
    r = run(_block_idf(lower_block=True), ctx(storeys=2))
    assert r["roof_adiabatic_m2"] == pytest.approx(W * W)
    assert r["I6_roof_dev"] == pytest.approx(0.0, abs=1e-9)
    assert r["I6_pass"] is True


def test_adiabatic_roof_under_a_zone_does_not_inflate_roof():
    r = run(_block_idf(covered_adiabatic=True), ctx(storeys=2))
    assert r["roof_adiabatic_m2"] == pytest.approx(W * W)
    assert r["roof_adiabatic_uncovered_m2"] == pytest.approx(0.0)
    assert r["I6_pass"] is True
    assert r["I6_roof_dev_literal"] > 0.4


def test_one_flat_on_three_storeys_expects_one_zone_each():
    r = run(make_idf(storeys=3), ctx(storeys=3, dwellings=1))
    assert r["I8_expected"] == "1;1;1"
    assert r["I8_value"] == "1;1;1"
    assert r["I8_pass"] is True
    assert r["I8_literal"] is True


def test_missing_flat_zone_on_storey_fails_i8():
    text = make_idf(storeys=3).replace("S_F1_dwelling_0", "S_F1_other_0")
    r = run(text, ctx(storeys=3, dwellings=1))
    assert r["I8_value"] == "1;0;1"
    assert r["I8_pass"] is False


def test_whole_zone_building_is_out_of_scope_for_i8():
    text = make_idf(storeys=2).replace("_dwelling_0", "_whole")
    r = run(text, ctx())
    assert r["I8_pass"] == "" and r["I8_note"] == "undivided"
    assert "undivided" in MOD.named_reasons("abc", r)


def test_window_free_home_without_outdoor_wall_passes_i9():
    text = make_idf().split("FENESTRATIONSURFACE:DETAILED,")[0].replace("outdoors", "adiabatic")
    r = run(text, ctx())
    assert r["outdoor_wall_m2"] == 0 and r["window_m2"] == 0
    assert r["I9_pass"] is True


def _equip_text(sched_dir, zones, subcat="EU_Step8_InternalGains", mean=3.0, wm2=1.0, hours=8760):
    out = []
    for i, z in enumerate(zones):
        fname = f"{z}_gain.csv"
        (sched_dir / fname).write_text("\n".join(str(mean) for _ in range(hours)) + "\n", encoding="utf-8")
        out.append(
            f"SCHEDULE:FILE,\n    G{i},\n    Any,\n    ../../schedules/abc/{fname},\n    1,\n    0,\n    8760,\n    Comma,\n    No,\n    60,\n    Yes;\n"
            f"OTHEREQUIPMENT,\n    E{i},\n    Electricity,\n    {z},\n    G{i},\n    Watts/Area,\n    ,\n    {wm2},\n    ,\n    0,\n    0,\n    0,\n    0,\n    {subcat};\n"
        )
    return "\n".join(out)


def test_internal_gain_schedule_mean_checked(tmp_path):
    c = ctx()
    c["schedule_dir"] = str(tmp_path)
    c["phi_int_w_m2"] = 3.0
    zones = ["S_F0_dwelling_0", "S_F1_dwelling_0"]
    r = run(make_idf() + _equip_text(tmp_path, zones, mean=3.0), c)
    assert r["I10_pass"] is True and r["I10_value"] == 0
    r = run(make_idf() + _equip_text(tmp_path, zones, mean=3.15), c)
    assert r["I10_pass"] is False and r["I10_value"] == 2
    assert r["I10_worst_mean_dev"] == pytest.approx(0.05, abs=1e-6)


def test_internal_gain_wrong_object_fails_i10(tmp_path):
    c = ctx()
    c["schedule_dir"] = str(tmp_path)
    c["phi_int_w_m2"] = 3.0
    zones = ["S_F0_dwelling_0", "S_F1_dwelling_0"]
    assert run(make_idf() + _equip_text(tmp_path, zones, wm2=2.0), c)["I10_pass"] is False
    assert run(make_idf() + _equip_text(tmp_path, zones[:1]), c)["I10_pass"] is False
    legacy = _equip_text(tmp_path, zones) + _equip_text(tmp_path, ["S_F0_dwelling_0"], subcat="EU_InternalGains")
    assert run(make_idf() + legacy, c)["I10_pass"] is False


def test_i13_new_reason_codes():
    c = ctx()
    c["area_0908"] = 100.0
    c["t06s_rerun"] = True
    assert run(make_idf(), c)["I13_reason"] == "t06s_fold_fix;up_class_09-08_short"
    c2 = ctx(storeys=2, levels=2)
    c2["storey_count"] = 1
    c2["area_0908"] = W * W
    r = run(make_idf(), c2)
    assert r["I13_reason"] == "storey_source_levels"
    assert r["I13_pass"] is True


def test_reference_from_layout_file(tmp_path):
    import json
    lay = tmp_path / "way_1.json"
    lay.write_text(json.dumps({"building_id": "way/1", "storeys": 2}), encoding="utf-8")
    c = ctx(storeys=1, levels=float("nan"))
    c["layout_paths"] = [str(tmp_path / "missing.json"), str(lay)]
    r = run(make_idf(storeys=2), c)
    assert r["storey_source"] == "layout_0908" and r["storeys_ref"] == 2
    assert r["I1_pass"] is True and r["I3_pass"] is True and r["I4_pass"] is True


def test_reference_from_old_idf_height(tmp_path):
    old = tmp_path / "abc.idf"
    old.write_text(make_idf(storeys=2), encoding="utf-8")
    c = ctx(storeys=1, levels=float("nan"))
    c["old_idf_paths"] = [str(old)]
    r = run(make_idf(storeys=2), c)
    assert r["storey_source"] == "idf_height_0907" and r["storeys_ref"] == 2
    assert r["I1_pass"] is True
    bad = tmp_path / "bad.idf"
    bad.write_text(make_idf(storeys=2, zone_height=2.7), encoding="utf-8")
    c["old_idf_paths"] = [str(bad)]
    r = run(make_idf(storeys=2), c)
    assert r["storey_source"] == "storey_rule_unreproduced"


def test_reference_from_catastro_sidecar():
    c = ctx(storeys=4, levels="")
    c["levels_sidecar"] = 4.0
    c["sidecar_overlap_m2"] = 250.0
    r = run(make_idf(storeys=4), c)
    assert r["storey_source"] == "levels_sidecar"
    assert r["storeys_ref"] == 4
    assert r["I1_pass"] is True
    assert r["sidecar_overlap_m2"] == 250.0
