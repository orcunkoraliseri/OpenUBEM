from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests  # noqa: E402
from openubem.acquisition.footprint_schema import finalize_footprints  # noqa: E402

SITE = "FI-HEL-KALLIO"
SOURCE = "HELSINKI_REKISTERI"
WFS = "https://kartta.hel.fi/ws/geoserver/avoindata/wfs"
LAYER = "avoindata:Rakennukset_alue_rekisteritiedot"
LAYER_PERUSPIIRI = "avoindata:Maavesi_peruspiirit"
LAYER_OSA = "avoindata:Maavesi_osa_alueet"
PERUSPIIRI_ID = "301"
SRC_CRS = "EPSG:3879"
EXPECTED_CRS = "EPSG:32635"
LICENCE = "CC BY 4.0, City of Helsinki (Buildings in Helsinki, hri.fi/data/en/dataset/helsingin-rakennukset)"
EVIDENCE = ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-22" / SITE
EU02 = ROOT / "openubem" / "outputs" / "eu02" / SITE
CODE_TAG = {"011": "detached", "021": "terrace", "022": "terrace", "032": "apartments"}
RESIDENTIAL_PREFIXES = ("01", "02", "03", "04")
CROSSWALK = {"residential": "residential", "non_residential": "non_residential", "unknown": "unknown"}
MIN_YEAR, MAX_YEAR = 1500, 2026
LOW, HIGH = 500, 1000
TYPE_RESIDENTIAL = "Asuinrakennus"
TYPE_TAG = "tyyppi:Asuinrakennus"
MAPPED_FIELDS = {"id", "c_kayttark", "i_kerrlkm", "c_valmpvm", "i_asuinhuoneistojen_lkm", "postinumero"}


def parse_year(value) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    match = re.match(r"^\s*(\d{4})", str(value))
    if not match:
        return None
    year = int(match.group(1))
    return year if MIN_YEAR <= year <= MAX_YEAR else None


def positive_int(value) -> int | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() and number > 0 else None


def use_class_for_code(code) -> str:
    if code is None or (isinstance(code, float) and pd.isna(code)) or str(code).strip() == "":
        return "unknown"
    return "residential" if str(code).strip()[:2] in RESIDENTIAL_PREFIXES else "non_residential"


def load_code_labels(path: Path | str) -> dict[str, str]:
    items = json.loads(Path(path).read_text(encoding="utf-8"))
    return {x["code"]: x["classificationItemNames"][0]["name"] for x in items if len(x["code"]) == 3}


def map_buildings(raw: gpd.GeoDataFrame, labels: dict[str, str]) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    if raw.crs is None:
        raw = raw.set_crs(SRC_CRS)
    missing = {"id", "c_kayttark", "i_kerrlkm", "c_valmpvm", "i_asuinhuoneistojen_lkm"} - set(raw.columns)
    if missing:
        raise ValueError(f"Helsinki layer misses fields: {sorted(missing)}")
    raw = raw.reset_index(drop=True)
    code = raw["c_kayttark"].map(lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "" else str(v).strip())
    out = gpd.GeoDataFrame(geometry=raw.geometry, crs=raw.crs)
    out["osm_id"] = raw["id"].map(lambda v: f"FI-HEL-{int(v)}")
    if not out["osm_id"].is_unique:
        raise ValueError("Helsinki id values are not unique")
    out["building_tag"] = code.map(lambda c: CODE_TAG.get(c, "") if c else "")
    tyyppi = raw["tyyppi"] if "tyyppi" in raw.columns else pd.Series([None] * len(raw), index=raw.index)
    type_res = code.isna() & tyyppi.map(lambda v: isinstance(v, str) and v.strip() == TYPE_RESIDENTIAL)
    out["function_tag"] = [TYPE_TAG if tr else (labels.get(c, "") if c else "") for c, tr in zip(code, type_res)]
    out["levels"] = pd.array([positive_int(v) for v in raw["i_kerrlkm"]], dtype="Int64")
    out["height_m"] = pd.Series(float("nan"), index=raw.index, dtype="float64")
    out["year_built"] = pd.array([parse_year(v) for v in raw["c_valmpvm"]], dtype="Int64")
    out["postcode"] = raw["postinumero"].map(lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)) if "postinumero" in raw else None
    out["underground"] = pd.array([0] * len(out), dtype="Int64")
    out["roof_shape"] = ""
    out["roof_height_m"] = float("nan")
    extra = [c for c in raw.columns if c not in MAPPED_FIELDS and c != "geometry"]
    out["surplus_tags"] = [
        json.dumps({c: str(raw.at[i, c]) for c in extra if pd.notna(raw.at[i, c])}, ensure_ascii=False) for i in range(len(raw))
    ]
    attrs = pd.DataFrame(
        {
            "osm_id": out["osm_id"].values,
            "c_kayttark": code.values,
            "use_class": ["residential" if tr else use_class_for_code(c) for c, tr in zip(code, type_res)],
            "observed_dwellings": pd.array([positive_int(v) for v in raw["i_asuinhuoneistojen_lkm"]], dtype="Int64"),
        }
    ).set_index("osm_id")
    return out, attrs


