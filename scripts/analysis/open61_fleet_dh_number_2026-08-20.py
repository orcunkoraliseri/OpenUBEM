import pandas as pd
import numpy as np

CSV = "openubem/outputs/comparisons/open61_census_fleet.csv"

df = pd.read_csv(CSV)

print("=" * 70)
print("A. POPULATION ACCOUNTING")
print("=" * 70)

n_total = len(df)
status_counts = df["status"].value_counts(dropna=False)
n_ok = int(status_counts.get("ok", 0))
n_not_ok = n_total - n_ok

print(f"{'status':<62} {'n':>6}")
for status, n in status_counts.items():
    print(f"{str(status):<62} {n:>6}")
print(f"{'TOTAL':<62} {n_total:>6}")
print()
print(f"total rows                          : {n_total}")
print(f"status != 'ok'                      : {n_not_ok}")
print(f"of which not_simulated_upstream_*   : "
      f"{int(status_counts.get('not_simulated_upstream_excluded_from_census_population', 0))}")
print(f"of which failed_energyplus_oom_*    : "
      f"{int(status_counts.get('failed_energyplus_oom_crash_no_fatal_no_end', 0))}")
print(f"'ok' rows                           : {n_ok}")

ok = df[df["status"] == "ok"].copy()
null_dh = ok["dh_total_kwh"].isna() | (ok["dh_total_kwh"].astype(str).str.strip() == "")
n_null_dh = int(null_dh.sum())
print(f"of 'ok', null/empty dh_total_kwh    : {n_null_dh}")

pop = ok[~null_dh].copy()
n_pop = len(pop)
print(f"ANALYSABLE POPULATION (ok, dh not null): {n_pop}")

if n_pop != 8144:
    print()
    print(f"*** DISCREPANCY: expected 8144, computed {n_pop}. STOPPING. ***")
    raise SystemExit(1)

print()
print("=" * 70)
print("B. HEADLINE — pooled fleet DH intensity")
print("=" * 70)

sum_dh_kwh = pop["dh_total_kwh"].sum()
sum_area = pop["parsed_floor_area_m2"].sum()
headline_pooled = sum_dh_kwh / sum_area

print(f"n                                    : {n_pop}")
print(f"sum(dh_total_kwh)                    : {sum_dh_kwh:,.1f} kWh")
print(f"sum(parsed_floor_area_m2)            : {sum_area:,.1f} m2")
print(f"HEADLINE POOLED = sum(dh)/sum(area)  : {headline_pooled:.4f} kWh/m2")
print()

per_bldg_ratio = pop["dh_total_kwh"] / pop["parsed_floor_area_m2"]
print("NOT the headline — per-building ratio distribution (for reference only):")
print(f"  mean of per-building ratio         : {per_bldg_ratio.mean():.4f} kWh/m2")
print(f"  median of per-building ratio        : {per_bldg_ratio.median():.4f} kWh/m2")

print()
print("=" * 70)
print("C. PER-CELL (12 numbers, pooled within each cell — never averaged together)")
print("=" * 70)

cell_rows = []
for cell, g in pop.groupby("cell"):
    n = len(g)
    total_kwh = g["dh_total_kwh"].sum()
    total_area = g["parsed_floor_area_m2"].sum()
    pooled = total_kwh / total_area
    cell_rows.append((cell, n, pooled, total_kwh))

cell_rows.sort(key=lambda r: -r[1])
print(f"{'cell':<18} {'n':>6} {'pooled kWh/m2':>15} {'total kWh':>18}")
for cell, n, pooled, total_kwh in cell_rows:
    print(f"{cell:<18} {n:>6} {pooled:>15.4f} {total_kwh:>18,.1f}")
print(f"{'sum':<18} {sum(r[1] for r in cell_rows):>6}")

print()
print("=" * 70)
print("D. PER-ARCHETYPE (sorted by n descending)")
print("=" * 70)

arch_rows = []
for arch, g in pop.groupby("archetype_id"):
    n = len(g)
    total_kwh = g["dh_total_kwh"].sum()
    total_area = g["parsed_floor_area_m2"].sum()
    pooled = total_kwh / total_area
    arch_rows.append((arch, n, pooled, total_kwh))

