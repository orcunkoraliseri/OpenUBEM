"""Build the 50-row CSV template for hand-labelling (Boston-30 + Chicago-20).
Run after build_osm_fixtures.py: py tests/fixtures/build_labelled_template.py
Binding contract: docs/docs_step2/PLAN_step-2.5-oq7-labelled-fixture.md §6 L1
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

_FIXTURES_DIR = Path(__file__).parent
_TEMPLATE_OUT = _FIXTURES_DIR / "labelled_archetypes_50.template.csv"

_SOURCES = [
    ("boston_downtown_500m", "boston_downtown_500m.gpkg", 30),
    ("chicago_loop_500m",    "chicago_loop_500m.gpkg",    20),
]

_COLS_OUT = [
    "osm_id",
    "source_fixture",
    "building_tag",
    "function_tag",
    "levels",
    "height_m",
    "footprint_area_m2",
    "expected_archetype",
    "expected_coarse_class",
    "notes",
]


def _load_and_sample(slug: str, filename: str, n: int) -> pd.DataFrame:
    gpkg_path = _FIXTURES_DIR / filename
    if not gpkg_path.exists():
        raise FileNotFoundError(
            f"Run tests/fixtures/build_osm_fixtures.py first to materialise {gpkg_path}"
        )
    gdf = gpd.read_file(gpkg_path, layer=slug)
    sample = gdf.sample(n=n, random_state=42)
    df = pd.DataFrame({
        "osm_id":              sample["osm_id"].astype(str),
        "source_fixture":      slug,
        "building_tag":        sample["building_tag"],
        "function_tag":        sample["function_tag"],
        "levels":              sample["levels"],
        "height_m":            sample["height_m"],
        "footprint_area_m2":   sample["footprint_area_m2"],
        "expected_archetype":  "",
        "expected_coarse_class": "",
        "notes":               "",
    })
    return df


if __name__ == "__main__":
    frames = []
    for slug, filename, n in _SOURCES:
        frames.append(_load_and_sample(slug, filename, n))

    combined = (
        pd.concat(frames, ignore_index=True)
        .sort_values(["source_fixture", "osm_id"])
        .reset_index(drop=True)
    )

    combined[_COLS_OUT].to_csv(_TEMPLATE_OUT, index=False)
    print(f"wrote template: {len(combined)} rows -> {_TEMPLATE_OUT}")
    print("Fill 'expected_archetype' and 'expected_coarse_class', then save as labelled_archetypes_50.csv")
