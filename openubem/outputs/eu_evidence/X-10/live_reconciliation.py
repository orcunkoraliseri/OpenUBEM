"""Manual EU-02 France source reconciliation; never run from pytest."""
from __future__ import annotations

import json
from pathlib import Path

from openubem.acquisition.bdtopo_fetcher import fetch_bdtopo
from openubem.acquisition.boundary_clip import clip_to_boundary


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).parent
BBOX = (45.774784, 45.768891, 4.837450, 4.823612)
BOUNDARY = ROOT / "docs/docs_ACTIVE/europeanLocations/outputs/EU02_neighbourhood_selection_2026-08-24/eu02_boundaries/eu02_boundary_FR-LYO-HAUTCOEURPENTES.geojson"
SHA256 = "8832ec13e7bb96aff3cca4fee52b76d0f8644bffb9157a56c6eed2c77f4b0739"


def classification(row) -> str:
    values = {value for value in (row.usage_1, row.usage_2) if value not in (None, "")}
    if "Résidentiel" in values:
        return "residential"
    if "Annexe" in values:
        return "annex"
    if "Indifférencié" in values:
        return "unknown"
    return "non_residential"


def main() -> None:
    raw = fetch_bdtopo(BBOX)
    clipped = clip_to_boundary(raw, BOUNDARY, verify_sha256=SHA256)
    classes = clipped.apply(classification, axis=1)
    payload = {
        "site_id": "FR-LYO-HAUTCOEURPENTES",
        "source": "IGN BD TOPO V3 batiment",
        "endpoint": "https://data.geopf.fr/wfs/ows",
        "licence": "Licence Ouverte / Open Licence 2.0 (Etalab)",
        "attribution": "IGN — BD TOPO",
        "boundary_sha256": SHA256,
        "bbox_features": len(raw),
        "within_boundary": len(clipped),
        "residential": int((classes == "residential").sum()),
        "unknown": int((classes == "unknown").sum()),
        "non_residential": int((classes == "non_residential").sum()),
        "annexes_removed": int((classes == "annex").sum()),
        "expected": {"within_boundary": 891, "residential": 544, "unknown": 278, "non_residential": 52, "annexes_removed": 23},
    }
    (OUT / "fr_live_reconciliation.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
