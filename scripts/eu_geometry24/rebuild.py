from __future__ import annotations

import json
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

ENGINE = Path(sys.argv[1]).resolve()
LABEL = sys.argv[2]
FRAME = sys.argv[3]
OUTCSV = Path(sys.argv[4])
SCRATCH = Path(sys.argv[5])
SIDE = sys.argv[6] if len(sys.argv) > 6 else "none"
sys.path.insert(0, str(ENGINE))
sys.path.insert(1, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd
from shapely.affinity import translate
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from metrics import idf_metrics
from openubem.geometry.european_residential import (
    _stabilize_ring_coords,
    allocate_european_dwellings,
    european_building_layout_to_zone_specs,
    generate_european_building_dwelling_layout,
)
from geomeppy import IDF as GeomIDF
from openubem.geometry.zoning import build_zones
from scripts.run_eu_s2_campaign import (
    FLOOR_TO_FLOOR_M, ZONE_WINDING_SIGN, build_european_context, build_idf_for_building,
    IDF_HEADER_TEMPLATE, SHADOW_CALCULATION_METHOD, SHADOW_CALCULATION_UPDATE_FREQUENCY_METHOD,
    SHADOW_CALCULATION_UPDATE_FREQUENCY_DAYS, _has_near_duplicate_vertex_surfaces, _drop_redundant_ring_vertices,
)
from openubem.geometry.european_residential import RING_STABILIZATION_GRID_M
from openubem.idf.surfaces import (
    extrude_geometry, find_mismatched_interzone_pairs, _force_reroute_room_layout_to_one_zone_per_floor,
)
from openubem.config import ENERGYPLUS_IDD_PATH


def fork_build(zones, run_dir, name, epw_path):
    try:
        GeomIDF.setiddname(str(ENERGYPLUS_IDD_PATH))
    except Exception:
        pass
    with epw_path.open(encoding="utf-8", errors="replace") as stream:
        f = stream.readline().strip().split(",")
    lat, lon, tz, el = (float(v) for v in f[6:10])
    run_dir.mkdir(parents=True, exist_ok=True)
    p = run_dir / f"{name}.idf"
    p.write_text(IDF_HEADER_TEMPLATE.format(city=f[1], latitude=lat, longitude=lon, time_zone=tz, elevation=el,
                 shadow_method=SHADOW_CALCULATION_METHOD, shadow_update_method=SHADOW_CALCULATION_UPDATE_FREQUENCY_METHOD,
                 shadow_update_days=SHADOW_CALCULATION_UPDATE_FREQUENCY_DAYS), encoding="utf-8")
    idf = GeomIDF(str(p))
    for z in zones:
        z.pop("mode", None)
        poly = z.get("floor_polygon")
        if poly is not None:
            z["coords_m"] = _stabilize_ring_coords(poly)
        c = z.get("coords_m")
        if c:
            z["coords_m"] = _drop_redundant_ring_vertices(c)
    tol = RING_STABILIZATION_GRID_M
    canon = []

    def snap(pt):
        for c in canon:
            if abs(c[0] - pt[0]) <= tol and abs(c[1] - pt[1]) <= tol:
                return c
        canon.append(pt)
        return pt

    for z in zones:
        if z.get("coords_m"):
            z["coords_m"] = [snap(tuple(pt)) for pt in z["coords_m"]]
    extrude_geometry(idf, zones, [])
    mism = find_mismatched_interzone_pairs(idf)
    nd = _has_near_duplicate_vertex_surfaces(idf)
    verdict = "clean"
    if mism or nd:
        did = _force_reroute_room_layout_to_one_zone_per_floor(idf, zones, "interzone_vertex_mismatch" if mism else "near_duplicate_vertex")
        if did:
            verdict = "rerouted"
        elif mism:
            verdict = "REFUSED_interzone_vertex_mismatch_unresolved"
        else:
            verdict = "tolerated_near_duplicate"
    idf.save(str(p))
    return p, verdict, len(mism)

MAIN = Path(__file__).resolve().parents[2]
EV = MAIN / "openubem" / "outputs" / "eu_evidence" / "EU-11"
G = EV / "geometry_24_2026-10-10"
OFFSETS = {"IT-BOL-GALVANI2": (685000.0, 4928000.0), "ES-MAD-BERRUGUETE": (440000.0, 4478000.0)}
MEDIAN_H = 15.0

inv = pd.read_csv(G / "geometry_24_inventory.csv", dtype=str)
gpk, bclean = {}, {}
for d in OFFSETS:
    dx, dy = OFFSETS[d]
    g = gpd.read_file(MAIN / "openubem" / "outputs" / "eu02" / d / "02_residential_manifest.gpkg").set_index("osm_id", drop=False)
    b = gpd.read_file(MAIN / "openubem" / "outputs" / "eu02" / d / "01_buildings_clean.gpkg")
    if FRAME == "local":
        g["geometry"] = g.geometry.apply(lambda x: translate(x, -dx, -dy))
        b["geometry"] = b.geometry.apply(lambda x: translate(x, -dx, -dy))
    gpk[d], bclean[d] = g, b
recs = {c: json.loads((MAIN / "openubem" / "data" / "construction" / f"tabula_archetypes_{c}.json").read_text(encoding="utf-8"))["records"] for c in ("es", "it")}

rows = []
for _, r in inv.iterrows():
    d, bid, stem = r["district"], r["building_id"], r["stem"]
    country = "es" if d.startswith("ES") else "it"
    t0 = time.time()
    out = {"engine": LABEL, "frame": FRAME, "district": d, "building_id": bid, "stem": stem}
    try:
        grow = gpk[d].loc[bid]
        prep = pd.read_csv(EV / f"{d}_win_2026-10-06" / "prepared_buildings.csv", dtype=str).set_index("building_id").loc[bid]
        record = next(x for x in recs[country] if x["archetype_id"] == prep["archetype_id"])
        footprint = grow.geometry
        n_storey = int(float(r["storeys"]))
        count = int(float(r["flat_new_count"]))
        allocation = allocate_european_dwellings(
            archetype_id=prep["archetype_id"], building_type=prep["building_type"],
            n_apartment=count, n_storey=n_storey, plate_area_m2=float(footprint.area),
        )
        layout = generate_european_building_dwelling_layout(footprint, floor_allocations=allocation.floor_allocations)
        out["layout_emitted"] = bool(layout.dwelling_layout_emitted)
        out["layout_reason"] = layout.fallback_reason or ""
        if not layout.dwelling_layout_emitted:
            zones = build_zones(stem, footprint, prep["archetype_id"], n_storey, "one_zone_per_floor", FLOOR_TO_FLOOR_M)
        else:
            zones = european_building_layout_to_zone_specs(layout, building_id=(bid if SIDE != "none" else stem), height_m=FLOOR_TO_FLOOR_M)
        if SIDE != "none":
            sp = EV / f"{d}_win_2026-10-06" / "layouts" / (bid + ".json")
            side = json.loads(sp.read_text(encoding="utf-8"))
            smap = {z["name"]: z for fl in side["floors"] for z in fl["zones"]}
            miss = [z["name"] for z in zones if z["name"] not in smap]
            out["sidecar_missing_zones"] = len(miss)
            for z in zones:
                sz = smap.get(z["name"])
                if sz is None:
                    continue
                pts = [tuple(c) for c in sz["coords_m"]]
                if FRAME == "local":
                    ox, oy = OFFSETS[d]
                    pts = [(a - ox, b - oy) for a, b in pts]
                if len(pts) > 1 and pts[0] == pts[-1]:
                    pts = pts[:-1]
                z["floor_polygon"] = Polygon(pts)
                z["_raw_side"] = pts
        for z in zones:
            poly = orient(z["floor_polygon"], sign=ZONE_WINDING_SIGN)
            z["floor_polygon"] = poly
            if SIDE in ("raw", "fork") and "_raw_side" in z:
                z["coords_m"] = [tuple(c) for c in list(poly.exterior.coords)[:-1]]
            else:
                z["coords_m"] = _stabilize_ring_coords(poly)
        out["zones_built"] = len(zones)
        mrow = pd.Series({"building_id": (bid.replace("/", "_") if SIDE != "none" else stem), "osm_id": bid, "archetype_id": prep["archetype_id"],
                          "building_type": prep["building_type"], "age_band": prep["age_band"], "geometry": footprint})
        ctx = build_european_context(bid, footprint, bclean[d], MEDIAN_H, Counter())
        epw = next((EV / f"{d}_win_2026-10-06" / "weather").glob("*.epw"))
        run_dir = SCRATCH / LABEL / FRAME / stem
        if SIDE == "fork":
            path, verdict, nmis = fork_build(zones, run_dir, bid.replace("/", "_"), epw)
            out["fork_verdict"] = verdict
            out["fork_gate_mismatch_pairs"] = nmis
        else:
            path = build_idf_for_building(mrow, record, zones, run_dir, epw_path=epw, context=ctx)
        out["status"] = "ok"
        out["fallback_tag"] = next((z["fallback_reason"] for z in zones if z.get("fallback_reason")), "")
        out["gen_note"] = next((z["generation_status_note"] for z in zones if z.get("generation_status_note")), "")
        out["idf"] = str(path)
        out.update(idf_metrics(GeomIDF(str(path))))
    except Exception as exc:
        out["status"] = "raised"
        out["error"] = (type(exc).__name__ + ": " + str(exc))[:400].replace("\n", " ")
    out["seconds"] = round(time.time() - t0, 1)
    rows.append(out)
    print(LABEL, FRAME, d, bid, out["status"], out.get("error", "")[:90], out["seconds"], flush=True)
    pd.DataFrame(rows).to_csv(OUTCSV, index=False)
