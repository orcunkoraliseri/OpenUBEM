"""Update docs/docs_ACTIVE/europeanLocations/outputs_3D/ with harvested simulation results and new 3D geometry.

Reads:
- IDFs from openubem/outputs/eu_evidence/EU-11/<DISTRICT>_finding249_remedy_2026-09-04/idfs/
- Manifest from openubem/outputs/eu_evidence/EU-11/<DISTRICT>_finding249_remedy_2026-09-04/<district>_manifest.csv
- Summary from openubem/outputs/eu_evidence/EU-11/<DISTRICT>_finding249_remedy_2026-09-04/summary.json

Updates and mirrors:
- docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_<DISTRICT>_viewer.html
- docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_<DISTRICT>_data/buildings.csv
- docs/docs_ACTIVE/europeanLocations/outputs_3D/eu_<DISTRICT>_data/index.html
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import geopandas as gpd
import pandas as pd

from scripts.eu_idf_plan_reader import BuildingPlan, read_district
from scripts.generate_eu_3d_viewers import (
    DISTRICT_SPECS,
    HTML_HEADER_TEMPLATE,
    HTML_FOOTER,
    _build_plan_payload,
    _file_sha256,
)

RUN_SUFFIX = "finding249_remedy_2026-09-04"
EVIDENCE_ROOT = REPO_ROOT / "openubem" / "outputs" / "eu_evidence" / "EU-11"
OUT_DIR_3D = REPO_ROOT / "openubem" / "outputs" / "3D"
MIRROR_DIR_3D = REPO_ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "outputs_3D"


def update_district_viewer(district: str) -> None:
    spec = DISTRICT_SPECS[district]
    data_dir_name = f"eu_{district}_data"
    viewer_name = f"eu_{district}_viewer.html"

    dist_evidence_dir = EVIDENCE_ROOT / f"{district}_{RUN_SUFFIX}"
    if not dist_evidence_dir.exists():
        raise FileNotFoundError(f"Evidence directory not found: {dist_evidence_dir}")

    target_data_dir = OUT_DIR_3D / data_dir_name
    target_data_dir.mkdir(parents=True, exist_ok=True)

    # Load EU-02 spatial manifests
    eu02_dir = REPO_ROOT / "openubem" / "outputs" / "eu02" / district
    res_gpkg_path = eu02_dir / "02_residential_manifest.gpkg"
    exc_gpkg_path = eu02_dir / "02_excluded_manifest.gpkg"
    res_gdf = gpd.read_file(res_gpkg_path)
    exc_gdf = gpd.read_file(exc_gpkg_path)
    res_gdf["class"] = "residential"
    exc_gdf["class"] = "excluded"
    combined_gdf = pd.concat([res_gdf, exc_gdf], ignore_index=True)

    all_geoms = list(combined_gdf.geometry)
    minx = min(g.bounds[0] for g in all_geoms)
    miny = min(g.bounds[1] for g in all_geoms)
    maxx = max(g.bounds[2] for g in all_geoms)
    maxy = max(g.bounds[3] for g in all_geoms)
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    span = round(float(max(maxx - minx, maxy - miny)), 1)

    heights, height_sources, prov_codes = [], [], []
    for _, row in combined_gdf.iterrows():
        hm = row.get("height_m")
        lvl = row.get("levels")
        if pd.notna(hm) and float(hm) > 0:
            heights.append(round(float(hm), 1))
            height_sources.append("measured (source)")
            prov_codes.append(0)
        elif pd.notna(lvl) and float(lvl) > 0:
            heights.append(round(float(lvl) * 3.0, 1))
            height_sources.append("storeys x 3.0 m")
            prov_codes.append(1)
        else:
            heights.append(9.0)
            height_sources.append("assumed 9.0 m")
            prov_codes.append(2)

    combined_gdf["height_m"] = heights
    combined_gdf["height_source"] = height_sources
    combined_gdf["provenance_code"] = prov_codes

    # Load simulation manifest if available
    manifest_csv = dist_evidence_dir / f"{district}_manifest.csv"
    sim_data: dict[str, dict[str, Any]] = {}
    if manifest_csv.exists():
        m_df = pd.read_csv(manifest_csv, dtype={"building_id": str})
        for _, m_row in m_df.iterrows():
            bid = str(m_row["building_id"])
            sim_data[bid] = {
                "eui_kwh_m2": m_row.get("eui_kwh_m2"),
                "heating_kwh": m_row.get("heating_kwh"),
                "eplus_return_code": m_row.get("eplus_return_code"),
                "severe_errors": m_row.get("severe_errors"),
                "fatal_errors": m_row.get("fatal_errors"),
                "run_seconds": m_row.get("run_seconds"),
            }

    # Load plans directly from the remedy IDFs
    print(f"[{district}] Reading IDFs from {dist_evidence_dir / 'idfs'} ...")
    plans_by_id: dict[str, BuildingPlan] = {
        p.building_id: p for p in read_district(district, dist_evidence_dir)
    }

    # Existing footprint rings
    existing_html = OUT_DIR_3D / viewer_name
    existing_rings: list[list[list[float]]] = []
    if existing_html.exists():
        try:
            txt = existing_html.read_text(encoding="utf-8")
            tag = '<script type="application/json" id="scene">'
            i1 = txt.find(tag) + len(tag)
            i2 = txt.find("</script>", i1)
            prev_scene = json.loads(txt[i1:i2])
            existing_rings = [b["r"] for b in prev_scene["buildings"]]
        except Exception:
            existing_rings = []

    scene_buildings: list[dict[str, Any]] = []
    buildings_csv_rows: list[dict[str, Any]] = []
    ruled_count = massing_count = no_idf_count = 0

    for i, row in combined_gdf.iterrows():
        bid = str(row["osm_id"])
        is_res = (row["class"] == "residential")
        c = 0 if is_res else 1
        h = float(row["height_m"])
        p = int(row["provenance_code"])
        tag = str(row["building_tag"]) if pd.notna(row.get("building_tag")) else ""
        area = round(float(row["footprint_area_m2"]), 1) if pd.notna(row.get("footprint_area_m2")) else 0.0
        levels = int(row["levels"]) if (pd.notna(row.get("levels")) and float(row["levels"]) > 0) else None
        year = int(row["year_built"]) if (pd.notna(row.get("year_built")) and float(row["year_built"]) > 0) else None

        if i < len(existing_rings):
            ring = existing_rings[i]
        else:
            poly = row.geometry
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda pg: pg.area)
            poly_s = poly.simplify(0.05, preserve_topology=True)
            ring = [[round(pt[0] - cx, 2), round(pt[1] - cy, 2)] for pt in list(poly_s.exterior.coords)[:-1]]

        layout_state: str | None = None
        pl_obj: dict[str, Any] | None = None
        if is_res:
            plan = plans_by_id.get(bid)
            if plan is None or not plan.zones:
                layout_state = "no_idf"
                no_idf_count += 1
            elif plan.is_ruled():
                layout_state = "ruled"
                ruled_count += 1
                idf_path = dist_evidence_dir / "idfs" / f"{plan.stem}.idf"
                pl_obj = _build_plan_payload(plan, idf_path, None, cx, cy)
            else:
                layout_state = "massing_box"
                massing_count += 1
                idf_path = dist_evidence_dir / "idfs" / f"{plan.stem}.idf"
                pl_obj = _build_plan_payload(plan, idf_path, None, cx, cy)

        s_info = sim_data.get(bid, {})
        eui_val = s_info.get("eui_kwh_m2")
        eui_num = float(eui_val) if pd.notna(eui_val) else None
        hkwh_val = s_info.get("heating_kwh")
        hkwh_num = float(hkwh_val) if pd.notna(hkwh_val) else None

        b_obj: dict[str, Any] = {
            "r": ring,
            "h": h,
            "p": p,
            "c": c,
            "id": bid,
            "t": tag,
            "a": area,
            "l": levels,
            "y": year,
            "ls": layout_state,
            "pl": pl_obj,
            "eui": round(eui_num, 1) if eui_num is not None else None,
            "rc": s_info.get("eplus_return_code") if pd.notna(s_info.get("eplus_return_code")) else None,
        }
        scene_buildings.append(b_obj)

        buildings_csv_rows.append({
            "building_id": bid,
            "class": row["class"],
            "building_tag": tag,
            "footprint_area_m2": area,
            "levels": levels,
            "height_m": h,
            "height_source": row["height_source"],
            "year_built": year,
            "layout_state": layout_state if layout_state is not None else "",
            "storey_count": pl_obj["st"] if pl_obj else "",
            "dwelling_count": pl_obj["dw"] if pl_obj else "",
            "gross_area_m2": pl_obj["gm"] if pl_obj else "",
            "conditioned_area_m2": pl_obj["cm"] if pl_obj else "",
            "circulation_pct": pl_obj["cp"] if pl_obj else "",
            "eplus_return_code": s_info.get("eplus_return_code", ""),
            "heating_kwh": round(hkwh_num, 1) if hkwh_num is not None else "",
            "eui_kwh_m2": round(eui_num, 2) if eui_num is not None else "",
            "run_seconds": s_info.get("run_seconds", ""),
        })

    n_res = len(res_gdf)
    n_exc = len(exc_gdf)

    # Compute district summary metrics
    valid_euis = [b["eui"] for b in scene_buildings if b.get("eui") is not None]
    mean_eui = round(sum(valid_euis) / len(valid_euis), 1) if valid_euis else 0.0
    n_sim_rc0 = sum(1 for b in scene_buildings if b.get("rc") == 0)

    scene_dict = {
        "cell": district,
        "name": spec["name"],
        "place": spec["place"],
        "crs": spec["crs"],
        "licence": spec["licence"],
        "layer": spec["layer"],
        "endpoint": spec["endpoint"],
        "n_res": n_res,
        "n_exc": n_exc,
        "cx": round(cx, 2),
        "cy": round(cy, 2),
        "span": span,
        "counts": {
            "measured": int((combined_gdf["provenance_code"] == 0).sum()),
            "levels": int((combined_gdf["provenance_code"] == 1).sum()),
            "assumed": int((combined_gdf["provenance_code"] == 2).sum()),
        },
        "data_dir": data_dir_name,
        "layout_counts": {
            "ruled": ruled_count,
            "massing_box": massing_count,
            "no_idf": no_idf_count,
        },
        "simulation_summary": {
            "n_completed_rc0": n_sim_rc0,
            "mean_eui_kwh_m2": mean_eui,
        },
        "buildings": scene_buildings,
    }

    # Write buildings.csv
    csv_df = pd.DataFrame(buildings_csv_rows)
    csv_path = target_data_dir / "buildings.csv"
    csv_df.to_csv(csv_path, index=False)
    print(f"[{district}] Written {len(csv_df)} rows to {csv_path}")

    # Build and write HTML viewer
    page_title = f"{spec['name']} -- 3D Building Simulation & Dwelling Layouts"
    hud_sub = f"{spec['place']} -- {n_res:,} residential buildings -- Simulated Energy Demand & Floor Plans"
    callout_html = (
        f"<b>EU-19 Resimulation Campaign ({RUN_SUFFIX}).</b> {n_sim_rc0:,}/{n_res:,} simulated clean (RC=0). "
        f"District Mean Heating EUI: <b>{mean_eui} kWh/m²</b>. "
        f"{ruled_count:,} carry an emitted no-core dwelling layout, {massing_count:,} simulated as per-storey massing."
    )

    html_content = (
        HTML_HEADER_TEMPLATE.format(page_title=spec["page_title"])
        + json.dumps(scene_dict, separators=(",", ":"), ensure_ascii=False)
        + HTML_FOOTER
    )
    viewer_path = OUT_DIR_3D / viewer_name
    viewer_path.write_text(html_content, encoding="utf-8")
    print(f"[{district}] Written HTML viewer -> {viewer_path} ({len(html_content)} bytes)")

    # Mirror to docs/docs_ACTIVE/europeanLocations/outputs_3D/
    MIRROR_DIR_3D.mkdir(parents=True, exist_ok=True)
    mirror_viewer = MIRROR_DIR_3D / viewer_name
    shutil.copy2(viewer_path, mirror_viewer)

    mirror_data_dir = MIRROR_DIR_3D / data_dir_name
    if mirror_data_dir.exists():
        shutil.rmtree(mirror_data_dir)
    shutil.copytree(target_data_dir, mirror_data_dir)
    print(f"[{district}] Successfully updated and mirrored to {MIRROR_DIR_3D}")


def main():
    parser = argparse.ArgumentParser(description="Update 3D viewers and data with simulation results")
    parser.add_argument("--district", choices=list(DISTRICT_SPECS.keys()), help="Update single district")
    parser.add_argument("--all", action="store_true", help="Update all districts")
    args = parser.parse_args()

    districts = list(DISTRICT_SPECS.keys()) if args.all else ([args.district] if args.district else list(DISTRICT_SPECS.keys()))
    for d in districts:
        update_district_viewer(d)


if __name__ == "__main__":
    main()
