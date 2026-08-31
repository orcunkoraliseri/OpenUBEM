"""EU-04 `S3` annual controlled-baseline campaign over the frozen 96.

Authority: ``D-EU-23`` G1 -- 96 buildings, **mixed mode**, both axes printed.
Composition: ``D-EU-22`` F1 -- **FR + ES**.

Every physics decision here is the one `S2` was accepted on.  The IDF assembly,
the EnergyPlus invocation and the heating extraction are **imported** from
``scripts/run_eu_s2_campaign.py`` rather than re-implemented, so an `S3` number
is comparable with the accepted `S2` number by construction and not by
assertion.  What this module adds is only what `S3` is: a second country, and
therefore a second TABULA registry, a second pinned EPW fold and a second
manifest CRS.

Two axes are recorded per building and never collapsed (`D-EU-23` G1):

* ``layout_mode`` -- ``DWELLING_LAYOUT_EMITTED`` or ``FALLBACK_PENDING_LAYOUT``
* ``simulation_mode`` -- ``EUROPEAN_DWELLING_LAYOUT`` or
  ``FALLBACK_ONE_ZONE_PER_FLOOR``

Manifests are loaded in their **native** CRS and never reprojected (`S1`
finding, ``OpenUBEM_debug_References.md`` ch. 5).

Usage:
    .venv/Scripts/python.exe scripts/run_eu_s3_campaign.py --dry-run
    .venv/Scripts/python.exe scripts/run_eu_s3_campaign.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import geopandas as gpd
import pandas as pd

from openubem.acquisition.european_weather import sha256_file
from scripts.run_eu_s2_campaign import (
    build_geometry_for_row,
    build_idf_for_building,
    run_energyplus_for_building,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "openubem/outputs/eu_evidence/EU-04/s3"
SAMPLE_PATH = EVIDENCE / "s3_sample.csv"
SUMMARY_PATH = EVIDENCE / "s3_sample_summary.json"
RUN_ROOT = EVIDENCE / "s3_campaign"
CAMPAIGN_MANIFEST_PATH = EVIDENCE / "s3_campaign_manifest.csv"
REGISTRY_PATH = ROOT / "openubem/data/weather/weather_registry.json"

TARGET_ROWS = 96

#: site -> (country stock code, weather fold). Both folds are `EU-07` pinned.
SITE_CONTEXT = {
    "FR-LYO-HAUTCOEURPENTES": ("FR", "fr"),
    "ES-MAD-BERRUGUETE": ("ES", "es"),
}

MANIFEST_COLUMNS = [
    "building_id", "run_slug", "neighbourhood_id", "country_stock_code", "archetype_id",
    "building_type", "age_band", "s3_cell", "layout_mode", "simulation_mode",
    "zone_count", "idf_sha256", "weather_fold", "weather_sha256",
    "eplus_return_code", "severe_errors", "fatal_errors", "heating_kwh",
    "floor_area_m2", "eui_kwh_m2", "run_seconds",
]

LAYOUT_TO_SIMULATION_MODE = {
    "DWELLING_LAYOUT_EMITTED": "EUROPEAN_DWELLING_LAYOUT",
}
FALLBACK_SIMULATION_MODE = "FALLBACK_ONE_ZONE_PER_FLOOR"


def run_slug(building_id: str) -> str:
    """A filesystem- and EnergyPlus-safe name for one building.

    Lyon's BD TOPO ids are already safe; Madrid's OSM ids are ``way/123`` and
    ``relation/456``, whose slash would open a directory level in every IDF,
    zone and schedule path.  The true ``building_id`` is what the manifest
    records -- this is only how the run is named on disk.
    """
    return str(building_id).replace("/", "_")


def load_frozen_sample(path: Path = SAMPLE_PATH) -> pd.DataFrame:
    """Load the frozen 96; never re-form, reorder or re-derive it here."""
    sample = pd.read_csv(path)
    if len(sample) != TARGET_ROWS:
        raise ValueError(f"frozen S3 sample must contain {TARGET_ROWS} rows, found {len(sample)}")
    not_ready = sample.loc[sample["mapping_status"] != "MAPPED_LAYOUT_READY", "building_id"].tolist()
    if not_ready:
        raise ValueError(f"S3 campaign requires MAPPED_LAYOUT_READY for every row; not ready: {not_ready}")
    unknown = set(sample["neighbourhood_id"]) - set(SITE_CONTEXT)
    if unknown:
        raise ValueError(f"S3 sample holds rows from unscoped sites: {sorted(unknown)}")
    return sample


def load_manifest_native(site_id: str) -> gpd.GeoDataFrame:
    """Load one site's manifest in its own CRS. Reprojection is never performed."""
    path = ROOT / "openubem/outputs/eu02" / site_id / "02_residential_manifest.gpkg"
    if not path.is_file():
        raise ValueError(f"Manifest does not exist: {path}")
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        raise ValueError(f"Manifest {path} carries no CRS; refusing to guess one")
    return gdf


def load_archetype_record(country_stock_code: str, archetype_id: str) -> dict[str, object]:
    path = ROOT / "openubem/data/construction" / f"tabula_archetypes_{country_stock_code.lower()}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    for record in payload["records"]:
        if record["archetype_id"] == archetype_id:
            return record
    raise ValueError(f"archetype_id not found in the {country_stock_code} TABULA registry: {archetype_id!r}")


