import pandas as pd
import glob
import os

CELLS = [f"{city}_{zone}" for city in ("austin", "la", "nyc") for zone in ("centre", "rural", "suburban", "urban")]

def load_evidence(root):
    frames = []
    for cell in CELLS:
        p = os.path.join(root, cell, "results", "05_results.csv")
        if not os.path.exists(p):
            return None
        df = pd.read_csv(p)
        df["cell"] = cell
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

def pooled(df):
    e = df["total_eui_kwh_m2"] * df["floor_area_m2"]
    return e.sum() / df["floor_area_m2"].sum(), df["floor_area_m2"].sum(), len(df)

EVID = r"evidence\open48_refleet4"
TEMP = os.path.expandvars(r"%LOCALAPPDATA%\Temp\ubem_validation\open48_refleet4")

print("=== evidence/open48_refleet4 ===")
df_all = load_evidence(EVID)
print("rows(all):", len(df_all))

a = df_all
b = df_all[df_all["simulation_status"] == "success"]
c = b[b["floor_area_m2"] > 0]
d = b[b["total_eui_kwh_m2"].notna()]

for name, sub in [("a_all8160", a), ("b_success8153", b), ("c_success_area_pos", c), ("d_success_eui_notnull", d)]:
    pe, area, n = pooled(sub)
    print(f"{name}: n={n} area={area:.1f} pooled={pe:.4f}")

print("\n=== per-cell pooled (row set b) vs restatement table ===")
restated = {
    "austin_centre": 158.16, "austin_rural": 154.42, "austin_suburban": 159.20, "austin_urban": 173.62,
    "la_centre": 129.73, "la_rural": 121.51, "la_suburban": 108.42, "la_urban": 130.59,
    "nyc_centre": 166.57, "nyc_rural": 233.63, "nyc_suburban": 188.66, "nyc_urban": 148.21,
}
rows = []
for cell in CELLS:
    sub = b[b["cell"] == cell]
    pe, area, n = pooled(sub)
    diff = pe - restated[cell]
    print(f"{cell}: n={n} pooled={pe:.4f} restated={restated[cell]} diff={diff:.4f}")
    rows.append({"cell": cell, "n_success": n, "recomputed_pooled_eui": round(pe, 4),
                 "restated_table_eui": restated[cell], "diff": round(diff, 4)})
pd.DataFrame(rows).to_csv(r"openubem\outputs\comparisons\t01_headline-reproduction_percell_2026-08-21b.csv", index=False)

print("\n=== rounding hypothesis on row set b ===")
pe_b, area_b, n_b = pooled(b)
for prec in range(0, 6):
    print(f"round({prec}) = {round(pe_b, prec)}")

print("\n=== C1 check ===")
print(f"row set b pooled = {pe_b:.4f} (expect 153.8304 +/- 0.0002)")

print("\n=== different source: TEMP ubem_validation copy (cited provenance of the adopted number) ===")
df_temp = load_evidence(TEMP)
if df_temp is None:
    print("TEMP source missing one or more cells; skipped")
else:
    b_temp = df_temp[df_temp["simulation_status"] == "success"]
    pe_t, area_t, n_t = pooled(b_temp)
    print(f"TEMP success: n={n_t} area={area_t:.1f} pooled={pe_t:.4f}")
    same_id = df_all["osm_id"].astype(str).sort_values().reset_index(drop=True).equals(
        df_temp["osm_id"].astype(str).sort_values().reset_index(drop=True)
    )
    print(f"evidence vs TEMP osm_id sets identical (sorted equal): {same_id}")

print("\n=== other run directories under evidence/open48_refleet* ===")
for d in sorted(glob.glob(r"evidence\open48_refleet*")):
    name = os.path.basename(d)
    if name == "open48_refleet4":
        continue
    found = [c for c in CELLS if os.path.exists(os.path.join(d, c, "results", "05_results.csv"))]
    print(f"{name}: cells with 05_results.csv = {len(found)}/12 -> {found if len(found) < 12 else 'ALL'}")
    if len(found) == 12:
        df_other = load_evidence(d)
        if "floor_area_m2" not in df_other.columns:
            print(f"  {name}: no floor_area_m2 column (schema: {list(df_other.columns)[:6]}...) - cannot pool, SKIPPED")
            continue
        b_other = df_other[df_other["simulation_status"] == "success"]
        pe_o, area_o, n_o = pooled(b_other)
        print(f"  {name} success pooled = n={n_o} area={area_o:.1f} pooled={pe_o:.4f}")
