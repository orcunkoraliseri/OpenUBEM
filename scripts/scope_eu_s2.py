"""Measure, but do not yet execute, the EU-04 S2 32-building ladder.

S2 requires old/new and high/low data-completeness coverage.  This script
measures those strata over the complete retained Lyon manifest and then
re-applies the real-footprint layout contract to every mapping-ready row.
It deliberately does not select an outcome-balanced sample or run EnergyPlus.
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.geometry.european_residential import (
    allocate_european_dwellings,
    generate_european_dwelling_layout,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "openubem/outputs/eu02/FR-LYO-HAUTCOEURPENTES/02_residential_manifest.gpkg"
READINESS = ROOT / "openubem/outputs/eu_evidence/EU-04/observed_archetype_mapping_readiness.csv"
OUT = ROOT / "openubem/outputs/eu_evidence/EU-04"


def _age_band(year: object) -> str:
    if pd.isna(year):
        return "UNKNOWN_YEAR"
    return "OLD_PRE_1945" if int(year) <= 1945 else "NEW_POST_1945"


def _shape_class(geometry) -> str:
    if geometry is None:
        return "NO_RETAINED_GEOMETRY"
    if geometry.geom_type != "Polygon":
        return "MULTIPART"
    convex = abs(float(geometry.convex_hull.area) - float(geometry.area)) <= 1e-8
    return "SIMPLE_CONVEX" if convex and not geometry.interiors else "IRREGULAR_OR_COURTYARD"


def measure() -> tuple[pd.DataFrame, dict[str, object]]:
    readiness = pd.read_csv(READINESS)
    manifest = gpd.read_file(MANIFEST)
    manifest["building_id"] = manifest["osm_id"].astype(str)
    rows = readiness.merge(
        manifest[["building_id", "levels", "height_m", "surplus_tags", "geometry"]],
        on="building_id",
        how="left",
        validate="one_to_one",
    )
    rows["completeness_band"] = rows["layout_ready"].map({True: "HIGH_MAPPING_INPUT_COMPLETENESS", False: "LOW_OR_INCOMPLETE_MAPPING_INPUTS"})
    rows["age_band"] = rows["year_built"].map(_age_band)
    rows["shape_class"] = rows["geometry"].map(_shape_class)
    rows["observed_storeys"] = pd.to_numeric(rows["levels"], errors="coerce")
    rows["observed_dwellings"] = rows["surplus_tags"].map(
        lambda raw: (
            float(json.loads(raw).get("nombre_de_logements"))
            if isinstance(raw, str) and json.loads(raw).get("nombre_de_logements") not in (None, "")
            else float("nan")
        )
    )
    rows["layout_status_measured"] = "NOT_ATTEMPTED_MAPPING_BLOCKED"
    rows["layout_reason_measured"] = rows["reason"].fillna("")
    rows["units_per_floor_measured"] = pd.NA

    for index, row in rows.loc[rows["layout_ready"]].iterrows():
        allocation = allocate_european_dwellings(
            archetype_id=str(row["archetype_id"]),
            building_type=str(row["building_type"]),
            n_apartment=int(row["observed_dwellings"]),
            n_storey=int(row["observed_storeys"]),
            plate_area_m2=float(row["geometry"].area),
        )
        rows.at[index, "units_per_floor_measured"] = allocation.units_per_floor
        layout = generate_european_dwelling_layout(
            row["geometry"], requested_dwelling_count=allocation.units_per_floor
        )
        if layout.dwelling_layout_emitted:
            rows.at[index, "layout_status_measured"] = "DWELLING_LAYOUT_EMITTED"
            rows.at[index, "layout_reason_measured"] = ""
        else:
            rows.at[index, "layout_status_measured"] = "FALLBACK_PENDING_LAYOUT"
            rows.at[index, "layout_reason_measured"] = layout.fallback_reason or ""

    target = rows.loc[
        rows["building_type"].notna() & rows["age_band"].isin(["OLD_PRE_1945", "NEW_POST_1945"])
    ].copy()
    target["stratum"] = (
        target["building_type"].astype(str) + "|" + target["age_band"] + "|" + target["completeness_band"]
    )
    stratum_counts = target.groupby("stratum", dropna=False).size().sort_index().to_dict()
    feasible_32 = all(int(stratum_counts.get(stratum, 0)) >= 2 for stratum in sorted({
        f"{building_type}|{age}|{completeness}"
        for building_type in ("SFH", "TH", "MFH", "AB")
        for age in ("OLD_PRE_1945", "NEW_POST_1945")
        for completeness in ("HIGH_MAPPING_INPUT_COMPLETENESS", "LOW_OR_INCOMPLETE_MAPPING_INPUTS")
    }))
    summary = {
        "manifest_rows": int(len(rows)),
        "mapping_ready_rows": int(rows["layout_ready"].sum()),
        "mapping_incomplete_rows": int((~rows["layout_ready"]).sum()),
        "layout_emitted_rows": int((rows["layout_status_measured"] == "DWELLING_LAYOUT_EMITTED").sum()),
        "layout_fallback_rows": int((rows["layout_status_measured"] == "FALLBACK_PENDING_LAYOUT").sum()),
        "layout_reason_counts": rows.loc[rows["layout_status_measured"] == "FALLBACK_PENDING_LAYOUT", "layout_reason_measured"].value_counts().to_dict(),
        "mapping_ready_by_type": rows.loc[rows["layout_ready"], "building_type"].value_counts().sort_index().to_dict(),
        "mapping_ready_by_age": rows.loc[rows["layout_ready"], "age_band"].value_counts().sort_index().to_dict(),
        "stratum_counts_for_old_new_typed_rows": {str(k): int(v) for k, v in stratum_counts.items()},
        "s2_target_cases": 32,
        "s2_target_rule": "2 rows per type x age band x completeness band cell; building_id order; measurement only",
        "s2_target_formable": bool(feasible_32),
        "interpretation": "High/low completeness is measured at mapping-input level; layout-ready rows are high, all excluded rows are low/incomplete. No outcome-balanced selection is made.",
    }
    keep = [
        "neighbourhood_id", "building_id", "building_type", "year_built", "archetype_id",
        "mapping_status", "reason", "layout_ready", "type_provenance", "age_band",
        "completeness_band", "shape_class", "observed_dwellings", "observed_storeys",
        "units_per_floor_measured", "layout_status_measured", "layout_reason_measured",
    ]
    return rows[keep], summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    census, summary = measure()
    census.to_csv(OUT / "s2_scope_measurement.csv", index=False)
    (OUT / "s2_scope_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
