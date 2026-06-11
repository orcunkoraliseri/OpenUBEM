"""One-time script: download EPA eGRID 2022 and build data/carbon/egrid_2022.json.

Usage:
    python scripts/build_egrid_json.py

Requires: openpyxl (dev extra), requests (runtime dep).
Network call: downloads eGRID2022_data.xlsx from EPA once; result committed to the repo.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import requests

# ── Source (P2) ───────────────────────────────────────────────────────────────
_URL = (
    "https://www.epa.gov/system/files/documents/2024-01/egrid2022_data.xlsx"
)
_RETRIEVAL_DATE = "2026-06-10"
_SHEET = "ST22"          # state-level summary tab in eGRID 2022
# eGRID 2022 xlsx has row 0 = long-form headers, row 1 = short-code headers (PSTATABB etc.)
# We use row 1 short-code headers to find columns
_STATE_COL = "PSTATABB"  # 2-letter state abbreviation
_FACTOR_COL = "STC2ERTA" # state annual CO2e total output emission rate, lb/MWh
# US territories (PR, VI, ...) included in the sheet but outside OpenUBEM's continental scope
_EXCLUDE_STATES = frozenset({"PR", "VI", "AS", "GU", "MP"})  # territories

# lb/MWh → kg/kWh: ×0.453592 (lb→kg) ÷ 1000 (MWh→kWh)
_LB_MWH_TO_KG_KWH = 0.453592 / 1000.0

_OUT = Path(__file__).parent.parent / "openubem" / "data" / "carbon" / "egrid_2022.json"
_PROV = Path(__file__).parent.parent / "openubem" / "data" / "carbon" / "PROVENANCE.md"


def _download(url: str) -> bytes:
    print(f"Downloading {url} ...", flush=True)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    return resp.content


def _build_table(xlsx_bytes: bytes) -> dict[str, dict]:
    import openpyxl
    import io

    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), read_only=True, data_only=True)
    ws = wb[_SHEET]

    rows = list(ws.iter_rows(values_only=True))
    # Row 0 = long-form headers, row 1 = short-code headers (PSTATABB etc.), row 2+ = data
    shortcode_header = [str(c).strip() if c is not None else "" for c in rows[1]]

    try:
        i_state = shortcode_header.index(_STATE_COL)
        i_factor = shortcode_header.index(_FACTOR_COL)
    except ValueError as exc:
        raise RuntimeError(
            f"Expected short-code columns {_STATE_COL!r}, {_FACTOR_COL!r} "
            f"in row 1 of sheet {_SHEET!r}. Found: {shortcode_header}"
        ) from exc

    result: dict[str, dict] = {}
    for row in rows[2:]:
        state = row[i_state]
        factor_raw = row[i_factor]
        if state is None or factor_raw is None:
            continue
        state = str(state).strip().upper()
        if len(state) != 2 or state in _EXCLUDE_STATES:
            continue
        try:
            factor_lb_mwh = float(factor_raw)
        except (TypeError, ValueError):
            continue
        factor_kg_kwh = round(factor_lb_mwh * _LB_MWH_TO_KG_KWH, 6)
        result[state] = {
            "subregion": "",  # state sheet does not carry subregion (see PROVENANCE.md)
            "factor_kgco2_kwh": factor_kg_kwh,
        }

    wb.close()
    return result


def _validate(table: dict) -> None:
    assert len(table) == 51, f"Expected 51 entries (50 states + DC), got {len(table)}"
    assert "MA" in table, "Massachusetts (MA) missing"
    for state, rec in table.items():
        f = rec["factor_kgco2_kwh"]
        assert 0.01 < f < 1.2, (
            f"{state}: factor {f} outside (0.01, 1.2) kg/kWh plausibility band"
        )
    print(f"Validation OK: {len(table)} entries, MA factor = {table['MA']['factor_kgco2_kwh']}")


def main() -> None:
    _OUT.parent.mkdir(parents=True, exist_ok=True)

    xlsx_bytes = _download(_URL)
    sha256 = hashlib.sha256(xlsx_bytes).hexdigest()
    print(f"SHA-256: {sha256}", flush=True)

    table = _build_table(xlsx_bytes)
    _validate(table)

    _OUT.write_text(json.dumps(table, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Written: {_OUT} ({len(table)} entries)", flush=True)

    prov = f"""# PROVENANCE — openubem/data/carbon/egrid_2022.json

## Source
- Dataset: EPA eGRID 2022 (Emissions & Generation Resource Integrated Database)
- URL: {_URL}
- Retrieval date: {_RETRIEVAL_DATE}
- SHA-256 of downloaded xlsx: {sha256}
- Excel sheet: {_SHEET} (state-level summary)
- Short-code header row (row 1): {_STATE_COL} = 2-letter USPS abbreviation; {_FACTOR_COL} = state annual CO₂e total output emission rate (lb/MWh)
- Territories excluded: {sorted(_EXCLUDE_STATES)} (outside OpenUBEM continental-US scope)
- Note: subregion not available in ST22 sheet; set to "" in output (informational field only per PLAN P2)

## Conversion
factor_kgco2_kwh = {_FACTOR_COL}_lb_mwh × (0.453592 lb/kg) ÷ 1000 (MWh/kWh)

## Simplification (documented per PLAN P2)
The factor used in OpenUBEM is the **state-level** total output CO₂e rate, not the
subregion rate. EPA publishes both; the state-level rate is used here because the `state`
key is the foreign key OpenUBEM has available from Step 2.1 (county→state join). The
`subregion` field is retained as an informational annotation for audit; it is not used
in any computation.

## Coverage
51 entries: 50 US states + DC (PR, VI, etc. excluded — outside OpenUBEM's continental-US
scope, and not present in the ST22 sheet alongside state totals for the 50+DC).

## MA factor
MA: subregion = {table.get('MA', {}).get('subregion', 'N/A')},
    factor = {table.get('MA', {}).get('factor_kgco2_kwh', 'N/A')} kg CO₂e/kWh

## Downstream use (DESIGN §3E, PLAN F7)
- Heating GWP: × 0.181 kg CO₂e/kWh (natural gas, Iseri et al. 2025)
- Cooling / Lighting / Equipment GWP: × egrid_2022[state]['factor_kgco2_kwh']
- Convention: load_referenced_v1 (no η or COP applied — see DESIGN §3E)
"""
    _PROV.write_text(prov, encoding="utf-8")
    print(f"Written: {_PROV}", flush=True)

    print("\nMA entry:", json.dumps(table["MA"], indent=2))


if __name__ == "__main__":
    main()
