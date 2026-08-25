"""Manual EU-02 live OSM acquisition; never run from pytest."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from openubem.acquisition.boundary_clip import clip_to_boundary, split_residential, write_manifests
from openubem.acquisition.osm_fetcher import ingest_buildings


ROOT = Path(__file__).resolve().parents[4]
BOUNDARIES = ROOT / "docs" / "docs_ACTIVE" / "europeanLocations" / "outputs" / "EU02_neighbourhood_selection_2026-08-24" / "eu02_boundaries"
OUTPUT_ROOT = ROOT / "openubem" / "outputs" / "eu02"
OSM_LICENCE = "Open Database License (ODbL) v1.0"
OSM_ENDPOINT = "https://overpass-api.de/api/interpreter"

SITES = (
    {
        "id": "ES-MAD-BERRUGUETE",
        "bbox": (40.463907, 40.453976, -3.698399, -3.711403),
        "expected_residential": 1195,
        "boundary": "eu02_boundary_ES-MAD-BERRUGUETE.geojson",
    },
    {
        "id": "GB-LDN-STDUNSTANS",
        "bbox": (51.524248, 51.512597, -0.033744, -0.050013),
        "expected_residential": 1241,
        "boundary": "eu02_boundary_GB-LDN-STDUNSTANS.geojson",
    },
)


def main() -> None:
    crosswalk = json.loads((ROOT / "openubem" / "data" / "osm_to_use_class.json").read_text(encoding="utf-8"))
    use_classes = crosswalk["tag_to_use_class"]
    split_crosswalk = {
        tag: "residential" if use_class == "residential" else "non_residential"
        for tag, use_class in use_classes.items()
    }
    results = []
    for site in SITES:
        output_dir = OUTPUT_ROOT / site["id"]
        raw = ingest_buildings(bbox=site["bbox"], tags={"building": True}, output_dir=output_dir)
        boundary = BOUNDARIES / site["boundary"]
        boundary_sha256 = hashlib.sha256(boundary.read_bytes()).hexdigest()
        clipped = clip_to_boundary(raw, boundary, verify_sha256=boundary_sha256)
        residential, excluded, counts = split_residential(clipped, split_crosswalk)
        write_manifests(
            residential,
            excluded,
            counts,
            output_dir,
            neighbourhood_id=site["id"],
            source_endpoint=OSM_ENDPOINT,
            source_layer="OpenStreetMap building features",
            licence=OSM_LICENCE,
        )
        results.append(
            {
                "site_id": site["id"],
                "bbox_openubem_order": site["bbox"],
                "boundary_sha256": boundary_sha256,
                "raw_schema_rows": len(raw),
                "clipped_rows": len(clipped),
                "expected_residential": site["expected_residential"],
                "residential_rows": len(residential),
                "excluded_rows": len(excluded),
                "exclusion_counts": counts,
            }
        )
    evidence = {
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_endpoint": OSM_ENDPOINT,
        "source_licence": OSM_LICENCE,
        "sites": results,
    }
    (Path(__file__).with_name("osm_live_acquisition.json")).write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
