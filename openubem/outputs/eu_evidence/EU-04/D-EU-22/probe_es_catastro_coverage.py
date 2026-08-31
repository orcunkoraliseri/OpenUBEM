# -*- coding: utf-8 -*-
"""D-EU-22 Option F1 -- ES coverage probe. MEASUREMENT ONLY.

Ruled 2026-08-27 (owner, Option F1, live retrieval authorised).

What this does: for the ES-MAD-BERRUGUETE study bbox it asks the ruled D-EU-10
attribute source -- Direccion General del Catastro INSPIRE Buildings WFS -- how
many building features it returns, how many carry a construction year, a
residential current-use, a dwelling count and a storey count, and what fraction
of the EXISTING EU-02 residential footprint manifest they join to.

What this does NOT do, by the ruling's own words: no ingest, no adapter, no
manifest rebuild, no S3 sample. Nothing under openubem/outputs/eu02/ is written
or touched. The only artefacts are under this directory.

Usage:  .venv/Scripts/python.exe openubem/outputs/eu_evidence/EU-04/D-EU-22/probe_es_catastro_coverage.py
"""
import io
import json
import os
import sys
import time
import xml.etree.ElementTree as ET

import geopandas as gpd
import requests
from shapely.geometry import Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))

SITE = "ES-MAD-BERRUGUETE"
MANIFEST = os.path.join(ROOT, "openubem", "outputs", "eu02", SITE,
                        "02_residential_manifest.gpkg")

ENDPOINT = "https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx"
UA = "OpenUBEM-D-EU-22-coverage-probe/1.0 (research; measurement only)"

# The study bbox, taken from the EU-02 manifest itself and not from a constant.
TILE_DEG = 0.002
PAUSE_S = 1.5
MAX_TRIES = 4

OUT_JSON = os.path.join(HERE, "es_catastro_coverage_probe.json")
OUT_CSV = os.path.join(HERE, "es_catastro_probe_features.csv")

# Catastro currentUse values that are dwellings. Recorded, not guessed: the
# probe prints the full observed histogram so the ruling can see every value.
RESIDENTIAL_USES = ("1_residential",)


def local(tag):
    return tag.rsplit("}", 1)[-1]


def find_all(el, name):
    return [e for e in el.iter() if local(e.tag) == name]


def find_one(el, name):
    for e in el.iter():
        if local(e.tag) == name:
            return e
    return None


def fetch(session, bbox, log):
    """One WFS GetFeature. Returns response text, or raises after MAX_TRIES."""
    params = {
        "service": "wfs",
        "version": "2.0.0",
        "request": "GetFeature",
        "TYPENAMES": "bu:Building",
        "SRSNAME": "urn:ogc:def:crs:EPSG::4326",
        "BBOX": "%s,urn:ogc:def:crs:EPSG::4326" % bbox,
    }
    last = None
    for attempt in range(1, MAX_TRIES + 1):
        try:
            r = session.get(ENDPOINT, params=params, timeout=300)
            if r.status_code == 200:
                return r.text
            last = "HTTP %d" % r.status_code
        except Exception as exc:                      # noqa: BLE001
            last = "%s: %s" % (type(exc).__name__, exc)
        wait = PAUSE_S * (2 ** attempt)
        log.append("retry %d/%d on %s after %s (sleep %.1fs)"
                   % (attempt, MAX_TRIES, bbox, last, wait))
        time.sleep(wait)
    raise RuntimeError("tile %s failed after %d tries: %s"
                       % (bbox, MAX_TRIES, last))