def split_counts(total: int, weights: list[float]) -> list[int]:
    n = len(weights)
    if total < n:
        order = sorted(range(n), key=lambda i: -weights[i])
        return [1 if i in order[:total] else 0 for i in range(n)]
    wsum = float(sum(weights))
    ideal = [total * w / wsum for w in weights] if wsum > 0 else [total / n] * n
    counts = [int(x) for x in ideal]
    for i in sorted(range(n), key=lambda i: -(ideal[i] - counts[i]))[: total - sum(counts)]:
        counts[i] += 1
    for i in range(n):
        while counts[i] < 1:
            donor = max(range(n), key=lambda j: counts[j])
            counts[donor] -= 1
            counts[i] += 1
    return counts


def split_part_dwellings(gdf: gpd.GeoDataFrame, base: pd.Series) -> pd.array:
    values = gdf["observed_dwellings"].astype("Int64").copy()
    area = gdf["footprint_area_m2"] if "footprint_area_m2" in gdf.columns else gdf.geometry.area
    levels = gdf["levels"].astype("float64").fillna(1.0) if "levels" in gdf.columns else pd.Series(1.0, index=gdf.index)
    is_part = gdf["osm_id"].str.contains(r"_part\d+$")
    for _, idx in gdf[is_part].groupby(base[is_part]).groups.items():
        idx = list(idx)
        total = values.loc[idx[0]]
        if pd.isna(total) or len(idx) < 2:
            continue
        counts = split_counts(int(total), [float(area.loc[i] * levels.loc[i]) for i in idx])
        for i, c in zip(idx, counts):
            values.loc[i] = c if c > 0 else pd.NA
    return pd.array(values.values, dtype="Int64")


def attach_attributes(gdf: gpd.GeoDataFrame, attrs: pd.DataFrame) -> gpd.GeoDataFrame:
    base = gdf["osm_id"].str.replace(r"_part\d+$", "", regex=True)
    out = gdf.copy()
    out["observed_dwellings"] = pd.array(attrs["observed_dwellings"].reindex(base).values, dtype="Int64")
    out["observed_dwellings"] = split_part_dwellings(out, base)
    out["c_kayttark"] = attrs["c_kayttark"].reindex(base).values
    out["use_class"] = attrs["use_class"].reindex(base).values
    return out


