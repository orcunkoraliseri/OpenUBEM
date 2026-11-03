"""Manual EU-02 Lyon BD TOPO manifest acquisition; never run from pytest."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from openubem.acquisition.bdtopo_fetcher import ATTRIBUTION, DEFAULT_WFS, LICENCE, classify_bdtopo_use
from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests
from openubem.acquisition.osm_fetcher import ingest_buildings


ROOT = Path(__file__).resolve().parents[4]
SITE_ID = "FR-LYO-HAUTCOEURPENTES"
BBOX = (45.774784, 45.768891, 4.837450, 4.823612)
BOUNDARY = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "outputs" / "EU02_neighbourhood_selection_2026-08-24" / "eu02_boundaries" / "eu02_boundary_FR-LYO-HAUTCOEURPENTES.geojson"
BOUNDARY_SHA256 = "8832ec13e7bb96aff3cca4fee52b76d0f8644bffb9157a56c6eed2c77f4b0739"
OUTPUT_DIR = ROOT / "openubem" / "outputs" / "eu02" / SITE_ID


def main() -> None:
    raw = ingest_buildings(bbox=BBOX, source="bdtopo", output_dir=OUTPUT_DIR)
    clipped = clip_to_boundary(raw, BOUNDARY, verify_sha256=BOUNDARY_SHA256)
    classified = clipped.copy()
    classified["eu02_use_class"] = classify_bdtopo_use(classified)
    residential, excluded, counts = split_residential(
        classified,
        {"residential": "residential", "unknown": "unknown", "annex": "annex", "non_residential": "non_residential"},
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
        source_endpoint=DEFAULT_WFS,
        source_layer=ATTRIBUTION,
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
        "expected_raw_boundary_counts": {"total": 891, "residential": 544, "unknown": 278, "non_residential": 46, "annexes_removed": 23},
    }
    Path(__file__).with_name("fr_manifest_acquisition.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
