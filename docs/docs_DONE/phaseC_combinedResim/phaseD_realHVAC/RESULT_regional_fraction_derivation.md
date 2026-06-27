# RESULT — Regional End-Use Fraction Derivation (CP-1 audit data, DD3b ratio-tilt)

- **Task:** T01 (re-derivation) / T02, PLAN_regional_service_load_fractions.md
- **Method:** DD3b ratio-tilt (CP-1 RULING, PLAN §8 lines 117-131). Supersedes the original DD3 wholesale-CBECS-swap.
- **Script:** `scripts/validation/cbecs_regional_enduse_fractions.py`
- **Output artifact:** `openubem/data/service_loads/enduse_fractions_regional.json`
- **Date:** 2026-06-26
- **CBECS source:** `%TEMP%/cbecs_2018_raw/cbecs2018_final_public.csv` (6,436 rows, 1,249 cols; 6,357 clean after dropping NaN/zero MFBTU or NaN FINALWT)

---

## §0 GUARD ASSERTION (the proof the climate tilt points the right way)

**Required (DD3b):** for `large_office`, `mf_adj[middle_atlantic] > 0.83 > mf_adj[pacific]` (cold MA rises above national table4 level; mild PAC falls below).

| quantity | value |
|---|---|
| mf_cb_nat[large_office] (CBECS national modeled_frac, all CENDIVs) | 0.5849 |
| mf_t4[large_office] (table4 national modeled_frac) | 0.8300 |
| mf_adj[middle_atlantic] | **0.8633** |
| mf_adj[pacific] | **0.7706** |
| mf_adj[west_south_central] | 0.8093 |

**RESULT: GUARD PASS** — MA(0.8633) > 0.8300 > PAC(0.7706). WSC=0.8093 (mild interior, just below national). The climate tilt is now anchored on the validated table4 level; the CBECS "Other"-allocation level artifact (which deflated all uplifts uniformly under DD3) is cancelled by the r_factor ratio.

---

## §1 DD3b method

For each (region r, group g) with regional CBECS data (not thin-cell/residential fallback):

```
mf_cb_nat[g]    = CBECS national modeled_frac (ALL CENDIVs, FINALWT-weighted)
mf_cb_reg[r][g] = CBECS regional modeled_frac (that division)
mf_t4[g]        = table4 national modeled_frac (sh+sc+lt+ep)
r_factor        = mf_cb_reg[r][g] / mf_cb_nat[g]
mf_adj          = clamp(mf_t4[g] * r_factor, 0.30, 0.97)
9 fractions     = table4[g] rebuilt: modeled keys * (mf_adj/mf_t4), non-modeled keys * ((1-mf_adj)/(1-mf_t4))
```

r_factor is a PURE CBECS climate ratio; the absolute level comes from the validated table4. No city anchor consulted (not anchor-fitting).

**Predicted-direction note:** MA mf_adj > national (0.8300) -> NYC office uplift (1/mf) DOWN -> NYC reconstructed EUI DOWN -> NYC national NMBE +12.2 SHRINKS. PAC mf_adj < national -> LA office uplift UP -> LA reconstructed EUI UP -> LA national NMBE -16.8 RISES toward 0.

---

## §2 CBECS national modeled_frac per group (the DD3b anchor denominator)

| group | n (all CENDIVs) | mf_cb_nat | mf_t4 (table4) |
|---|---|---|---|
| full_service_restaurant | 218 | 0.2385 | 0.3300 |
| hospital | 562 | 0.5152 | 0.8100 |
| large_hotel | 418 | 0.2901 | 0.6400 |
| large_office | 1434 | 0.5849 | 0.8300 |
| primary_school | 936 | 0.6651 | 0.7800 |
| secondary_school | 936 | 0.6651 | 0.7900 |
| small_office | 1329 | 0.5809 | 0.8500 |
| standalone_retail | 546 | 0.5026 | 0.8100 |
| supermarket | 91 | 0.2386 | 0.3600 |
| warehouse | 712 | 0.6963 | 0.6800 |

