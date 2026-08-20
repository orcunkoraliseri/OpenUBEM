"""T07 of PLAN_ten-items-2026-08-19.md -- OPEN-12 / OPEN-35: is the height-residual
population a strict subset of the storey-count population, or the other way round?

The register asserts, never computed: "1,589 of `nyc_suburban`'s buildings have neither
input, so they are 61% of OPEN-35's 2,611" (INVESTIGATION_open-items-register.md:4497-4498).
Two items that are one population should not be tracked as two; two items that merely
overlap must not be folded. This script re-derives BOTH populations from the fleet's own
Stage-1 files, fresh -- it does not reuse the carried figures 2,806 (OPEN-12) and 2,611
(OPEN-35), because those figures are exactly what is being tested.

Definitions, taken from the register's own re-derivations (both director-verified):
  OPEN-12  = buildings with no `height_m` (register: 2,806 / 8,160 = 34.39 %), regardless
             of `levels` -- INVESTIGATION_open-items-register.md:4440.
  OPEN-35  = buildings with NEITHER `levels` NOR `height_m` -- the population that reaches
             both fallbacks (_impute_levels vs derive_num_floors), register: 2,611 / 8,160
             = 32.00 % -- INVESTIGATION_open-items-register.md:2881, using
             `_impute_levels`'s own predicate (pd.notna(levels); pd.notna(h) and h > 0).

By these definitions OPEN-35's predicate (both null) is logically nested inside OPEN-12's
predicate (height null only) -- OPEN-35 cannot be larger than OPEN-12 and any building in
OPEN-35 is automatically in OPEN-12. What is NOT given for free, and what this script
actually measures, is (a) whether the two carried figures reproduce on the same corpus
under directly comparable predicates, (b) the exact overlap counts and the residual
195-building difference, and (c) whether the nyc_suburban 1,589/61% claim holds to the
building.

Hard rule 10 (imputation tier distribution cross-check): the Stage-1 `data_quality_flag`
column is stamped at acquisition (openubem/acquisition/osm_fetcher.py:510) with
`no_floors` / `no_height` tokens whenever the raw OSM tag is absent -- entirely independent
of the `levels`/`height_m` notna() checks used to build the two populations here. This
script cross-checks the two mechanisms against each other before quoting any number: if
they disagree, that is reported as a finding, not silently reconciled.

Corpus: run 2 (open48_refleet), same corpus X04 (2026-08-18 overnight) used, which
reproduced the register's 2,611 to the unit. Frozen inputs re-verified present on disk at
the top of main() (hard rule 11) -- not cited from a prior census.

Emits openubem/outputs/comparisons/open12_open35_subset_check.csv (per-cell contingency)
and openubem/outputs/comparisons/open12_open35_subset_check_buildings.csv (per-building,
for anyone who needs to re-check a specific osm_id).
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = Path("C:/Users/o_iseri/AppData/Local/Temp/ubem_validation/open48_refleet")
RESULTS = ROOT / "docs/validations/overAll/results/open48_refleet"
OUT = ROOT / "openubem" / "outputs" / "comparisons"

CELLS = ["nyc_centre", "nyc_urban", "nyc_suburban", "nyc_rural",
         "la_centre", "la_urban", "la_suburban", "la_rural",
         "austin_centre", "austin_urban", "austin_suburban", "austin_rural"]

CARRIED = {
    "open12_height_null": (2806, 8160, "34.39 %"),
    "open35_neither": (2611, 8160, "32.00 %"),
}


def verify_inputs_present() -> None:
    missing = []
    for cell in CELLS:
        gp = BASE / cell / "01_buildings.gpkg"
        if not gp.exists():
            missing.append(str(gp))
    if missing:
        raise SystemExit("STOP AND REPORT -- missing Stage-1 files:\n" + "\n".join(missing))
    print(f"Re-verified on disk: all {len(CELLS)} Stage-1 01_buildings.gpkg present under {BASE}")


def dq_has_token(flag: str, token: str) -> bool:
    if not isinstance(flag, str) or not flag:
        return False
    return token in [t.strip() for t in flag.split(",")]


def main() -> int:
    verify_inputs_present()
    OUT.mkdir(parents=True, exist_ok=True)

    per_cell_rows = []
    building_frames = []

    for cell in CELLS:
        gp = BASE / cell / "01_buildings.gpkg"
        g = gpd.read_file(gp)
        n = len(g)

        height_null = g["height_m"].isna()
        levels_null = g["levels"].isna()
        neither = height_null & levels_null
        height_only = height_null & ~levels_null
        levels_only = ~height_null & levels_null
        both_present = ~height_null & ~levels_null

        # hard rule 10 cross-check: data_quality_flag tokens, stamped independently at
        # acquisition, must agree with the notna() predicates used to build the two
        # populations. Disagreement is reported, not silently reconciled.
        dq_no_height = g["data_quality_flag"].apply(lambda f: dq_has_token(f, "no_height"))
        dq_no_floors = g["data_quality_flag"].apply(lambda f: dq_has_token(f, "no_floors"))
        height_agree = int((dq_no_height == height_null).sum())
        levels_agree = int((dq_no_floors == levels_null).sum())

        # present-but-zero height check (register: zero fleet-wide; re-verify per cell)
        height_present_zero = int((g["height_m"] == 0).sum())

        rec = {
            "cell": cell,
            "n_buildings": n,
            "height_null": int(height_null.sum()),
            "levels_null": int(levels_null.sum()),
            "neither": int(neither.sum()),
            "height_only": int(height_only.sum()),
            "levels_only": int(levels_only.sum()),
            "both_present": int(both_present.sum()),
            "height_present_but_zero": height_present_zero,
            "dq_token_agree_height": height_agree,
            "dq_token_disagree_height": n - height_agree,
            "dq_token_agree_levels": levels_agree,
            "dq_token_disagree_levels": n - levels_agree,
        }

        # join to persisted results 'levels' for the specific claim check
        rp = RESULTS / cell / "05_results.csv"
        if rp.exists() and "osm_id" in g.columns:
            r = pd.read_csv(rp)[["osm_id", "levels"]].rename(columns={"levels": "persisted_levels"})
            gid = g[["osm_id"]].copy()
            gid["neither"] = neither.values
            gid["height_only"] = height_only.values
            gid["cell"] = cell
            joined = gid.merge(r, on="osm_id", how="left")
            n_neither_at_1 = int((joined.loc[joined["neither"], "persisted_levels"] == 1.0).sum())
            n_neither_total = int(joined["neither"].sum())
            rec["neither_persisted_levels_1"] = n_neither_at_1
            rec["neither_persisted_levels_1_pct"] = (
                round(100.0 * n_neither_at_1 / n_neither_total, 4) if n_neither_total else 0.0
            )
            building_frames.append(joined)
        per_cell_rows.append(rec)

    df = pd.DataFrame(per_cell_rows)
    dest = OUT / "open12_open35_subset_check.csv"
    df.to_csv(dest, index=False)

    with pd.option_context("display.width", 260, "display.max_columns", 40):
        print("\n=== per-cell contingency (Stage-1, run 2 / open48_refleet) ===")
        print(df[["cell", "n_buildings", "height_null", "levels_null", "neither",
                   "height_only", "levels_only", "both_present"]].to_string(index=False))

    tot_n = int(df["n_buildings"].sum())
    tot_height_null = int(df["height_null"].sum())
    tot_levels_null = int(df["levels_null"].sum())
    tot_neither = int(df["neither"].sum())
    tot_height_only = int(df["height_only"].sum())
    tot_levels_only = int(df["levels_only"].sum())
    tot_both = int(df["both_present"].sum())

    print(f"\nfleet total: {tot_n} buildings across {len(df)} cells")
    print("\n=== fleet-wide 2x2 contingency (height_null x levels_null) ===")
    print(f"  neither missing (both present)              : {tot_both}")
    print(f"  height missing only (levels present)         : {tot_height_only}")
    print(f"  levels missing only (height present)          : {tot_levels_only}")
    print(f"  neither present (OPEN-35 trigger population)  : {tot_neither}")
    check_sum = tot_both + tot_height_only + tot_levels_only + tot_neither
    print(f"  sum of four cells = {check_sum}  (fleet n = {tot_n})  "
          f"{'OK' if check_sum == tot_n else 'MISMATCH -- CONTROL FAILED'}")
    if check_sum != tot_n:
        raise SystemExit("STOP AND REPORT -- 2x2 contingency does not sum to the fleet total.")

    print("\n=== hard rule 10: data_quality_flag token cross-check ===")
    print("(no_height / no_floors tokens stamped independently at acquisition; must agree")
    print(" with height_m.isna() / levels.isna() used to build the populations above)")
    print(df[["cell", "dq_token_disagree_height", "dq_token_disagree_levels"]].to_string(index=False))
    total_disagree_h = int(df["dq_token_disagree_height"].sum())
    total_disagree_l = int(df["dq_token_disagree_levels"].sum())
    print(f"\n  total disagreements, height: {total_disagree_h}   levels: {total_disagree_l}")
    if total_disagree_h or total_disagree_l:
        print("  FINDING: data_quality_flag tokens and notna() predicates disagree -- "
              "reported, not reconciled. Numbers below still stand on the notna() predicate, "
              "the same one the register's own carried figures were built on.")
    else:
        print("  Zero disagreements fleet-wide -- the two independent mechanisms "
              "(acquisition-time flag, Stage-1 notna()) agree exactly. Populations trusted.")

    total_zero_height = int(df["height_present_but_zero"].sum())
    print(f"\n  present-but-zero height_m fleet-wide: {total_zero_height} "
          f"({'confirms register note' if total_zero_height == 0 else 'DIFFERS from register note of zero'})")

    print("\n=== reproduction against carried register figures ===")
    for key, col in (("open12_height_null", "height_null"), ("open35_neither", "neither")):
        num, den, pct = CARRIED[key]
        got = int(df[col].sum())
        print(f"  {key}: register {num} / {den} = {pct}   |   re-derived {got} / {tot_n} = "
              f"{100.0*got/tot_n:.2f} %   |   "
              f"{'REPRODUCES EXACTLY' if got == num else 'DIFFERS -- both stand, reported as a finding'}")

    print("\n=== subset verdict ===")
    print(f"  OPEN-35 (neither, n={tot_neither}) is nested inside OPEN-12 (height_null, n={tot_height_null}) "
          f"by construction: every 'neither' row has height_m null, so OPEN-35 subseteq OPEN-12.")
    residual = tot_height_only
    print(f"  OPEN-12 \\ OPEN-35 (height missing, levels present) = {residual} buildings fleet-wide "
          f"({100.0*residual/tot_height_null:.2f} % of OPEN-12's population).")
    print(f"  OPEN-35 \\ OPEN-12 = 0 buildings (impossible by the predicate; levels_only={tot_levels_only} "
          f"is disjoint from both populations, not a counter-example).")
    if tot_neither < tot_height_null and residual > 0:
        print("  VERDICT: OPEN-35 is a STRICT (proper) SUBSET of OPEN-12 fleet-wide -- not equal, "
              "not disjoint. OPEN-12 is the wider population; OPEN-35 is its 'and levels is also "
              "missing' refinement. This is the reverse direction from T07's title phrasing "
              "('is the height-residual population [OPEN-12] a strict subset of the storey-count "
              "population [OPEN-35]?') -- the answer to the title as literally posed is NO, "
              f"because OPEN-12 (n={tot_height_null}) is larger than OPEN-35 (n={tot_neither}) and a "
              "larger set cannot be a subset of a smaller one.")
    elif tot_neither == tot_height_null:
        print("  VERDICT: the two populations are IDENTICAL fleet-wide.")
    else:
        print("  VERDICT: unexpected relationship -- inspect the contingency table above.")

    print("\n=== nyc_suburban specific claim: '1,589 ... 61% of OPEN-35's 2,611' ===")
    row = df[df["cell"] == "nyc_suburban"].iloc[0]
    ns_height_null = int(row["height_null"])
    ns_neither = int(row["neither"])
    pct_of_2611 = 100.0 * ns_neither / tot_neither if tot_neither else float("nan")
    print(f"  nyc_suburban height_null : {ns_height_null} / {int(row['n_buildings'])}")
    print(f"  nyc_suburban neither     : {ns_neither} / {int(row['n_buildings'])}")
    print(f"  claim's numerator (1,589) vs re-derived neither: "
          f"{'MATCHES' if ns_neither == 1589 else 'DIFFERS (re-derived %d)' % ns_neither}")
    print(f"  {ns_neither} / OPEN-35's fleet total {tot_neither} = {pct_of_2611:.2f} %  "
          f"(claim: 61 %) -- {'MATCHES to the stated rounding' if round(pct_of_2611) == 61 else 'DIFFERS'}")
    print(f"  within nyc_suburban, height_null == neither: "
          f"{'YES (100% of the cell lacks both inputs, so the two populations coincide inside this cell)' if ns_height_null == ns_neither else 'NO -- %d height-null buildings in nyc_suburban have levels present' % (ns_height_null - ns_neither)}")

    if "neither_persisted_levels_1" in df.columns:
        a = int(df["neither_persisted_levels_1"].sum())
        b = int(df["neither"].sum())
        print(f"\n=== control: OPEN-35's 'neither' population persisted at levels=1.0 in results ===")
        print(f"  {a} / {b} = {100.0*a/b:.4f} %  "
              f"({'matches register: every one of the 2,611 persisted at levels=1.0, no exceptions' if a == b else 'DIFFERS from register -- exceptions found, reported'})")

    if building_frames:
        bdf = pd.concat(building_frames, ignore_index=True)
        bdest = OUT / "open12_open35_subset_check_buildings.csv"
        bdf.to_csv(bdest, index=False)
        print(f"\nwrote {bdest} ({len(bdf)} rows)")

    print(f"\nwrote {dest}")
    print("\nRECOMMENDATION (not taken -- user's call per hard rule 5 / plan instruction): "
          "OPEN-35 is a proper subset of OPEN-12, not an equivalent population -- the two items "
          "describe different-sized populations sharing a common core (2,611 of OPEN-12's 2,806). "
          "A merge would need to explicitly carry forward the 195-building residual "
          "(height missing, levels present) that OPEN-35's narrower definition excludes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
