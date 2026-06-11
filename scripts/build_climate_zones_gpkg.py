"""One-off builder: downloads US Census county boundaries + ResStock county→climate-zone
matrix, joins them, and emits openubem/data/climate_zones/ashrae_climate_zones.gpkg.

Sources (P1, PLAN §5):
  - Census cb_2023_us_county_500k  (public domain)
  - NREL ResStock county/PUMA TSV  (Creative Commons, ASHRAE 169/IECC 2004-consistent)

The ResStock file encodes the DOE/PNNL county→zone assignment as a probability matrix
(Dependency=ASHRAE IECC Climate Zone 2004 vs county GISJOINs).  Each county is assigned
the zone with the highest probability mass (effectively deterministic: each county belongs
to exactly one zone in the source data).

Re-run this script whenever you need to refresh the bundled GPKG.
"""
from __future__ import annotations

import hashlib
import io
import tempfile
import zipfile
from datetime import date
from pathlib import Path

import geopandas as gpd
import pandas as pd
import requests

CENSUS_URL = (
    "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_county_500k.zip"
)
RESSTOCK_CZ_URL = (
    "https://raw.githubusercontent.com/NREL/resstock/main/"
    "project_national/housing_characteristics/County%20and%20PUMA.tsv"
)

# F3 vocabulary (DESIGN line 64); ResStock uses '7A', '7AK', '7B', '8AK' for zones 7 & 8.
_F3_VOCAB: frozenset[str] = frozenset(
    {"1A", "2A", "2B", "3A", "3B", "3C", "4A", "4B", "4C", "5A", "5B", "5C", "6A", "6B", "7", "8"}
)
_RESSTOCK_NORMALISE = {
    "7A": "7", "7AK": "7", "7B": "7", "8AK": "8",
}

OUT_DIR = Path(__file__).parent.parent / "openubem" / "data" / "climate_zones"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get(url: str, label: str) -> bytes:
    print(f"  GET {label} ...")
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    print(f"  OK  {len(r.content):,} bytes")
    return r.content


def _load_counties_win() -> tuple[gpd.GeoDataFrame, str]:
    data = _get(CENSUS_URL, "Census cb_2023_us_county_500k")
    sha = _sha256(data)
    tmpdir = Path(tempfile.mkdtemp(prefix="county_shp_"))
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(str(tmpdir))
    shp_files = list(tmpdir.glob("*.shp"))
    if not shp_files:
        raise RuntimeError(f"No .shp file found in Census zip; extracted to {tmpdir}")
    gdf = gpd.read_file(str(shp_files[0]))
    gdf = gdf[["GEOID", "STUSPS", "geometry"]].rename(
        columns={"GEOID": "county_geoid", "STUSPS": "state_abbrev"}
    )
    gdf = gdf.to_crs(epsg=4326)
    return gdf, sha


