import os
import pandas as pd

CELLS = [
    "austin_centre", "austin_rural", "austin_suburban", "austin_urban",
    "la_centre", "la_rural", "la_suburban", "la_urban",
    "nyc_centre", "nyc_rural", "nyc_suburban", "nyc_urban",
]
ROOT = r"C:\Users\o_iseri\Desktop\OpenUBEM\evidence\open48_refleet4"
OUT = r"C:\Users\o_iseri\Desktop\OpenUBEM\openubem\outputs\comparisons\open19_city_offset_2026-08-21.csv"

frames = []
for cell in CELLS:
    df = pd.read_csv(os.path.join(ROOT, cell, "results", "05_results.csv"))
    df["cell"] = cell
    df["city"] = cell.split("_")[0]
    frames.append(df)

fleet = pd.concat(frames, ignore_index=True)
ok = fleet[fleet["simulation_status"] == "success"].copy()

print(f"fleet rows total = {len(fleet)}, success = {len(ok)}")

def pooled(df, energy_col="total_eui_kwh_m2", area_col="floor_area_m2"):
    energy = (df[energy_col] * df[area_col]).sum()
    area = df[area_col].sum()
    return energy / area, energy, area

# C20 check: whole fleet pooled figure
p_all, e_all, a_all = pooled(ok)
print(f"C20 check: pooled fleet EUI = {p_all:.4f} kWh/m2 over n={len(ok)}, area={a_all:.1f} m2")

# by city
city_rows = []
for city, grp in ok.groupby("city"):
    p, e, a = pooled(grp)
    p_h, _, _ = pooled(grp, "heating_eui_kwh_m2")
    p_c, _, _ = pooled(grp, "cooling_eui_kwh_m2")
    city_rows.append({"level": "city", "key": city, "n": len(grp), "pooled_total_eui": p,
                       "pooled_heating_eui": p_h, "pooled_cooling_eui": p_c, "floor_area_m2": a})

city_df = pd.DataFrame(city_rows).set_index("key")
print("\n=== pooled EUI by city (mix included) ===")
print(city_df.to_string())

la_p = city_df.loc["la", "pooled_total_eui"]
austin_p = city_df.loc["austin", "pooled_total_eui"]
nyc_p = city_df.loc["nyc", "pooled_total_eui"]
print(f"\nLA vs Austin offset (mix-included) = {(la_p/austin_p - 1)*100:.2f}%")
print(f"LA vs NYC offset (mix-included) = {(la_p/nyc_p - 1)*100:.2f}%")

# by cell
cell_rows = []
for cell, grp in ok.groupby("cell"):
    p, e, a = pooled(grp)
    cell_rows.append({"level": "cell", "key": cell, "n": len(grp), "pooled_total_eui": p,
                       "pooled_heating_eui": pooled(grp, "heating_eui_kwh_m2")[0],
                       "pooled_cooling_eui": pooled(grp, "cooling_eui_kwh_m2")[0],
                       "floor_area_m2": a})
cell_df = pd.DataFrame(cell_rows)
print("\n=== pooled EUI by cell ===")
print(cell_df.to_string(index=False))

# archetype-matched: archetypes present in all three cities
arch_by_city = ok.groupby(["city", "archetype_id"]).size().unstack(fill_value=0)
common_archs = [a for a in arch_by_city.columns if (arch_by_city[a] > 0).all()]
print(f"\narchetypes present in all 3 cities: {common_archs}")

matched = ok[ok["archetype_id"].isin(common_archs)]
arch_rows = []
for (city, arch), grp in matched.groupby(["city", "archetype_id"]):
    p, e, a = pooled(grp)
    arch_rows.append({"level": "archetype_matched", "key": f"{city}:{arch}", "city": city,
                       "archetype_id": arch, "n": len(grp), "pooled_total_eui": p,
                       "pooled_heating_eui": pooled(grp, "heating_eui_kwh_m2")[0],
                       "pooled_cooling_eui": pooled(grp, "cooling_eui_kwh_m2")[0],
                       "floor_area_m2": a})
arch_df = pd.DataFrame(arch_rows)
print("\n=== archetype-matched pooled EUI ===")
print(arch_df.sort_values(["archetype_id", "city"]).to_string(index=False))

# archetype-matched pooled overall (mix-free): pool matched-archetype rows only, by city
mm_rows = []
for city, grp in matched.groupby("city"):
    p, e, a = pooled(grp)
    mm_rows.append({"city": city, "n": len(grp), "pooled_total_eui": p, "floor_area_m2": a})
mm_df = pd.DataFrame(mm_rows).set_index("city")
print("\n=== archetype-matched-only pooled EUI (mix-free-ish, still area-weighted within archetype), by city ===")
print(mm_df.to_string())
la_mm = mm_df.loc["la", "pooled_total_eui"]
austin_mm = mm_df.loc["austin", "pooled_total_eui"]
nyc_mm = mm_df.loc["nyc", "pooled_total_eui"]
print(f"LA vs Austin offset (archetype-matched) = {(la_mm/austin_mm - 1)*100:.2f}%")
print(f"LA vs NYC offset (archetype-matched) = {(la_mm/nyc_mm - 1)*100:.2f}%")

# write combined csv
combined = pd.concat([city_df.reset_index().rename(columns={"key": "key"}), cell_df, arch_df], ignore_index=True, sort=False)
combined.to_csv(OUT, index=False)
print(f"\nRows written: {len(combined)} -> {OUT}")
