"""T10 (OPEN-04) worker: classify the CURRENT labelled fixture using one commit's
classifier code, loaded from an arbitrary openubem root (main tree or a disposable
worktree). Emits one JSON object to stdout: {"rows": [...]}.

Invoked as a subprocess per commit by open04_ruletoken_by_commit.py so that each
commit's version of openubem.semantic.building_classifier is imported cleanly,
with no cross-commit module-cache contamination in a single process.

Usage:
    python open04_ruletoken_worker.py <openubem_root> <fixture_root>

<openubem_root>  directory containing an openubem/ package (worktree or main tree).
<fixture_root>   directory containing tests/fixtures/ — always the MAIN tree, so the
                  fixture (inputs AND labels) is held constant across every commit.
"""

import json
import sys
from pathlib import Path

openubem_root = Path(sys.argv[1]).resolve()
fixture_root = Path(sys.argv[2]).resolve()

sys.path.insert(0, str(openubem_root))

import geopandas as gpd
import pandas as pd

from openubem.semantic.building_classifier import BuildingClassifier, _INPUT_SCHEMA_COLUMNS

csv_path = fixture_root / "tests" / "fixtures" / "labelled_archetypes_50.csv"
lab = pd.read_csv(csv_path, comment="#")
bos = gpd.read_file(fixture_root / "tests" / "fixtures" / "boston_downtown_500m.gpkg")
chi = gpd.read_file(fixture_root / "tests" / "fixtures" / "chicago_loop_500m.gpkg")

for gdf in (bos, chi):
    for col in ("levels", "year_built", "underground"):
        if col in gdf.columns:
            gdf[col] = gdf[col].astype("Int64")


def _reorder(gdf):
    geom_col = gdf.geometry.name
    cols = [geom_col] + [c for c in _INPUT_SCHEMA_COLUMNS if c != geom_col and c in gdf.columns]
    return gdf[cols]


bos = _reorder(bos)
chi = _reorder(chi)

clf = BuildingClassifier()
bos_out = clf.classify(bos)
chi_out = clf.classify(chi)

results = pd.concat([
    bos_out[["osm_id", "archetype_id", "archetype_confidence", "archetype_source"]],
    chi_out[["osm_id", "archetype_id", "archetype_confidence", "archetype_source"]],
])
results["osm_id"] = results["osm_id"].astype(str)
lab["osm_id"] = lab["osm_id"].astype(str)

merged = lab.merge(results, on="osm_id", how="left")
merged["rule_token"] = merged["archetype_source"].astype(str).str.split(",").str[0]
merged["match"] = merged["archetype_id"] == merged["expected_archetype"]

out_rows = merged[[
    "osm_id", "source_fixture", "expected_archetype", "archetype_id",
    "archetype_confidence", "archetype_source", "rule_token", "match",
]].to_dict("records")

print(json.dumps({"n": len(merged), "rows": out_rows}, default=str))