Note: mf_cb_nat << mf_t4 for most groups — this IS the "Other"-allocation level artifact the CP-1 ruling identified. It cancels in r_factor (appears in both regional numerator and national denominator), so only the cross-region tilt survives.

---

## §3 r_factor, mf_adj vs national per region x group

Key: r_factor = mf_cb_reg/mf_cb_nat (CBECS climate ratio); mf_adj = clamp(mf_t4*r_factor); uplift = 1/mf_adj.

| region | group | n | mf_cb_reg | r_factor | mf_t4 | mf_adj | uplift (1/mf_adj) | nat uplift (1/mf_t4) |
|---|---|---|---|---|---|---|---|---|
| middle_atlantic | large_office | 205 | 0.6084 | 1.0401 | 0.8300 | 0.8633 | 1.158 | 1.205 |
| middle_atlantic | small_office | 194 | 0.6074 | 1.0456 | 0.8500 | 0.8888 | 1.125 | 1.176 |
| middle_atlantic | primary_school | 170 | 0.7072 | 1.0633 | 0.7800 | 0.8294 | 1.206 | 1.282 |
| middle_atlantic | secondary_school | 170 | 0.7072 | 1.0633 | 0.7900 | 0.8400 | 1.190 | 1.266 |
| middle_atlantic | standalone_retail | 48 | 0.5808 | 1.1554 | 0.8100 | 0.9359 | 1.069 | 1.235 |
| middle_atlantic | large_hotel | 54 | 0.3141 | 1.0826 | 0.6400 | 0.6929 | 1.443 | 1.562 |
| middle_atlantic | hospital | 93 | 0.5152 | 0.9999 | 0.8100 | 0.8099 | 1.235 | 1.235 |
| middle_atlantic | warehouse | 85 | 0.7588 | 1.0897 | 0.6800 | 0.7410 | 1.350 | 1.471 |
| pacific | large_office | 209 | 0.5431 | 0.9284 | 0.8300 | 0.7706 | 1.298 | 1.205 |
| pacific | small_office | 189 | 0.5455 | 0.9391 | 0.8500 | 0.7982 | 1.253 | 1.176 |
| pacific | primary_school | 85 | 0.5588 | 0.8402 | 0.7800 | 0.6553 | 1.526 | 1.282 |
| pacific | secondary_school | 85 | 0.5588 | 0.8402 | 0.7900 | 0.6638 | 1.507 | 1.266 |
| pacific | standalone_retail | 63 | 0.3739 | 0.7439 | 0.8100 | 0.6026 | 1.660 | 1.235 |
| pacific | full_service_restaurant | 29 | 0.2117 | 0.8875 | 0.3300 | 0.3000 | 3.333 | 3.030 |
| pacific | large_hotel | 65 | 0.2377 | 0.8195 | 0.6400 | 0.5245 | 1.907 | 1.562 |
| pacific | hospital | 84 | 0.4363 | 0.8468 | 0.8100 | 0.6859 | 1.458 | 1.235 |
| pacific | warehouse | 117 | 0.5828 | 0.8370 | 0.6800 | 0.5692 | 1.757 | 1.471 |
| west_south_central | large_office | 160 | 0.5704 | 0.9751 | 0.8300 | 0.8093 | 1.236 | 1.205 |
| west_south_central | small_office | 146 | 0.5581 | 0.9606 | 0.8500 | 0.8165 | 1.225 | 1.176 |
| west_south_central | primary_school | 112 | 0.6156 | 0.9255 | 0.7800 | 0.7219 | 1.385 | 1.282 |
| west_south_central | secondary_school | 112 | 0.6156 | 0.9255 | 0.7900 | 0.7312 | 1.368 | 1.266 |
| west_south_central | standalone_retail | 82 | 0.5101 | 1.0148 | 0.8100 | 0.8219 | 1.217 | 1.235 |
| west_south_central | full_service_restaurant | 30 | 0.2326 | 0.9754 | 0.3300 | 0.3219 | 3.107 | 3.030 |
| west_south_central | large_hotel | 51 | 0.3112 | 1.0726 | 0.6400 | 0.6865 | 1.457 | 1.562 |
| west_south_central | hospital | 59 | 0.5101 | 0.9900 | 0.8100 | 0.8019 | 1.247 | 1.235 |
| west_south_central | warehouse | 82 | 0.6085 | 0.8739 | 0.6800 | 0.5942 | 1.683 | 1.471 |

