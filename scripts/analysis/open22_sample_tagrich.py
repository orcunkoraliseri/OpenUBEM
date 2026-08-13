"""T03 (OPEN-22): draw a stratified 100-row sample from the 592-row tag-rich pool
(director's §4.2 pool: boston_downtown_500m.gpkg + chicago_loop_500m.gpkg, rows with
a specific building_tag != 'yes', OR a function_tag present).

Stratifies by building_tag (or, when building_tag=='yes', by 'function:<function_tag>')
so the sample is not all office. Allocation is proportional (Hare quota, largest
remainder for the leftover seats), capped at each stratum's own population — no
stratum can be allocated more rows than it has. No forced per-stratum minimum: a
population-1 stratum has roughly a 17% (1/6) chance of winning a remainder seat
this run, same as any other, which is why several 1-row strata are absent from the
draw (see the printed allocation table).

Emits scratch CSV of the 100 raw (unlabelled) rows for the labeller to work from —
this script performs NO classification and reads no classifier code.

Fixed seed: 20260812 (documented here and in the fixture's provenance comment).

Usage: python scripts/analysis/open22_sample_tagrich.py <output_csv>
"""

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

SEED = 20260812
TARGET = 100

REPO_ROOT = Path(__file__).resolve().parents[2]


def load_pool() -> pd.DataFrame:
    bos = gpd.read_file(REPO_ROOT / "tests/fixtures/boston_downtown_500m.gpkg")
    chi = gpd.read_file(REPO_ROOT / "tests/fixtures/chicago_loop_500m.gpkg")
    bos["source_fixture"] = "boston_downtown_500m"
    chi["source_fixture"] = "chicago_loop_500m"
    bos_df = pd.DataFrame(bos.drop(columns="geometry"))
    chi_df = pd.DataFrame(chi.drop(columns="geometry"))
    return pd.concat([bos_df, chi_df], ignore_index=True)


def tagrich_mask(pool: pd.DataFrame) -> pd.Series:
    bt = pool["building_tag"].astype(str)
    ft = pool["function_tag"].astype(str)
    bt_present_not_yes = pool["building_tag"].notna() & (bt.str.strip() != "") & (bt.str.lower() != "yes")
    ft_present = pool["function_tag"].notna() & (ft.str.strip() != "")
    return bt_present_not_yes | ft_present


def stratum_of(row) -> str:
    bt = str(row["building_tag"]).strip()
    if bt and bt.lower() != "yes":
        return bt.lower()
    return "function:" + str(row["function_tag"]).strip().lower()


def allocate(counts: pd.Series, target: int) -> pd.Series:
    n = counts.sum()
    quota = counts * target / n
    alloc = np.floor(quota).astype(int)
    deficit = target - alloc.sum()
    remainder = quota - np.floor(quota)
    room = counts - alloc
    order = remainder.sort_values(ascending=False).index.tolist()
    i = 0
    guard = 0
    while deficit > 0 and guard < 100_000:
        s = order[i % len(order)]
        if room[s] > 0:
            alloc[s] += 1
            room[s] -= 1
            deficit -= 1
        i += 1
        guard += 1
    assert alloc.sum() == target, f"allocation totalled {alloc.sum()}, expected {target}"
    assert (alloc <= counts).all(), "a stratum was allocated more than its population"
    return alloc


def main(out_csv: str) -> None:
    pool = load_pool()
    sub = pool[tagrich_mask(pool)].copy()
    assert len(sub) == 592, f"tag-rich pool is {len(sub)}, expected 592 (director's §4.2 figure)"
    sub["stratum"] = sub.apply(stratum_of, axis=1)

    counts = sub["stratum"].value_counts()
    alloc = allocate(counts, TARGET)

    print(f"seed={SEED}  pool={len(sub)}  target={TARGET}  strata={len(counts)}  "
          f"strata_represented={(alloc > 0).sum()}")
    print(alloc[alloc > 0].sort_values(ascending=False).to_string())

    picked = []
    for stratum, k in alloc.items():
        if k == 0:
            continue
        grp = sub[sub["stratum"] == stratum]
        if k >= len(grp):
            picked.append(grp)
        else:
            picked.append(grp.sample(n=int(k), random_state=SEED))
    sample = pd.concat(picked, ignore_index=True)
    assert len(sample) == TARGET, f"drew {len(sample)} rows, expected {TARGET}"
    assert sample["osm_id"].is_unique

    sample = sample.sort_values(["source_fixture", "stratum", "osm_id"]).reset_index(drop=True)
    sample.to_csv(out_csv, index=False)
    print(f"\nwrote {len(sample)} rows to {out_csv}")


if __name__ == "__main__":
    main(sys.argv[1])
