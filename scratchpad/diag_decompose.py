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
m=m[(m.archetype_id_b!="OpenUBEMUnknown")&(m.archetype_id_a!="OpenUBEMUnknown")].copy()
m["flipped"]=m.archetype_id_b!=m.archetype_id_a
m["city"]=m.city_b

print(f"{'city':<8}{'N':>6} | {'med_b':>7}{'med_a':>7}{'d_tot':>7} | "
      f"{'d_clf':>7}{'d_drift':>8}{'resid':>7} || {'mean d_tot':>10}{'mean d_clf':>11}{'mean d_drift':>12}")
for city in ("nyc","la","austin"):
    c=m[m.city==city].copy()
    med_b=c.total_eui_kwh_m2_b.median(); med_a=c.total_eui_kwh_m2_a.median()
    # counterfactual: classifier-only  -> flipped take AFTER, unchanged stay BEFORE
    clf=np.where(c.flipped, c.total_eui_kwh_m2_a, c.total_eui_kwh_m2_b)
    # counterfactual: drift-only        -> unchanged take AFTER, flipped stay BEFORE
    drift=np.where(c.flipped, c.total_eui_kwh_m2_b, c.total_eui_kwh_m2_a)
    d_clf=np.median(clf)-med_b
    d_drift=np.median(drift)-med_b
    d_tot=med_a-med_b
    resid=d_tot-(d_clf+d_drift)
    # exact (linear) MEAN decomposition: per-building delta split by flip flag
    dd=c.total_eui_kwh_m2_a-c.total_eui_kwh_m2_b
    mean_tot=dd.mean()
    mean_clf=dd[c.flipped].sum()/len(c)
    mean_drift=dd[~c.flipped].sum()/len(c)
    print(f"{city.upper():<8}{len(c):>6} | {med_b:>7.1f}{med_a:>7.1f}{d_tot:>+7.1f} | "
          f"{d_clf:>+7.1f}{d_drift:>+8.1f}{resid:>+7.1f} || {mean_tot:>+10.2f}{mean_clf:>+11.2f}{mean_drift:>+12.2f}")

print("\nNotes:")
print(" d_clf   = median shift if ONLY reclassified buildings changed (drift stripped from unchanged)")
print(" d_drift = median shift if ONLY unchanged-archetype buildings drifted (reclassification stripped)")
print(" resid   = median non-additivity (d_tot - d_clf - d_drift); mean columns are EXACTLY additive")
