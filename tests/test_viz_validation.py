"""T14 — the six V14 faithfulness checkpoints as tests (5 automatable + 1 manual).

These are the enforcement mechanism for the faithful-to-model constraint: each is
"fail = block ship" (PLAN §T14). They run on the pinned pilot cell (nyc_centre,
738 buildings). Geometry/IDFs come from the live Step-3 run if present, else from
the durable archive zip beside the pilot's Step-5 outputs (so the suite survives a
Temp wipe).

  CP-Geometry        — sampled vertex round-trip THROUGH the stored Option-A
                       offsets: (CityJSON_vertex + common_origin) − centroid == IDF.
  CP-Value           — 100% of displayed EUI/carbon/end-use == real 05_results.csv.
  CP-Provenance      — available badge fields round-trip; absent fields appear in
                       provenance_coverage; zero-imputation negative case.
  CP-LOD             — per-mode sub-surface count + no synthetic zone geometry
                       (single_zone can never show zones).
  CP-Reproducibility — two builds → identical content hash EXCLUDING timestamp;
                       timestamp lives outside the hashed region.
  CP-Accessibility   — documented MANUAL procedure (+ an automatable contrast /
                       CVD-margin sanity on the shipped palette).

Plus the T13 self-contained assertion: the emitted HTML has zero fetchable
external references.

Phase E (T16-T20) adds four more, all against the SAME pilot:
  CP-Basemap-Georef  — a known UTM corner round-trips through
                       `extent_local + common_origin` exactly.
  CP-Offline         — still zero external fetches with a basemap embedded
                       (a `data:` URI is not an external reference).
  CP-Reproducibility — content_hash is unaffected by basemap presence (it
                       only ever hashes `scene["cityjson"]`).
  CP-FlatFootprint   — Grand Central / Times Sq-42nd carry the raw
                       `data_quality_flag`/`provenance_height_m` provenance
                       the client-side `heightMissing()` (T18) reads.
"""

from __future__ import annotations

import copy
import json
import math
import re
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from openubem.viz.cityjson_emitter import _LOD1_CATEGORIES, dumps, footprint_centroids_utm
from openubem.viz.geometry_extract import collect_geometry
from openubem.viz.metadata_block import content_hash
from openubem.viz.viewer_export import _inject, build_scene

_REPO = Path(__file__).resolve().parents[1]
_PILOT = (_REPO / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results"
          / "phaseE" / "nyc_centre")
_RESULTS_CSV = _PILOT / "05_results.csv"
_BUILDINGS = _PILOT / "01_buildings.gpkg"
_ARCHIVE = _PILOT / "nyc_centre_step3_idfs_archive.zip"
import os  # noqa: E402
_LIVE_MANIFEST = (Path(os.environ.get("LOCALAPPDATA", "")) / "Temp" / "ubem_validation"
                  / "phaseE" / "nyc_centre" / "step3" / "03_idf_manifest.parquet")

_FIXED_TS = "2020-01-01T00:00:00+00:00"

pytestmark = pytest.mark.skipif(
    not _RESULTS_CSV.exists() or not _BUILDINGS.exists()
    or not (_LIVE_MANIFEST.exists() or _ARCHIVE.exists()),
    reason="pilot artifacts (05_results.csv / 01_buildings.gpkg / IDFs) not available",
)


def _usable_manifest(tmp_dir: Path) -> pd.DataFrame:
    """Return the Step-3 manifest with idf_path pointing at readable IDFs.

    Prefer the live Temp run; if its IDFs are gone, extract the durable archive
    and rewrite idf_path to the extracted copies.
    """
    if _LIVE_MANIFEST.exists():
        df = pd.read_parquet(_LIVE_MANIFEST)
        if df["idf_path"].map(lambda p: Path(p).exists()).all():
            return df
    with zipfile.ZipFile(_ARCHIVE) as z:
        z.extractall(tmp_dir)
    df = pd.read_parquet(tmp_dir / "step3" / "03_idf_manifest.parquet")
    idf_dir = tmp_dir / "step3" / "idfs"
    df = df.copy()
    df["idf_path"] = df["idf_path"].map(lambda p: str(idf_dir / Path(str(p)).name))
    return df


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("nyc_centre_idfs")
    manifest_df = _usable_manifest(tmp_dir)
    buildings_gdf = gpd.read_file(_BUILDINGS)
    results_df = pd.read_csv(_RESULTS_CSV)
    scene = build_scene(manifest_df, buildings_gdf, results_df,
                        run_id="nyc_centre", timestamp=_FIXED_TS)
    centroids = footprint_centroids_utm(buildings_gdf)
    return {
        "scene": scene,
        "cityjson": scene["cityjson"],
        "coverage": scene["provenance_coverage"],
        "manifest_df": manifest_df,
        "buildings_gdf": buildings_gdf,
        "results_df": results_df,
        "centroids": centroids,
        "idf_by_osm": {str(r.osm_id): r.idf_path
                       for r in manifest_df.itertuples(index=False)},
    }


