from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

import pandas as pd

from scripts.cluster import harvest_eu11_merged as hm

WIN5_TAG = hm.WIN5_TAG
WIN6_TAG = hm.WIN6_TAG
TAGS = (WIN5_TAG, WIN6_TAG)
ALLOWED = ("GB-LDN-STDUNSTANS", "IT-BOL-GALVANI2")
BUILDINGS_ROOT = REPO / "openubem" / "outputs" / "3D"
OUT_COLUMNS = ["building_id", "old_count", "new_count", "dwellings_source", "status"]
STATUSES = ["simulated", "run_failed", "undivided_excluded", "not_residential", "no_model"]


def build_flat_counts(district: str, tag: str = WIN5_TAG) -> pd.DataFrame:
    if district not in ALLOWED:
        raise ValueError(f"{district}: flat counts are exported for {ALLOWED} only")
    if tag not in TAGS:
        raise ValueError(f"tag {tag}: flat counts are exported for {TAGS} only")
    date = tag[len("win_"):]
    win_dir = hm._dist_dir(district, tag)
    counts = pd.read_csv(win_dir / f"dwelling_counts_{date}.csv", dtype=str).drop_duplicates("building_id")
    counts = counts.set_index("building_id")
    merged_path = hm._manifest_path(district, f"merged_{tag}")
    if not merged_path.exists():
        raise FileNotFoundError(f"missing {merged_path}")
    merged = pd.read_csv(merged_path, dtype=str)
    source = dict(zip(merged["building_id"], merged["eui_source"]))
    undivided = hm._undivided_ids_win5(district)
    buildings = pd.read_csv(BUILDINGS_ROOT / f"eu_{district}_data" / "buildings.csv", dtype=str)

    rows = []
    for _, b in buildings.iterrows():
        bid = str(b["building_id"])
        src = source.get(bid)
        if src == tag:
            status = "simulated"
        elif src == "win_failed":
            status = "run_failed"
        elif bid in undivided:
            status = "undivided_excluded"
        elif b.get("class") == "excluded":
            status = "not_residential"
        else:
            status = "no_model"
        c = counts.loc[bid] if bid in counts.index else None
        rows.append({
            "building_id": bid,
            "old_count": c["old_count"] if c is not None else "",
            "new_count": c["new_count"] if c is not None else "",
            "dwellings_source": c["dwellings_source"] if c is not None else "",
            "status": status,
        })
    return pd.DataFrame(rows, columns=OUT_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", required=True)
    parser.add_argument("--tag", default=WIN5_TAG, choices=TAGS)
    args = parser.parse_args()
    df = build_flat_counts(args.district, args.tag)
    out = hm._dist_dir(args.district, f"merged_{args.tag}") / f"flat_counts_{args.tag[len('win_'):]}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"[{args.district}] {out} ({len(df)} rows)")
    for s in STATUSES:
        print(f"  {s}: {int((df['status'] == s).sum())}")


if __name__ == "__main__":
    main()
