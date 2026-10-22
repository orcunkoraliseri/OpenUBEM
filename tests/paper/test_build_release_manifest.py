import importlib.util
from pathlib import Path

import pandas as pd

_P = Path(__file__).resolve().parents[2] / "scripts" / "paper" / "build_release_manifest.py"
_spec = importlib.util.spec_from_file_location("build_release_manifest", _P)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)

OUT = Path(__file__).resolve().parents[2] / "openubem" / "outputs" / "comparisons" / "paper_release_manifest_2026-10-21.csv"


def test_decide_rules():
    assert m.decide("ZA-CPT-WOODSTOCK", "anything")[0] == "no"
    assert m.decide("AM-EVN-NORNORK", "anything")[0] == "no"
    assert m.decide("FI-HEL-KALLIO", "CC BY 4.0")[0] == "yes"
    assert m.decide("FI-HEL-KALLIO", "")[0] == "no"
    assert m.decide("FI-HEL-KALLIO", "CC BY 4.0", mixed=True)[0] == "no"


def test_checks_synthetic():
    df = pd.DataFrame({
        "path": ["a/ZA-CPT-WOODSTOCK/x", "b/y", "c/AM-EVN-NORNORK/z"],
        "site": ["ZA-CPT-WOODSTOCK", "FI-HEL-KALLIO", "AM-EVN-NORNORK"],
        "licence": ["L", "", "L"],
        "release": ["no", "yes", "no"],
    })
    c = m.checks(df)
    assert c["cape_town_rows"] == 1 and c["cape_town_yes"] == 0
    assert c["armenia_rows"] == 1 and c["armenia_yes"] == 0
    assert c["empty_licence"] == 1 and c["yes"] == 1 and c["no"] == 2


def test_written_manifest():
    df = m.build()
    c = m.checks(df)
    assert c["rows"] > 0
    assert c["cape_town_rows"] > 0 and c["cape_town_yes"] == 0
    assert c["armenia_yes"] == 0
    assert c["empty_licence"] == 0
    assert c["restricted_path_rows"] == 0
    assert df["path"].is_unique
    assert not df["path"].str.contains("resources/UK", case=False).any()
    saved = pd.read_csv(OUT, keep_default_na=False)
    assert len(saved) == len(df)
    assert (saved["licence"].astype(str).str.strip() != "").all()