# ── CP-Geometry ───────────────────────────────────────────────────────────────
def _stratified_sample(bundle) -> list[str]:
    """≥1 building per (archetype_id × zoning_strategy) present."""
    cj = bundle["cityjson"]
    zoning = {str(r.osm_id): getattr(r, "zoning_strategy", None)
              for r in bundle["manifest_df"].itertuples(index=False)}
    seen, sample = set(), []
    for osm_id, co in cj["CityObjects"].items():
        key = (co["attributes"].get("archetype_id"), zoning.get(osm_id))
        if key not in seen:
            seen.add(key)
            sample.append(osm_id)
    return sample


def test_cp_geometry_roundtrip_through_offsets(bundle):
    cj = bundle["cityjson"]
    ox, oy, _ = cj["metadata"]["+common_origin_utm"]
    verts = cj["vertices"]
    sample = _stratified_sample(bundle)
    assert len(sample) >= 5, "stratified sample too small — archetype×zoning spread"

    max_err = 0.0
    checked = 0
    for osm_id in sample:
        cx, cy = bundle["centroids"][osm_id]
        g = collect_geometry(bundle["idf_by_osm"][osm_id], recentre=False)
        opaque = sorted(
            ((sn, cat, vs) for (_, _, cat, vs, sn) in g["faces"]
             if cat in _LOD1_CATEGORIES),
            key=lambda t: t[0])
        lod1 = cj["CityObjects"][osm_id]["geometry"][0]
        assert lod1["lod"] == "1"
        for i, (sn, cat, vs) in enumerate(opaque):
            ring = lod1["boundaries"][i][0]
            for k, vidx in enumerate(ring):
                mm = verts[vidx]
                scene = (mm[0] / 1000.0, mm[1] / 1000.0, mm[2] / 1000.0)
                # reverse the stored Option-A transform: source = scene + origin − centroid
                recon = (scene[0] + ox - cx, scene[1] + oy - cy, scene[2])
                src = vs[k]
                err = math.dist(recon, src)
                max_err = max(max_err, err)
                checked += 1
    assert checked > 0
    assert max_err <= 0.01, f"round-trip error {max_err*1000:.3f} mm exceeds 1 cm"


# ── CP-Value ──────────────────────────────────────────────────────────────────
def test_cp_value_displayed_equals_real_results_csv(bundle):
    from openubem.viz.attribute_binding import _RESULT_VALUE_COLS
    cj = bundle["cityjson"]
    fresh = pd.read_csv(_RESULTS_CSV)  # the REAL csv, re-read (not a cached copy)
    by_osm = {str(r.osm_id): r for r in fresh.itertuples(index=False)}

    mismatches = []
    compared = 0
    for osm_id, co in cj["CityObjects"].items():
        r = by_osm.get(osm_id)
        if r is None:
            continue
        attrs = co["attributes"]
        for col in _RESULT_VALUE_COLS:
            src = getattr(r, col, None)
            src_missing = src is None or (isinstance(src, float) and math.isnan(src))
            if col in attrs:
                compared += 1
                a = attrs[col]
                if isinstance(a, (int, float)) and isinstance(src, (int, float)):
                    if not math.isclose(a, src, rel_tol=1e-9, abs_tol=1e-9):
                        mismatches.append((osm_id, col, a, src))
                elif str(a) != str(src):
                    mismatches.append((osm_id, col, a, src))
            elif not src_missing:
                mismatches.append((osm_id, col, "<absent>", src))
    assert compared > 1000, "too few value bindings compared"
    assert not mismatches, f"{len(mismatches)} value mismatches: {mismatches[:5]}"


