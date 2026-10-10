from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests  # noqa: E402
from openubem.acquisition.footprint_schema import finalize_footprints  # noqa: E402

SITE = "CA-MTL-PLATEAU"
SOURCE = "MTL_ROLE"
EXPECTED_CRS = "EPSG:32618"
BOROUGH_NAME = "Le Plateau-Mont-Royal"
LICENCE = "CC BY 4.0, Ville de Montreal (Batiments 2D 2016; Unites d'evaluation fonciere); Statistics Canada boundary files under the Open Government Licence - Canada"
ENDPOINT = "https://donnees.montreal.ca/dataset/batiment-2d ; https://donnees.montreal.ca/dataset/unites-evaluation-fonciere"
LAYER = "CARTO_BAT_TOIT (Batiments 2D 2016) joined to uniteevaluationfonciere.geojson"
EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-22" / SITE
EU02 = ROOT / "openubem" / "outputs" / "eu02" / SITE
RAW = EVIDENCE / "raw"
ROOF_GPKG = RAW / "batiment-2d" / "CARTO_BAT_TOIT.gpkg"
ROOF_ZIP = RAW / "batiment-2d" / "batiments_2d_2016_arrondissements_gpkg.zip"
ROLL_GEOJSON = RAW / "role-evaluation" / "uniteevaluationfonciere.geojson"
ROLL_ZIP = RAW / "role-evaluation" / "uniteevaluationfonciere.geojson.zip"
LIMITS = RAW / "limites-admin" / "limites-administratives-agglomeration-nad83.geojson"
CT_SHP = RAW / "statcan-ct" / "lct_000a21a_e.shp"
CROSSWALK = {"residential": "residential", "non_residential": "non_residential", "unknown": "unknown"}
RES_LOW, RES_HIGH = 1000, 1999
MIN_YEAR = 1600
MISSING_YEAR = 9999
LOW, HIGH = 500, 1000
TOUCH_TOL_M = 0.3
MIN_PIECE_M2 = 15.0


def clean_count(value) -> float:
    if value is None or pd.isna(value):
        return np.nan
    number = float(value)
    return number if number > 0 else np.nan


def clean_year(value) -> float:
    if value is None or pd.isna(value):
        return np.nan
    number = float(value)
    if number == MISSING_YEAR or number < MIN_YEAR:
        return np.nan
    return number


def parse_code(value) -> float:
    if value is None or pd.isna(value):
        return np.nan
    try:
        return float(int(str(value).strip()))
    except ValueError:
        return np.nan


def is_residential_code(code) -> bool:
    return not pd.isna(code) and RES_LOW <= code <= RES_HIGH


def _mode_year(years: pd.Series) -> float:
    years = years.dropna()
    if years.empty:
        return np.nan
    counts = years.value_counts()
    return float(sorted(counts[counts == counts.max()].index)[0])


def _mode_code(codes: pd.Series) -> float:
    codes = codes.dropna()
    if codes.empty:
        return np.nan
    counts = codes.value_counts()
    return float(sorted(counts[counts == counts.max()].index)[0])