def _load_resstock_zones() -> tuple[pd.DataFrame, str]:
    """Parse ResStock county/PUMA TSV → DataFrame(county_geoid, climate_zone)."""
    data = _get(RESSTOCK_CZ_URL, "ResStock County and PUMA TSV")
    sha = _sha256(data)

    lines = [l for l in data.decode("utf-8").split("\n") if l.strip() and not l.startswith("#")]

    header_cols = lines[0].split("\t")  # first col = Dependency=..., rest = Option=GISJOIN,...

    def _parse_gisjoin(opt_str: str) -> str | None:
        # format: "Option=G{state2d}0{county3d}, {puma5d}"
        gisjoin = opt_str.replace("Option=", "").split(",")[0].strip()
        # GISJOIN: G + 2-digit state + 0 + 3-digit county (8 chars total)
        if len(gisjoin) == 8 and gisjoin.startswith("G"):
            return gisjoin[1:3] + gisjoin[4:7]
        return None

    county_fips_list = []
    for col in header_cols[1:]:
        fips = _parse_gisjoin(col)
        county_fips_list.append(fips)

    zone_county_map: dict[str, dict[str, float]] = {}
    for line in lines[1:]:
        parts = line.split("\t")
        if not parts:
            continue
        raw_zone = parts[0].strip()
        zone = _RESSTOCK_NORMALISE.get(raw_zone, raw_zone)
        if zone not in _F3_VOCAB:
            continue
        for i, val in enumerate(parts[1:len(county_fips_list) + 1]):
            try:
                v = float(val)
            except ValueError:
                continue
            if v <= 0:
                continue
            fips = county_fips_list[i]
            if fips is None:
                continue
            if fips not in zone_county_map:
                zone_county_map[fips] = {}
            zone_county_map[fips][zone] = v

    records = []
    for fips, zones in zone_county_map.items():
        best_zone = max(zones, key=zones.get)
        records.append({"county_geoid": fips, "climate_zone": best_zone})

    return pd.DataFrame(records), sha


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Loading Census county boundaries ===")
    counties_gdf, census_sha = _load_counties_win()
    print(f"  Counties loaded: {len(counties_gdf)} rows")

    print("=== Loading ResStock county->climate-zone matrix ===")
    doe_df, resstock_sha = _load_resstock_zones()
    print(f"  Zone rows: {len(doe_df)}")

    print("=== Joining ===")
    merged = counties_gdf.merge(doe_df, on="county_geoid", how="left")
    n_no_zone = merged["climate_zone"].isna().sum()
    if n_no_zone:
        print(f"  {n_no_zone} counties without a zone mapping (territories) — dropped")
    merged = merged.dropna(subset=["climate_zone"])

    bad_zones = set(merged["climate_zone"].unique()) - _F3_VOCAB
    if bad_zones:
        raise ValueError(f"Unexpected zone tokens after join: {bad_zones}")
    assert merged["county_geoid"].is_unique, "county_geoid not unique after join"
    assert 3000 <= len(merged) <= 3300, f"Unexpected row count: {len(merged)}"

    print(f"  Final: {len(merged)} counties, zones: {sorted(merged['climate_zone'].unique())}")

    # Validate 8 fixture cities
    _FIXTURE = {
        "Miami-Dade (12086)": ("12086", "1A"),
        "Maricopa (04013)": ("04013", "2B"),
        "San Francisco (06075)": ("06075", "3C"),
        "Suffolk MA (25025)": ("25025", "5A"),
        "Cook IL (17031)": ("17031", "5A"),
        "Denver CO (08031)": ("08031", "5B"),
        "St. Louis MN (27137)": ("27137", "7"),
        "Fairbanks NS AK (02090)": ("02090", "8"),
    }
    lookup = merged.set_index("county_geoid")["climate_zone"].to_dict()
    all_ok = True
    for label, (fips, expected) in _FIXTURE.items():
        got = lookup.get(fips, "NOT FOUND")
        status = "OK" if got == expected else "FAIL"
        print(f"  {status}  {label}: expected {expected}, got {got}")
        if status == "FAIL":
            all_ok = False
    if not all_ok:
        raise ValueError("One or more fixture-city zone assertions failed — check source data.")

    out_path = OUT_DIR / "ashrae_climate_zones.gpkg"
    merged.to_file(str(out_path), layer="counties", driver="GPKG")
    gpkg_data = out_path.read_bytes()
    gpkg_sha = _sha256(gpkg_data)
    print(f"  Written: {out_path}")
    print(f"  GPKG SHA-256: {gpkg_sha}")

    prov = f"""# PROVENANCE — ashrae_climate_zones.gpkg

## Sources

| Artifact | URL | Retrieved | SHA-256 |
|---|---|---|---|
| Census cb_2023_us_county_500k | {CENSUS_URL} | {date.today()} | {census_sha} |
| ResStock County and PUMA TSV | {RESSTOCK_CZ_URL} | {date.today()} | {resstock_sha} |
| ashrae_climate_zones.gpkg (emitted) | (local) | {date.today()} | {gpkg_sha} |

## Edition

ASHRAE 169-2013-consistent county→zone assignments sourced from the NREL ResStock
housing-characteristics matrix (Dependency=ASHRAE IECC Climate Zone 2004).  Each county
is assigned the zone with the highest probability mass in that matrix (deterministic:
all probabilities in the ResStock data are 0 or 1 for IECC climate zones).

OQ-1 resolution (PLAN §4 F16): pinned to ASHRAE 169-2013-consistent edition to match
the bundled 90.1-2019 construction tables.  IECC-2021 re-assignments not applied.

ResStock zone tokens 7A, 7AK, 7B → F3 vocab token `7`; 8AK → `8`.

## License

US Census Bureau cartographic boundary files: public domain (US government work).
NREL ResStock housing characteristics: Creative Commons Attribution 4.0 International
(https://github.com/NREL/resstock/blob/main/LICENSE.md).

## Layer spec

- Layer name: `counties`
- CRS: EPSG:4326
- Columns: `county_geoid` (5-digit FIPS, str), `state_abbrev` (2-letter USPS, str),
  `climate_zone` (16-token closed vocab per DESIGN line 64), `geometry`
- Row count: {len(merged)} (territories with no zone assignment dropped: {n_no_zone})
- `county_geoid` is unique

## Fixture-city validation (all passed)

| City | county_geoid | Expected zone | Got |
|---|---|---|---|
| Miami-Dade FL | 12086 | 1A | {lookup.get('12086','?')} |
| Maricopa AZ | 04013 | 2B | {lookup.get('04013','?')} |
| San Francisco CA | 06075 | 3C | {lookup.get('06075','?')} |
| Suffolk MA | 25025 | 5A | {lookup.get('25025','?')} |
| Cook IL | 17031 | 5A | {lookup.get('17031','?')} |
| Denver CO | 08031 | 5B | {lookup.get('08031','?')} |
| St. Louis MN | 27137 | 7 | {lookup.get('27137','?')} |
| Fairbanks NS AK | 02090 | 8 | {lookup.get('02090','?')} |

## Refresh

Re-run `scripts/build_climate_zones_gpkg.py` from the project root with network access.
"""
    (OUT_DIR / "PROVENANCE.md").write_text(prov, encoding="utf-8")
    print("  PROVENANCE.md written.")
    print(f"\n=== Done. Row count: {len(merged)}, GPKG SHA-256: {gpkg_sha} ===")


if __name__ == "__main__":
    main()