# ── CP-Provenance ─────────────────────────────────────────────────────────────
def test_cp_provenance_available_fields_roundtrip(bundle):
    from openubem.viz.attribute_binding import (
        _PROV_FROM_BUILDINGS, _PROV_FROM_MANIFEST, _PROV_FROM_RESULTS)
    cj = bundle["cityjson"]
    cov = bundle["coverage"]
    present = set(cov["present"])

    man = {str(r.osm_id): r for r in bundle["manifest_df"].itertuples(index=False)}
    res = {str(r.osm_id): r for r in bundle["results_df"].itertuples(index=False)}
    bld = {str(r.osm_id): r for r in bundle["buildings_gdf"].itertuples(index=False)}
    srcmap = {**{f: ("m", man) for f in _PROV_FROM_MANIFEST},
              **{f: ("r", res) for f in _PROV_FROM_RESULTS},
              **{f: ("b", bld) for f in _PROV_FROM_BUILDINGS}}

    checked = 0
    for field in present:
        _, table = srcmap[field]
        for osm_id, co in cj["CityObjects"].items():
            if field in co["attributes"]:
                row = table.get(osm_id)
                assert row is not None and hasattr(row, field)
                src = getattr(row, field)
                assert str(co["attributes"][field]) == str(src)
                checked += 1
                break  # one round-trip witness per present field is enough
    assert checked == len(present), "every present field must have a live witness"


def test_cp_provenance_absent_fields_in_coverage(bundle):
    cj = bundle["cityjson"]
    cov = bundle["coverage"]
    # PLAN §9.7: the pilot is a legacy run — these MUST be absent + recorded.
    expected_absent = {"resolution_mode", "archetype_confidence", "archetype_source",
                       "mean_imputation_confidence", "imputed_fields_count"}
    assert expected_absent.issubset(set(cov["absent"]))
    # and no building may carry an absent field as an attribute.
    for field in cov["absent"]:
        for co in cj["CityObjects"].values():
            assert field not in co["attributes"], f"{field} bound despite absence"


def test_cp_provenance_zero_imputation_negative_case(bundle):
    cj = bundle["cityjson"]
    cov = bundle["coverage"]
    assert cov["trust_confidence_computable"] is False
    assert cov["trust_confidence_computed_any"] is False
    for co in cj["CityObjects"].values():
        assert "trust_confidence" not in co["attributes"]
        assert "imputed_fields_count" not in co["attributes"]


# ── CP-LOD ────────────────────────────────────────────────────────────────────
def test_cp_lod_dual_lod_no_synthetic_zones(bundle):
    cj = bundle["cityjson"]
    for osm_id, co in cj["CityObjects"].items():
        assert co["type"] == "Building"  # never a Zone/BuildingRoom object
        lods = [g["lod"] for g in co["geometry"]]
        assert lods == ["1", "3"], f"{osm_id} unexpected LODs {lods}"
        n_lod1 = len(co["geometry"][0]["boundaries"])
        n_lod3 = len(co["geometry"][1]["boundaries"])
        # LOD-B is opaque shell + sub-surfaces: never fewer than the mass.
        assert n_lod3 >= n_lod1


def test_cp_lod_subsurface_count_matches_idf(bundle):
    from openubem.viz.cityjson_emitter import _SUBSURFACE_CATEGORIES
    cj = bundle["cityjson"]
    sample = _stratified_sample(bundle)
    for osm_id in sample:
        g = collect_geometry(bundle["idf_by_osm"][osm_id], recentre=False)
        n_sub = sum(1 for (_, _, cat, vs, _) in g["subwin"]
                    if cat in _SUBSURFACE_CATEGORIES and len(vs) >= 3)
        lod3 = cj["CityObjects"][osm_id]["geometry"][1]
        n_opaque = len(cj["CityObjects"][osm_id]["geometry"][0]["boundaries"])
        n_lod3 = len(lod3["boundaries"])
        assert n_lod3 - n_opaque == n_sub, (
            f"{osm_id}: LOD-B sub-surface count {n_lod3 - n_opaque} != IDF {n_sub}")