def aggregate_lots(roll: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    df = roll.copy()
    df["_wkb"] = df.geometry.to_wkb()
    df["_code"] = df["CODE_UTILISATION"].map(parse_code)
    df["_res"] = df["_code"].map(is_residential_code)
    df["_storeys"] = df["ETAGE_HORS_SOL"].map(clean_count)
    df["_dw"] = df["NOMBRE_LOGEMENT"].map(clean_count)
    df["_year"] = df["ANNEE_CONSTRUCTION"].map(clean_year)
    rows = []
    for _, grp in df.groupby("_wkb", sort=False):
        res = grp[grp["_res"]]
        pool = res if len(res) else grp
        n_res = int(len(res))
        if n_res and res["_dw"].notna().all():
            dwellings = float(res["_dw"].sum())
        else:
            dwellings = np.nan
        code = _mode_code(pool["_code"])
        if n_res:
            use_class = "residential"
        elif pool["_code"].notna().any():
            use_class = "non_residential"
        else:
            use_class = "unknown"
        label_rows = pool[pool["_code"] == code]["LIBELLE_UTILISATION"].dropna()
        label = str(label_rows.iloc[0]) if len(label_rows) else ""
        if use_class == "residential" and not np.isnan(dwellings) and dwellings == 1 and code == RES_LOW:
            tag_single = True
        else:
            tag_single = False
        rows.append(
            {
                "n_units": int(len(grp)),
                "n_res_units": n_res,
                "n_res_units_dw_missing": int(res["_dw"].isna().sum()) if n_res else 0,
                "use_class": use_class,
                "use_code": code,
                "use_label": label,
                "year_built": _mode_year(pool["_year"]),
                "storeys": float(pool["_storeys"].max()) if pool["_storeys"].notna().any() else np.nan,
                "lot_dwellings": dwellings,
                "single_dwelling": tag_single,
                "geometry": grp.geometry.iloc[0],
            }
        )
    lots = gpd.GeoDataFrame(rows, geometry="geometry", crs=roll.crs)
    lots["lot_id"] = [f"LOT{i:06d}" for i in range(len(lots))]
    return lots


def split_largest_remainder(total: int, weights: list[float]) -> list[int]:
    n = len(weights)
    if n == 0:
        return []
    if total <= n:
        return [1] * n
    w = np.array([w if w > 0 else 1.0 for w in weights], dtype=float)
    base = np.ones(n, dtype=int)
    spare = total - n
    ideal = spare * w / w.sum()
    floors = np.floor(ideal).astype(int)
    rest = spare - int(floors.sum())
    order = sorted(range(n), key=lambda i: (-(ideal[i] - floors[i]), -w[i], i))
    out = base + floors
    for i in order[:rest]:
        out[i] += 1
    return [int(x) for x in out]


def explode_roofs(roofs: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    rows = []
    for fid, geom in zip(roofs.index, roofs.geometry):
        parts = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        for k, part in enumerate(parts):
            suffix = "" if len(parts) == 1 else f"_part{k}"
            rows.append({"osm_id": f"CA-MTL-{int(fid)}{suffix}", "geometry": part})
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=roofs.crs)


def _polygons(geom) -> list:
    if geom is None or geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        out = []
        for g in geom.geoms:
            out.extend(_polygons(g))
        return out
    return []


def split_roofs_by_lots(roofs: gpd.GeoDataFrame, lots: gpd.GeoDataFrame, *, min_area: float = MIN_PIECE_M2) -> tuple[gpd.GeoDataFrame, dict]:
    if roofs.crs != lots.crs:
        raise ValueError(f"CRS mismatch: roofs {roofs.crs} lots {lots.crs}")
    parts = explode_roofs(roofs)
    tree = lots.sindex
    lot_geoms = lots.geometry.values
    lot_ids = lots["lot_id"].values
    rows = []
    dropped, dropped_area = 0, 0.0
    roofs_split = roofs_no_lot = overlap_roofs = 0
    max_cover = 0.0
    for base, geom in zip(parts["osm_id"], parts.geometry):
        hits = [int(h) for h in tree.query(geom, predicate="intersects")]
        pieces = []
        covered = []
        for h in sorted(hits, key=lambda i: lot_ids[i]):
            inter = geom.intersection(lot_geoms[h])
            polys = _polygons(inter)
            if polys:
                covered.append(lot_geoms[h])
            for k, poly in enumerate(polys):
                pieces.append((lot_ids[h], k, len(polys), poly))
        if covered:
            rest = geom.difference(gpd.GeoSeries(covered, crs=roofs.crs).union_all())
            for k, poly in enumerate(_polygons(rest)):
                pieces.append((None, k, len(_polygons(rest)), poly))
            cover = sum(p[3].area for p in pieces if p[0] is not None) / geom.area
            max_cover = max(max_cover, cover)
            if cover > 1.005:
                overlap_roofs += 1
        else:
            roofs_no_lot += 1
            pieces.append((None, 0, 1, geom))
        kept = 0
        for lot, k, n, poly in pieces:
            if poly.area < min_area:
                dropped += 1
                dropped_area += poly.area
                continue
            tag = "NOLOT" if lot is None else str(lot)
            oid = f"{base}-{tag}" + ("" if n == 1 else f"-{k}")
            rows.append({"osm_id": oid, "lot_id": lot, "roof_id": base, "geometry": poly})
            kept += 1
        if kept > 1:
            roofs_split += 1
    out = gpd.GeoDataFrame(rows, geometry="geometry", crs=roofs.crs)
    rep = {
        "n_roof_parts": int(len(parts)),
        "n_pieces": int(len(out)),
        "pieces_dropped_under_min_area": int(dropped),
        "pieces_dropped_area_m2": round(float(dropped_area), 2),
        "min_piece_area_m2": float(min_area),
        "roofs_cut_into_several_buildings": int(roofs_split),
        "roofs_touching_no_lot": int(roofs_no_lot),
        "pieces_outside_every_lot": int(out["lot_id"].isna().sum()),
        "roofs_where_lot_pieces_overlap": int(overlap_roofs),
        "max_lot_cover_ratio": round(float(max_cover), 4),
    }
    return out, rep


def touching_flags(buildings: gpd.GeoDataFrame) -> pd.Series:
    geoms = buildings.geometry.values
    tree = gpd.GeoSeries(geoms, crs=buildings.crs).sindex
    flags = []
    for i, g in enumerate(geoms):
        hits = tree.query(g.buffer(TOUCH_TOL_M), predicate="intersects")
        flags.append(any(int(j) != i for j in hits))
    return pd.Series(flags, index=buildings.index)


def build_mapped(roofs: gpd.GeoDataFrame, lots: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, pd.DataFrame, dict]:
    b, rep = split_roofs_by_lots(roofs, lots)
    lot_attr = lots.set_index("lot_id")
    has = b["lot_id"].notna()
    touching = touching_flags(b)

    def col(name):
        return b["lot_id"].map(lot_attr[name])

    use_class = col("use_class").where(has, "unknown").fillna("unknown")
    lot_dw = col("lot_dwellings")
    single = col("single_dwelling").where(has, False).astype(bool)
    tags = ["terrace" if (single.iloc[i] and touching.iloc[i]) else "detached" if single.iloc[i] else "" for i in range(len(b))]
    out = gpd.GeoDataFrame(geometry=b.geometry, crs=b.crs)
    out["osm_id"] = b["osm_id"].values
    out["building_tag"] = tags
    out["function_tag"] = col("use_label").fillna("").astype(str).values
    out["levels"] = pd.array(col("storeys").values, dtype="float64").astype("Int64")
    out["height_m"] = pd.Series(np.nan, index=b.index, dtype="float64").values
    out["year_built"] = pd.array(col("year_built").values, dtype="float64").astype("Int64")
    out["postcode"] = None
    out["underground"] = pd.array([0] * len(b), dtype="Int64")
    out["roof_shape"] = ""
    out["roof_height_m"] = np.nan
    out["surplus_tags"] = [
        json.dumps({"lot_id": None if pd.isna(l) else str(l), "roof_id": str(r)}) for l, r in zip(b["lot_id"], b["roof_id"])
    ]
    attrs = pd.DataFrame(
        {
            "osm_id": b["osm_id"].values,
            "lot_id": b["lot_id"].values,
            "use_class": use_class.values,
            "use_code": col("use_code").values,
            "lot_dwellings": lot_dw.values,
            "touching": touching.values,
        }
    ).set_index("osm_id")
    rep["buildings_with_no_lot"] = int((~has).sum())
    return out, attrs, rep


def assign_dwellings(clean: gpd.GeoDataFrame, attrs: pd.DataFrame) -> gpd.GeoDataFrame:
    out = clean.copy()
    meta = attrs.reindex(out["osm_id"])
    out["use_class"] = meta["use_class"].values
    out["use_code"] = meta["use_code"].values
    out["lot_id"] = meta["lot_id"].values
    lot_dw = meta["lot_dwellings"].values
    observed = pd.array([pd.NA] * len(out), dtype="Int64")
    source = np.array(["missing"] * len(out), dtype=object)
    levels = out["levels"].astype(float).fillna(1.0).values
    area = out["footprint_area_m2"].values
    idx_by_lot: dict[str, list[int]] = {}
    for i, (lot, cls) in enumerate(zip(out["lot_id"], out["use_class"])):
        if isinstance(lot, str) and cls == "residential":
            idx_by_lot.setdefault(lot, []).append(i)
    ids = out["osm_id"].values
    for lot, idxs in idx_by_lot.items():
        idxs = sorted(idxs, key=lambda i: ids[i])
        total = lot_dw[idxs[0]]
        if pd.isna(total):
            continue
        counts = split_largest_remainder(int(total), [area[i] * levels[i] for i in idxs])
        for i, c in zip(idxs, counts):
            observed[i] = c
            source[i] = "observed" if len(idxs) == 1 else "observed_split"
    out["observed_dwellings"] = observed
    out["dwellings_source"] = source
    return out


def build_clean_buildings(roofs: gpd.GeoDataFrame, roll: gpd.GeoDataFrame, output_dir=None) -> tuple[gpd.GeoDataFrame, dict, gpd.GeoDataFrame]:
    lots = aggregate_lots(roll).to_crs(roofs.crs)
    mapped, attrs, rep = build_mapped(roofs, lots)
    clean = finalize_footprints(mapped, source=SOURCE, output_dir=output_dir)
    clean = assign_dwellings(clean, attrs)
    clean["provenance_geometry"] = "MTL_BATIMENT2D_SPLIT_BY_LOT"
    rep["pieces_kept_after_cleaner"] = int(len(clean))
    rep["pieces_dropped_by_shared_cleaner_under_20m2"] = int(rep["n_pieces"] - len(clean))
    rep["lots_with_several_buildings"] = int((clean[clean["lot_id"].notna()].groupby("lot_id").size() > 1).sum())
    return clean, rep, lots


def choose_subunits(ct: gpd.GeoDataFrame, residential: gpd.GeoDataFrame, borough_geom, *, low: int = LOW, high: int = HIGH) -> dict:
    ct = ct.to_crs(residential.crs).copy()
    ct["inside"] = ct.geometry.intersection(borough_geom).area / ct.geometry.area
    points = residential.geometry.representative_point()
    ct["n_res"] = [int(points.within(g).sum()) for g in ct.geometry]
    ct["area_km2"] = ct.geometry.area / 1e6
    ct["density"] = ct["n_res"] / ct["area_km2"]
    inside = ct[(ct["inside"] >= 0.5) & (ct["n_res"] > 0)].copy()
    cand = inside.sort_values("density", ascending=False).reset_index(drop=True)
    if cand.empty:
        raise ValueError("No census tracts inside the borough")
    ranking = [
        {"ctuid": r.CTUID, "residential": int(r.n_res), "area_km2": round(float(r.area_km2), 4), "per_km2": round(float(r.density), 1)}
        for r in cand.itertuples()
    ]
    first = cand.iloc[0]
    chosen, total, steps = [first.CTUID], int(first.n_res), []
    if total > high:
        raise ValueError(f"First census tract {first.CTUID} holds {total} > {high}; no lower level defined")
    union, skipped = first.geometry, []
    while total < low:
        rest = inside[~inside.CTUID.isin(chosen + skipped)]
        near = rest[rest.geometry.apply(lambda g: g.intersects(union.buffer(1.0)))].copy()
        if near.empty:
            raise ValueError(f"Only {total} residential buildings reachable; no touching census tract left")
        near["dist"] = near.geometry.centroid.distance(first.geometry.centroid)
        pick = near.sort_values("dist").iloc[0]
        if total + int(pick.n_res) > high:
            skipped.append(pick.CTUID)
            continue
        chosen.append(pick.CTUID)
        total += int(pick.n_res)
        union = union.union(pick.geometry)
        steps.append({"added": pick.CTUID, "residential": int(pick.n_res), "running_total": total})
    return {
        "chosen": chosen,
        "total": total,
        "ranking": ranking,
        "borough_total": int(points.within(borough_geom).sum()),
        "expansion_steps": steps,
        "skipped_over_cap": skipped,
    }


def dwelling_agreement(residential: gpd.GeoDataFrame, lots: gpd.GeoDataFrame, boundary_geom) -> dict:
    inside = lots[(lots["use_class"] == "residential") & lots.geometry.representative_point().within(boundary_geom)]
    roll_total = int(inside["lot_dwellings"].sum())
    site_total = int(residential["observed_dwellings"].fillna(0).sum())
    return {
        "residential_lots_in_boundary": int(len(inside)),
        "residential_lots_in_boundary_without_count": int(inside["lot_dwellings"].isna().sum()),
        "roll_dwellings_in_boundary_lots": roll_total,
        "manifest_observed_dwellings_sum": site_total,
        "site_vs_roll_ratio": round(site_total / roll_total, 4) if roll_total else None,
    }


def coverage(res: gpd.GeoDataFrame) -> dict:
    n = len(res)
    pct = lambda s: round(100.0 * float(s) / n, 2) if n else 0.0
    return {
        "n": n,
        "storeys_observed": int(res["levels"].notna().sum()), "storeys_pct": pct(res["levels"].notna().sum()),
        "year_observed": int(res["year_built"].notna().sum()), "year_pct": pct(res["year_built"].notna().sum()),
        "dwellings_observed": int(res["observed_dwellings"].notna().sum()), "dwellings_pct": pct(res["observed_dwellings"].notna().sum()),
        "use_code_observed": int(res["use_code"].notna().sum()), "use_code_pct": pct(res["use_code"].notna().sum()),
    }


def _extract(zip_path: Path, member: str, dest: Path) -> None:
    if dest.exists():
        return
    with zipfile.ZipFile(zip_path) as z:
        z.extract(member, dest.parent)


def run() -> dict:
    _extract(ROOF_ZIP, "CARTO_BAT_TOIT.gpkg", ROOF_GPKG)
    _extract(ROLL_ZIP, "uniteevaluationfonciere.geojson", ROLL_GEOJSON)
    limits = gpd.read_file(LIMITS)
    borough = limits[limits["NOM"].map(lambda s: "Plateau" in str(s))]
    if len(borough) != 1:
        raise ValueError("Plateau-Mont-Royal borough not found in the agglomeration limits")
    roofs_crs = gpd.read_file(ROOF_GPKG, rows=1).crs
    borough_roof = borough.to_crs(roofs_crs).geometry.iloc[0]
    roofs = gpd.read_file(ROOF_GPKG, bbox=tuple(borough.to_crs(roofs_crs).total_bounds), fid_as_index=True)
    n_bbox = len(roofs)
    roofs = roofs[roofs.geometry.representative_point().within(borough_roof)]
    roll_bbox = tuple(borough.to_crs(4326).total_bounds)
    roll = gpd.read_file(ROLL_GEOJSON, bbox=roll_bbox)
    clean, rep, lots = build_clean_buildings(roofs, roll, output_dir=EU02)
    if clean.crs.to_string() != EXPECTED_CRS:
        raise ValueError(f"CRS {clean.crs} != {EXPECTED_CRS}")
    ct = gpd.read_file(CT_SHP)
    borough_utm = borough.to_crs(clean.crs).geometry.iloc[0]
    sel = choose_subunits(ct, clean[clean["use_class"] == "residential"], borough_utm)
    units = ct[ct["CTUID"].isin(sel["chosen"])]
    boundary = gpd.GeoDataFrame({"site": [SITE], "units": [",".join(sel["chosen"])]}, geometry=[units.geometry.union_all()], crs=units.crs)
    boundary_path = EVIDENCE / "boundary.geojson"
    boundary.to_file(boundary_path, driver="GeoJSON")
    sha = hashlib.sha256(boundary_path.read_bytes()).hexdigest()
    (EVIDENCE / "boundary.sha256").write_text(sha + "\n", encoding="utf-8")
    clipped = clip_to_boundary(clean, boundary_path, verify_sha256=sha)
    residential, excluded, counts = split_residential(clipped, CROSSWALK, class_column="use_class")
    residential = residential.drop(columns=["use_class", "lot_id"])
    excluded = excluded.drop(columns=["use_class", "lot_id"])
    write_manifests(residential, excluded, counts, EU02, neighbourhood_id=SITE, source_endpoint=ENDPOINT, licence=LICENCE, source_layer=LAYER)
    cov = coverage(residential)
    table = {}
    for code, grp in clean.groupby(clean["use_code"].fillna(-1).astype(int)):
        table[str(code)] = {
            "label": str(grp["function_tag"].mode().iloc[0]) if len(grp) else "",
            "class": str(grp["use_class"].iloc[0]),
            "tag_detached": int((grp["building_tag"] == "detached").sum()),
            "tag_terrace": int((grp["building_tag"] == "terrace").sum()),
            "n_clean": int(len(grp)),
            "n_residential_manifest": int((residential["use_code"].fillna(-1).astype(int) == code).sum()),
        }
    roll_counts = {
        "roll_rows_in_bbox": int(len(roll)),
        "lots_distinct_polygons": int(len(lots)),
        "lots_residential": int((lots["use_class"] == "residential").sum()),
        "lots_residential_dwellings_partial_missing": int(((lots["use_class"] == "residential") & lots["lot_dwellings"].isna()).sum()),
        "roll_year_9999": int((roll["ANNEE_CONSTRUCTION"] == MISSING_YEAR).sum()),
    }
    bound_geom = boundary.to_crs(clean.crs).geometry.iloc[0]
    agree = dwelling_agreement(residential, lots.to_crs(clean.crs), bound_geom)
    roll_counts.update(agree)
    roofs_per_lot = clean[clean["lot_id"].notna()].groupby("lot_id").size()
    lots_per_roof = _lots_per_roof(roofs, lots)
    report = {
        "site": SITE, "crs": clean.crs.to_string(), "roof_source_crs": str(roofs_crs), "licence": LICENCE,
        "n_roof_bbox": int(n_bbox), "n_roof_in_borough": int(len(roofs)), "n_clean": int(len(clean)), "n_clipped": int(len(clipped)),
        "split_counts": counts, "subunits": sel, "coverage_residential": cov, "code_mapping": table, "join": rep, "roll": roll_counts,
        "dwellings_source_counts_residential": residential["dwellings_source"].value_counts().to_dict(),
        "building_id": "GeoPackage FID of CARTO_BAT_TOIT (the layer carries no building id field)",
        "roof_polygon_check": lots_per_roof,
        "buildings_per_lot_distribution": roofs_per_lot.value_counts().sort_index().head(10).to_dict(),
        "fields_used": {"storeys": "ETAGE_HORS_SOL (max over residential units)", "year": "ANNEE_CONSTRUCTION (mode over residential units)",
                        "dwellings": "NOMBRE_LOGEMENT (sum over residential units, only when every residential unit has a value)", "use": "CODE_UTILISATION"},
    }
    (EVIDENCE / "acquisition_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return report


def _lots_per_roof(roofs: gpd.GeoDataFrame, lots: gpd.GeoDataFrame) -> dict:
    lots = lots.to_crs(roofs.crs)
    lots = lots[lots.geometry.representative_point().within(roofs.geometry.union_all())]
    pts = gpd.GeoDataFrame(geometry=lots.geometry.centroid.values, crs=roofs.crs)
    r = roofs.reset_index().rename(columns={roofs.index.name or "index": "bid"})[["bid", "geometry"]]
    j = gpd.sjoin(pts, r, predicate="within", how="inner")
    per = j.groupby("bid").size()
    return {
        "roofs_holding_at_least_one_lot_centroid": int(len(per)),
        "roofs_holding_more_than_one_lot_centroid": int((per > 1).sum()),
        "median_lots_per_roof": float(per.median()) if len(per) else 0.0,
        "max_lots_per_roof": int(per.max()) if len(per) else 0,
    }


def main(argv: list[str] | None = None) -> int:
    argparse.ArgumentParser().parse_args(argv)
    report = run()
    print(json.dumps({k: report[k] for k in ("n_roof_in_borough", "n_clean", "n_clipped", "split_counts", "coverage_residential", "join", "roof_polygon_check")}, default=str))
    print(json.dumps({k: v for k, v in report["subunits"].items() if k != "ranking"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