**Direction check (mf_adj vs national mf_t4):** Office and schools in cold MA have mf_adj ABOVE national (uplift below national); mild PAC/WSC have mf_adj BELOW national (uplift above national). This is the climate-correct direction. Only clamp triggered: PAC full_service_restaurant (mf_adj_raw 0.2929 -> floor 0.30).

---

## §4 SIGNATURE CHECK (mf_adj ordered cold > mild for Office and heating-sensitive groups)

| group | MA mf_adj | PAC mf_adj | WSC mf_adj | direction (high mf_adj = cold = low uplift) |
|---|---|---|---|---|
| large_office | 0.8633 | 0.7706 | 0.8093 | MA > WSC > PAC — MA coldest HOLDS |
| small_office | 0.8888 | 0.7982 | 0.8165 | MA > WSC > PAC — MA coldest HOLDS |
| primary_school | 0.8294 | 0.6553 | 0.7219 | MA > WSC > PAC — MA coldest HOLDS |
| secondary_school | 0.8400 | 0.6638 | 0.7312 | MA > WSC > PAC — MA coldest HOLDS |
| standalone_retail | 0.9359 | 0.6026 | 0.8219 | MA > WSC > PAC — MA coldest HOLDS |
| hospital | 0.8099 | 0.6859 | 0.8019 | MA > WSC > PAC — MA coldest HOLDS |
| warehouse | 0.7410 | 0.5692 | 0.5942 | MA > WSC > PAC — MA coldest HOLDS |
| large_hotel | 0.6929 | 0.5245 | 0.6865 | MA > WSC > PAC — MA coldest HOLDS |
| full_service_restaurant | national | 0.3000 | 0.3219 | MA(national thin-cell); PAC < WSC |
| supermarket | national | national | national | thin-cell all three — N/A |

The cold-MA-highest-mf_adj signature holds unambiguously for every group that received regional data. Pacific (coastal mild) consistently has the lowest mf_adj; WSC (interior, more heating+cooling than coastal LA) sits between — the expected climate ordering.

---

## §5 Full rebuilt 9-fraction tables per region

Key: sh=space_heat, sc=space_cool, vf=vent_fans, pm=pumps, sw=swh_dhw, lt=lighting, ep=equip_plug, rf=refrig, co=cooking_other. [NATIONAL] = thin-cell/residential fallback (national table4 verbatim, not written as override).

### middle_atlantic

| group | src | sh | sc | vf | pm | sw | lt | ep | rf | co | mf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full_service_restaurant | NATIONAL | 0.1200 | 0.0700 | 0.0700 | 0.0150 | 0.0800 | 0.0500 | 0.0900 | 0.1500 | 0.3550 | 0.3300 |
| hospital | regional | 0.4000 | 0.1400 | 0.1000 | 0.0350 | 0.0300 | 0.1100 | 0.1600 | 0.0100 | 0.0150 | 0.8099 |
| large_hotel | regional | 0.2706 | 0.1516 | 0.0683 | 0.0256 | 0.1706 | 0.1083 | 0.1624 | 0.0171 | 0.0256 | 0.6929 |
| large_office | regional | 0.3120 | 0.1456 | 0.0885 | 0.0282 | 0.0121 | 0.1248 | 0.2808 | 0.0040 | 0.0040 | 0.8633 |
| mid_rise_apartment | NATIONAL | 0.2800 | 0.1100 | 0.0500 | 0.0100 | 0.2300 | 0.0800 | 0.2200 | 0.0100 | 0.0100 | 0.6900 |
| primary_school | regional | 0.4041 | 0.0851 | 0.0931 | 0.0233 | 0.0233 | 0.1489 | 0.1914 | 0.0078 | 0.0233 | 0.8294 |
| secondary_school | regional | 0.3828 | 0.1063 | 0.0838 | 0.0229 | 0.0305 | 0.1489 | 0.2020 | 0.0076 | 0.0152 | 0.8400 |
| small_office | regional | 0.3660 | 0.1046 | 0.0890 | 0.0074 | 0.0074 | 0.1568 | 0.2614 | 0.0037 | 0.0037 | 0.8888 |
| standalone_retail | regional | 0.3235 | 0.1502 | 0.0405 | 0.0051 | 0.0051 | 0.2542 | 0.2080 | 0.0051 | 0.0084 | 0.9359 |
| supermarket | NATIONAL | 0.0900 | 0.0600 | 0.1000 | 0.0100 | 0.0100 | 0.1300 | 0.0800 | 0.5000 | 0.0200 | 0.3600 |
| warehouse | regional | 0.5558 | 0.0327 | 0.0728 | 0.0081 | 0.0081 | 0.1090 | 0.0436 | 0.0405 | 0.1295 | 0.7410 |

