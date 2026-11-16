from __future__ import annotations
from pathlib import Path
import pandas as pd, numpy as np
ROOT=Path(__file__).resolve().parents[1]
BEFORE=ROOT/"docs"/"docs_VALIDATION"/"validations"/"overAll"/"results"/"phaseE"
AFTER =ROOT/"docs"/"validations"/"overAll"/"results"/"phaseE_er33"
CELLS=["nyc_centre","nyc_urban","nyc_suburban","nyc_rural","la_centre","la_urban","la_suburban","la_rural","austin_centre","austin_urban","austin_suburban","austin_rural"]
SUCCESS={"success","success_cached","success_csv_fallback"}
def load(base):
    fr=[]
    for c in CELLS:
        d=pd.read_csv(base/c/"05_results.csv",dtype={"osm_id":str}); d["cell"]=c; d["city"]=c.split("_")[0]; fr.append(d)
    return pd.concat(fr,ignore_index=True)
b=load(BEFORE); a=load(AFTER)
b=b[b.simulation_status.isin(SUCCESS)]; a=a[a.simulation_status.isin(SUCCESS)]
m=b.merge(a,on=["cell","osm_id"],suffixes=("_b","_a"))
m=m[(m.archetype_id_b!="OpenUBEMUnknown")&(m.archetype_id_a!="OpenUBEMUnknown")]
unch=m[m.archetype_id_b==m.archetype_id_a].copy()
unch["d"]=unch.total_eui_kwh_m2_a-unch.total_eui_kwh_m2_b
print(f"unchanged-archetype matched rows: {len(unch):,}")
for thr in (0.1,1,5,20):
    print(f"  |dEUI|>{thr:>4}: {int((unch['d'].abs()>thr).sum()):>5}")
print("\nBy archetype, count moved>1 and median move:")
mv=unch[unch['d'].abs()>1]
print(mv.groupby("archetype_id_b").agg(n=("d","size"),med_d=("d","median"),max_abs=("d",lambda x:x.abs().max())).sort_values("n",ascending=False).head(15).to_string())
# check if levels changed on moved rows (imputation drift?)
if "levels_b" in unch.columns and "levels_a" in unch.columns:
    lv=unch[unch.levels_b!=unch.levels_a]
    print(f"\nunchanged-archetype rows whose 'levels' changed: {len(lv)}")
