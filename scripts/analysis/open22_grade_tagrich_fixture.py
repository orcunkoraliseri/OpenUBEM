"""T03 (OPEN-22): grade the classifier (HEAD) against the new tag-rich v2 fixture,
and confirm the OLD fixture still scores 44/50 = 88.0% (a required precondition per
the plan: "if it does not, stop, because something else has changed").

This is the ONLY script in this task that imports the classifier — deliberately run
after tests/fixtures/labelled_archetypes_tagrich_v2.csv was written by
open22_build_tagrich_fixture.py (which never imports it), so the labels cannot have
been influenced by classifier output.

Emits openubem/outputs/comparisons/open22_v2_fixture_breakdown.csv:
osm_id, source, label, emitted, rule_token, confidence, match (one row per fixture
row, UNDETERMINED rows included but excluded from the accuracy computation).

Usage: python scripts/analysis/open22_grade_tagrich_fixture.py
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

from openubem.semantic.building_classifier import BuildingClassifier, _INPUT_SCHEMA_COLUMNS

REPO_ROOT = Path(__file__).resolve().parents[2]


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


def main() -> None:
    print("=== Precondition: old fixture (labelled_archetypes_50.csv) must still score 44/50 = 88.0% ===")
    old = classify_fixture(REPO_ROOT / "tests/fixtures/labelled_archetypes_50.csv")
    old_match = (old["archetype_id"] == old["expected_archetype"])
    old_acc = old_match.mean()
    print(f"old fixture: {old_match.sum()}/{len(old)} = {old_acc:.1%}")
    if abs(old_acc - 0.88) > 0.005:
        print("STOP: old fixture did not reproduce 88.0% — something else has changed. "
              "Not proceeding to grade the new fixture.")
        raise SystemExit(1)
    print("Confirmed: old fixture reproduces 88.0% exactly. Proceeding.\n")

    print("=== New fixture: labelled_archetypes_tagrich_v2.csv ===")
    new = classify_fixture(REPO_ROOT / "tests/fixtures/labelled_archetypes_tagrich_v2.csv")
    new["rule_token"] = new["archetype_source"].astype(str).str.split(",").str[0]

    graded = new[new["expected_archetype"] != "UNDETERMINED"].copy()
    graded["match"] = graded["archetype_id"] == graded["expected_archetype"]

    n_total = len(new)
    n_undetermined = (new["expected_archetype"] == "UNDETERMINED").sum()
    n_graded = len(graded)
    n_match = graded["match"].sum()
    acc_overall = n_match / n_graded

    n_fallback = (graded["rule_token"] == "FALLBACK_SIZE_DEFAULT").sum()
    fallback_share = n_fallback / n_graded

    excl_fb = graded[graded["rule_token"] != "FALLBACK_SIZE_DEFAULT"]
    acc_excl_fb = excl_fb["match"].mean() if len(excl_fb) else float("nan")

    print(f"rows total: {n_total}  UNDETERMINED (excluded): {n_undetermined}  graded: {n_graded}")
    print(f"accuracy overall (graded rows): {n_match}/{n_graded} = {acc_overall:.1%}")
    print(f"FALLBACK_SIZE_DEFAULT rows: {n_fallback}/{n_graded} = {fallback_share:.1%}  "
          f"(old fixture: 17/50 = 34.0%)")
    print(f"accuracy excluding FALLBACK_SIZE_DEFAULT rows: "
          f"{excl_fb['match'].sum()}/{len(excl_fb)} = {acc_excl_fb:.1%}")

    out = new[[
        "osm_id", "source_fixture", "expected_archetype", "archetype_id",
        "archetype_confidence", "rule_token",
    ]].copy()
    out["match"] = (out["archetype_id"] == out["expected_archetype"]).astype(object)
    out.loc[new["expected_archetype"] == "UNDETERMINED", "match"] = pd.NA
    out.columns = ["osm_id", "source", "label", "emitted", "confidence", "rule_token", "match"]
    out = out[["osm_id", "source", "label", "emitted", "rule_token", "confidence", "match"]]

    out_path = REPO_ROOT / "openubem/outputs/comparisons/open22_v2_fixture_breakdown.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path, index=False)
    print(f"\nwrote {out_path} ({len(out)} rows)")


if __name__ == "__main__":
    main()