arch_rows.sort(key=lambda r: -r[1])
print(f"{'archetype_id':<28} {'n':>6} {'pooled kWh/m2':>15} {'total kWh':>18}")
for arch, n, pooled, total_kwh in arch_rows:
    print(f"{arch:<28} {n:>6} {pooled:>15.4f} {total_kwh:>18,.1f}")
print(f"{'sum':<28} {sum(r[1] for r in arch_rows):>6}")

print()
print("=" * 70)
print("E. C5 — comparison against prior estimates 8.7 / 17.2 / 20.2 kWh/m2")
print("=" * 70)

band_lo, band_hi = 8.7, 20.2
priors = {"F5 low": 8.7, "F5 mid": 17.2, "F5 high": 20.2}
print(f"headline pooled                     : {headline_pooled:.4f} kWh/m2")
print(f"prior band                          : {band_lo} - {band_hi} kWh/m2")
if band_lo <= headline_pooled <= band_hi:
    print("VERDICT: headline lands INSIDE the 8.7-20.2 band.")
else:
    if headline_pooled < band_lo:
        edge = band_lo
        direction = "below"
    else:
        edge = band_hi
        direction = "above"
    abs_diff = headline_pooled - edge
    pct_diff = abs_diff / edge * 100
    print(f"VERDICT: headline lands OUTSIDE the band, {direction} it.")
    print(f"  distance from nearest edge ({edge}) : {abs_diff:+.4f} kWh/m2 ({pct_diff:+.2f}%)")
for name, val in priors.items():
    abs_diff = headline_pooled - val
    pct_diff = abs_diff / val * 100
    print(f"  vs {name} ({val})                  : {abs_diff:+.4f} kWh/m2 ({pct_diff:+.2f}%)")

print()
print("=" * 70)
print("F. C6 — ratio statistic: DH divided by the DHW end-use")
print("=" * 70)
# Director correction 2026-08-20: the pre-registered ratio is dh / dhw_eui, not
# dh / total site energy. See PLAN_open61-census-open03-storeys-2026-08-20.md:101 (fact F5).
denom = pop["parsed_dhw_eui_kwh_m2"] * pop["parsed_floor_area_m2"]
mask_pos = denom > 0
ratio_share = (pop.loc[mask_pos, "dh_total_kwh"] / denom.loc[mask_pos])

n_ratio = int(mask_pos.sum())
n_excluded_zero_denom = n_pop - n_ratio
q1 = ratio_share.quantile(0.25)
q3 = ratio_share.quantile(0.75)
median_share = ratio_share.median()

print(f"n with denominator > 0               : {n_ratio} (excluded {n_excluded_zero_denom} with denom <= 0)")
print(f"pooled ratio (sum dh / sum dhw)      : {pop['dh_total_kwh'].sum() / denom.sum():.4f}")
print(f"fleet IQR                            : {q1:.4f} - {q3:.4f}")
print(f"fleet median                         : {median_share:.4f}")
print(f"pilot (60-building) IQR              : 0.362 - 0.840")
print(f"pilot (60-building) median           : 0.714")
if q1 <= 0.714 <= q3 or (q1 <= median_share <= q3):
    pass
overlap = not (q3 < 0.362 or q1 > 0.840)
print(f"IQR overlap with pilot IQR            : {'yes' if overlap else 'no'}")
median_diff = median_share - 0.714
print(f"median difference (fleet - pilot)     : {median_diff:+.4f}")
if overlap and abs(median_diff) < 0.10:
    verdict = "REPRESENTATIVE — fleet distribution is consistent with the 60-building pilot."
elif overlap:
    verdict = "PARTIALLY REPRESENTATIVE — IQRs overlap but medians diverge notably."
else:
    verdict = "NOT REPRESENTATIVE — fleet IQR does not overlap the pilot IQR."
print(f"VERDICT: {verdict}")

print()
print("=" * 70)
print("G. C7 — MidriseApartment vs fleet")
print("=" * 70)

