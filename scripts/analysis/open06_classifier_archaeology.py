"""OPEN-06 classifier archaeology.

For each historical state of openubem/semantic/building_classifier.py (six commits
that ever touched the file), classify the 41 buildings the register flags as
mislabelled Office (should be Hotel per raw OSM tags), using the same raw inputs
and production subsetting step2_classify_enrich() uses
(scripts/validation/v12_cell_pipeline.py:153-166):

    gdf_raw2 = gdf_raw[_INPUT_SCHEMA_COLUMNS].copy()
    gdf_raw2["levels"] = gdf_raw2["levels"].astype("Int64")
    gdf_26 = BuildingClassifier().classify(gdf_raw2)

Read-only git only. Historical module source files are pre-extracted into the
scratchpad via `git show <sha>:path > scratchpad/classifiers/classifier_<sha>.py`
(never `git checkout`). This script imports each of those files as an isolated
module (importlib, unique module name per commit) and calls its BuildingClassifier.
A version whose import raises is recorded as NOT_LOADABLE with the verbatim
exception text; the run continues to the next commit.

Emits openubem/outputs/comparisons/open06_classifier_archaeology.csv:
one row per (commit, cell, osm_id) with emitted_archetype (or NOT_LOADABLE /
CLASSIFY_ERROR), plus per-commit summary printed to stdout.
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
POPULATION_CSV = REPO_ROOT / "openubem/outputs/comparisons/open06_mislabel_population.csv"
PHASEE_ROOT = REPO_ROOT / "docs/docs_VALIDATION/validations/overAll/results/phaseE"
OUT_CSV = REPO_ROOT / "openubem/outputs/comparisons/open06_classifier_archaeology.csv"

SCRATCHPAD_CLASSIFIERS = Path(
    r"C:\Users\o_iseri\AppData\Local\Temp\claude\C--Users-o-iseri-Desktop-OpenUBEM"
    r"\09959dcb-5fc3-40a7-b556-ee8eb01480af\scratchpad\classifiers"
)

# The six commits that ever touched openubem/semantic/building_classifier.py,
# oldest first (per `git log --reverse -- openubem/semantic/building_classifier.py`).
COMMITS_OLDEST_FIRST = [
    "42f0c1d",
    "62e5968",
    "7635ce2",
    "67ede73",
    "0df422e",
    "6aeebb0",
]

HEAD_SHA = "6aeebb0"  # working tree is byte-identical to this commit (verified: git diff empty)


def load_population() -> pd.DataFrame:
    df = pd.read_csv(POPULATION_CSV)
    assert len(df) == 41, f"expected 41 rows, got {len(df)}"
    return df


def load_raw_full_cell(cell: str, input_schema_columns: list[str]) -> gpd.GeoDataFrame:
    """Load and subset the FULL cell (production classifies a whole cell in one
    call; group-median levels imputation (GROUPMEDIAN_LEVELS_MED) depends on the
    batch it is given, so classifying only the population subset in isolation
    changes its result — confirmed empirically: subsetting first before classify()
    flipped 2/41 rows LargeHotel->SmallHotel in austin_centre vs. N04/N07's own
    full-cell method. Filter to the population osm_ids AFTER classify(), not before."""
    gpkg_path = PHASEE_ROOT / cell / "01_buildings.gpkg"
    gdf_raw = gpd.read_file(str(gpkg_path))
    gdf_raw2 = gdf_raw[input_schema_columns].copy()
    gdf_raw2["levels"] = gdf_raw2["levels"].astype("Int64")
    return gdf_raw2


def import_classifier_module(sha: str):
    """Import scratchpad/classifiers/classifier_<sha>.py as an isolated module.
    Returns (module, error_text). error_text is None on success.
    """
    src_path = SCRATCHPAD_CLASSIFIERS / f"classifier_{sha}.py"
    mod_name = f"_open06_archaeology_classifier_{sha}"
    try:
        spec = importlib.util.spec_from_file_location(mod_name, src_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
        return module, None
    except Exception:
        sys.modules.pop(mod_name, None)
        return None, traceback.format_exc()


def run_commit(sha: str, population: pd.DataFrame) -> list[dict]:
    rows = []

    if sha == HEAD_SHA:
        # Working tree is byte-identical to 6aeebb0 (verified via `git diff 6aeebb0 --
        # openubem/semantic/building_classifier.py` -> empty). Use the real,
        # already-installed package import rather than re-importing the scratchpad
        # copy under a synthetic module name, so this is a true control run through
        # the actual package (matching N04/N07's own method).
        from openubem.semantic.building_classifier import BuildingClassifier, _INPUT_SCHEMA_COLUMNS
        classifier_cls = BuildingClassifier
        input_schema_columns = list(_INPUT_SCHEMA_COLUMNS)
        load_error = None
    else:
        module, load_error = import_classifier_module(sha)
        classifier_cls = getattr(module, "BuildingClassifier", None) if module else None
        input_schema_columns = list(getattr(module, "_INPUT_SCHEMA_COLUMNS", [])) if module else None

    if load_error is not None or classifier_cls is None:
        for _, prow in population.iterrows():
            rows.append({
                "commit": sha,
                "cell": prow["cell"],
                "osm_id": prow["osm_id"],
                "emitted_archetype": "NOT_LOADABLE",
                "load_error": (load_error or "BuildingClassifier not found in module").strip(),
            })
        return rows

    for cell, group in population.groupby("cell"):
        osm_ids = group["osm_id"].tolist()
        try:
            gdf_full_cell = load_raw_full_cell(cell, input_schema_columns)
            bc = classifier_cls()
            gdf_out = bc.classify(gdf_full_cell)
            emitted = dict(zip(gdf_out["osm_id"], gdf_out["archetype_id"]))
        except Exception:
            err_text = traceback.format_exc()
            for oid in osm_ids:
                rows.append({
                    "commit": sha,
                    "cell": cell,
                    "osm_id": oid,
                    "emitted_archetype": "CLASSIFY_ERROR",
                    "load_error": err_text.strip(),
                })
            continue

        for oid in osm_ids:
            rows.append({
                "commit": sha,
                "cell": cell,
                "osm_id": oid,
                "emitted_archetype": emitted.get(oid, "MISSING_FROM_OUTPUT"),
                "load_error": "",
            })

    return rows


def main() -> None:
    population = load_population()

    # --- Control first: HEAD must reproduce N04 exactly: 41/41, 33 LargeHotel + 8 SmallHotel ---
    control_rows = run_commit(HEAD_SHA, population)
    control_df = pd.DataFrame(control_rows)
    n_large_hotel = int((control_df["emitted_archetype"] == "LargeHotel").sum())
    n_small_hotel = int((control_df["emitted_archetype"] == "SmallHotel").sum())
    n_total = len(control_df)
    print(f"CONTROL (HEAD / {HEAD_SHA}): {n_total} rows, LargeHotel={n_large_hotel}, SmallHotel={n_small_hotel}")
    if n_total != 41 or n_large_hotel != 33 or n_small_hotel != 8:
        print("CONTROL DID NOT REPRODUCE N04 (41/41, 33 LargeHotel + 8 SmallHotel). STOPPING.")
        control_df.insert(0, "is_control_check", True)
        control_df.to_csv(OUT_CSV, index=False)
        sys.exit(1)
    print("CONTROL REPRODUCED N04 EXACTLY. Proceeding to historical archaeology.")

    all_rows: list[dict] = []
    all_rows.extend(control_rows)  # HEAD / 6aeebb0's rows, already computed

    for sha in COMMITS_OLDEST_FIRST:
        if sha == HEAD_SHA:
            continue  # already computed as the control
        rows = run_commit(sha, population)
        all_rows.extend(rows)
        n_loadable = sum(1 for r in rows if r["emitted_archetype"] not in ("NOT_LOADABLE", "CLASSIFY_ERROR"))
        n_office = sum(1 for r in rows if "Office" in str(r["emitted_archetype"]))
        print(f"{sha}: {len(rows)} rows, loadable={n_loadable}, contains 'Office'={n_office}")

    out_df = pd.DataFrame(all_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_CSV, index=False)
    print(f"\nWrote {len(out_df)} rows to {OUT_CSV}")

    # Per-commit summary
    print("\nPer-commit summary:")
    for sha in COMMITS_OLDEST_FIRST:
        sub = out_df[out_df["commit"] == sha]
        n_not_loadable = int((sub["emitted_archetype"] == "NOT_LOADABLE").sum())
        n_classify_error = int((sub["emitted_archetype"] == "CLASSIFY_ERROR").sum())
        n_office = int(sub["emitted_archetype"].astype(str).str.contains("Office").sum())
        n_hotel = int(sub["emitted_archetype"].astype(str).str.contains("Hotel").sum())
        print(f"  {sha}: total={len(sub)} not_loadable={n_not_loadable} classify_error={n_classify_error} "
              f"office={n_office} hotel={n_hotel}")


if __name__ == "__main__":
    main()
