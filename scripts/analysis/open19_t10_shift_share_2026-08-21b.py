"""T10 of PLAN_ten-live-items-2026-08-21-night.md.

Shift-share decomposition of the LA-vs-Austin and LA-vs-NYC pooled EUI gap into
an archetype-mix component and a within-archetype-intensity component, on the
15-archetype matched set already built for OPEN-19 (F13). Measurement only, no
re-simulation, no remedy.
"""
import pandas as pd
import numpy as np

EVID = "evidence/open48_refleet4"
CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
CITY_OF = {c: c.split("_", 1)[0] for c in CELLS}

# ---- C20: reproduce F13's three pooled city numbers from 05_results.csv directly ----
frames = []
for cell in CELLS:
    r = pd.read_csv(f"{EVID}/{cell}/results/05_results.csv")
    r["city"] = CITY_OF[cell]
    r["cell"] = cell
    frames.append(r)
full = pd.concat(frames, ignore_index=True)
ok = full[full["simulation_status"] == "success"].copy()

print("=== C20 reproduction ===")
city_pooled = {}
for city, g in ok.groupby("city"):
    pooled = (g["total_eui_kwh_m2"] * g["floor_area_m2"]).sum() / g["floor_area_m2"].sum()
    city_pooled[city] = pooled
    print(f"{city}: n={len(g)} pooled_total_eui={pooled:.2f} floor_area_m2={g['floor_area_m2'].sum():.1f}")
print("F13 target: austin=161.00 la=128.13 nyc=165.27")

# ---- shift-share on the archetype-matched (15-archetype) set ----
am = pd.read_csv("openubem/outputs/comparisons/open19_city_offset_2026-08-21.csv")
am = am[am["level"] == "archetype_matched"].copy()
n_archetypes = am["archetype_id"].nunique()
print(f"\narchetype-matched set: {n_archetypes} archetypes, {len(am)} city x archetype rows")

pivot_eui = am.pivot(index="archetype_id", columns="city", values="pooled_total_eui")
pivot_area = am.pivot(index="archetype_id", columns="city", values="floor_area_m2")
pivot_heat = am.pivot(index="archetype_id", columns="city", values="pooled_heating_eui")
pivot_cool = am.pivot(index="archetype_id", columns="city", values="pooled_cooling_eui")

total_area = pivot_area.sum(axis=0)
share = pivot_area.div(total_area, axis=1)

matched_pooled = (pivot_eui * share).sum(axis=0)
print("\nmatched-set (15-archetype) pooled EUI, share-weighted reconstruction:")
for city in ["austin", "la", "nyc"]:
    print(f"  {city}: {matched_pooled[city]:.2f}")
print("F13 §3 target (matched subset): austin=154.94 la=129.09 nyc=172.77")

def shift_share(base_city, comp_city):
    share_base = share[base_city]
    share_comp = share[comp_city]
    int_base = pivot_eui[base_city]
    int_comp = pivot_eui[comp_city]
    mix = ((share_comp - share_base) * int_base).sum()
    intensity = (share_comp * (int_comp - int_base)).sum()
    gap = matched_pooled[comp_city] - matched_pooled[base_city]
    residual = (mix + intensity) - gap
    return mix, intensity, gap, residual

print("\n=== C21: shift-share, LA vs Austin (base=austin, comp=la) ===")
mix, intensity, gap, resid = shift_share("austin", "la")
print(f"gap (la - austin, matched basis) = {gap:.4f}")
print(f"mix effect = {mix:.4f} ({100*mix/gap:.1f}% of gap)")
print(f"intensity effect = {intensity:.4f} ({100*intensity/gap:.1f}% of gap)")
print(f"mix + intensity = {mix+intensity:.4f}; residual vs gap = {resid:.6f}")

print("\n=== C21: shift-share, LA vs NYC (base=nyc, comp=la) ===")
mix2, intensity2, gap2, resid2 = shift_share("nyc", "la")
print(f"gap (la - nyc, matched basis) = {gap2:.4f}")
print(f"mix effect = {mix2:.4f} ({100*mix2/gap2:.1f}% of gap)")
print(f"intensity effect = {intensity2:.4f} ({100*intensity2/gap2:.1f}% of gap)")
print(f"mix + intensity = {mix2+intensity2:.4f}; residual vs gap = {resid2:.6f}")

# ---- top archetypes by combined matched-set area, heating/cooling split ----
archetype_total_area = pivot_area.sum(axis=1)
top_n = 4
top_archetypes = archetype_total_area.sort_values(ascending=False).head(top_n).index.tolist()
print(f"\n=== top {top_n} archetypes by combined matched-set floor area ===")
for a in top_archetypes:
    print(f"{a}: combined_area={archetype_total_area[a]:.0f}")
    for city in ["austin", "la", "nyc"]:
        print(f"    {city}: heating={pivot_heat.loc[a, city]:.2f} cooling={pivot_cool.loc[a, city]:.2f} total={pivot_eui.loc[a, city]:.2f}")

# ---- EPW / climate manifest per cell ----
print("\n=== EPW file per cell ===")
import os
for cell in CELLS:
    epw = pd.read_parquet(f"{EVID}/{cell}/02a_climate_epw.parquet")
    n_unique = epw["epw_path"].nunique()
    top = os.path.basename(epw["epw_path"].mode().iloc[0])
    cols = epw.columns.tolist()
    print(f"{cell}: n_unique_epw={n_unique} file={top}")
print("02a_climate_epw.parquet columns:", pd.read_parquet(f'{EVID}/austin_centre/02a_climate_epw.parquet').columns.tolist())
print("degree-day proxy column present? searched columns above for HDD/CDD/degree-day tokens: none found")

out = pd.DataFrame({
    "archetype_id": pivot_eui.index,
    "share_austin": share["austin"], "share_la": share["la"], "share_nyc": share["nyc"],
    "eui_austin": pivot_eui["austin"], "eui_la": pivot_eui["la"], "eui_nyc": pivot_eui["nyc"],
    "area_austin": pivot_area["austin"], "area_la": pivot_area["la"], "area_nyc": pivot_area["nyc"],
}).reset_index(drop=True)
out_path = "openubem/outputs/comparisons/open19_t10_shift_share_2026-08-21b.csv"
out.to_csv(out_path, index=False)
print("\nwrote:", out_path, "rows:", len(out))
