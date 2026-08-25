"""Manual EU-02 Bologna cadastral manifest acquisition; never run from pytest."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from openubem.acquisition.bologna_fetcher import ATTRIBUTION, DEFAULT_BASE, DEFAULT_DATASET, LICENCE, classify_bologna_rifter
from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests
from openubem.acquisition.osm_fetcher import ingest_buildings


ROOT = Path(__file__).resolve().parents[4]
SITE_ID = "IT-BOL-GALVANI2"
BBOX = (44.492249, 44.484404, 11.358017, 11.339551)
BOUNDARY = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "outputs" / "EU02_neighbourhood_selection_2026-08-24" / "eu02_boundaries" / "eu02_boundary_IT-BOL-GALVANI2.geojson"
BOUNDARY_SHA256 = "7d7dcb8d9553ca2325f71ee5b7ca82ef3180ae4365627ef247007523d956714b"
OUTPUT_DIR = ROOT / "openubem" / "outputs" / "eu02" / SITE_ID
ENDPOINT = f"{DEFAULT_BASE}/{DEFAULT_DATASET}/exports/geojson?limit=-1"


def main() -> None:
    raw = ingest_buildings(
        bbox=BBOX,
        source="bologna",
        source_options={"dataset": DEFAULT_DATASET},
        output_dir=OUTPUT_DIR,
    )
    clipped = clip_to_boundary(raw, BOUNDARY, verify_sha256=BOUNDARY_SHA256)
    classified = clipped.copy()
    classified["eu02_use_class"] = classify_bologna_rifter(classified)
    residential, excluded, counts = split_residential(
        classified,
        {"residential": "residential", "non_residential": "non_residential"},
        class_column="eu02_use_class",
    )
    residential = residential.drop(columns="eu02_use_class")
    excluded = excluded.drop(columns="eu02_use_class")
    write_manifests(
        residential,
        excluded,
        counts,
        OUTPUT_DIR,
        neighbourhood_id=SITE_ID,
        source_endpoint=ENDPOINT,
        source_layer=ATTRIBUTION + " — " + DEFAULT_DATASET,
        licence=LICENCE,
    )
    payload = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "site_id": SITE_ID,
        "bbox_openubem_order": BBOX,
        "boundary_sha256": hashlib.sha256(BOUNDARY.read_bytes()).hexdigest(),
        "raw_schema_rows": len(raw),
        "clipped_rows": len(clipped),
        "exclusion_counts": counts,
        "expected_raw_boundary_counts": {"total": 1372, "non_residential": 42, "residential": 1330},
    }
    Path(__file__).with_name("bologna_manifest_acquisition.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
