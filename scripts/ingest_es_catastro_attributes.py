"""Ingest the ruled Madrid attribute source into an EU-02 sidecar.

Authority: ``D-EU-23`` ruled 2026-08-27, Option G1 -- *"FR + ES ingestion for
Madrid and Lyon is fully authorized to proceed."*  ``D-EU-22`` (Option F1)
already authorised the live retrieval and measured its coverage; this script is
the ingestion that record explicitly did **not** perform.

It writes exactly two files, both under ``openubem/outputs/eu_evidence/EU-04``:

* ``es_catastro_attribute_sidecar.csv`` -- one row per EU-02 footprint,
* ``es_catastro_attribute_sidecar_summary.json`` -- the counts and the reasons.

``openubem/outputs/eu02/`` is opened read-only and is never written.  No sample
is formed and no simulation is run here.

Usage:  .venv/Scripts/python.exe scripts/ingest_es_catastro_attributes.py
"""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd

from openubem.acquisition.catastro_inspire_fetcher import (
    build_es_attribute_sidecar,
    fetch_catastro_buildings,
    sidecar_sha256,
    sidecar_summary,
)


ROOT = Path(__file__).resolve().parents[1]
SITE = "ES-MAD-BERRUGUETE"
MANIFEST = ROOT / "openubem/outputs/eu02" / SITE / "02_residential_manifest.gpkg"
OUT_DIR = ROOT / "openubem/outputs/eu_evidence/EU-04"
SIDECAR_PATH = OUT_DIR / "es_catastro_attribute_sidecar.csv"
SUMMARY_PATH = OUT_DIR / "es_catastro_attribute_sidecar_summary.json"


def main() -> None:
    manifest = gpd.read_file(MANIFEST)
    bounds = tuple(manifest.to_crs(4326).total_bounds)
    print(f"{SITE}: {len(manifest)} footprints, study bbox {bounds}")

    catastro, report = fetch_catastro_buildings(bounds)
    print(
        f"Catastro: {report.tiles_requested} tiles, {report.features_returned} features, "
        f"{report.unique_features} unique in bbox, {report.residential_features} residential, "
        f"{report.seconds:.1f}s, {len(report.retries)} retries"
    )

    sidecar = build_es_attribute_sidecar(manifest, catastro, neighbourhood_id=SITE)
    summary = sidecar_summary(sidecar, report)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sidecar.to_csv(SIDECAR_PATH, index=False)
    summary["sidecar_sha256"] = sidecar_sha256(SIDECAR_PATH)
    summary["manifest_sha256"] = sidecar_sha256(MANIFEST)
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"Wrote {SIDECAR_PATH} ({len(sidecar)} rows)")


if __name__ == "__main__":
    main()