def _expand_whole_district(osa, points, district, ranking, district_total: int, *, low: int, high: int) -> dict:
    inside_ids = osa[osa["inside"] >= 0.5].tunnus.tolist()
    ring = osa[(osa["inside"] < 0.5) & osa.geometry.apply(lambda g: g.intersects(district.buffer(1.0)))].copy()
    ring["outside_geom"] = ring.geometry.apply(lambda g: g.difference(district))
    ring["n_out"] = [int(points.within(g).sum()) for g in ring["outside_geom"]]
    ring["dist"] = ring.geometry.centroid.distance(district.centroid)
    ring = ring.sort_values("dist")
    chosen, total, steps, skipped, union = [], district_total, [], [], district
    for r in ring.itertuples():
        if total >= low:
            break
        if r.n_out == 0:
            continue
        if total + r.n_out > high:
            skipped.append(r.tunnus)
            continue
        chosen.append(r.tunnus)
        total += r.n_out
        union = union.union(r.outside_geom)
        steps.append({"added": r.tunnus, "nimi_fi": r.nimi_fi, "residential": r.n_out, "running_total": total, "inside_district": False, "dist_to_district_centroid_m": round(float(r.dist), 1)})
    if total < low:
        raise ValueError(f"Only {total} residential buildings reachable; no touching sub-unit left")
    return {
        "mode": "whole_district_plus_touching_outside", "district_whole": True, "district_total": district_total, "inside_units": inside_ids,
        "chosen": inside_ids + chosen, "added_outside": chosen, "total": total, "ranking": ranking, "expansion_steps": steps, "skipped_over_cap": skipped,
        "boundary_geom": union,
    }


def choose_subunits(osa: gpd.GeoDataFrame, residential: gpd.GeoDataFrame, district_geom, *, low: int = LOW, high: int = HIGH) -> dict:
    osa = osa.to_crs(residential.crs).copy()
    district = gpd.GeoSeries([district_geom], crs=SRC_CRS).to_crs(residential.crs).iloc[0]
    osa["inside"] = osa.geometry.intersection(district).area / osa.geometry.area
    points = residential.geometry.representative_point()
    osa["n_res"] = [int(points.within(g).sum()) for g in osa.geometry]
    osa["area_km2"] = osa.geometry.area / 1e6
    osa["density"] = osa["n_res"] / osa["area_km2"]
    cand = osa[(osa["inside"] >= 0.5) & (osa["n_res"] > 0)].sort_values("density", ascending=False).reset_index(drop=True)
    if cand.empty:
        raise ValueError("No sub-unit candidates inside the district")
    ranking = [
        {"tunnus": r.tunnus, "nimi_fi": r.nimi_fi, "residential": int(r.n_res), "area_km2": round(float(r.area_km2), 4), "per_km2": round(float(r.density), 1)}
        for r in cand.itertuples()
    ]
    district_total = int(points.within(district).sum())
    if district_total < low:
        return _expand_whole_district(osa, points, district, ranking, district_total, low=low, high=high)
    first = cand.iloc[0]
    chosen, total, steps = [first.tunnus], int(first.n_res), []
    if total > high:
        raise ValueError(f"First sub-unit {first.tunnus} holds {total} > {high} residential buildings; no lower level defined")
    union, skipped = first.geometry, []
    pool = osa[osa["n_res"] > 0]
    while total < low:
        rest = pool[~pool.tunnus.isin(chosen + skipped)]
        near = rest[rest.geometry.apply(lambda g: g.intersects(union.buffer(1.0)))].copy()
        if near.empty:
            raise ValueError(f"Only {total} residential buildings reachable; no touching sub-unit left")
        near["dist"] = near.geometry.centroid.distance(first.geometry.centroid)
        pick = near.sort_values("dist").iloc[0]
        if total + int(pick.n_res) > high:
            skipped.append(pick.tunnus)
            continue
        chosen.append(pick.tunnus)
        total += int(pick.n_res)
        union = union.union(pick.geometry)
        steps.append({"added": pick.tunnus, "nimi_fi": pick.nimi_fi, "residential": int(pick.n_res), "running_total": total, "inside_district": bool(pick.inside >= 0.5)})
    return {"chosen": chosen, "total": total, "ranking": ranking, "district_total": district_total, "expansion_steps": steps, "skipped_over_cap": skipped}


