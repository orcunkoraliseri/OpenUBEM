"""T02 (PLAN_ten-live-items-2026-08-21): meter-only EUI vs published EUI, auto arm.
Standalone, read-only. No production code touched.
"""
import sqlite3
import csv
import random
from pathlib import Path
from collections import Counter, defaultdict

import pandas as pd

HARVEST_ROOT = Path(r"C:\Users\o_iseri\AppData\Local\Temp\ubem_e02_harvest")
CENSUS_CSV = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open53_harvest_sql_census_2026-08-21.csv")
EVIDENCE_ROOT = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\evidence\open48_refleet4")
OUT_CSV = Path(r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open53_meter_only_eui_2026-08-21.csv")

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]

J_PER_KWH = 3.6e6


def norm_stem(osm_id: str) -> str:
    return osm_id.strip().lower().replace("/", "_")


def meter_only_eui(sql_path: Path, floor_area_m2: float):
    con = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute(
        "SELECT rdd.Name, rd.Value FROM ReportData rd "
        "JOIN ReportDataDictionary rdd ON rd.ReportDataDictionaryIndex = rdd.ReportDataDictionaryIndex "
        "WHERE rdd.ReportingFrequency = 'Run Period' AND rdd.Name LIKE '%:Facility'"
    )
    rows = cur.fetchall()
    con.close()
    total_j = 0.0
    meters = []
    for name, value in rows:
        total_j += value
        meters.append(name)
    eui = (total_j / J_PER_KWH) / floor_area_m2
    return eui, meters


def independent_recompute(sql_path: Path, floor_area_m2: float):
    """C5: a second, independently written query over the same data."""
    con = sqlite3.connect(f"file:{sql_path}?mode=ro", uri=True)
    cur = con.cursor()
    cur.execute(
        "SELECT ReportDataDictionaryIndex FROM ReportDataDictionary "
        "WHERE ReportingFrequency = 'Run Period' AND Name LIKE '%:Facility'"
    )
    idxs = [r[0] for r in cur.fetchall()]
    total_j = 0.0
    for idx in idxs:
        cur.execute("SELECT SUM(Value) FROM ReportData WHERE ReportDataDictionaryIndex = ?", (idx,))
        v = cur.fetchone()[0]
        total_j += (v or 0.0)
    con.close()
    return (total_j / J_PER_KWH) / floor_area_m2


