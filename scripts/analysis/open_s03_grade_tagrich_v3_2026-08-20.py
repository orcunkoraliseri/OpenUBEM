"""S03 T02: run the classifier (HEAD) over labelled_archetypes_tagrich_v3.csv (592 rows, no
sampling) and report fine/coarse top-1 as a MEASUREMENT, not a gate -- no pass mark from the
old fixtures carries over to this new exam (checklist ruling 2a).

This is the only script in the S03 task that imports the classifier.

Usage: python scripts/analysis/open_s03_grade_tagrich_v3_2026-08-20.py
"""

from collections import Counter
from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.semantic.building_classifier import BuildingClassifier, _INPUT_SCHEMA_COLUMNS, _VALID_30

REPO_ROOT = Path(__file__).resolve().parents[2]

_COARSE_CLASS_MAP: dict[str, str] = {
    "MidriseApartment": "residential",
    "HighriseApartment": "residential",
    **{aid: "commercial" for aid in _VALID_30 - {"MidriseApartment", "HighriseApartment"}},
}


def _reorder(gdf):
    geom_col = gdf.geometry.name
    cols = [geom_col] + [c for c in _INPUT_SCHEMA_COLUMNS if c != geom_col and c in gdf.columns]
    return gdf[cols]


def classify_fixture(csv_path: Path) -> pd.DataFrame:
    lab = pd.read_csv(csv_path, comment="#")
    bos = gpd.read_file(REPO_ROOT / "tests/fixtures/boston_downtown_500m.gpkg")
    chi = gpd.read_file(REPO_ROOT / "tests/fixtures/chicago_loop_500m.gpkg")
    for gdf in (bos, chi):
        for col in ("levels", "year_built", "underground"):
            if col in gdf.columns:
                gdf[col] = gdf[col].astype("Int64")
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
    return lab.merge(results, on="osm_id", how="left")


def report(name: str, df: pd.DataFrame) -> None:
    fine_acc = (df["archetype_id"] == df["expected_archetype"]).mean()
    pred_coarse = df["archetype_id"].map(_COARSE_CLASS_MAP)
    coarse_acc = (pred_coarse == df["expected_coarse_class"]).mean()
    print(f"{name}: n={len(df)}  fine top-1={fine_acc:.1%}  coarse top-1={coarse_acc:.1%}")


def main() -> None:
    merged = classify_fixture(REPO_ROOT / "tests/fixtures/labelled_archetypes_tagrich_v3.csv")
    merged["rule_token"] = merged["archetype_source"].astype(str).str.split(",").str[0]
    merged["match"] = merged["archetype_id"] == merged["expected_archetype"]

    print("=== S03 v3 measurement (not a gate) ===")
    report("all 592", merged)
    strong = merged[merged["evidence_strength"] == "strong"]
    report("strong subset", strong)
    thin = merged[merged["evidence_strength"] == "thin"]
    report("thin subset (n=3)", thin)

    confusion = Counter(
        zip(merged.loc[~merged["match"], "expected_archetype"], merged.loc[~merged["match"], "archetype_id"])
    )
    print("\ntop confusion pairs (expected -> emitted : count):")
    for (exp, emit), n in confusion.most_common(10):
        print(f"  {exp} -> {emit} : {n}")

    out = merged[[
        "osm_id", "source_fixture", "expected_archetype", "expected_coarse_class",
        "evidence_strength", "flagged_for_ruling", "archetype_id", "archetype_confidence",
        "rule_token", "match",
    ]].copy()
    out.columns = [
        "osm_id", "source", "label", "label_coarse", "evidence_strength", "flagged_for_ruling",
        "emitted", "confidence", "rule_token", "match",
    ]
    out_path = REPO_ROOT / "openubem/outputs/comparisons/open_s03_v3_fixture_breakdown.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path} ({len(out)} rows)")


if __name__ == "__main__":
    main()
