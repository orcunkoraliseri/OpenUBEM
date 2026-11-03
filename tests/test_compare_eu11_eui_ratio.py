import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "cluster"))

from compare_eu11_eui_ratio import compare, slug_of  # noqa: E402


def _row(bid, rc, heat, fa, variant="fix", geo="X"):
    return {"building_id": bid, "geometry_outcome": geo, "eplus_return_code": rc, "heating_kwh": heat,
            "floor_area_m2": fa, "eui_kwh_m2": heat / fa if heat is not None else None, "idf_variant": variant}


def _toy():
    base = pd.DataFrame([
        _row("a", 0, 100.0, 100.0), _row("b", 0, 100.0, 100.0), _row("c", 0, 100.0, 100.0),
        _row("d", 0, 100.0, 100.0), _row("e", 0, None, 100.0),
    ])
    new = pd.DataFrame([
        _row("a", 0, 200.0, 100.0),
        _row("b", 0, 100.0, 50.0, variant="t06f"),
        _row("c", 1, 500.0, 100.0),
        _row("d", 0, 110.0, 100.0),
        _row("e", 0, 100.0, 100.0),
        _row("z", 0, 100.0, 100.0),
    ])
    return new, base


def test_slug():
    assert slug_of("GB-LDN-STDUNSTANS") == "gb_ldn_stdunstans"


def test_rc_filter_and_join():
    j, s = compare(*_toy())
    assert s["n_joined"] == 3
    assert set(j["building_id"]) == {"a", "b", "d"}


def test_ratio_math():
    j, _ = compare(*_toy())
    a = j[j["building_id"] == "a"].iloc[0]
    assert abs(a["eui_ratio"] - 2.0) < 1e-9
    assert abs(a["heating_ratio"] - 2.0) < 1e-9
    assert abs(a["floor_area_ratio"] - 1.0) < 1e-9


def test_flags_and_split():
    j, s = compare(*_toy())
    assert dict(zip(j["building_id"], j["flag_out"])) == {"a": True, "b": True, "d": False}
    assert s["flag_out"] == 2
    assert s["flag_floor_changed"] == 1
    assert s["flag_heating_only"] == 1
    assert s["by_idf_variant"]["fix"]["flag_heating_only"] == 1
    assert s["by_idf_variant"]["t06f"]["flag_floor_changed"] == 1


def test_pooled():
    _, s = compare(*_toy())
    assert abs(s["pooled_eui_new"] - 410.0 / 250.0) < 1e-9
    assert abs(s["pooled_eui_old_0908"] - 1.0) < 1e-9


def _reason_case():
    ids = ["g", "f", "o", "h", "s", "u", "ok"]
    base = pd.DataFrame([_row(i, 0, 100.0, 100.0, geo="X") for i in ids])
    rows = [
        _row("g", 0, 200.0, 100.0, variant="fix"),
        _row("f", 0, 200.0, 50.0),
        _row("o", 0, 200.0, 100.0, geo="Y"),
        _row("h", 0, 50.0, 100.0),
        _row("s", 0, 200.0, 100.0),
        _row("u", 0, 200.0, 100.0),
        _row("ok", 0, 100.0, 100.0),
    ]
    new = pd.DataFrame(rows)
    hid = pd.DataFrame({
        "building_id": ["h", "s", "u"], "hidden_outdoor_m2": [5.0, 0.0, 0.0], "hidden_ground_m2": [0.0, 0.0, 0.0],
        "outdoor_wall_m2": [100.0] * 3, "roof_m2": [50.0] * 3, "ground_floor_m2": [50.0] * 3, "outdoor_floor_m2": [0.0] * 3,
    })
    gate = pd.DataFrame({
        "building_id": ["s", "u"], "union_ratio_vs_0908": [1.2, 1.0], "G4": [True, True], "constant_outline": [True, True],
    })
    t06g = pd.DataFrame({"building_id": ["g"]})
    return new, base, {"hidden": hid, "gate": gate, "t06g": t06g}


def test_named_reasons():
    new, base, aux = _reason_case()
    j, s = compare(new, base, aux)
    got = dict(zip(j["building_id"], j["reason"]))
    assert got == {"g": "t06g_fault", "f": "floor_changed", "o": "outcome_changed", "h": "hidden_0908",
                   "s": "storey_outline", "u": "unexplained", "ok": ""}
    assert s["reason_counts"]["unexplained"] == 1
    assert sum(s["reason_counts"].values()) == s["flag_out"]
    assert abs(j.set_index("building_id").loc["h", "hidden_share_0908"] - 0.025) < 1e-9
    assert j.set_index("building_id").loc["s", "union_ratio_vs_0908"] == 1.2


def test_t06g_variant_not_fault():
    new, base, aux = _reason_case()
    new.loc[new["building_id"] == "g", "idf_variant"] = "t06g"
    j, _ = compare(new, base, aux)
    assert dict(zip(j["building_id"], j["reason"]))["g"] == "unexplained"


def test_g4_false_and_not_constant_is_storey_outline():
    new, base, aux = _reason_case()
    aux["gate"].loc[aux["gate"]["building_id"] == "u", ["G4", "constant_outline"]] = [False, False]
    j, _ = compare(new, base, aux)
    assert dict(zip(j["building_id"], j["reason"]))["u"] == "storey_outline"


def test_nowin_base_summary():
    from compare_eu11_eui_ratio import compare_nowin

    def r(bid, heat, win, rc=0):
        d = _row(bid, rc, heat, 100.0)
        d["window_m2"] = win
        return d

    new = pd.DataFrame([r("a", 90.0, 0.0), r("b", 120.0, 10.0), r("c", 150.0, 20.0), r("d", 100.0, 5.0), r("f", 1.0, 1.0, rc=1)])
    base = pd.DataFrame([_row(b, 0, 100.0, 100.0) for b in "abcdf"])
    base["eui_source"] = ["fix_2026-10-01", "fix_2026-10-01", "fix_2026-10-01", "merged_2026-09-08_carry", "fix_2026-10-01"]
    j, s = compare_nowin(new, base, "nowin")
    assert s["n_joined"] == 3
    assert set(j["building_id"]) == {"a", "b", "c"}
    assert "eui_kwh_m2_nowin" in j.columns
    assert "window_m2_per_floor_m2" in j.columns
    assert s["n_zero_window_ratio_outside_0.99_1.01"] == 1
    assert s["n_heating_ratio_below_1"] == 1
    assert s["heating_ratio_vs_window_spearman"] == 1.0
    assert abs(s["heating_ratio"]["median"] - 1.2) < 1e-9