def main():
    census = pd.read_csv(CENSUS_CSV)
    auto_census = census[(census["mode"] == "auto") & (census["has_sql"] == True)]  # noqa: E712

    results_frames = []
    for cell in CELLS:
        rp = EVIDENCE_ROOT / cell / "results" / "05_results.csv"
        df = pd.read_csv(rp)
        df["cell"] = cell
        df["stem_norm"] = df["osm_id"].apply(norm_stem)
        results_frames.append(df)
    results = pd.concat(results_frames, ignore_index=True)

    n_auto_population = len(auto_census)

    joined = auto_census.merge(
        results, left_on=["cell", "stem"], right_on=["cell", "stem_norm"], how="left", suffixes=("", "_res")
    )
    n_join_matched = joined["osm_id"].notna().sum()
    n_join_lost = n_auto_population - n_join_matched

    eligible = joined[
        joined["osm_id"].notna()
        & (joined["simulation_status"] == "success")
        & joined["total_eui_kwh_m2"].notna()
        & (joined["floor_area_m2"] > 0)
    ].copy()

    out_rows = []
    meter_name_counter = Counter()
    sum_meter_energy_kwh = 0.0
    sum_floor_area = 0.0
    sum_published_energy_kwh = 0.0

    for _, r in eligible.iterrows():
        sql_path = HARVEST_ROOT / f"{r['cell']}_auto" / r["stem"] / "eplusout.sql"
        try:
            eui, meters = meter_only_eui(sql_path, r["floor_area_m2"])
        except Exception as e:  # noqa: BLE001
            out_rows.append(
                {
                    "cell": r["cell"], "osm_id": r["osm_id"], "archetype_id": r.get("archetype_id"),
                    "meter_only_eui": None, "published_eui": r["total_eui_kwh_m2"],
                    "diff": None, "pct_diff": None, "meters_used": f"ERROR:{e}",
                }
            )
            continue
        for m in meters:
            meter_name_counter[m] += 1
        diff = eui - r["total_eui_kwh_m2"]
        pct_diff = 100.0 * diff / r["total_eui_kwh_m2"]
        out_rows.append(
            {
                "cell": r["cell"], "osm_id": r["osm_id"], "archetype_id": r.get("archetype_id"),
                "meter_only_eui": eui, "published_eui": r["total_eui_kwh_m2"],
                "diff": diff, "pct_diff": pct_diff, "meters_used": ";".join(sorted(set(meters))),
            }
        )
        sum_meter_energy_kwh += eui * r["floor_area_m2"]
        sum_floor_area += r["floor_area_m2"]
        sum_published_energy_kwh += r["total_eui_kwh_m2"] * r["floor_area_m2"]

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cell", "osm_id", "archetype_id", "meter_only_eui", "published_eui", "diff", "pct_diff", "meters_used"])
        w.writeheader()
        w.writerows(out_rows)

    n_compared = sum(1 for r in out_rows if r["meter_only_eui"] is not None)
    pct_diffs = sorted(r["pct_diff"] for r in out_rows if r["pct_diff"] is not None)

    def pctl(arr, p):
        if not arr:
            return None
        k = (len(arr) - 1) * p
        f = int(k)
        c = min(f + 1, len(arr) - 1)
        if f == c:
            return arr[f]
        return arr[f] + (arr[c] - arr[f]) * (k - f)

    median = pctl(pct_diffs, 0.5)
    q1 = pctl(pct_diffs, 0.25)
    q3 = pctl(pct_diffs, 0.75)

    pooled_meter_eui = sum_meter_energy_kwh / sum_floor_area if sum_floor_area else None
    pooled_published_eui = sum_published_energy_kwh / sum_floor_area if sum_floor_area else None

    n_over10 = [r for r in out_rows if r["pct_diff"] is not None and abs(r["pct_diff"]) > 10.0]

    print(f"n_auto_population={n_auto_population}")
    print(f"n_join_matched={n_join_matched}")
    print(f"n_join_lost={n_join_lost}  pct_lost={100.0*n_join_lost/n_auto_population:.3f}%")
    print(f"n_eligible={len(eligible)}")
    print(f"n_compared={n_compared}")
    print(f"median_pct_diff={median:.4f}")
    print(f"q1_pct_diff={q1:.4f}  q3_pct_diff={q3:.4f}  iqr={q3-q1:.4f}")
    print(f"pooled_meter_only_eui={pooled_meter_eui:.4f}")
    print(f"pooled_published_eui={pooled_published_eui:.4f}")
    print(f"n_over_10pct_abs_diff={len(n_over10)}")
    print(f"meter_names_used={dict(meter_name_counter)}")

    print("\n--- pct_diff > 10% abs, identity ---")
    for r in n_over10[:60]:
        print(r["cell"], r["osm_id"], f"{r['pct_diff']:.2f}%")
    if len(n_over10) > 60:
        print(f"... ({len(n_over10)-60} more, see CSV)")

    print("\n--- per-archetype breakdown (n, median pct_diff) ---")
    by_arch = defaultdict(list)
    for r in out_rows:
        if r["pct_diff"] is not None:
            by_arch[r["archetype_id"]].append(r["pct_diff"])
    for arch, vals in sorted(by_arch.items(), key=lambda kv: -len(kv[1])):
        vals_sorted = sorted(vals)
        med = pctl(vals_sorted, 0.5)
        print(f"archetype={arch!s:30s} n={len(vals):5d} median_pct_diff={med:8.3f}")

    # C5 — independent recompute check on 3 buildings
    print("\n--- C5: independent recompute check (3 buildings) ---")
    random.seed(2026)
    check_rows = random.sample(out_rows, 3) if len(out_rows) >= 3 else out_rows
    for r in check_rows:
        cell = r["cell"]
        stem = norm_stem(r["osm_id"])
        sql_path = HARVEST_ROOT / f"{cell}_auto" / stem / "eplusout.sql"
        indep = independent_recompute(sql_path, r["published_eui"] and eligible.loc[
            (eligible["cell"] == cell) & (eligible["osm_id"] == r["osm_id"]), "floor_area_m2"
        ].iloc[0])
        orig = r["meter_only_eui"]
        agree = abs(indep - orig) < 1e-6 * max(abs(indep), abs(orig), 1e-12)
        print(f"{cell} {r['osm_id']}: original={orig:.6f} independent={indep:.6f} agree_6sf={agree}")

    print(f"\nCHECK C6: pooled_meter_only_eui={pooled_meter_eui:.4f} vs 153.8231 -> "
          f"{'WITHIN 1%' if abs(pooled_meter_eui-153.8231)/153.8231 <= 0.01 else 'NOT within 1%'}")


if __name__ == "__main__":
    main()