def verify_weather(fold: str) -> tuple[Path, str]:
    """Return the pinned EPW for ``fold`` after checking its SHA-256, or abort."""
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    target = next(entry for entry in registry["targets"] if entry["fold"] == fold)
    epw_path = ROOT / str(target["weather_file"])
    recorded = str(target["sha256"])
    recomputed = sha256_file(epw_path)
    if recorded != recomputed:
        raise ValueError(
            f"{fold} EPW SHA-256 mismatch: registry={recorded} recomputed={recomputed} file={epw_path}"
        )
    return epw_path, recomputed


def run_campaign(dry_run: bool = False, limit: int | None = None) -> pd.DataFrame:
    sample = load_frozen_sample()
    manifests = {site_id: load_manifest_native(site_id) for site_id in SITE_CONTEXT}
    # The EPW is resolved and checksummed even on a dry run: an IDF built
    # against the wrong site's weather header is not a useful dry run.
    weather = {fold: verify_weather(fold) for _, fold in SITE_CONTEXT.values()}

    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    ordered = sample.sort_values(["neighbourhood_id", "building_id"], kind="stable")
    if limit is not None:
        ordered = ordered.head(limit)

    for position, (_, row) in enumerate(ordered.iterrows(), start=1):
        site_id = row["neighbourhood_id"]
        country, fold = SITE_CONTEXT[site_id]
        building_id = row["building_id"]
        record = load_archetype_record(country, row["archetype_id"])
        zones, layout_mode = build_geometry_for_row(row, manifests[site_id])
        simulation_mode = LAYOUT_TO_SIMULATION_MODE.get(layout_mode, FALLBACK_SIMULATION_MODE)
        slug = run_slug(building_id)
        for zone in zones:
            zone["name"] = run_slug(zone["name"])
        named = row.copy()
        named["building_id"] = slug
        run_dir = RUN_ROOT / site_id / slug
        epw_path = weather[fold][0]
        idf_path = build_idf_for_building(named, record, zones, run_dir, epw_path=epw_path)
        floor_area_m2 = sum(float(zone["floor_polygon"].area) for zone in zones)

        result_row: dict[str, object] = {
            "building_id": building_id,
            "run_slug": slug,
            "neighbourhood_id": site_id,
            "country_stock_code": country,
            "archetype_id": row["archetype_id"],
            "building_type": row["building_type"],
            "age_band": row["age_band"],
            "s3_cell": row["s3_cell"],
            "layout_mode": layout_mode,
            "simulation_mode": simulation_mode,
            "zone_count": len(zones),
            "idf_sha256": sha256_file(idf_path),
            "weather_fold": fold,
            "weather_sha256": "",
            "eplus_return_code": "",
            "severe_errors": "",
            "fatal_errors": "",
            "heating_kwh": "",
            "floor_area_m2": round(floor_area_m2, 4),
            "eui_kwh_m2": "",
            "run_seconds": "",
        }

        if not dry_run:
            outcome = run_energyplus_for_building(idf_path, run_dir, epw_path=epw_path)
            result_row["weather_sha256"] = weather[fold][1]
            result_row["eplus_return_code"] = outcome["eplus_return_code"]
            result_row["severe_errors"] = outcome["severe_errors"]
            result_row["fatal_errors"] = outcome["fatal_errors"]
            result_row["run_seconds"] = outcome["run_seconds"]
            if outcome["completed"]:
                heating_kwh = outcome["heating_kwh"]
                result_row["heating_kwh"] = round(heating_kwh, 6)
                result_row["eui_kwh_m2"] = (
                    round(heating_kwh / floor_area_m2, 6) if floor_area_m2 > 0 else ""
                )
                status = "EPLUS_COMPLETED"
            else:
                fatal = re.search(r"^.*\*\*\s*Fatal\s*\*\*.*$", outcome["err_text"], re.MULTILINE)
                severe = re.search(r"^.*\*\*\s*Severe\s*\*\*.*$", outcome["err_text"], re.MULTILINE)
                first = (fatal or severe).group(0).strip()[:300] if (fatal or severe) else "no Severe/Fatal line in eplusout.err"
                status = "EPLUS_FATAL"
                print(f"    first_error: {first}", flush=True)
            print(
                f"  [{position}/{len(ordered)}] {site_id} {building_id}: layout={layout_mode} "
                f"simulation={simulation_mode} zones={len(zones)} status={status} "
                f"run_seconds={outcome['run_seconds']}",
                flush=True,
            )

        rows.append(result_row)

    frame = pd.DataFrame.from_records(rows, columns=MANIFEST_COLUMNS)
    if not dry_run:
        frame.to_csv(CAMPAIGN_MANIFEST_PATH, index=False)
    return frame


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="build IDFs only; do not run EnergyPlus")
    parser.add_argument("--limit", type=int, default=None, help="run only the first N rows (resource probe)")
    args = parser.parse_args()
    frame = run_campaign(dry_run=args.dry_run, limit=args.limit)
    if not args.dry_run:
        print(f"Wrote {CAMPAIGN_MANIFEST_PATH} ({len(frame)} rows)")


if __name__ == "__main__":
    main()