### pacific

| group | src | sh | sc | vf | pm | sw | lt | ep | rf | co | mf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full_service_restaurant | regional | 0.1091 | 0.0636 | 0.0731 | 0.0157 | 0.0836 | 0.0455 | 0.0818 | 0.1567 | 0.3709 | 0.3000 |
| hospital | regional | 0.3387 | 0.1186 | 0.1653 | 0.0579 | 0.0496 | 0.0932 | 0.1355 | 0.0165 | 0.0248 | 0.6859 |
| large_hotel | regional | 0.2049 | 0.1147 | 0.1057 | 0.0396 | 0.2642 | 0.0820 | 0.1229 | 0.0264 | 0.0396 | 0.5245 |
| large_office | regional | 0.2785 | 0.1300 | 0.1484 | 0.0472 | 0.0202 | 0.1114 | 0.2507 | 0.0067 | 0.0067 | 0.7706 |
| mid_rise_apartment | NATIONAL | 0.2800 | 0.1100 | 0.0500 | 0.0100 | 0.2300 | 0.0800 | 0.2200 | 0.0100 | 0.0100 | 0.6900 |
| primary_school | regional | 0.3193 | 0.0672 | 0.1880 | 0.0470 | 0.0470 | 0.1176 | 0.1512 | 0.0157 | 0.0470 | 0.6553 |
| secondary_school | regional | 0.3025 | 0.0840 | 0.1761 | 0.0480 | 0.0640 | 0.1176 | 0.1596 | 0.0160 | 0.0320 | 0.6638 |
| small_office | regional | 0.3287 | 0.0939 | 0.1614 | 0.0135 | 0.0135 | 0.1409 | 0.2348 | 0.0067 | 0.0067 | 0.7982 |
| standalone_retail | regional | 0.2083 | 0.0967 | 0.2510 | 0.0314 | 0.0314 | 0.1637 | 0.1339 | 0.0314 | 0.0523 | 0.6026 |
| supermarket | NATIONAL | 0.0900 | 0.0600 | 0.1000 | 0.0100 | 0.0100 | 0.1300 | 0.0800 | 0.5000 | 0.0200 | 0.3600 |
| warehouse | regional | 0.4269 | 0.0251 | 0.1212 | 0.0135 | 0.0135 | 0.0837 | 0.0335 | 0.0673 | 0.2154 | 0.5692 |

### west_south_central