def test_cp_lod_single_zone_present_and_never_zoned(bundle):
    # single_zone buildings exist in this pilot and carry no zone geometry.
    cj = bundle["cityjson"]
    zs = [co["attributes"].get("zoning_strategy") for co in cj["CityObjects"].values()]
    assert "single_zone" in zs
    # invariant already asserted structurally above: no CityObject exposes zones.


# ── CP-Reproducibility ────────────────────────────────────────────────────────
def test_cp_reproducibility_hash_excludes_timestamp(bundle):
    manifest_df = bundle["manifest_df"]
    buildings_gdf = bundle["buildings_gdf"]
    results_df = bundle["results_df"]
    # Two independent builds with DIFFERENT timestamps.
    a = build_scene(manifest_df, buildings_gdf, results_df,
                    run_id="nyc_centre", timestamp="2020-01-01T00:00:00+00:00")
    b = build_scene(manifest_df, buildings_gdf, results_df,
                    run_id="nyc_centre", timestamp="2099-12-31T23:59:59+00:00")
    ca, cb = a["cityjson"], b["cityjson"]

    # timestamps differ (it lives in the model) ...
    assert (ca["metadata"]["+openubem_build_timestamp"]
            != cb["metadata"]["+openubem_build_timestamp"])
    # ... yet the content hash is identical (timestamp excluded from hashed region).
    assert content_hash(ca) == content_hash(cb)
    # and the serialization is byte-identical once the timestamp is removed.
    da, db = copy.deepcopy(ca), copy.deepcopy(cb)
    da["metadata"].pop("+openubem_build_timestamp")
    db["metadata"].pop("+openubem_build_timestamp")
    assert dumps(da) == dumps(db)


# ── T13 self-contained: zero fetchable external references ────────────────────
def test_t13_html_is_self_contained(bundle):
    html = _inject(bundle["scene"], "nyc_centre")
    # No element that triggers a network fetch.
    assert not re.search(r"<link\b", html, re.I), "external stylesheet link present"
    assert not re.findall(r"<script\b[^>]*\bsrc\s*=", html, re.I), "external script src"
    assert not re.findall(r"<(?:img|iframe|source|audio|video)\b[^>]*\bsrc\s*=", html, re.I)
    assert not re.findall(r'\b(?:src|href)\s*=\s*["\']\s*(?:https?:)?//', html, re.I), \
        "external/protocol-relative resource reference"
    # CSS is inlined in a <style> block — no remote @import / url(http…).
    style = re.search(r"<style>(.*?)</style>", html, re.S)
    assert style and "@import" not in style.group(1)
    assert not re.search(r"url\(\s*['\"]?https?:", style.group(1), re.I)
    # The scene payload is an inline application/json island (not a fetch).
    assert '<script id="scene-data" type="application/json">' in html


# ── Phase E / T16-T20: basemap (F1) + flat-footprint clarity (F2) ─────────────
def _write_fixture_basemap(tmp_path, extent_utm):
    """A tiny hand-written PNG + sidecar — no rasterio/contextily needed here;
    that reprojection path is T16's own concern (test_viz_basemap_raster.py).
    This exercises the T19 exporter seam: cache-on-disk -> embedded scene key.
    """
    from PIL import Image
    png_path = tmp_path / "06_basemap_utm.png"
    Image.new("RGBA", (2, 2), (10, 20, 30, 255)).save(png_path)
    sidecar = {
        "crs": "EPSG:32618", "extent_utm": list(extent_utm),
        "attribution": "© OpenStreetMap contributors © CARTO",
        "provider": "CartoDB.PositronNoLabels", "fetched_px": [2, 2], "zoom": 16,
    }
    (tmp_path / "06_basemap_utm.json").write_text(json.dumps(sidecar), encoding="utf-8")
    return png_path.read_bytes()


