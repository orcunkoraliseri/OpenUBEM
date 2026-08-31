"""Measure the EU-04 `S3` 96-building corpus over the ruled FR + ES sites.

Authority: ``D-EU-22`` (F1) settled the composition -- `S3` is **FR + ES** --
and ``D-EU-23`` (G1) settled how it is built: 96 buildings in **mixed mode**,
with the *layout* axis and the *simulation* axis recorded in separate columns
and never collapsed.  This script measures; it selects nothing and runs no
EnergyPlus.

Two axes, kept apart on purpose (the `S1` rule, `MVP` EU-04):

* ``layout_status_measured`` -- did the ruled real-footprint layout contract
  emit a dwelling partition for this footprint?
* ``simulation_mode_expected`` -- what the campaign would therefore run:
  ``EUROPEAN_DWELLING_LAYOUT`` where it emitted, else the already-ruled
  ``FALLBACK_ONE_ZONE_PER_FLOOR``.

Geometry is evaluated in each manifest's **native** CRS with no reprojection.
That is not a convenience: ``generate_european_dwelling_layout`` rotates about
the coordinate origin while the partition audit uses an absolute area
tolerance, so a reprojected corpus reports near-zero emitted layouts for the
same buildings (`S1` finding, ``OpenUBEM_debug_References.md`` ch. 5).

Usage:  .venv/Scripts/python.exe scripts/scope_eu_s3.py
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
from openubem.semantic.european_archetype_mapping import (
    apply_attribute_sidecar,
    write_eu02_archetype_mapping_readiness,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_ROOT = ROOT / "openubem/outputs/eu02"
EVIDENCE = ROOT / "openubem/outputs/eu_evidence/EU-04"
OUT = EVIDENCE / "s3"
ES_SIDECAR = EVIDENCE / "es_catastro_attribute_sidecar.csv"

#: The ruled `S3` composition (`D-EU-22` F1). Italy contributes zero under
#: every option (1,220 of 1,220 `UNMAPPABLE_RESIDENTIAL_TYPE`) and London is
#: credential-blocked, not empty -- both are recorded, neither is scoped here.
S3_SITES = {
    "FR-LYO-HAUTCOEURPENTES": "FR",
    "ES-MAD-BERRUGUETE": "ES",
}

TYPE_ORDER = ("AB", "MFH", "TH", "SFH")
AGE_ORDER = ("OLD_PRE_1945", "NEW_POST_1945")


def _age_band(year: object) -> str:
    if pd.isna(year):
        return "UNKNOWN_YEAR"
    return "OLD_PRE_1945" if int(year) <= 1945 else "NEW_POST_1945"


def _shape_class(geometry: object) -> str:
    if geometry is None:
        return "NO_RETAINED_GEOMETRY"
    if geometry.geom_type != "Polygon":
        return "MULTIPART"
    convex = abs(float(geometry.convex_hull.area) - float(geometry.area)) <= 1e-8
    return "SIMPLE_CONVEX" if convex and not geometry.interiors else "IRREGULAR_OR_COURTYARD"


def _site_frame(site_id: str, readiness: pd.DataFrame) -> pd.DataFrame:
    """Join one site's readiness rows to its manifest geometry and attributes."""
    manifest = gpd.read_file(MANIFEST_ROOT / site_id / "02_residential_manifest.gpkg")
    if site_id == "ES-MAD-BERRUGUETE":
        manifest = apply_attribute_sidecar(manifest, pd.read_csv(ES_SIDECAR))
    manifest["building_id"] = manifest["osm_id"].astype(str)

    columns = ["building_id", "levels", "surplus_tags", "geometry"]
    if "observed_dwellings" in manifest.columns:
        columns.insert(2, "observed_dwellings")
    rows = readiness.loc[readiness["neighbourhood_id"] == site_id].merge(
        manifest[columns], on="building_id", how="left", validate="one_to_one"
    )

    rows["completeness_band"] = rows["layout_ready"].map(
        {True: "HIGH_MAPPING_INPUT_COMPLETENESS", False: "LOW_OR_INCOMPLETE_MAPPING_INPUTS"}
    )
    rows["age_band"] = rows["year_built"].map(_age_band)
    rows["shape_class"] = rows["geometry"].map(_shape_class)
    rows["observed_storeys"] = pd.to_numeric(rows["levels"], errors="coerce")
    if "observed_dwellings" in rows.columns:
        counts = pd.to_numeric(rows["observed_dwellings"], errors="coerce")
    else:
        counts = pd.Series(float("nan"), index=rows.index)
    from_tags = rows["surplus_tags"].map(
        lambda raw: (
            float(json.loads(raw).get("nombre_de_logements"))
            if isinstance(raw, str) and json.loads(raw).get("nombre_de_logements") not in (None, "")
            else float("nan")
        )
    )
    rows["observed_dwellings"] = counts.where(counts.notna(), from_tags)
    rows["native_crs"] = str(manifest.crs)
    return _measure_layout_axis(rows)


