import csv
from pathlib import Path
from collections import defaultdict

ZONE_CSV = Path("openubem/outputs/comparisons/open56_volume-stub-zones_2026-08-21b.csv")
ERR_CSV = Path("openubem/outputs/comparisons/open38-09-45_err-census-buildings_2026-08-21b.csv")
OUT_CSV = Path("openubem/outputs/comparisons/open38-56_volume-degeneracy-vs-failure_2026-08-21b.csv")

if not ZONE_CSV.is_file():
    raise SystemExit(f"STOP: T02 output not found on disk: {ZONE_CSV}")
if not ERR_CSV.is_file():
    raise SystemExit(f"STOP: T06 output not found on disk: {ERR_CSV}")

stem_zones = defaultdict(lambda: {"n_zones": 0, "n_stub": 0, "vol_built": 0.0, "vol_expected": 0.0, "cell": None})

with ZONE_CSV.open(newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        key = (row["cell"], row["stem"])
        rec = stem_zones[key]
        rec["cell"] = row["cell"]
        rec["n_zones"] += 1
        if row["is_stub"] == "True":
            rec["n_stub"] += 1
        rec["vol_built"] += float(row["volume"])
        rec["vol_expected"] += float(row["expected_volume"])

err_rows = []
with ERR_CSV.open(newline="", encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        err_rows.append(row)

n_total = len(err_rows)
group_a = []
group_b = []
group_c = []
overlap_ab = []

out_rows = []
for row in err_rows:
    key = (row["cell"], row["stem"])
    zrec = stem_zones.get(key)
    is_fatal = row["is_fatal"] == "True"
    is_open09 = row["is_open09_signature"] == "True"

    if zrec is None or zrec["n_zones"] == 0:
        frac_stub = ""
        vol_ratio = ""
    else:
        frac_stub = zrec["n_stub"] / zrec["n_zones"]
        vol_ratio = (zrec["vol_built"] / zrec["vol_expected"]) if zrec["vol_expected"] else ""

    if is_fatal:
        group_a.append((key, frac_stub))
    if is_open09:
        group_b.append((key, frac_stub))
    if is_fatal and is_open09:
        overlap_ab.append(key)
    if not is_fatal and not is_open09:
        group_c.append((key, frac_stub))

    out_rows.append([
        row["cell"], row["stem"], is_fatal, is_open09,
        zrec["n_zones"] if zrec else 0,
        zrec["n_stub"] if zrec else 0,
        f"{frac_stub:.6f}" if frac_stub != "" else "",
        f"{vol_ratio:.6f}" if vol_ratio != "" else "",
    ])

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["cell", "stem", "is_fatal", "is_open09", "n_zones", "n_stub", "frac_stub", "vol_ratio"])
    w.writerows(out_rows)


def summarize(group, label):
    n = len(group)
    fracs = [v for _, v in group if v != ""]
    all_stub = sum(1 for v in fracs if v == 1.0)
    any_stub = sum(1 for v in fracs if v > 0.0)
    mean_frac = (sum(fracs) / len(fracs)) if fracs else None
    print(f"group {label}: n={n} (with zone data: {len(fracs)}); "
          f"all-zones-stubbed={all_stub}/{len(fracs)}; any-zone-stubbed={any_stub}/{len(fracs)}; "
          f"mean frac_stub={mean_frac:.6f}" if mean_frac is not None else f"group {label}: n={n}, no zone data")


print("=== T07 summary ===")
print(f"partition check: |a|(fatal)={len(group_a)} + |b|(open09)={len(group_b)} + |c|(neither)={len(group_c)} "
      f"vs n_total={n_total}; overlap(a AND b)={len(overlap_ab)}")
print(f"a + b + c - overlap(a,b) should equal n_total: "
      f"{len(group_a) + len(group_b) + len(group_c) - len(overlap_ab)} == {n_total} -> "
      f"{len(group_a) + len(group_b) + len(group_c) - len(overlap_ab) == n_total}")
summarize(group_a, "a=fatal")
summarize(group_b, "b=open09_signature")
summarize(group_c, "c=neither(everything else)")
print(f"wrote per-stem join csv: {OUT_CSV} ({len(out_rows)} rows)")