def test_t19_build_scene_wires_basemap_when_present(bundle, tmp_path):
    ox, oy, _ = bundle["cityjson"]["metadata"]["+common_origin_utm"]
    extent_utm = (ox + 10.0, oy + 20.0, ox + 510.0, oy + 420.0)
    _write_fixture_basemap(tmp_path, extent_utm)

    scene = build_scene(bundle["manifest_df"], bundle["buildings_gdf"],
                        bundle["results_df"], run_id="nyc_centre",
                        timestamp=_FIXED_TS, basemap_path=tmp_path)

    assert "basemap" in scene
    bm = scene["basemap"]
    assert bm["image"].startswith("data:image/png;base64,")
    assert bm["extent_local"] == [10.0, 20.0, 510.0, 420.0]
    assert bm["attribution"] == "© OpenStreetMap contributors © CARTO"
    assert bm["crs"] == "EPSG:32618"


def test_t19_build_scene_omits_basemap_when_absent(bundle, tmp_path):
    scene = build_scene(bundle["manifest_df"], bundle["buildings_gdf"],
                        bundle["results_df"], run_id="nyc_centre",
                        timestamp=_FIXED_TS, basemap_path=tmp_path / "nope")
    assert "basemap" not in scene
    # And with no path given at all (the MVP/legacy default behaviour).
    assert "basemap" not in bundle["scene"]


def test_t19_load_basemap_directly_present_absent_and_corrupt(tmp_path):
    from openubem.viz.viewer_export import _load_basemap
    origin = (1000.0, 2000.0, 0.0)

    assert _load_basemap(None, origin) is None
    assert _load_basemap(tmp_path / "missing", origin) is None

    _write_fixture_basemap(tmp_path, (1010.0, 2005.0, 1200.0, 2300.0))
    bm = _load_basemap(tmp_path, origin)
    assert bm is not None
    assert bm["extent_local"] == [10.0, 5.0, 200.0, 300.0]

    # Directly via the PNG path (the alternate contract T19 supports).
    bm2 = _load_basemap(tmp_path / "06_basemap_utm.png", origin)
    assert bm2 == bm

    # Corrupt sidecar -> graceful None, never a crash.
    (tmp_path / "06_basemap_utm.json").write_text("not json", encoding="utf-8")
    assert _load_basemap(tmp_path, origin) is None


# ── CP-Basemap-Georef ──────────────────────────────────────────────────────────
def test_cp_basemap_georef_utm_corner_roundtrips_through_extent_local(bundle, tmp_path):
    ox, oy, _ = bundle["cityjson"]["metadata"]["+common_origin_utm"]
    extent_utm = (585164.1, 4511216.0, 586729.7, 4512606.3)  # real pilot bbox (PLAN Phase-E)
    _write_fixture_basemap(tmp_path, extent_utm)

    scene = build_scene(bundle["manifest_df"], bundle["buildings_gdf"],
                        bundle["results_df"], run_id="nyc_centre",
                        timestamp=_FIXED_TS, basemap_path=tmp_path)
    minx_l, miny_l, maxx_l, maxy_l = scene["basemap"]["extent_local"]
    # A known UTM corner maps to the expected extent_local corner, exactly,
    # through `extent_local + common_origin` (T20 §How).
    assert (minx_l + ox, miny_l + oy) == pytest.approx((extent_utm[0], extent_utm[1]))
    assert (maxx_l + ox, maxy_l + oy) == pytest.approx((extent_utm[2], extent_utm[3]))


# ── CP-Offline (re-confirmed with a basemap embedded) ──────────────────────────
def test_cp_offline_html_with_basemap_still_zero_external_fetches(bundle, tmp_path):
    _write_fixture_basemap(tmp_path, (585164.1, 4511216.0, 586729.7, 4512606.3))
    scene = build_scene(bundle["manifest_df"], bundle["buildings_gdf"],
                        bundle["results_df"], run_id="nyc_centre",
                        timestamp=_FIXED_TS, basemap_path=tmp_path)
    assert "basemap" in scene, "test is meaningless without a basemap actually embedded"
    html = _inject(scene, "nyc_centre")

    assert not re.findall(r"<(?:img|iframe|source|audio|video)\b[^>]*\bsrc\s*=", html, re.I)
    assert not re.findall(r'\b(?:src|href)\s*=\s*["\']\s*(?:https?:)?//', html, re.I), \
        "external/protocol-relative resource reference (a data: URI is not external)"
    assert scene["basemap"]["image"] in html or \
        scene["basemap"]["image"].replace("/", "\\/") in html, \
        "the basemap data-URI must be embedded verbatim in the payload"