def _measure_layout_axis(rows: pd.DataFrame) -> pd.DataFrame:
    """Run the ruled layout contract over one site, in that site's own CRS.

    The geometry column is dropped on the way out.  The two sites are in
    different UTM zones and must never be brought into a common CRS to be
    concatenated -- reprojection is what silently destroys layout emission.
    """
    rows = rows.copy()
    rows["layout_status_measured"] = "NOT_ATTEMPTED_MAPPING_BLOCKED"
    rows["layout_reason_measured"] = rows["reason"].fillna("")
    rows["units_per_floor_measured"] = pd.NA
    rows["simulation_mode_expected"] = "NOT_SCOPED"

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
            rows.at[index, "simulation_mode_expected"] = "EUROPEAN_DWELLING_LAYOUT"
        else:
            rows.at[index, "layout_status_measured"] = "FALLBACK_PENDING_LAYOUT"
            rows.at[index, "layout_reason_measured"] = layout.fallback_reason or ""
            rows.at[index, "simulation_mode_expected"] = "FALLBACK_ONE_ZONE_PER_FLOOR"

    return pd.DataFrame(rows.drop(columns=["geometry"]))


def measure() -> tuple[pd.DataFrame, dict[str, object]]:
    readiness, readiness_summary = write_eu02_archetype_mapping_readiness(
        MANIFEST_ROOT, OUT, attribute_sidecars={"ES-MAD-BERRUGUETE": ES_SIDECAR}
    )

    frames = [_site_frame(site_id, readiness) for site_id in S3_SITES]
    rows = pd.concat(frames, ignore_index=True)

    eligible = rows.loc[rows["layout_ready"] & rows["age_band"].isin(AGE_ORDER)].copy()
    eligible["stratum"] = (
        eligible["country_stock_code"].astype(str)
        + "|"
        + eligible["building_type"].astype(str)
        + "|"
        + eligible["age_band"]
    )

    summary = {
        "evidence_scope": "eu04_s3_corpus_measurement_only",
        "ruling": (
            "D-EU-22 F1 (S3 composition = FR + ES) and D-EU-23 G1 "
            "(96 buildings, mixed mode, both axes printed)"
        ),
        "sites_scoped": list(S3_SITES),
        "native_crs_by_site": {
            site: sorted(set(rows.loc[rows["neighbourhood_id"] == site, "native_crs"]))
            for site in S3_SITES
        },
        "manifest_rows_scoped": int(len(rows)),
        "layout_ready_rows": int(rows["layout_ready"].sum()),
        "layout_ready_by_site": {
            site: int(((rows["neighbourhood_id"] == site) & rows["layout_ready"]).sum())
            for site in S3_SITES
        },
        "eligible_rows_typed_and_dated": int(len(eligible)),
        "stratum_counts": {
            str(key): int(value)
            for key, value in eligible.groupby("stratum").size().sort_index().items()
        },
        "layout_axis": {
            "DWELLING_LAYOUT_EMITTED": int(
                (rows["layout_status_measured"] == "DWELLING_LAYOUT_EMITTED").sum()
            ),
            "FALLBACK_PENDING_LAYOUT": int(
                (rows["layout_status_measured"] == "FALLBACK_PENDING_LAYOUT").sum()
            ),
        },
        "layout_axis_by_site": {
            site: {
                status: int(
                    (
                        (rows["neighbourhood_id"] == site)
                        & (rows["layout_status_measured"] == status)
                    ).sum()
                )
                for status in ("DWELLING_LAYOUT_EMITTED", "FALLBACK_PENDING_LAYOUT")
            }
            for site in S3_SITES
        },
        "layout_fallback_reasons": {
            str(key): int(value)
            for key, value in rows.loc[
                rows["layout_status_measured"] == "FALLBACK_PENDING_LAYOUT",
                "layout_reason_measured",
            ]
            .value_counts()
            .items()
        },
        "s3_target_cases": 96,
        "s3_formable_at_96": bool(len(eligible) >= 96),
        "readiness_summary": readiness_summary,
        "interpretation": (
            "The layout axis is measured for every layout-ready row and is NOT an input to any "
            "selection (D-EU-04-H). A row that falls back is a mixed-mode member of S3 under "
            "D-EU-23 G1, not an excluded row."
        ),
    }

    keep = [
        "neighbourhood_id", "country_stock_code", "building_id", "building_type",
        "year_built", "archetype_id", "mapping_status", "reason", "layout_ready",
        "type_provenance", "dwellings_provenance", "age_band", "completeness_band",
        "shape_class", "native_crs", "observed_dwellings", "observed_storeys",
        "units_per_floor_measured", "layout_status_measured", "layout_reason_measured",
        "simulation_mode_expected",
    ]
    return rows[keep], summary


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    census, summary = measure()
    census.to_csv(OUT / "s3_scope_measurement.csv", index=False)
    (OUT / "s3_scope_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))


if __name__ == "__main__":
    main()
