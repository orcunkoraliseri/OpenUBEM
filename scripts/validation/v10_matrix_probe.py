"""V10: Case-study matrix definition — Overpass building-COUNT probe.

Queries building counts for the 12-cell matrix:
    {city-centre, urban, suburban, rural} x {New York City, Los Angeles, Austin}

Never downloads full building geometries. Writes results to:
    docs/validations/overAll/V10_matrix_proposal.md
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

REPO = Path(__file__).parent.parent.parent
sys.path.insert(0, str(REPO))

from openubem.acquisition.epw_manager import load_stations, resolve_station
from openubem import config

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_DELAY_S = 5.0

MATRIX: list[dict] = [
    {
        "city": "New York City",
        "layer": "city-centre",
        "lat": 40.7549,
        "lon": -73.9840,
        "radius_m": 500,
        "expected_cz": "4A",
    },
    {
        "city": "New York City",
        "layer": "urban",
        "lat": 40.7721,
        "lon": -73.9301,
        "radius_m": 500,
        "expected_cz": "4A",
    },
    {
        "city": "New York City",
        "layer": "suburban",
        "lat": 40.7052,
        "lon": -73.5985,
        "radius_m": 500,
        "expected_cz": "4A",
    },
    {
        "city": "New York City",
        "layer": "rural",
        "lat": 42.0396,
        "lon": -74.1143,
        "radius_m": 1000,
        "expected_cz": "5A",
    },
    {
        "city": "Los Angeles",
        "layer": "city-centre",
        "lat": 34.0522,
        "lon": -118.2437,
        "radius_m": 500,
        "expected_cz": "3B",
    },
    {
        "city": "Los Angeles",
        "layer": "urban",
        "lat": 34.0584,
        "lon": -118.3040,
        "radius_m": 500,
        "expected_cz": "3B",
    },
    {
        "city": "Los Angeles",
        "layer": "suburban",
        "lat": 33.8359,
        "lon": -118.3406,
        "radius_m": 500,
        "expected_cz": "3B",
    },
    {
        "city": "Los Angeles",
        "layer": "rural",
        "lat": 34.7420,
        "lon": -118.2130,
        "radius_m": 1500,
        "expected_cz": "3B",
    },
    {
        "city": "Austin",
        "layer": "city-centre",
        "lat": 30.2672,
        "lon": -97.7431,
        "radius_m": 500,
        "expected_cz": "2A",
    },
    {
        "city": "Austin",
        "layer": "urban",
        "lat": 30.3072,
        "lon": -97.7400,
        "radius_m": 500,
        "expected_cz": "2A",
    },
    {
        "city": "Austin",
        "layer": "suburban",
        "lat": 30.5085,
        "lon": -97.6789,
        "radius_m": 500,
        "expected_cz": "2A",
    },
    {
        "city": "Austin",
        "layer": "rural",
        "lat": 30.5788,
        "lon": -98.2700,
        "radius_m": 1000,
        "expected_cz": "2A",
    },
]


_HEADERS = {"User-Agent": "OpenUBEM-ValidationProbe/1.0 (research; non-commercial)"}


def count_buildings(lat: float, lon: float, radius_m: float, retries: int = 3) -> int:
    query = (
        f"[out:json][timeout:60];"
        f"("
        f"  way[building](around:{radius_m},{lat},{lon});"
        f"  relation[building](around:{radius_m},{lat},{lon});"
        f");"
        f"out count;"
    )
    for attempt in range(retries):
        try:
            resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=90, headers=_HEADERS)
            resp.raise_for_status()
            data = resp.json()
            elements = data.get("elements", [])
            if elements and elements[0].get("type") == "count":
                tags = elements[0].get("tags", {})
                return int(tags.get("total", 0))
            return 0
        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code in (429, 504):
                wait = 15 * (attempt + 1)
                print(f"           HTTP {exc.response.status_code} — waiting {wait}s before retry {attempt+1}/{retries}")
                time.sleep(wait)
            else:
                raise
        except requests.exceptions.Timeout:
            wait = 15 * (attempt + 1)
            print(f"           Timeout — waiting {wait}s before retry {attempt+1}/{retries}")
            time.sleep(wait)
    raise RuntimeError(f"count_buildings failed after {retries} retries for ({lat},{lon}) r={radius_m}")


def resolve_epw(lat: float, lon: float, stations) -> tuple[str, float]:
    station, dist_km = resolve_station(lat, lon, stations)
    resolvable = dist_km <= config.EPW_MAX_STATION_KM
    label = f"{station['name']} ({station['state']}, {dist_km:.0f} km)"
    return label, resolvable


def main() -> None:
    stations = load_stations()
    results = []

    print(f"Querying Overpass for {len(MATRIX)} cells (3 s delay between queries)...")

    for i, cell in enumerate(MATRIX):
        print(f"  [{i+1:02d}/{len(MATRIX)}] {cell['city']} / {cell['layer']}  "
              f"({cell['lat']:.4f}, {cell['lon']:.4f})  r={cell['radius_m']} m")

        count = count_buildings(cell["lat"], cell["lon"], cell["radius_m"])
        station_label, epw_ok = resolve_epw(cell["lat"], cell["lon"], stations)

        cell_result = {
            **cell,
            "osm_count": count,
            "epw_station": station_label,
            "epw_resolvable": epw_ok,
            "flag": count < 30,
        }
        results.append(cell_result)
        print(f"           count={count}  epw_ok={epw_ok}  flag={'LOW-COUNT' if count < 30 else 'ok'}")

        if i < len(MATRIX) - 1:
            time.sleep(REQUEST_DELAY_S)

    _write_proposal(results)
    print("\nDone. Proposal written.")


def _write_proposal(results: list[dict]) -> None:
    out_path = REPO / "docs" / "validations" / "overAll" / "V10_matrix_proposal.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# V10 Case-Study Matrix Proposal",
        "",
        "> **Generated by:** `scripts/validation/v10_matrix_probe.py`  ",
        "> **Date:** 2026-06-11  ",
        "> **Status:** PENDING USER APPROVAL — do not execute V11 until approved.",
        "",
        "## Proposed 12-cell matrix",
        "",
        "| # | City | Layer | Centre (lat, lon) | radius_m | OSM building count | Expected ASHRAE CZ | EPW resolvable | Notes |",
        "|---|------|-------|-------------------|----------|--------------------|--------------------|----------------|-------|",
    ]

    for i, r in enumerate(results, start=1):
        coord = f"{r['lat']:.4f}, {r['lon']:.4f}"
        epw_status = "Yes" if r["epw_resolvable"] else "No"
        notes = ""
        if r["flag"]:
            notes = f"**FLAG: count {r['osm_count']} < 30 — see adjustment below**"
        lines.append(
            f"| {i} | {r['city']} | {r['layer']} "
            f"| {coord} | {r['radius_m']} "
            f"| {r['osm_count']} "
            f"| {r['expected_cz']} "
            f"| {epw_status} "
            f"| {notes} |"
        )

    flagged = [r for r in results if r["flag"]]
    lines += [
        "",
        "## EPW station assignments",
        "",
        "| # | City | Layer | Nearest EPW station |",
        "|---|------|-------|---------------------|",
    ]
    for i, r in enumerate(results, start=1):
        lines.append(f"| {i} | {r['city']} | {r['layer']} | {r['epw_station']} |")

    if flagged:
        lines += [
            "",
            "## Flagged cells (count < 30) — proposed adjustments",
            "",
        ]
        for r in flagged:
            lines.append(f"### {r['city']} / {r['layer']}")
            lines.append(
                f"- Current: ({r['lat']:.4f}, {r['lon']:.4f}), r={r['radius_m']} m, count={r['osm_count']}"
            )
            lines.append(_suggest_adjustment(r))
            lines.append("")
    else:
        lines += [
            "",
            "## Flagged cells",
            "",
            "None — all cells have OSM building count >= 30.",
            "",
        ]

    lines += [
        "",
        "## User approval",
        "",
        "Please review and edit cell coordinates/radii as needed, then confirm approval to proceed to V11.",
        "The pilot cell for V11 is the **NYC city-centre** cell (row 1) unless you specify otherwise.",
        "",
    ]

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Proposal written to: {out_path}")


def _suggest_adjustment(r: dict) -> str:
    city = r["city"]
    layer = r["layer"]

    suggestions = {
        ("New York City", "rural"): (
            "Increase radius to 1500 m or move centre to a denser Ulster County hamlet "
            "(e.g., Woodstock, NY ~42.0396, -74.1143)."
        ),
        ("Los Angeles", "rural"): (
            "Move centre to Palmdale/Lancaster edge (e.g., 34.5794, -118.1165) which has "
            "more mapped residential grid; or increase radius to 2000 m."
        ),
        ("Austin", "rural"): (
            "Move centre closer to Marble Falls / Johnson City area (~30.5788, -98.2700) "
            "with denser town core; or increase radius to 2000 m."
        ),
    }
    key = (city, layer)
    suggestion = suggestions.get(key, "Increase radius by 500 m or relocate to a nearby denser area.")
    return f"- Suggested adjustment: {suggestion}"


if __name__ == "__main__":
    main()
