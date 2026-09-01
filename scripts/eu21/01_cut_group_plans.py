import json, sys, csv, collections, statistics
sys.path.insert(0, r"C:\Users\o_iseri\Desktop\OpenUBEM")
from pathlib import Path
import geopandas as gpd
import shapely
from shapely.geometry import Polygon
from shapely.affinity import translate
from openubem.geometry.european_residential import (
    generate_european_ruled_storey_layout,
    generate_european_courtyard_perimeter_band_layout,
    generate_european_wing_spine_decomposition_layout,
    generate_european_regularized_envelope_grid_layout,
    generate_european_row_house_depth_bands_layout,
    _ray_sector_cuts,
)

ROOT = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM")
EU02 = ROOT / "openubem" / "outputs" / "eu02"
EU20 = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-20"
OUT = Path(__file__).with_name("group_plans.json")
DISTRICTS = ["ES-MAD-BERRUGUETE", "FR-LYO-HAUTCOEURPENTES", "GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2"]
ORDER = ["COURTYARD", "SLIVER", "SQUARE", "RECTANGLE", "SLAB", "TRIANGLE",
         "TRAPEZOID", "L_SHAPE", "U_OR_T_SHAPE", "COMPLEX_MULTI_WING"]
GALLERY_WIDTH_M = 1.8


def cls(r):
    if float(r["n_interior_rings"]) >= 1: return "COURTYARD"
    if float(r["min_rot_rect_w_m"]) < 8.0: return "SLIVER"
    rec, ar, rf = float(r["rectangularity"]), float(r["aspect_ratio"]), float(r["reflex_count"])
    if rec >= 0.90 and ar < 1.5: return "SQUARE"
    if rec >= 0.90 and 1.5 <= ar < 3.0: return "RECTANGLE"
    if rec >= 0.90 and ar >= 3.0: return "SLAB"
    if float(r["n_edges_ge_15pct_perimeter"]) <= 3 and rf == 0: return "TRIANGLE"
    if rf == 0 and rec < 0.90: return "TRAPEZOID"
    if rf == 1: return "L_SHAPE"
    if rf == 2: return "U_OR_T_SHAPE"
    return "COMPLEX_MULTI_WING"


PROPOSED = {
    "COURTYARD": generate_european_courtyard_perimeter_band_layout,
    "SLIVER": generate_european_row_house_depth_bands_layout,
    "L_SHAPE": generate_european_wing_spine_decomposition_layout,
    "U_OR_T_SHAPE": generate_european_wing_spine_decomposition_layout,
    "COMPLEX_MULTI_WING": generate_european_wing_spine_decomposition_layout,
    "TRIANGLE": generate_european_regularized_envelope_grid_layout,
    "TRAPEZOID": generate_european_regularized_envelope_grid_layout,
    "SQUARE": generate_european_regularized_envelope_grid_layout,
    "RECTANGLE": generate_european_regularized_envelope_grid_layout,
    "SLAB": generate_european_regularized_envelope_grid_layout,
}
NO_CORE_BY_DESIGN = {"SLIVER"}


def rings_of(geom):
    out = []
    gs = list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]
    for g in gs:
        if g.is_empty:
            continue
        out.append([list(g.exterior.coords)] + [list(i.coords) for i in g.interiors])
    return out


def capture(dwell_polys, circ_poly):
    dw, circ = [], []
    for d in dwell_polys:
        dw.extend(rings_of(d))
    if circ_poly is not None and not circ_poly.is_empty:
        for r in rings_of(circ_poly):
            circ.append(r[0])
    return dw, circ


def gallery_ring(poly, n):
    """S5 proposal: a deck-access band along the courtyard face, flats behind it."""
    if not poly.interiors:
        return None
    void = max((Polygon(r) for r in poly.interiors), key=lambda g: g.area)
    gal = poly.intersection(void.buffer(GALLERY_WIDTH_M))
    if gal.is_empty or gal.area <= 0.0:
        return None
    band = poly.difference(gal)
    if band.is_empty or band.geom_type != "Polygon":
        return None
    try:
        seg = _ray_sector_cuts(band, void.representative_point(), n)
    except (ValueError, IndexError):
        return None
    if len(seg) != n or any(s.is_empty or s.area <= 0.0 for s in seg):
        return None
    return seg, gal, "courtyard_gallery_ring"