| group | src | sh | sc | vf | pm | sw | lt | ep | rf | co | mf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| full_service_restaurant | regional | 0.1170 | 0.0683 | 0.0708 | 0.0152 | 0.0810 | 0.0488 | 0.0878 | 0.1518 | 0.3593 | 0.3219 |
| hospital | regional | 0.3960 | 0.1386 | 0.1042 | 0.0365 | 0.0313 | 0.1089 | 0.1584 | 0.0104 | 0.0156 | 0.8019 |
| large_hotel | regional | 0.2682 | 0.1502 | 0.0697 | 0.0261 | 0.1742 | 0.1073 | 0.1609 | 0.0174 | 0.0261 | 0.6865 |
| large_office | regional | 0.2925 | 0.1365 | 0.1234 | 0.0393 | 0.0168 | 0.1170 | 0.2633 | 0.0056 | 0.0056 | 0.8093 |
| mid_rise_apartment | NATIONAL | 0.2800 | 0.1100 | 0.0500 | 0.0100 | 0.2300 | 0.0800 | 0.2200 | 0.0100 | 0.0100 | 0.6900 |
| primary_school | regional | 0.3517 | 0.0740 | 0.1517 | 0.0379 | 0.0379 | 0.1296 | 0.1666 | 0.0126 | 0.0379 | 0.7219 |
| secondary_school | regional | 0.3332 | 0.0926 | 0.1408 | 0.0384 | 0.0512 | 0.1296 | 0.1759 | 0.0128 | 0.0256 | 0.7312 |
| small_office | regional | 0.3362 | 0.0961 | 0.1468 | 0.0122 | 0.0122 | 0.1441 | 0.2402 | 0.0061 | 0.0061 | 0.8165 |
| standalone_retail | regional | 0.2841 | 0.1319 | 0.1125 | 0.0141 | 0.0141 | 0.2232 | 0.1827 | 0.0141 | 0.0234 | 0.8219 |
| supermarket | NATIONAL | 0.0900 | 0.0600 | 0.1000 | 0.0100 | 0.0100 | 0.1300 | 0.0800 | 0.5000 | 0.0200 | 0.3600 |
| warehouse | regional | 0.4457 | 0.0262 | 0.1141 | 0.0127 | 0.0127 | 0.0874 | 0.0350 | 0.0634 | 0.2029 | 0.5942 |

---

## §6 Thin-cell / residential fallbacks (kept national, no regional override written)

| division x group | n | reason |
|---|---|---|
| middle_atlantic x supermarket | 6 | thin-cell (DD6, n<25) |
| middle_atlantic x full_service_restaurant | 12 | thin-cell (DD6, n<25) |
| pacific x supermarket | 9 | thin-cell (DD6, n<25) |
| west_south_central x supermarket | 13 | thin-cell (DD6, n<25) |
| all x mid_rise_apartment | — | residential, CBECS excludes (DD5) |

All other group cells have n >= 25 and received DD3b regional overrides.

---

## §7 Per-cell raw n (regional pass)

| group | PBA codes | n_MA | n_PAC | n_WSC |
|---|---|---|---|---|
| large_office | 2,7 | 205 | 209 | 160 |
| small_office | 2,7 | 194 | 189 | 146 |
| primary_school | 14 | 170 | 85 | 112 |
| secondary_school | 14 | 170 | 85 | 112 |
| standalone_retail | 23,25 | 48 | 63 | 82 |
| supermarket | 6 | 6 | 9 | 13 |
| full_service_restaurant | 15 | 12 | 29 | 30 |
| large_hotel | 18 | 54 | 65 | 51 |
| hospital | 4,8,16 | 93 | 84 | 59 |
| warehouse | 5 | 85 | 117 | 82 |

primary_school and secondary_school share PBA 14 (Education); they get identical mf_cb_reg / r_factor within each division (rebuilt fractions differ only because mf_t4 differs: 0.78 vs 0.79).

---

## §8 Validation checks

- GUARD ASSERTION (large_office MA > 0.83 > PAC): **PASS** (0.8633 > 0.8300 > 0.7706)
- All regional override fraction sets sum to 1.0 +/- 1e-6: **PASS**
- national `fractions` block in regional JSON == table4.json: **PASS** (Python equality)
- national `archetype_map` block == table4.json: **PASS**
- Rebuilt modeled_frac == mf_adj (verified: MA large_office 0.8633, PAC 0.7706): **PASS**
- No anchor-fitting: r_factor is pure FINALWT-weighted CBECS climate ratio; absolute level is pre-validated table4; no city anchor consulted

---

_Auto-generated from cbecs_regional_enduse_fractions.py, 2026-06-26 (DD3b ratio-tilt). Data only — no simulation output altered._
