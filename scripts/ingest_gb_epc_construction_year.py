"""EU-11 D-EU-22 b1/b2: read the observed `construction_year` already cached for GB EPC certificates.

Offline sidecar builder. The EPC harvester searched for `construction_age_band` only; full-SAP
certificates (new build / on-construction) do not carry a band but do carry an explicit calendar
year at `/body/data/sap_building_parts[i]/construction_year`. This script reads that field out of
the certificate payloads already cached on disk and writes it to a separate sidecar CSV, joined by
`osm_id`, without rewriting the delivered `gb_epc_certificates.csv` evidence artefact.

No network call. No arguments.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GB_EPC = ROOT / "openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_certificates.csv"
CACHE_DIR = ROOT / "openubem/outputs/eu_evidence/EU-04/D-EU-22/_cache/certificate"
SIDECAR = ROOT / "openubem/outputs/eu_evidence/EU-04/D-EU-22/gb_epc_construction_year_sidecar.csv"

COLUMNS = ["osm_id", "certificateNumber", "registrationDate", "construction_year", "source_key"]


def build_sidecar() -> dict:
    cert = pd.read_csv(GB_EPC)
    rows: list[dict] = []
    cache_files_missing = 0
    for _, row in cert.iterrows():
        cert_number = row["certificateNumber"]
        path = CACHE_DIR / f"{cert_number}.json"
        if not path.exists():
            cache_files_missing += 1
            continue
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        data = payload["body"]["data"]
        for i, part in enumerate(data.get("sap_building_parts") or []):
            v = part.get("construction_year")
            if v is None or v == "":
                continue
            try:
                y = int(v)
            except (TypeError, ValueError):
                continue
            if not (1000 <= y <= 2026):
                continue
            rows.append({
                "osm_id": row["osm_id"],
                "certificateNumber": cert_number,
                "registrationDate": row["registrationDate"],
                "construction_year": y,
                "source_key": f"/sap_building_parts[{i}]/construction_year",
            })
    out = pd.DataFrame(rows, columns=COLUMNS)
    out.to_csv(SIDECAR, index=False)
    return {
        "rows": len(out),
        "certificates": out["certificateNumber"].nunique(),
        "osm_ids": out["osm_id"].nunique(),
        "cache_files_missing": cache_files_missing,
    }


def main() -> None:
    summary = build_sidecar()
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