def _paged(layer: str, bbox: tuple, out_dir: Path, page: int = 1000) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    base = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": layer, "srsName": SRC_CRS,
        "outputFormat": "application/json", "sortBy": "id", "count": page,
        "bbox": ",".join(f"{v:.0f}" for v in bbox) + f",{SRC_CRS}",
    }
    paths, i = [], 0
    while True:
        response = requests.get(WFS, params={**base, "startIndex": i * page}, timeout=180)
        response.raise_for_status()
        path = out_dir / f"p{i}.json"
        path.write_bytes(response.content)
        paths.append(path)
        if len(response.json()["features"]) < page:
            return paths
        i += 1


def _fetch_layer(layer: str, dest: Path) -> None:
    response = requests.get(
        WFS, params={"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": layer, "srsName": SRC_CRS, "outputFormat": "application/json"}, timeout=180
    )
    response.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(response.content)


def read_pages(*pages_dirs: Path) -> gpd.GeoDataFrame:
    features, seen = [], set()
    for pages_dir in pages_dirs:
        paths = sorted(glob.glob(str(pages_dir / "p*.json")), key=lambda s: int(re.search(r"p(\d+)\.json$", s).group(1)))
        for p in paths:
            for f in json.loads(Path(p).read_text(encoding="utf-8"))["features"]:
                key = f["properties"]["id"]
                if key not in seen:
                    seen.add(key)
                    features.append(f)
    return gpd.GeoDataFrame.from_features(features, crs=SRC_CRS)


def ring_bounds(osa: gpd.GeoDataFrame, district_geom) -> tuple:
    ring = osa[osa.geometry.apply(lambda g: g.intersects(district_geom.buffer(1.0)))]
    return tuple(ring.total_bounds)


def coverage(res: gpd.GeoDataFrame) -> dict:
    n = len(res)
    pct = lambda s: round(100.0 * float(s) / n, 2) if n else 0.0
    return {
        "n": n,
        "storeys_observed": int(res["levels"].notna().sum()), "storeys_pct": pct(res["levels"].notna().sum()),
        "year_observed": int(res["year_built"].notna().sum()), "year_pct": pct(res["year_built"].notna().sum()),
        "dwellings_observed": int(res["observed_dwellings"].notna().sum()), "dwellings_pct": pct(res["observed_dwellings"].notna().sum()),
        "use_code_observed": int(res["c_kayttark"].notna().sum()), "use_code_pct": pct(res["c_kayttark"].notna().sum()),
    }


