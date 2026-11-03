import importlib.util
from pathlib import Path

import pandas as pd

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "provenance_breakdown.py"
_spec = importlib.util.spec_from_file_location("provenance_breakdown", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


def test_classify_token_known_forms():
    c = m.classify_token
    assert c(None) == "observed" and c("") == "observed" and c(float("nan")) == "observed"
    assert c("OSM_OBSERVED") == "observed" and c("observed_split") == "observed"
    assert c("FUSED_OVERTURE_HIGH") == "fused" and c("CPT_LIDAR_2023_HEIGHT_DERIVED") == "fused"
    assert c("IMPUTED_NEIGHBOUR_NEAREST_6.4M") == "spatial" and c("HOTDECK_NEIGHBOR_MED") == "spatial"
    assert c("IMPUTED_DISTRICT_MODE") == "statistical_default" and c("area_imputed") == "statistical_default"
    assert c("GROUPMODE_MED") == "statistical_default"
    assert c("OSM_MISSING") == "missing_not_tokenised"
    assert c("IMPUTED_NEIGHBOUR_TOUCHING+IMPUTED_NEIGHBOUR_TOUCHING") == "spatial"


def test_unknown_token_is_counted_not_dropped():
    cats = pd.Series([m.classify_token(t) for t in ["OSM_OBSERVED", "WHAT_IS_THIS", "x"]])
    rows = m.tally("S", "t", "a", cats, "v", "s")
    got = {r["category"]: r["n"] for r in rows}
    assert got["unknown_token"] == 2 and got["observed"] == 1
    assert abs(sum(r["share_pct"] for r in rows) - 100.0) < 1e-3


def test_us_year_tokens_come_from_flag():
    assert m.us_category("OSM_MISSING", "year_built", "no_year|HOTDECK_NEIGHBOR_HIGH") == "spatial"
    assert m.us_category("OSM_MISSING", "year_built", "no_year|GROUPMODE_MED") == "statistical_default"
    assert m.us_category("OSM_MISSING", "levels", "no_floors|GROUPMODE_MED") == "missing_not_tokenised"
    assert m.us_category("OSM_OBSERVED", "levels", "") == "observed"


def test_output_shares_sum_to_100_and_no_unknown():
    df = pd.read_csv(m.OUT_CSV)
    sums = df.groupby(["site", "attribute"])["share_pct"].sum()
    assert (sums.sub(100).abs() < 1e-3).all()
    assert df.loc[df["category"] == "unknown_token", "n"].sum() == 0
    assert df["site"].nunique() == 13
