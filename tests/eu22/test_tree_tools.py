from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
NEW = {"AT": "EPSG:32633", "KR": "EPSG:32652", "CA": "EPSG:32618", "FI": "EPSG:32635", "ZA": "EPSG:32734", "HU": "EPSG:32634", "AM": "EPSG:32638"}
OLD_SHIFTED = {"FR": "EPSG:32631", "IT": "EPSG:32632"}


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / "eu21" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def m12():
    return _load("eu22_m12", "12_drop_degenerate.py")


@pytest.fixture(scope="module")
def m13():
    return _load("eu22_m13", "13_model_integrity.py")


@pytest.fixture(scope="module")
def m09():
    return _load("eu22_m09", "09_plans3d_from_idf.py")


def test_12_sites_and_crs(m12):
    from scripts.run_eu_s2_district_campaign import DISTRICTS

    for cc in NEW:
        assert cc in m12.DISTRICTS
        assert m12.DISTRICTS[cc] in DISTRICTS
    assert {**OLD_SHIFTED, **NEW} == m12.CRS
    assert m12._tag("_win_2026-10-08") == "2026-10-08"
    assert m12._tag("_dw_2026-10-08") == "2026-10-08"


def test_13_sites_and_shift(m13):
    from scripts.run_eu_s2_district_campaign import DISTRICTS

    assert set(m13.NEW_SITES) == set(NEW)
    for cc in NEW:
        assert m13.DISTRICTS[cc] in DISTRICTS
    assert set(m13.SHIFTED) == set(OLD_SHIFTED) | set(NEW)
    assert {"ES", "FR", "GB", "IT"} <= set(m13.DISTRICTS)


def test_09_new_sites_have_no_four_site_exclusions(m09):
    assert len(m09.FOUR_SITES) == 4
    for d in ("AT-VIE-RUDOLFSHEIM", "KR-SEO-MAPO", "HU-BUD-ERZSEBETVAROS"):
        assert d not in m09.FOUR_SITES
        assert m09.undivided_ids(d) == set()
        assert m09.fault_ids(d) == set()
    assert m09.ROOT == ROOT
