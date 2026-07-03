"""Diagnostic: WHY does E-R3-3 move city EUI further below measured?

Read-only. Matches before(phaseE) <-> after(phaseE_er33) by osm_id per cell,
isolates archetype flips, decomposes the fleet-median shift into
(a) buildings that flipped archetype vs (b) buildings that did not,
and reports per-archetype and per-end-use intensities.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT / "docs" / "docs_VALIDATION" / "validations" / "overAll" / "results" / "phaseE"
AFTER  = ROOT / "docs" / "validations" / "overAll" / "results" / "phaseE_er33"

CELLS = ["nyc_centre","nyc_urban","nyc_suburban","nyc_rural",
         "la_centre","la_urban","la_suburban","la_rural",
         "austin_centre","austin_urban","austin_suburban","austin_rural"]
MEASURED = {"nyc":219.2,"la":113.6,"austin":162.0}
SUCCESS = {"success","success_cached","success_csv_fallback"}
END_USES = ["heating_eui_kwh_m2","cooling_eui_kwh_m2","lighting_eui_kwh_m2",
            "equipment_eui_kwh_m2","fans_eui_kwh_m2","pumps_eui_kwh_m2",
            "dhw_eui_kwh_m2","cooking_eui_kwh_m2","refrigeration_eui_kwh_m2"]

def load(base):
    frames=[]
    for c in CELLS:
        df=pd.read_csv(base/c/"05_results.csv",dtype={"osm_id":str})
        df["cell"]=c; df["city"]=c.split("_")[0]
        frames.append(df)
    return pd.concat(frames,ignore_index=True)

b=load(BEFORE); a=load(AFTER)
b=b[b["simulation_status"].isin(SUCCESS)].copy()
a=a[a["simulation_status"].isin(SUCCESS)].copy()

key=["cell","osm_id"]
m=b.merge(a,on=key,suffixes=("_b","_a"))
m=m[(m["archetype_id_b"]!="OpenUBEMUnknown")&(m["archetype_id_a"]!="OpenUBEMUnknown")].copy()
print(f"matched success rows (both sides, excl Unknown): {len(m):,}")

flip=m["archetype_id_b"]!="archetype_id_a"
m["flipped"]=m["archetype_id_b"]!=m["archetype_id_a"]
print(f"  archetype changed: {int(m['flipped'].sum()):,}   unchanged: {int((~m['flipped']).sum()):,}")

print("\n=== [1] Which flips, and their total-EUI delta ===")
ft=m[m["flipped"]]
tab=ft.groupby(["archetype_id_b","archetype_id_a"]).agg(
    n=("osm_id","size"),
    eui_b=("total_eui_kwh_m2_b","median"),
    eui_a=("total_eui_kwh_m2_a","median"),
).reset_index().sort_values("n",ascending=False)
for _,r in tab.iterrows():
    print(f"  {r['archetype_id_b']:>16} -> {r['archetype_id_a']:<16} n={int(r['n']):>5}  "
          f"EUI {r['eui_b']:6.1f} -> {r['eui_a']:6.1f}  (dmed {r['eui_a']-r['eui_b']:+6.1f})")

print("\n=== [2] Per-archetype median total EUI (after) vs measured city anchors ===")
for arch in ["SmallOffice","MediumOffice","LargeOffice"]:
    sub=a[a["archetype_id"]==arch]
    print(f"  {arch:<14} n={len(sub):>5}  median EUI={sub['total_eui_kwh_m2'].median():6.1f}  "
          f"mean={sub['total_eui_kwh_m2'].mean():6.1f}")
print(f"  measured city anchors: NYC {MEASURED['nyc']}, LA {MEASURED['la']}, Austin {MEASURED['austin']}")

print("\n=== [3] End-use decomposition: Medium/LargeOffice -> SmallOffice flips (median, kWh/m2) ===")
dt=ft[ft["archetype_id_a"]=="SmallOffice"]
print(f"  n flips into SmallOffice: {len(dt)}")
print(f"  {'end use':<22}{'before':>9}{'after':>9}{'delta':>9}")
for eu in END_USES+["total_eui_kwh_m2"]:
    vb=dt[f"{eu}_b"].median(); va=dt[f"{eu}_a"].median()
    print(f"  {eu:<22}{vb:>9.1f}{va:>9.1f}{va-vb:>+9.1f}")

print("\n=== [4] Decompose fleet-median shift: flipped vs unchanged (per city) ===")
for city in ("nyc","la","austin"):
    cm=m[m["city_b"]==city]
    med_b=cm["total_eui_kwh_m2_b"].median()
    med_a=cm["total_eui_kwh_m2_a"].median()
    # unchanged buildings: did their EUI move at all? (should be ~0 -> geometry frozen)
    unch=cm[~cm["flipped"]]
    unch_moved=(unch["total_eui_kwh_m2_a"]-unch["total_eui_kwh_m2_b"]).abs()
    print(f"  {city.upper():<7} median {med_b:6.1f} -> {med_a:6.1f} (d {med_a-med_b:+5.1f}) | "
          f"unchanged rows: {len(unch):>5}, max|dEUI|={unch_moved.max():.3f}, "
          f"#moved>0.1={int((unch_moved>0.1).sum())}")

print("\n=== [5] Sanity: SmallOffice share of each city's success fleet (after) ===")
for city in ("nyc","la","austin"):
    ca=a[a["city"]==city]
    ca=ca[ca["archetype_id"]!="OpenUBEMUnknown"]
    so=int((ca["archetype_id"]=="SmallOffice").sum())
    print(f"  {city.upper():<7} SmallOffice {so:>5} / {len(ca):>5} = {100*so/len(ca):4.1f}%")