def parse(text):
    """Yield one dict per bu-ext2d:Building in a WFS response."""
    root = ET.fromstring(text.encode("utf-8") if isinstance(text, str) else text)
    for b in [e for e in root.iter() if local(e.tag) == "Building"]:
        rec = {"gml_id": None, "local_id": None, "year": None, "raw_begin": None,
               "current_use": None, "n_dwellings": None, "n_units": None,
               "n_floors": None, "condition": None, "wkt": None,
               "n_floors_nil_reason": None}
        for k, v in b.attrib.items():
            if local(k) == "id":
                rec["gml_id"] = v
        lid = find_one(b, "localId")
        if lid is not None and lid.text:
            rec["local_id"] = lid.text.strip()
        doc = find_one(b, "dateOfConstruction")
        if doc is not None:
            beg = find_one(doc, "beginning")
            if beg is not None and beg.text:
                rec["raw_begin"] = beg.text.strip()
                head = rec["raw_begin"][:4]
                if head.isdigit():
                    rec["year"] = int(head)
        for name, key in (("currentUse", "current_use"),
                          ("numberOfDwellings", "n_dwellings"),
                          ("numberOfBuildingUnits", "n_units"),
                          ("numberOfFloorsAboveGround", "n_floors"),
                          ("conditionOfConstruction", "condition")):
            e = find_one(b, name)
            if e is not None and e.text:
                rec[key] = e.text.strip()
            elif e is not None and key == "n_floors":
                # an empty element is not the same as an absent one: keep the
                # source's own stated reason instead of reporting a bare null
                for ak, av in e.attrib.items():
                    if local(ak) == "nilReason":
                        rec["n_floors_nil_reason"] = av
        for key in ("n_dwellings", "n_units", "n_floors"):
            if rec[key] is not None:
                try:
                    rec[key] = int(rec[key])
                except ValueError:
                    pass
        pos = find_one(b, "posList")
        if pos is not None and pos.text:
            vals = [float(x) for x in pos.text.split()]
            # SRSNAME urn:...EPSG::4326 -> the axis order is lat, lon.
            pts = [(vals[i + 1], vals[i]) for i in range(0, len(vals) - 1, 2)]
            if len(pts) >= 4:
                try:
                    rec["wkt"] = Polygon(pts).wkt
                except Exception:                     # noqa: BLE001
                    rec["wkt"] = None
        yield rec


