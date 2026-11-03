import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("hourly_pilot_merge", ROOT / "scripts" / "paper" / "hourly_pilot_merge.py")
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

SERIES = ["heating_kwh", "cooling_kwh", "electricity_kwh", "gas_kwh", "district_hot_water_kwh"]
ANNUAL = {"heating_kwh": 1000.0, "cooling_kwh": 2000.0, "electricity_kwh": 3000.0, "gas_kwh": 500.0,
          "district_hot_water_kwh": 100.0}


def _frame(scale=1.0):
    hours = pd.DataFrame({"month": np.repeat([1, 7], 24), "day": 1, "hour": list(range(1, 25)) * 2})
    for s in SERIES:
        hours[s] = ANNUAL[s] / 48.0 * scale
    return hours


def _write(out, stem, annual=None, run_period=None, scale=1.0):
    frame = _frame(scale)
    frame.to_csv(out / f"{stem}.csv.gz", index=False, compression="gzip")
    side = {"annual_kwh": dict(annual or {s: float(frame[s].sum()) for s in SERIES}),
            "run_period_kwh": dict(run_period or ANNUAL)}
    (out / f"{stem}.json").write_text(json.dumps(side), encoding="utf-8")


def _cases(stems_cities):
    rows = []
    for i, (stem, city) in enumerate(stems_cities, start=1):
        rows.append({"task": i, "city": city, "cell": f"{city}_centre", "osm_id": f"way/{i}", "stem": stem,
                     "ref_heating_kwh": 1000.0, "ref_cooling_kwh": 2000.0,
                     "ref_district_hot_water_kwh": 100.0, "ref_electricity_gas_kwh": 3500.0})
    return pd.DataFrame(rows)


def _run(tmp_path, cases, out):
    case_csv = tmp_path / "cases.csv"
    cases.to_csv(case_csv, index=False)
    rc = m.run(case_csv, out, tmp_path / "check.csv", tmp_path / "profiles.csv", tmp_path / "fig.png")
    return rc


def test_all_pass_writes_profiles_and_figure(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    _write(out, "a", scale=1.0)
    _write(out, "b", scale=1.0)
    cases = _cases([("a", "nyc"), ("b", "la")])
    assert _run(tmp_path, cases, out) == 0
    check = pd.read_csv(tmp_path / "check.csv")
    assert check["passed"].all() and len(check) == 2
    prof = pd.read_csv(tmp_path / "profiles.csv")
    assert set(prof["city"]) == {"nyc", "la"}
    assert set(prof["series"]) == set(SERIES[:4])
    assert {"population", "vintage"} <= set(prof.columns)
    assert (tmp_path / "fig.png").stat().st_size > 0
    winter = prof[(prof["city"] == "nyc") & (prof["kind"] == "winter_avg_day") & (prof["series"] == "heating_kwh")]
    assert len(winter) == 24 and winter["kwh"].iloc[0] == pytest.approx(1000.0 / 48.0)


def test_run_period_edge_passes_just_inside_and_fails_just_outside(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    inside = dict(ANNUAL, heating_kwh=1000.0 * (1 + 0.00099))
    outside = dict(ANNUAL, heating_kwh=1000.0 * (1 + 0.00101))
    exact = dict(ANNUAL, heating_kwh=1001.0)
    _write(out, "in", annual=inside)
    _write(out, "out", annual=outside)
    _write(out, "exact", annual=exact)
    cases = _cases([("in", "nyc"), ("out", "nyc"), ("exact", "nyc")])
    assert _run(tmp_path, cases, out) == 1
    check = pd.read_csv(tmp_path / "check.csv").set_index("stem")
    assert bool(check.loc["in", "passed"]) and bool(check.loc["exact", "passed"])
    assert not bool(check.loc["out", "passed"])
    assert not bool(check.loc["out", "pass_run_period"]) and not bool(check.loc["out", "pass_reference"])


def test_failure_writes_no_profiles(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    _write(out, "ok")
    _write(out, "bad", annual=dict(ANNUAL, cooling_kwh=2100.0))
    assert _run(tmp_path, _cases([("ok", "nyc"), ("bad", "la")]), out) == 1
    assert not (tmp_path / "profiles.csv").exists()
    assert not (tmp_path / "fig.png").exists()
    assert (tmp_path / "check.csv").exists()


def test_reference_failure_alone_fails_the_building(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    _write(out, "a")
    cases = _cases([("a", "nyc")])
    cases["ref_heating_kwh"] = 1100.0
    assert _run(tmp_path, cases, out) == 1
    check = pd.read_csv(tmp_path / "check.csv")
    assert bool(check.loc[0, "pass_run_period"]) and not bool(check.loc[0, "pass_reference"])


def test_missing_output_is_a_failure(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    assert _run(tmp_path, _cases([("gone", "nyc")]), out) == 1
    check = pd.read_csv(tmp_path / "check.csv")
    assert check.loc[0, "status"] == "missing"


def test_series_absent_everywhere_counts_as_zero_consumption(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    annual = dict(ANNUAL)
    annual["gas_kwh"] = float("nan")
    annual["district_hot_water_kwh"] = float("nan")
    run_period = dict(ANNUAL, gas_kwh=float("nan"), district_hot_water_kwh=float("nan"))
    _write(out, "a", annual=annual, run_period=run_period)
    cases = _cases([("a", "nyc")])
    cases["ref_district_hot_water_kwh"] = 0.0
    cases["ref_electricity_gas_kwh"] = 3000.0
    assert _run(tmp_path, cases, out) == 0
