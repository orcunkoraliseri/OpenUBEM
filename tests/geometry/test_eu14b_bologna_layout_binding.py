"""EU-14B T02/T03 acceptance tests.

Bologna (`IT-BOL-GALVANI2`) never had a dwelling-layout pop-up before EU-14B.
T01 made the side-car emitter safe to run against its ISTAT-imputed rows; T02
ran it for real, using EU-13B's grid partitioner/conservation fix/>8-per-floor
cap instead of the pre-EU-13B strip cutter; T03 adds the construction-period
imputation tag to every side-car alongside the existing dwelling-count tag.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from openubem.geometry.european_residential import RULED_GRID_MAX_DWELLINGS_PER_FLOOR

ROOT = Path(__file__).resolve().parents[2]
DISTRICT = "IT-BOL-GALVANI2"
LAYOUTS_DIR = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / DISTRICT / "layouts"
MANIFEST_PATH = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11" / DISTRICT / "it_bol_galvani2_manifest.csv"
VIEWER_PATH = ROOT / "openubem" / "outputs" / "3D" / f"eu_{DISTRICT}_viewer.html"


def _sidecar_paths() -> list[Path]:
    return sorted(LAYOUTS_DIR.rglob("*.json"))


SIDECARS = _sidecar_paths()
pytestmark = pytest.mark.skipif(not SIDECARS, reason="EU-14B Bologna side-cars not present in this environment")


# --- T02 ---------------------------------------------------------------


def test_t02_one_sidecar_per_simulated_building():
    import pandas as pd

    # 1,201, not the pre-T05 1,204: T05's resimulation excludes 3 buildings via
    # IDF_ASSEMBLY_FAILED_ZeroDivisionError (openubem/idf/surfaces.py's
    # EU-13B-T09 reroute residual, same failure mode as Madrid/Lyon/London).
    manifest_df = pd.read_csv(MANIFEST_PATH)
    assert len(manifest_df) == 1201
    assert len(SIDECARS) == 1201
    sidecar_bids = {p.stem for p in SIDECARS}
    manifest_bids = set(manifest_df["building_id"].astype(str))
    assert sidecar_bids == manifest_bids


def test_t02_emitted_zone_count_conserves_declared_total():
    checked = 0
    failures = []
    for path in SIDECARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not str(data.get("geometry_outcome", "")).startswith("DWELLING_LAYOUT_EMITTED"):
            continue
        checked += 1
        zone_names = {zone["name"] for floor in data["floors"] for zone in floor["zones"]}
        emitted = len(zone_names)
        if emitted != data["dwellings_total"]:
            failures.append((path.name, emitted, data["dwellings_total"]))
    assert checked > 0
    assert failures == [], f"{len(failures)}/{checked} side-cars do not conserve: {failures[:5]}"


def test_t02_no_storey_exceeds_the_ruled_grid_ceiling():
    for path in SIDECARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not str(data.get("geometry_outcome", "")).startswith("DWELLING_LAYOUT_EMITTED"):
            continue
        for floor in data["floors"]:
            assert len(floor["zones"]) <= RULED_GRID_MAX_DWELLINGS_PER_FLOOR, path.name


def test_t02_popup_header_and_unconditioned_core_agree():
    # D-EU-39 (2026-08-30) resolved D-EU-36 as CARVE (EU-15 T05):
    # has_unconditioned_core is no longer hardcoded False, it is true
    # wherever a storey carved and emitted the core -- the invariant this
    # test actually needs is that the flag agrees with the area accounting,
    # not that it is always False.
    for path in SIDECARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("has_unconditioned_core"):
            gross = data.get("gross_footprint_area_m2")
            conditioned = data.get("conditioned_floor_area_m2")
            assert gross is not None and conditioned is not None and conditioned < gross, path.name
        outcome = data.get("geometry_outcome")
        assert outcome in ("DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT", "FALLBACK_PENDING_LAYOUT"), (path.name, outcome)
        if outcome == "DWELLING_LAYOUT_EMITTED_IMPUTED_COUNT":
            assert data.get("floors"), path.name
        else:
            assert data.get("fallback_reason"), path.name


# --- T03 ---------------------------------------------------------------


def test_t03_both_provenance_tags_present_on_every_sidecar():
    checked = 0
    for path in SIDECARS:
        data = json.loads(path.read_text(encoding="utf-8"))
        checked += 1
        assert data.get("construction_period_provenance") == "IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD", path.name
        assert data.get("dwelling_count_provenance"), path.name
    assert checked == 1201


@pytest.mark.skipif(not VIEWER_PATH.exists(), reason="Bologna viewer not generated in this environment")
def test_t03_construction_period_badge_appears_in_generated_viewer():
    html = VIEWER_PATH.read_text(encoding="utf-8")
    assert "CONSTRUCTION PERIOD IMPUTED" in html
    assert '"cprov":"IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD"' in html
