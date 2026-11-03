"""One-off builder: parses the climate.onebuilding.org KML for WMO Region 4 / USA,
extracts station metadata, and emits openubem/data/epw_stations.csv.

Source (P2, PLAN §5):
  - climate.onebuilding.org/sources/Region4_USA_TMYx_EPW_Processing_locations.kml

TMYx edition policy (OQ-3, F17): where multiple TMYx editions exist for one station,
prefer the most recent (sort by period string descending, keep newest).

Re-run this script whenever you need to refresh the bundled CSV.
"""
from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path

import pandas as pd
import requests

KML_URL = (
    "https://climate.onebuilding.org/sources/"
    "Region4_USA_TMYx_EPW_Processing_locations.kml"
)

OUT_DIR = Path(__file__).parent.parent / "openubem" / "data"

# Required: 8 fixture-city WMO IDs (F17, T03)
_FIXTURE_WMO = {
    "725090": "Boston Logan",
    "725300": "Chicago OHare",
    "722020": "Miami Intl",
    "722780": "Phoenix Sky Harbor",
    "724940": "San Francisco Intl",
    "725650": "Denver Intl",
    "727450": "Duluth Intl",
    "702610": "Fairbanks Intl",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _parse_dms(coord_str: str) -> float | None:
    """Parse 'N 36 deg 40.98' -> 36.683 or 'W 121 deg 46.02' -> -121.767."""
    m = re.match(r"([NSEW])\s*(\d+)&deg;\s*([\d.]+)'?", coord_str.strip())
    if not m:
        return None
    sign = -1.0 if m.group(1) in ("S", "W") else 1.0
    return sign * (float(m.group(2)) + float(m.group(3)) / 60.0)


def _parse_kml(text: str) -> pd.DataFrame:
    """Extract station rows from the KML text."""
    pm_pattern = re.compile(r"<Placemark>(.*?)</Placemark>", re.DOTALL)
    # ZIP URL pattern: captures the full onebuilding.org URL
    zip_pattern = re.compile(
        r"(https://climate\.onebuilding\.org/"
        r"WMO_Region_4_North_and_Central_America/USA_[^\"]+\.zip)"
    )
    # WMO ID
    wmo_pattern = re.compile(r"WMO\s*<b>(\d+)</b>")
    # Lat/Lon from description: "N 36&deg; 40.98'   W 121&deg; 46.02'"
    latlon_pattern = re.compile(r"([NS])\s*(\d+)&deg;\s*([\d.]+)'\s*([EW])\s*(\d+)&deg;\s*([\d.]+)'")
    # Coordinates element (lon,lat,elev)
    coords_pattern = re.compile(r"<coordinates>(.*?)</coordinates>", re.DOTALL)

    rows: list[dict] = []
    for pm_match in pm_pattern.finditer(text):
        pm = pm_match.group(1)

        zip_urls = zip_pattern.findall(pm)
        if not zip_urls:
            continue

        wmo_m = wmo_pattern.search(pm)
        if not wmo_m:
            continue
        wmo = wmo_m.group(1).zfill(6)

        # Coordinates from <Point>
        coords_m = coords_pattern.search(pm)
        if not coords_m:
            continue
        parts = coords_m.group(1).strip().split(",")
        if len(parts) < 2:
            continue
        lon = float(parts[0])
        lat = float(parts[1])

        # Station name: parse from first ZIP URL basename
        # e.g. USA_CA_Marina.Muni.AP.690070_TMYx.zip -> "Marina.Muni.AP.690070"
        zip_url = zip_urls[0]
        basename = zip_url.split("/")[-1].replace(".zip", "")
        # basename e.g. USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2007-2021
        # state = second segment
        seg = basename.split("_")
        state = seg[1] if len(seg) > 1 else ""

        # Name = station name portion (drop country prefix and WMO suffix and edition)
        # USA_MA_Boston-Logan.Intl.AP.725090_TMYx.2007-2021
        # name = "Boston-Logan.Intl.AP.725090"
        name_full = seg[2] if len(seg) > 2 else ""
        # Strip trailing WMO from name for display
        name = re.sub(r"\." + re.escape(wmo) + r"$", "", name_full)

        # Each placemark has exactly one ZIP URL (one edition).
        # Dedup step at the caller level will pick the newest per station_id.
        best_url = zip_urls[0]
        tmy_m = re.search(r"TMYx\.([\d-]+)", best_url)
        tmy_edition = "TMYx." + tmy_m.group(1) if tmy_m else "TMYx"

        rows.append({
            "station_id": wmo,
            "name": name,
            "state": state,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "url": best_url,
            "tmy_edition": tmy_edition,
        })

    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Downloading USA TMYx KML from climate.onebuilding.org ===")
    r = requests.get(KML_URL, timeout=120)
    r.raise_for_status()
    kml_data = r.content
    kml_sha = _sha256(kml_data)
    print(f"  OK  {len(kml_data):,} bytes,  SHA-256: {kml_sha}")

    print("=== Parsing KML placemarks ===")
    df = _parse_kml(kml_data.decode("utf-8"))
    print(f"  Raw rows: {len(df)}")

    # Deduplicate: per station_id keep newest TMYx (sort by tmy_edition descending)
    # Each KML placemark = one edition; we may have multiple rows per WMO ID.
    # Edition strings: "TMYx.2011-2025" > "TMYx.2009-2023" > "TMYx.2007-2021" > "TMYx.2004-2018" > "TMYx"
    # Sorting descending string-wise puts "TMYx.2011-2025" first (OQ-3 policy).
    df = df.sort_values("tmy_edition", ascending=False)
    df = df.drop_duplicates(subset="station_id", keep="first")
    print(f"  After dedup on station_id (newest TMYx kept): {len(df)}")

    # Validate fixture stations
    all_ok = True
    for wmo, label in _FIXTURE_WMO.items():
        hit = df[df["station_id"] == wmo]
        if hit.empty:
            print(f"  MISSING fixture station WMO {wmo} ({label})")
            all_ok = False
        else:
            row = hit.iloc[0]
            print(f"  OK  WMO {wmo} ({label}): {row['name']}, {row['state']}, lat={row['lat']}, url={row['url'][-50:]}")

    if not all_ok:
        raise ValueError("One or more fixture stations missing from parsed CSV.")

    out_path = OUT_DIR / "epw_stations.csv"
    df.to_csv(str(out_path), index=False)
    csv_data = out_path.read_bytes()
    csv_sha = _sha256(csv_data)
    print(f"\n  Written: {out_path}")
    print(f"  CSV rows: {len(df)},  SHA-256: {csv_sha}")

    # Append to PROVENANCE.md
    prov_path = OUT_DIR / "climate_zones" / "PROVENANCE.md"
    prov_addition = f"""

## epw_stations.csv

| Artifact | URL | Retrieved | SHA-256 |
|---|---|---|---|
| Region4_USA_TMYx KML | {KML_URL} | {date.today()} | {kml_sha} |
| epw_stations.csv (emitted) | (local) | {date.today()} | {csv_sha} |

- Rows: {len(df)} unique US weather stations (TMYx editions)
- Columns: station_id (WMO 6-digit str), name, state, lat, lon, url, tmy_edition
- TMYx edition policy: newest edition kept where multiple exist (OQ-3, PLAN §5 P2)
- License: data from climate.onebuilding.org — free for non-commercial use; see
  https://climate.onebuilding.org/

## Refresh

Re-run `scripts/build_epw_stations_csv.py` from the project root with network access.
"""
    if prov_path.exists():
        with open(str(prov_path), "a", encoding="utf-8") as f:
            f.write(prov_addition)
    else:
        # Write standalone provenance if GPKG provenance doesn't exist yet
        (OUT_DIR / "epw_stations_PROVENANCE.md").write_text(prov_addition, encoding="utf-8")

    print(f"\n=== Done. Rows: {len(df)}, CSV SHA-256: {csv_sha} ===")


if __name__ == "__main__":
    main()