def main():
    log = []
    t0 = time.time()

    man = gpd.read_file(MANIFEST)
    man84 = man.to_crs(4326)
    w, s, e, n = man84.total_bounds
    log.append("manifest %s: %d rows, native %s, bbox %.6f,%.6f,%.6f,%.6f"
               % (SITE, len(man), str(man.crs), w, s, e, n))

    # tiles, half a tile of margin so an edge building is not missed
    lats, cur = [], s - TILE_DEG / 2.0
    while cur < n + TILE_DEG / 2.0:
        lats.append(cur)
        cur += TILE_DEG
    lons, cur = [], w - TILE_DEG / 2.0
    while cur < e + TILE_DEG / 2.0:
        lons.append(cur)
        cur += TILE_DEG
    tiles = ["%.6f,%.6f,%.6f,%.6f" % (la, lo, la + TILE_DEG, lo + TILE_DEG)
             for la in lats for lo in lons]
    log.append("tiling: %d tiles of %.4f deg" % (len(tiles), TILE_DEG))

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    by_id, anon, tile_counts = {}, [], []
    for i, bbox in enumerate(tiles, 1):
        text = fetch(session, bbox, log)
        got = 0
        for rec in parse(text):
            got += 1
            key = rec["local_id"] or rec["gml_id"]
            if key:
                by_id[key] = rec
            else:
                anon.append(rec)
        tile_counts.append({"bbox": bbox, "features": got})
        sys.stderr.write("tile %3d/%d  %s  %4d feat  (unique %d)\n"
                         % (i, len(tiles), bbox, got, len(by_id)))
        sys.stderr.flush()
        time.sleep(PAUSE_S)

    feats = list(by_id.values()) + anon
    log.append("fetched %d features, %d unique by localId, %d without an id"
               % (sum(t["features"] for t in tile_counts), len(by_id), len(anon)))

    gdf = gpd.GeoDataFrame(
        [{k: v for k, v in f.items() if k != "wkt"} for f in feats],
        geometry=gpd.GeoSeries.from_wkt([f["wkt"] or "POLYGON EMPTY" for f in feats]),
        crs=4326,
    )
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()].copy()

    # clip to the study bbox so the tiling margin does not inflate the count
    from shapely.geometry import box as shp_box
    study = shp_box(w, s, e, n)
    inside = gdf[gdf.geometry.intersects(study)].copy()

    use_hist = inside["current_use"].fillna("<null>").value_counts().to_dict()
    cond_hist = inside["condition"].fillna("<null>").value_counts().to_dict()

    res = inside[inside["current_use"].isin(RESIDENTIAL_USES)].copy()

    def nn(frame, col):
        return int(frame[col].notna().sum())

    # --- the join: Catastro polygon -> EU-02 residential footprint -----------
    man_m = man.to_crs(3035)
    res_m = res.to_crs(3035)
    man_m["_mi"] = range(len(man_m))
    res_m["_ci"] = range(len(res_m))
    pairs = gpd.sjoin(man_m[["_mi", "geometry"]], res_m[["_ci", "geometry"]],
                      how="inner", predicate="intersects")
    joined_manifest_rows = int(pairs["_mi"].nunique())
    joined_catastro_rows = int(pairs["_ci"].nunique())

    # a manifest row is "recoverable" only if the Catastro partner it touches
    # actually carries the year, and only the largest-overlap partner counts
    lookup = res_m.set_index("_ci")
    best = {}
    for mi, ci in zip(pairs["_mi"].to_numpy(), pairs["_ci"].to_numpy()):
        a = man_m.geometry.iloc[mi].intersection(lookup.geometry.loc[ci]).area
        if mi not in best or a > best[mi][1]:
            best[mi] = (ci, a)
    with_year = with_dw = with_fl = 0
    for mi, (ci, _a) in best.items():
        row = lookup.loc[ci]
        if row["year"] is not None and row["year"] == row["year"]:
            with_year += 1
        if row["n_dwellings"] is not None and row["n_dwellings"] == row["n_dwellings"]:
            with_dw += 1
        if row["n_floors"] is not None and row["n_floors"] == row["n_floors"]:
            with_fl += 1

    years = [int(y) for y in res["year"].dropna().tolist()]
    years.sort()
    nil_hist = (res["n_floors_nil_reason"].fillna("<absent>")
                .value_counts().to_dict())
    year_1900 = int(sum(1 for y in years if y == 1900))
    out = {
        "evidence_scope": "d_eu_22_option_f1_coverage_probe_es_only_measurement_only",
        "ruling": "D-EU-22 Option F1, owner-ruled 2026-08-27, live retrieval authorised",
        "site": SITE,
        "no_ingest_declaration": (
            "No adapter was written, no manifest was rebuilt, no S3 sample was "
            "formed. Nothing under openubem/outputs/eu02/ was written."),
        "source": {
            "name": "Direccion General del Catastro, INSPIRE Buildings (bu:Building)",
            "endpoint": ENDPOINT,
            "operation": "WFS 2.0.0 GetFeature, ad hoc BBOX query",
            "note": ("ListStoredQueries offers only parcel- and id-based queries; "
                     "there is no GetBuildingByBBOX. The ad hoc BBOX form works and "
                     "REQUIRES the ',urn:ogc:def:crs:EPSG::4326' suffix and lat,lon "
                     "axis order -- TYPENAME (singular) is rejected."),
            "licence_field_not_probed": True,
        },
        "study_bbox_crs84_w_s_e_n": [w, s, e, n],
        "tiles": {"deg": TILE_DEG, "n": len(tiles), "counts": tile_counts},
        "manifest_rows_residential": int(len(man)),
        "catastro": {
            "features_returned_total": int(sum(t["features"] for t in tile_counts)),
            "unique_buildings_in_study_bbox": int(len(inside)),
            "current_use_histogram": use_hist,
            "condition_histogram": cond_hist,
            "residential_rows": int(len(res)),
            "residential_with_year": nn(res, "year"),
            "residential_with_dwellings": nn(res, "n_dwellings"),
            "residential_with_floors": nn(res, "n_floors"),
            "residential_floors_nil_reason_histogram": nil_hist,
            "floors_note": (
                "numberOfFloorsAboveGround is served as xsi:nil with an explicit "
                "nilReason on the Building feature. That is a DECLARED "
                "non-population at this feature type, not missing data: Catastro "
                "carries the storey count on BuildingPart, reachable only through "
                "the GetBuildingPartByParcel stored query, which is per-parcel and "
                "was out of scope for a bbox coverage probe."),
            "residential_year_equals_1900": year_1900,
            "year_1900_note": (
                "1900-01-01 is Catastro's floor date for undated old stock. It is "
                "reported separately so a ruling can decide whether to treat it as "
                "observed or as a sentinel; it is NOT excluded here."),
            "year_min": (years[0] if years else None),
            "year_median": (years[len(years) // 2] if years else None),
            "year_max": (years[-1] if years else None),
        },
        "join_to_eu02_manifest": {
            "predicate": "intersects, EPSG:3035; year credited from the largest-overlap partner",
            "manifest_rows": int(len(man)),
            "manifest_rows_with_any_catastro_partner": joined_manifest_rows,
            "catastro_residential_rows_used": joined_catastro_rows,
            "manifest_rows_recoverable_year": with_year,
            "manifest_rows_recoverable_dwellings": with_dw,
            "manifest_rows_recoverable_floors": with_fl,
        },
        "elapsed_s": round(time.time() - t0, 1),
        "log": log,
    }
    with io.open(OUT_JSON, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(out, indent=2, ensure_ascii=False))
    inside.drop(columns=["geometry"]).to_csv(OUT_CSV, index=False, encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("tiles", "log")}, indent=2, ensure_ascii=False))
    print("\nwrote %s\nwrote %s" % (OUT_JSON, OUT_CSV))


if __name__ == "__main__":
    main()
