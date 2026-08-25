"""Manual NS-02 artifact gate audit for the four selected EU-02 sites."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

from openubem.acquisition.footprint_schema import SCHEMA_COLUMNS


ROOT = Path(__file__).resolve().parents[4]
OUTPUT_ROOT = ROOT / "openubem" / "outputs" / "eu02"
SITES = ("ES-MAD-BERRUGUETE", "GB-LDN-STDUNSTANS", "FR-LYO-HAUTCOEURPENTES", "IT-BOL-GALVANI2")
RECONCILIATION_EVIDENCE = {
    "ES-MAD-BERRUGUETE": ROOT / "openubem/outputs/eu_evidence/X-09/osm_live_acquisition.json",
    "GB-LDN-STDUNSTANS": ROOT / "openubem/outputs/eu_evidence/X-09/osm_live_acquisition.json",
    "FR-LYO-HAUTCOEURPENTES": ROOT / "openubem/outputs/eu_evidence/X-10/fr_live_reconciliation.json",
    "IT-BOL-GALVANI2": ROOT / "openubem/outputs/eu_evidence/X-11/bologna_live_reconciliation.json",
}


def main() -> None:
    rows = []
    for site in SITES:
        directory = OUTPUT_ROOT / site
        clean = gpd.read_file(directory / "01_buildings_clean.gpkg", layer="buildings")
        residential = gpd.read_file(directory / "02_residential_manifest.gpkg", layer="buildings")
        excluded = gpd.read_file(directory / "02_excluded_manifest.gpkg", layer="buildings")
        schema = json.loads((directory / "01_buildings_clean.schema.json").read_text(encoding="utf-8"))
        schema_by_name = {entry["name"]: entry["dtype"] for entry in schema}
        schema_metadata_valid = (
            set(schema_by_name) == set(SCHEMA_COLUMNS)
            and schema_by_name["levels"] == "Int64"
            and schema_by_name["year_built"] == "Int64"
            and schema_by_name["underground"] == "Int64"
        )
        counts = json.loads((directory / "02_exclusion_counts.json").read_text(encoding="utf-8"))
        source = json.loads((directory / "01_source.json").read_text(encoding="utf-8"))
        ids_disjoint = set(residential["osm_id"]).isdisjoint(excluded["osm_id"])
        counts_match = counts["total"] == len(residential) + len(excluded)
        sidecar_complete = all(source.get(key) for key in ("neighbourhood_id", "source_endpoint", "source_layer", "licence"))
        row = {
            "site_id": site,
            "clean_schema_rows": len(clean),
            "serialized_schema_metadata_valid": schema_metadata_valid,
            "residential_manifest_rows": len(residential),
            "excluded_manifest_rows": len(excluded),
            "disjoint": ids_disjoint,
            "counts_match_manifests": counts_match,
            "source_sidecar_complete": sidecar_complete,
            "reconciliation_evidence": str(RECONCILIATION_EVIDENCE[site].relative_to(ROOT)),
            "reconciliation_evidence_exists": RECONCILIATION_EVIDENCE[site].is_file() and RECONCILIATION_EVIDENCE[site].stat().st_size > 0,
        }
        row["ns02_contract_met"] = all((schema_metadata_valid, ids_disjoint, counts_match, sidecar_complete, row["reconciliation_evidence_exists"]))
        rows.append(row)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate": "NS-02",
        "scope": "four selected EU-02 neighbourhoods",
        "site_results": rows,
        "ns02_contract_met": all(row["ns02_contract_met"] for row in rows),
        "note": "Raw-source census and model-ready-clean manifest counts are reported separately in the cited reconciliation evidence; this audit verifies the required shared schema, standard artifacts, provenance sidecar, manifest partition, and evidence presence.",
    }
    target = Path(__file__).with_name("eu02_ns02_gate_audit.json")
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