# ── CP-Reproducibility (unaffected by the basemap — content_hash covers cityjson only) ──
def test_cp_reproducibility_unaffected_by_basemap(bundle, tmp_path):
    _write_fixture_basemap(tmp_path, (585164.1, 4511216.0, 586729.7, 4512606.3))
    no_bm = build_scene(bundle["manifest_df"], bundle["buildings_gdf"],
                        bundle["results_df"], run_id="nyc_centre", timestamp=_FIXED_TS)
    with_bm = build_scene(bundle["manifest_df"], bundle["buildings_gdf"],
                          bundle["results_df"], run_id="nyc_centre",
                          timestamp=_FIXED_TS, basemap_path=tmp_path)
    assert content_hash(no_bm["cityjson"]) == content_hash(with_bm["cityjson"])


# ── CP-FlatFootprint ────────────────────────────────────────────────────────────
def test_cp_flatfootprint_grand_central_and_times_sq_carry_the_provenance(bundle):
    """The two user-flagged flat slabs (PLAN Phase-E verified facts): faithful
    underground-transit footprints with no OSM above-ground massing, not a
    viewer bug. This asserts the RAW bound fields the client-side
    `heightMissing()` (viewer_logic.mjs, T18) reads are genuinely present —
    it does not re-implement that JS logic in Python.
    """
    cj = bundle["cityjson"]
    for osm_id in ("relation/11171793", "relation/11171765"):
        co = cj["CityObjects"].get(osm_id)
        assert co is not None, f"{osm_id} must be present in the pilot CityJSON"
        attrs = co["attributes"]
        flag = attrs.get("data_quality_flag", "")
        assert "no_height" in flag, f"{osm_id} data_quality_flag={flag!r}"
        assert attrs.get("provenance_height_m") == "OSM_MISSING"
        # Faithful-to-model: geometry is NOT fabricated — height/levels attrs
        # reflect the placeholder 1-level/3.5 m fallback, never a raised roof.
        assert attrs.get("levels") == 1.0
        assert attrs.get("total_eui_kwh_m2") is not None, \
            "still a real, simulated building — only its OSM height is missing"


# ── CP-Accessibility (documented manual + automatable palette sanity) ─────────
def _contrast_ratio(fg, bg):
    def lin(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    def L(rgb):
        r, g, b = (lin(x) for x in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    l1, l2 = L(fg), L(bg)
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def test_cp_accessibility_documented_and_palette_sanity():
    """CP-Accessibility (V14) — DOCUMENTED MANUAL PROCEDURE + automatable sanity.

    Manual steps (perform before CP-3 sign-off; record tool + result in §8):
      1. WCAG 1.4.3 (text 4.5:1): legend labels, detail-pane tokens, control text.
         Tool: browser DevTools / WebAIM Contrast Checker on the shipped viewer.
      2. WCAG 1.4.11 (non-text 3:1): swatch/badge outlines, compass, scale bar
         against the panel background.
      3. WCAG 2.1.1 (keyboard): every control (mode/ramp selects, back button,
         Esc, detail close) is keyboard-operable; focus order is sensible.
      4. CVD: run the shipped palette (viridis + cividis ramps, 13 sector hues,
         Fallback, no-data grey) through a deuteranopia/protanopia/tritanopia
         simulator; confirm classes remain distinguishable (aided by the
         always-shown text labels — colour is never the sole channel).

    Automatable sanity below: primary text contrast on the panel background.
    """
    # viewer.css: text #e8ecf2 on the panel (rgba(18,24,38,.92) ≈ #12182a).
    assert _contrast_ratio((0xe8, 0xec, 0xf2), (0x12, 0x18, 0x2a)) >= 4.5
    # muted legend subtext #8393ac still clears the 3:1 non-text/large bar.
    assert _contrast_ratio((0x83, 0x93, 0xac), (0x12, 0x18, 0x2a)) >= 3.0
