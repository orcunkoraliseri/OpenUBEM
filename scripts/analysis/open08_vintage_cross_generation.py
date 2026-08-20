"""X05 of PLAN_ten-items-2026-08-18-overnight.md -- OPEN-08's vintage half.

OPEN-08 has been half-measured since 2026-08-05: the ARCHETYPE side of the cross-generation
divergence is 13.40 % on 4,530 shared buildings, and the VINTAGE side has been blocked
throughout on a schema gap -- "no prior-generation source carries `vintage_standard`".
That blocker was already found stale once (T03, 2026-08-18) when OPEN-30 turned out to have
closed a week earlier. It is re-tested here rather than inherited.

What this task establishes first, on disk:
  * Does any corpus still carry `vintage_standard`? (The 2026-08-17 sweep emptied E02's
    `.sql` and `.idf`; whether it took the small parquet manifests too was never checked.)
  * Does run 2 / run 3 carry it? (They post-date every prior statement about this item.)

Then, if a source exists, it runs the comparison the item has never had: E02's PERSISTED
`vintage_standard` against a HEAD RE-DERIVATION from the same buildings' `year_built`,
using production `resolve_vintage()` -- not a re-implementation.

Mode is held fixed at `auto` on both sides, because run 2 is an `auto` fleet and comparing
across resolution modes would confound the generation question with the mode question.

Emits openubem/outputs/comparisons/open08_vintage_cross_generation.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

RUN2 = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
E02 = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_e02_fleet")
RESULTS = ROOT / "docs/validations/overAll/results/open48_refleet"
OUT = ROOT / "openubem" / "outputs" / "comparisons"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]


def main() -> int:
    from openubem.semantic.construction_sets import resolve_vintage

    print("=" * 78)
    print("X05 -- OPEN-08: is the vintage half measurable today?")
    print("=" * 78)
    print("\n--- step 1: which corpora survive, and which carry vintage_standard ---")
    for name, root, rel in (("E02", E02, "austin_centre/step3_auto/03_manifest.parquet"),
                            ("run 2", RUN2, "austin_centre/04_simulation_manifest.parquet")):
        p = root / rel
        ok = p.exists()
        cols = list(pd.read_parquet(p).columns) if ok else []
        print("  %-6s %-58s exists=%-5s vintage_standard=%s"
              % (name, rel, ok, "vintage_standard" in cols))

    rows = []
    for cell in CELLS:
        e = E02 / cell / "step3_auto" / "03_manifest.parquet"
        g = RUN2 / cell / "01_buildings.gpkg"
        r = RESULTS / cell / "05_results.csv"
        if not (e.exists() and g.exists() and r.exists()):
            print("  SKIP %s (e02=%s gpkg=%s res=%s)"
                  % (cell, e.exists(), g.exists(), r.exists()))
            continue
        em = pd.read_parquet(e)[["osm_id", "vintage_standard", "archetype_id"]]
        em = em.rename(columns={"vintage_standard": "e02_vintage",
                                "archetype_id": "e02_archetype"})
        # geometry is REQUIRED: resolve_vintage's tier-1 spatial donor calls knn_fill,
        # which silently degrades to the tier-2 group mode if the frame has no geometry.
        gd = gpd.read_file(g)[["osm_id", "year_built", "data_quality_flag", "geometry"]]
        rs = pd.read_csv(r)[["osm_id", "archetype_id"]].rename(
            columns={"archetype_id": "run2_archetype"})
        d = gd.merge(rs, on="osm_id", how="left")

        # HEAD re-derivation, production code, stratified exactly as production does
        d2 = gpd.GeoDataFrame(d.rename(columns={"run2_archetype": "archetype_id"}).copy(),
                              geometry="geometry", crs=gd.crs)
        vint, nan_rows, prov = resolve_vintage(d2)
        d["head_vintage"] = vint.values
        d["head_vintage_tier"] = "OBSERVED_YEAR"
        d.loc[d.index.isin(nan_rows), "head_vintage_tier"] = prov.reindex(nan_rows).values
        d["run2_archetype"] = d2["archetype_id"]

        d = pd.DataFrame(d.drop(columns=["geometry"]))
        j = d.merge(em, on="osm_id", how="inner")
        j["cell"] = cell
        rows.append(j)

    if not rows:
        print("\nno cell could be joined -- nothing to report")
        return 1
    df = pd.concat(rows, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "open08_vintage_cross_generation.csv", index=False)

    print("\n--- step 2: the cross-generation vintage comparison, `auto` mode both sides ---")
    print("shared buildings joined: %d across %d cells" % (len(df), df["cell"].nunique()))
    df["vintage_agrees"] = df["e02_vintage"].astype(str) == df["head_vintage"].astype(str)
    df["archetype_agrees"] = df["e02_archetype"].astype(str) == df["run2_archetype"].astype(str)

    dis = 100.0 * (~df["vintage_agrees"]).mean()
    print("\nVINTAGE disagreement (E02 persisted vs HEAD re-derivation): %d / %d = %.4f %%"
          % (int((~df["vintage_agrees"]).sum()), len(df), dis))
    print("ARCHETYPE disagreement, same join, as an in-task control      : %d / %d = %.4f %%"
          % (int((~df["archetype_agrees"]).sum()), len(df),
             100.0 * (~df["archetype_agrees"]).mean()))

    print("\n--- where the vintage disagreements are ---")
    print(df.groupby("cell")["vintage_agrees"]
          .agg(["count", "sum", lambda s: round(100.0 * (1 - s.mean()), 3)])
          .rename(columns={"<lambda_0>": "disagree_pct"}).to_string())

    print("\n--- the confusion, E02 label -> HEAD label (disagreements only) ---")
    bad = df[~df["vintage_agrees"]]
    if len(bad):
        print(pd.crosstab(bad["e02_vintage"], bad["head_vintage"]).to_string())
    else:
        print("  none")

    print("\n--- does disagreement track the imputation tier? ---")
    print(df.groupby("head_vintage_tier")["vintage_agrees"]
          .agg(["count", "mean"]).round(4).to_string())

    print("\n--- and does the vintage disagreement land on the SAME buildings as the "
          "archetype one? (the two-defect independence question) ---")
    print(pd.crosstab(df["vintage_agrees"], df["archetype_agrees"]).to_string())

    print("\nwrote %s" % (OUT / "open08_vintage_cross_generation.csv"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