mra = pop[pop["archetype_id"] == "MidriseApartment"]
n_mra = len(mra)
if n_mra > 0:
    mra_pooled = mra["dh_total_kwh"].sum() / mra["parsed_floor_area_m2"].sum()
else:
    mra_pooled = float("nan")
print(f"MidriseApartment n                   : {n_mra} (of {n_pop} analysable, {n_mra/n_pop*100:.1f}%)")
print(f"MidriseApartment pooled kWh/m2       : {mra_pooled:.4f}")
print(f"fleet pooled kWh/m2                  : {headline_pooled:.4f}")
print(f"difference (MidriseApartment - fleet): {mra_pooled - headline_pooled:+.4f} kWh/m2")

print()
print("=" * 70)
print("H. Sensitivity — recorded_floor_area_m2 vs parsed_floor_area_m2")
print("=" * 70)

both_present = pop["parsed_floor_area_m2"].notna() & pop["recorded_floor_area_m2"].notna() & (pop["recorded_floor_area_m2"] > 0)
n_both = int(both_present.sum())
sub = pop[both_present]
headline_parsed_sub = sub["dh_total_kwh"].sum() / sub["parsed_floor_area_m2"].sum()
headline_recorded_sub = sub["dh_total_kwh"].sum() / sub["recorded_floor_area_m2"].sum()
diff = headline_recorded_sub - headline_parsed_sub
pct = diff / headline_parsed_sub * 100
print(f"n with both floor-area columns present: {n_both}")
print(f"pooled headline, parsed_floor_area_m2 : {headline_parsed_sub:.4f} kWh/m2")
print(f"pooled headline, recorded_floor_area_m2: {headline_recorded_sub:.4f} kWh/m2")
print(f"difference (recorded - parsed)        : {diff:+.4f} kWh/m2 ({pct:+.2f}%)")

print()
print("=" * 70)
print("I. Named anomalies from T03 (not fixed, not averaged over)")
print("=" * 70)

for cell_id, osm_id, archetype in [
    ("la_rural", "way/472961047", "Warehouse"),
    ("la_centre", "way/319507579", "SecondarySchool"),
]:
    row = df[(df["cell"] == cell_id) & (df["osm_id"] == osm_id)]
    if len(row) == 1:
        r = row.iloc[0]
        print(f"{cell_id} {osm_id} ({archetype}):")
        print(f"  status={r['status']} parsed_parse_status={r['parsed_parse_status']} "
              f"dh_total_kwh={r['dh_total_kwh']} c1_diff_kwh_m2={r['c1_diff_kwh_m2']} "
              f"parsed_floor_area_m2={r['parsed_floor_area_m2']}")
    else:
        print(f"{cell_id} {osm_id} ({archetype}): row not found uniquely (matches={len(row)})")

print()
print("Materiality check: if each anomaly's missing DH were assigned a plausible value")
print("equal to its OWN archetype's pooled kWh/m2 rate x its own floor area, would the headline move?")
arch_pooled = {a: p for a, n, p, t in arch_rows}
for label, cell_id, osm_id, archetype in [
    ("la_rural way/472961047 (Warehouse)", "la_rural", "way/472961047", "Warehouse"),
    ("la_centre way/319507579 (SecondarySchool)", "la_centre", "way/319507579", "SecondarySchool"),
]:
    row = df[(df.cell == cell_id) & (df.osm_id == osm_id)]
    area = row["parsed_floor_area_m2"].iloc[0] if len(row) else np.nan
    plausible_rate = arch_pooled.get(archetype, np.nan)
    plausible_dh = plausible_rate * area
    new_sum_dh = sum_dh_kwh + plausible_dh
    new_sum_area = sum_area + (area if pd.notna(area) else 0)
    new_headline = new_sum_dh / new_sum_area
    delta = new_headline - headline_pooled
    print(f"  {label}: archetype pooled rate={plausible_rate:.4f} kWh/m2, own area={area:.1f} m2 "
          f"-> plausible dh_total_kwh={plausible_dh:,.1f} kWh -> headline shifts by "
          f"{delta:+.5f} kWh/m2 (n=1 of {n_pop} population)")

print()
print("=" * 70)
print("Done.")
print("=" * 70)
