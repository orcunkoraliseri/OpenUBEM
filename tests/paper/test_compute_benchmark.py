import importlib.util
from pathlib import Path

import pandas as pd

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "compute_benchmark.py"
_spec = importlib.util.spec_from_file_location("compute_benchmark", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


def test_parsers():
    assert m.parse_duration("00:00:15") == 15.0
    assert m.parse_duration("00:11.188") == 11.188
    assert m.parse_duration("1-02:00:00") == 86400 + 7200
    assert m.parse_rss_mb("2048K") == 2.0 and m.parse_rss_mb("1G") == 1024.0
    assert pd.isna(m.parse_rss_mb("")) and pd.isna(m.parse_duration(""))


def test_read_sacct_synthetic(tmp_path):
    p = tmp_path / "s.txt"
    p.write_text(
        "9_1|r05probe_la_rural_auto|COMPLETED|a|b|c|00:00:15|00:11.188||6G|0:0\n"
        "9_1.batch|batch|COMPLETED|a|b|c|00:00:15|00:11.186|2048K||0:0\n"
        "9_1.extern|extern|COMPLETED|a|b|c|00:00:15|00:00.001|0||0:0\n"
        "9_2|r05probe_la_rural_floor|FAILED|a|b|c|00:00:20|00:20.000||6G|1:0\n"
        "9_2.batch|batch|FAILED|a|b|c|00:00:20|00:19.000|4096K||1:0\n"
        "9_2.extern|extern|FAILED|a|b|c|00:00:20|00:00.001|0||1:0\n", encoding="utf-8")
    df = m.read_sacct(p)
    assert len(df) == 2
    r = df.set_index("jobid")
    assert r.loc["9_1", "cpu_s"] == 11.186 and r.loc["9_1", "maxrss_mb"] == 2.0
    assert r.loc["9_2", "mode"] == "floor" and r.loc["9_2", "state"] == "FAILED"


def test_row_counts_equal_cases_in_sources():
    raw = pd.read_csv(m.SACCT_RAW, sep="|", header=None, dtype=str, keep_default_na=False)
    n_tasks = int((~raw[0].str.contains(r"\.", regex=True)).sum())
    out = pd.read_csv(m.OUT_CSV)
    allrows = out[out["cell_or_site"] == "ALL"]
    assert int(allrows["n_cases"].sum()) == n_tasks == 1735
    per = out[(out["scope"] == "united_states_rural_probe") & (out["cell_or_site"] != "ALL")]
    assert int(per["n_cases"].sum()) == 1735 and len(per) == 10
    assert sorted(per[per["cell_or_site"] == "la_rural"]["n_cases"]) == [149] * 5
    assert sorted(per[per["cell_or_site"] == "nyc_rural"]["n_cases"]) == [198] * 5
    assert set(allrows["mode"]) == set(m.MODES)
    for site, rel in m.EU_MANIFESTS.items():
        n = len(pd.read_csv(m.EVID / rel, usecols=["building_id"]))
        got = out[(out["scope"] == "international_dwelling_zoning") & (out["cell_or_site"] == site)]
        assert int(got["n_cases"].iloc[0]) == n, site