def run(refresh: bool = False) -> dict:
    raw_dir = EVIDENCE / "raw" / "helsinki_wfs"
    peru_path, osa_path, pages = raw_dir / "peruspiirit.json", raw_dir / "osa_alueet.json", raw_dir / "pages"
    if refresh or not peru_path.exists():
        _fetch_layer(LAYER_PERUSPIIRI, peru_path)
    if refresh or not osa_path.exists():
        _fetch_layer(LAYER_OSA, osa_path)
    peru = gpd.read_file(peru_path)
    peru = peru[peru["tunnus"] == PERUSPIIRI_ID]
    if len(peru) != 1:
        raise ValueError("Kallio peruspiiri not found")
    district_geom = peru.geometry.iloc[0]
    if refresh or not list(pages.glob("p*.json")):
        _paged(LAYER, tuple(peru.total_bounds), pages)
    osa = gpd.read_file(osa_path)
    pages_ring = raw_dir / "pages_ring"
    covered = tuple(peru.total_bounds)
    need = ring_bounds(osa, district_geom)
    if refresh or (not list(pages_ring.glob("p*.json")) and not (need[0] >= covered[0] - 1 and need[1] >= covered[1] - 1 and need[2] <= covered[2] + 1 and need[3] <= covered[3] + 1)):
        _paged(LAYER, need, pages_ring)
    labels = load_code_labels(EVIDENCE / "raw" / "statfi_classification" / "rakennus_1_19940101.json")
    raw = read_pages(pages, pages_ring)
    mapped, attrs = map_buildings(raw, labels)
    clean = finalize_footprints(mapped, source=SOURCE, output_dir=EU02)
    if clean.crs.to_string() != EXPECTED_CRS:
        raise ValueError(f"CRS {clean.crs} != {EXPECTED_CRS}")
    clean = attach_attributes(clean, attrs)
    sel = choose_subunits(osa, clean[clean["use_class"] == "residential"], district_geom)
    boundary_geom = sel.pop("boundary_geom", None)
    if boundary_geom is not None:
        boundary_geom = gpd.GeoSeries([boundary_geom], crs=clean.crs).to_crs(SRC_CRS).iloc[0]
    else:
        boundary_geom = osa[osa["tunnus"].isin(sel["chosen"])].geometry.union_all()
    boundary = gpd.GeoDataFrame({"site": [SITE], "units": [",".join(sel["chosen"])]}, geometry=[boundary_geom], crs=SRC_CRS)
    boundary_path = EVIDENCE / "boundary.geojson"
    boundary.to_file(boundary_path, driver="GeoJSON")
    sha = hashlib.sha256(boundary_path.read_bytes()).hexdigest()
    (EVIDENCE / "boundary.sha256").write_text(sha + "\n", encoding="utf-8")
    clipped = clip_to_boundary(clean, boundary_path, verify_sha256=sha)
    residential, excluded, counts = split_residential(clipped, CROSSWALK, class_column="use_class")
    residential = residential.drop(columns=["use_class"])
    excluded = excluded.drop(columns=["use_class"])
    write_manifests(residential, excluded, counts, EU02, neighbourhood_id=SITE, source_endpoint=WFS, licence=LICENCE, source_layer=LAYER)
    cov = coverage(residential)
    mapping = {c: {"label": labels.get(c, ""), "tag": CODE_TAG.get(c, ""), "class": use_class_for_code(c),
                   "n_clean": int((clean["c_kayttark"] == c).sum()), "n_residential_manifest": int((residential["c_kayttark"] == c).sum())}
               for c in sorted(set(clean["c_kayttark"].dropna()))}
    report = {
        "site": SITE, "crs": clean.crs.to_string(), "licence": LICENCE, "n_downloaded": int(len(raw)), "n_clean": int(len(clean)),
        "n_clipped": int(len(clipped)), "split_counts": counts, "subunits": sel, "coverage_residential": cov, "code_mapping": mapping,
        "no_code_with_type_Asuinrakennus_in_clipped": int(((clipped["c_kayttark"].isna()) & (clipped["surplus_tags"].str.contains('"tyyppi": "Asuinrakennus"'))).sum()),
        "tyyppi_asuinrakennus_residential_in_manifest": int((residential["function_tag"] == TYPE_TAG).sum()),
        "ring_pages_downloaded": bool(list((raw_dir / "pages_ring").glob("p*.json"))),
        "multipart_parts": int(clean["osm_id"].str.contains(r"_part\d+$").sum()),
        "fields_used": {"storeys": "i_kerrlkm", "year": "c_valmpvm", "dwellings": "i_asuinhuoneistojen_lkm", "use": "c_kayttark", "id": "id"},
        "code_labels": "Statistics Finland Classification of Buildings 1994 (rakennus_1_19940101), raw/statfi_classification",
    }
    (EVIDENCE / "acquisition_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    report = run(refresh=parser.parse_args(argv).refresh)
    print(json.dumps({k: report[k] for k in ("n_downloaded", "n_clean", "n_clipped", "split_counts", "coverage_residential")}, default=str))
    print(json.dumps({k: v for k, v in report["subunits"].items() if k != "ranking"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