def options(poly, n, grp):
    """Every plan this plate can carry, best (has a core) first."""
    out, refusal = [], None
    for fn, status in ((generate_european_ruled_storey_layout, "in-force"),
                       (PROPOSED.get(grp), "proposed")):
        if fn is None:
            continue
        try:
            lay = fn(poly, dwelling_count=n)
        except Exception as exc:
            refusal = refusal or type(exc).__name__
            continue
        if not lay.dwelling_layout_emitted:
            refusal = refusal or lay.fallback_reason
            continue
        out.append((lay.dwelling_polygons, lay.circulation_polygon, lay.scheme, status,
                    float(lay.circulation_area_m2)))
    if grp == "COURTYARD":
        g = gallery_ring(poly, n)
        if g is not None:
            seg, gal, name = g
            out.insert(0, (tuple(seg), gal, name, "proposed", float(gal.area)))
    out.sort(key=lambda o: 0 if o[4] > 0.05 else 1)
    return out, refusal


geoms = {}
for d in DISTRICTS:
    gdf = gpd.read_file(EU02 / d / "02_residential_manifest.gpkg")
    idcol = "building_id" if "building_id" in gdf.columns else gdf.columns[0]
    for _, row in gdf.iterrows():
        g = shapely.force_2d(row.geometry)
        if g is None or g.geom_type != "Polygon":
            continue
        geoms[(d, str(row[idcol]))] = g

rows = list(csv.DictReader(open(EU20 / "morphology_census.csv")))
bygroup = collections.defaultdict(list)
perfloor = collections.defaultdict(list)
storeys = collections.defaultdict(list)
for r in rows:
    k = cls(r)
    st = max(1, int(float(r["storeys"])))
    tot = max(1, int(float(r["dwellings_total"])))
    r["_n"] = max(1, round(tot / st))
    r["_st"] = st
    bygroup[k].append(r)
    perfloor[k].append(r["_n"])
    storeys[k].append(st)

reps = {x["group"]: x for x in json.load(open(EU20 / "representatives.json"))}

out = []
for grp in ORDER:
    med = int(statistics.median(sorted(perfloor[grp])))
    n_draw = max(2, med)
    rep_id = str(reps[grp]["building_id"])
    members = sorted(bygroup[grp], key=lambda r: (r["building_id"] != rep_id, abs(r["_n"] - n_draw)))
    best = fallback = None
    first_refusal = None
    for cand in members[:60]:
        g = geoms.get((cand["district"], cand["building_id"]))
        if g is None:
            continue
        if not g.is_valid:
            g = g.buffer(0)
            if g.geom_type != "Polygon":
                continue
        p = translate(g, -g.centroid.x, -g.centroid.y)
        opts, why = options(p, n_draw, grp)
        first_refusal = first_refusal or why
        if not opts:
            continue
        pick = (cand, p, opts[0])
        if opts[0][4] > 0.05 or grp in NO_CORE_BY_DESIGN:
            best = pick
            break
        fallback = fallback or pick
    picked = best or fallback
    if picked is None:
        print(f"{grp:<20} NO PLAN DRAWABLE at n={n_draw}")
        out.append({"group": grp, "drawn_per_floor": n_draw, "status": None})
        continue
    cand, p, (dpolys, cpoly, scheme, status, carea) = picked
    dw, circ = capture(dpolys, cpoly)
    rec = {
        "group": grp,
        "district": cand["district"],
        "building_id": cand["building_id"],
        "is_representative": cand["building_id"] == rep_id,
        "storeys": cand["_st"],
        "median_per_floor": med,
        "drawn_per_floor": n_draw,
        "median_storeys": int(statistics.median(storeys[grp])),
        "area_m2": round(float(cand["area_m2"])),
        "footprint": [list(p.exterior.coords)] + [list(i.coords) for i in p.interiors],
        "dwellings": dw,
        "circulation": circ,
        "scheme": scheme,
        "status": status,
        "circ_m2": round(carea, 1),
        "refused_first": first_refusal,
    }
    out.append(rec)
    print(f'{grp:<20} n={n_draw} {status:<9} {scheme:<30} bld={cand["building_id"][:22]:<22} '
          f'rep={rec["is_representative"]} ndw={len(dw)} circ={len(circ)} '
          f'c_m2={rec["circ_m2"]} first_refusal={first_refusal}')

json.dump(out, open(OUT, "w"), separators=(",", ":"))
print("wrote", OUT, OUT.stat().st_size, "bytes")
