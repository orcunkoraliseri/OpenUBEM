"""EU-18c T03: the 3D viewer carries geometry only, and its per-building
floor-plan polygons are exactly what `read_building_plan` reads out of the
building's own IDF right now (`D-EU-59`, rule 3 -- never the side-cars).

Both tests are offline, against the four already-emitted HTML files under
`docs/docs_ACTIVE/europeanLocations/outputs_3D/`.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from scripts.eu_idf_plan_reader import read_building_plan
from scripts.generate_eu_3d_viewers import EU17_ROOT, REPO_ROOT, _scene_ring
from scripts.run_eu_s2_district_campaign import DISTRICTS

VIEWER_DIR = REPO_ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "outputs_3D"

FORBIDDEN_RE = re.compile(r"eui|kwh|eplus|severe|fatal|weather|epw|job.?id|not simulated", re.IGNORECASE)

# T03(b): 2 per district, at least 2 massing boxes -- fixed at generation
# time against the emitted scene JSON (EU-18c T01 sample).
SAMPLE: list[tuple[str, str, str]] = [
    ("ES-MAD-BERRUGUETE", "way/100704712", "ruled"),
    ("ES-MAD-BERRUGUETE", "way/100704656", "massing_box"),
    ("FR-LYO-HAUTCOEURPENTES", "BATIMENT0000000240877101_part0", "ruled"),
    ("FR-LYO-HAUTCOEURPENTES", "BATIMENT0000000013365727_part0", "massing_box"),
    ("GB-LDN-STDUNSTANS", "way/190348384", "ruled"),
    ("GB-LDN-STDUNSTANS", "way/14325891", "massing_box"),
    ("IT-BOL-GALVANI2", "32471", "ruled"),
    ("IT-BOL-GALVANI2", "32166", "massing_box"),
]


def _viewer_path(district: str) -> Path:
    return VIEWER_DIR / f"eu_{district}_viewer.html"


def _load_scene(district: str) -> dict:
    txt = _viewer_path(district).read_text(encoding="utf-8")
    tag = '<script type="application/json" id="scene">'
    i1 = txt.find(tag) + len(tag)
    i2 = txt.find("</script>", i1)
    return json.loads(txt[i1:i2])


def _district_center(district: str) -> tuple[float, float]:
    eu02_dir = REPO_ROOT / "openubem" / "outputs" / "eu02" / district
    res_gdf = gpd.read_file(eu02_dir / "02_residential_manifest.gpkg")
    exc_gdf = gpd.read_file(eu02_dir / "02_excluded_manifest.gpkg")
    combined = pd.concat([res_gdf, exc_gdf], ignore_index=True)
    geoms = list(combined.geometry)
    minx = min(g.bounds[0] for g in geoms)
    miny = min(g.bounds[1] for g in geoms)
    maxx = max(g.bounds[2] for g in geoms)
    maxy = max(g.bounds[3] for g in geoms)
    return (minx + maxx) / 2.0, (miny + maxy) / 2.0


@pytest.mark.parametrize("district", sorted(DISTRICTS))
def test_viewer_html_has_zero_forbidden_terms(district: str):
    text = _viewer_path(district).read_text(encoding="utf-8")
    matches = FORBIDDEN_RE.findall(text)
    assert matches == [], f"{district}: forbidden terms found: {matches[:10]}"


@pytest.mark.parametrize("district,building_id,expected_state", SAMPLE)
def test_scene_polygons_match_idf_right_now(district: str, building_id: str, expected_state: str):
    scene = _load_scene(district)
    b = next((x for x in scene["buildings"] if x["id"] == building_id), None)
    assert b is not None, f"{building_id} not found in {district} scene JSON"
    assert b["ls"] == expected_state

    root = EU17_ROOT / district
    prepared = pd.read_csv(root / "prepared_buildings.csv", dtype=str)
    row = prepared[prepared["building_id"] == building_id].iloc[0]
    stem = row["stem"]
    idf_path = root / "idfs" / f"{stem}.idf"

    plan = read_building_plan(
        idf_path,
        stem=stem,
        building_id=building_id,
        district=district,
        geometry_outcome=row["geometry_outcome"],
    )
    cx, cy = _district_center(district)

    zones_by_storey: dict[int, list] = {}
    for zone in plan.zones:
        zones_by_storey.setdefault(zone.storey, []).append(zone)

    pl = b["pl"]
    assert pl is not None
    assert len(pl["sf"]) == len(zones_by_storey)

    for storey_payload in pl["sf"]:
        storey_idx = storey_payload["i"]
        zones = zones_by_storey[storey_idx]
        dwelling_whole = [z for z in zones if z.kind in ("dwelling", "whole")]
        circulation = [z for z in zones if z.kind == "circulation"]

        assert len(storey_payload["z"]) == len(dwelling_whole)
        by_name = {z["nm"]: z for z in storey_payload["z"]}
        for zone in dwelling_whole:
            scene_zone = by_name[zone.name]
            expected_rings = [_scene_ring(ring, plan.origin_xy, cx, cy) for ring in zone.rings]
            expected_ring = expected_rings[0] if len(expected_rings) == 1 else [pt for r in expected_rings for pt in r]
            assert scene_zone["r"] == expected_ring, f"{district}/{building_id} storey {storey_idx} zone {zone.name}"
            assert scene_zone["ki"] == ("d" if zone.kind == "dwelling" else "w")

        if circulation:
            assert storey_payload["c"] is not None
            zone = circulation[0]
            expected_rings = [_scene_ring(ring, plan.origin_xy, cx, cy) for ring in zone.rings]
            expected_ring = expected_rings[0] if len(expected_rings) == 1 else [pt for r in expected_rings for pt in r]
            assert storey_payload["c"]["r"] == expected_ring
        else:
            assert storey_payload["c"] is None
