"""Materialise the two source fixtures (Boston + Chicago) for the OQ-7 labelled-accuracy gate.
Run once on your local machine: py tests/fixtures/build_osm_fixtures.py
Binding contract: docs/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md §6 L0
"""

from pathlib import Path

from openubem.acquisition.osm_fetcher import ingest_buildings

_CITIES = [
    ("boston_downtown_500m", "Downtown Boston, MA", 500.0, "boston_downtown_500m.gpkg"),
    ("chicago_loop_500m",    "The Loop, Chicago, IL", 500.0, "chicago_loop_500m.gpkg"),
]

if __name__ == "__main__":
    for slug, location, radius_m, filename in _CITIES:
        out_path = Path(__file__).parent / filename
        gdf = ingest_buildings(location=location, radius_m=radius_m)
        assert len(gdf) >= 100, f"{slug}: expected ≥ 100 rows, got {len(gdf)}"
        gdf.to_file(out_path, driver="GPKG", layer=slug)
        print(f"wrote {slug}: {len(gdf)} rows -> {out_path}")
