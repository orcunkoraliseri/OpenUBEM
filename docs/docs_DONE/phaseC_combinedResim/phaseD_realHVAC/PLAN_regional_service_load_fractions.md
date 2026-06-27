# PLAN — Regional CBECS Service-Load Fractions (post-phaseD2, Direction A)

- **Slug:** `regional-service-load-fractions`
- **Date:** 2026-06-26
- **Author:** Manager (Opus session)
- **Binding contract:** this PLAN + the V16 reconstruction method (`docs/docs_VALIDATION/overAll/V16_service_loads_reconstruction.md`) + REPORT §R6-4B scope authority (reporting-layer, **no resim, no IDF/DESIGN change, gates report-only**). Operates on the adopted **phaseD2** baseline (CP-8 ratified 2026-06-26).
- **Predecessor:** `PLAN_phaseD_real_hvac_resim.md` (Phase-6 / CP-8 → "Adopt, then tackle LA/Austin" → user chose Direction A: regional fractions).

## 0. Goal & thesis

The adopted model (phaseD2 + V16) uses a **single national** CBECS fraction table in the reconstruction `E_total = modeled_energy / modeled_frac`. Because `modeled_frac` is space-heating-share-dominated and applied climate-blind, it **over-restores** service loads on heating-heavy NYC (national CBECS NMBE **+12.2%**) and **under-restores** on mild LA/Austin (**−16.8% / −12.6%**). This arc replaces the national fraction table with **per-census-division** fractions derived from the SAME CBECS-2018 public microdata, and re-scores phaseD2 to test whether the climate-correct `modeled_frac` pulls the national NMBE toward zero **without anchor-fitting** (fractions come from EIA end-use disaggregation, never tuned to the city anchors).

**Predicted outcome (D2 prize-sizing, PLAN_phaseD §post-CP-8 scoping):** NYC national NMBE +12→single digits; LA/Austin −17/−13→single digits, on the MEAN only. CV(RMSE)/KS unchanged (structural). City anchors NYC/LA already pass and must NOT regress.

## 1. Hard rules for the executor

1. **Stay in `C:\Users\o_iseri\Desktop\OpenUBEM`.** No `cd` elsewhere.
2. **You execute this plan; you do not rewrite it.** If the spec is ambiguous or a verified fact below is contradicted by the code, **STOP and quote the conflict** — do not invent.
3. **No scope creep.** Reporting-layer only. No resim, no IDF change, no DESIGN/OVERVIEW edit, no `.py` under `docs/`. No cluster trips.
4. **No anchor-fitting (load-bearing integrity rule).** Regional fractions are derived purely from CBECS end-use BTU columns, FINALWT-weighted. No fraction may be hand-tuned toward a city anchor or national gate. The re-score is the TEST, not the fitting target. Any deviation = STOP.
5. **Backward compatibility is mandatory.** The national-fraction path must remain byte-identical to today (existing V16/phaseD callers + tests unchanged). Region-awareness is strictly additive.
6. **Default to no comments.** One short line max where the WHY is non-obvious.
7. **Append a progress-log entry (§8) per completed task.** Cite a verified-fact number or DESIGN line for any decision not literally spelled out here.
8. **Git is handled externally — never commit or offer to.**

## 2. File layout

```
scripts/validation/
  cbecs_regional_enduse_fractions.py     ← NEW: derive per-division fractions from CBECS microdata
  phaseD_regional_reconstruct_rescore.py ← NEW: re-score phaseD2 under national vs regional fractions
openubem/data/service_loads/
  enduse_fractions_regional.json         ← NEW data artifact (national block + fractions_by_region block)
openubem/results/
  service_loads.py                       ← EDIT (backward-compatible region-awareness only)
tests/
  test_regional_service_loads.py         ← NEW
docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/
  RESULT_regional_fraction_derivation.md ← NEW (CP-1 audit data)
  RESULT_phaseD2_regional_fractions.md   ← NEW (CP-2 verdict data)
```

No other files may be created or modified. Do NOT touch `enduse_fractions_table4.json`, `phaseD_reconstruct_rescore.py`, `phaseD_city_rescore.py`, `phaseD_national_cbecs_rescore.py`, `v19_*`, or any committed RESULT/REPORT.

## 3. Dependency decisions (pre-decided — do not re-debate)

- **DD1. Data source = the existing CBECS-2018 public file** `https://www.eia.gov/consumption/commercial/data/2018/xls/cbecs2018_final_public.csv` (the same file `scripts/extract_cbecs_reference.py` already downloads to `%TEMP%/cbecs_2018_raw/`). 6,436 rows, 1,249 cols. Reuse that download path; do not re-invent the fetch.
- **DD2. Region granularity = census division (CENDIV).** Only the 3 city divisions: **CENDIV 2 = middle_atlantic (NYC), 9 = pacific (LA), 7 = west_south_central (Austin)** — matching `_CITY_REGION` in `phaseD_national_cbecs_rescore.py` and the existing `inputs/reports/cbecs_2018_{slug}_eui.csv`. Plus the national block as fallback.
- **DD3. The validated quantity is `modeled_frac`, and it maps UNAMBIGUOUSLY to CBECS major-fuel end-use columns** (recon-verified 2026-06-26). Per (division × group), FINALWT-weighted:
  - `space_heat = Σ(FINALWT·MFHTBTU)/Σ(FINALWT·MFBTU)`
  - `space_cool = …MFCLBTU…`, `lighting = …MFLTBTU…`, `equip_plug = …(MFOFBTU+MFPCBTU)…`
  - `modeled_frac = space_heat + space_cool + lighting + equip_plug`
  - Recon terms (do NOT affect the validated total, only per-end-use columns): `vent_fans=MFVNBTU`, `swh_dhw=MFWTBTU`, `refrig=MFRFBTU`, `cooking_other=(MFCKBTU+MFOTBTU)`, `pumps=0` (CBECS has no separate pumps end-use; folded into MFOTBTU→cooking_other). All 9 normalized to sum 1.0.
- **DD4. PBA→group mapping = reuse `openubem/data/cbecs_pba_map.json` (archetype→PBA) inverted to PBA→V16-group** via the existing `archetype_map` in `enduse_fractions_table4.json`. Office PBA 2 covers both `small_office` and `large_office` groups → both receive the SAME division-level Office fractions (their national modeled_fracs already differ by <0.02, immaterial).
- **DD5. Coverage = commercial archetypes only.** CBECS excludes residential and data centers (`cbecs_pba_map.json` → null). Therefore **multifamily (`mid_rise_apartment`), data centers, and any null-PBA group KEEP the national fraction** (no regional split). Documented limitation: regional multifamily would need RECS, out of scope. This is acceptable — MF already passes its city anchor (NYC +8.8%, LA −9.2%); the lever is needed for Office, which IS CBECS-covered.
- **DD6. Thin-cell fallback.** If a (division × group) has weighted building count `< 25` (manager threshold; ratify at CP-1), that group falls back to the NATIONAL fraction for that division, logged in the derivation memo. Prevents noisy small-sample fractions.
- **DD7. Re-score on phaseD2.** Use the env-gated loader `OPENUBEM_PHASED_SUBDIR=phaseD2` (already wired in `phaseD_city_rescore.py:23`). Compare national vs regional fractions head-to-head on the same phaseD2 gpkgs.
- **DD8. JSON schema (additive).** `enduse_fractions_regional.json` = `{"fractions": {<national, copied verbatim from table4.json>}, "archetype_map": {<copied verbatim>}, "fractions_by_region": {"middle_atlantic": {<group: 9 fracs>}, "pacific": {…}, "west_south_central": {…}}}`. National `fractions` block must equal `enduse_fractions_table4.json` exactly (so the national path is unchanged).

## 4. Source-of-truth verified facts (manager-confirmed 2026-06-26 — cite, don't re-derive)

| # | Fact | Location / proof |
|---|------|------------------|
| F1 | CBECS-2018 public file has per-building MF end-use BTU cols: MFHTBTU, MFCLBTU, MFVNBTU, MFWTBTU, MFLTBTU, MFCKBTU, MFRFBTU, MFOFBTU, MFPCBTU, MFOTBTU (+ EL/NG/DH/FK splits + MFBTU total). | scratchpad recon `cbecs_enduse_recon.py`, 2026-06-26 |
| F2 | Per-division n (clean-ish): MA 851, PAC 828, WSC 768; Office (PBA 2) n = 194 / 189 / 146. Thin PBAs: food sales (6) 6–13, refrig warehouse (11) 3–6, enclosed mall (24) 3–8. | recon output |
| F3 | Reconstruction total = `modeled_energy / modeled_frac`; recon-term SPLITS do not change the total. So only `modeled_frac` (4 modeled fractions) affects the validated EUI. | `openubem/results/service_loads.py:79–92` |
| F4 | `reconstruct_building` maps `archetype_id`→group via `coeffs["archetype_map"]`, reads `coeffs["fractions"][group]`. Region-keying must hook here. | `service_loads.py:71–91` |
| F5 | City→region: NYC→middle_atlantic, LA→pacific, Austin→west_south_central. | `phaseD_national_cbecs_rescore.py` `_CITY_REGION` |
| F6 | Adopted phaseD2 national-fraction national NMBE: NYC +12.24, LA −16.79, Austin −12.64 (all FAIL); city anchors NYC Overall +5.6%, LA −4.8% (PASS), Austin −11.7% (proxy-confounded). | `RESULT_phaseD2_setback_rescore.md` (b),(d) |
| F7 | Existing CBECS extraction (download + CENDIV filter + FINALWT weighting + kBtu/ft²→kWh/m² ×3.15459) is reusable. | `scripts/extract_cbecs_reference.py` |

## 5. Task list

**T01 — Derive per-division end-use fractions.** Write `scripts/validation/cbecs_regional_enduse_fractions.py`: reuse the DD1 download path; for each division ∈ {2,9,7} and each CBECS-covered V16 group, FINALWT-weighted-sum the 10 MF end-use BTU columns over the PBAs mapped to that group (DD4), divide by FINALWT-weighted MFBTU, assemble the 9 V16 fractions per DD3, normalize to 1.0 (±1e-6), apply the DD6 thin-cell fallback to national. Emit `openubem/data/service_loads/enduse_fractions_regional.json` per the DD8 schema (national block copied verbatim from `enduse_fractions_table4.json`; multifamily/data-center/null groups stay national per DD5). *Why:* climate-correct `modeled_frac` is the lever (§0, F3, F6). *How:* drop rows with NaN/zero MFBTU or FINALWT (mirror `extract_cbecs_reference.py` cleaning); weight every sum by FINALWT; guard divide-by-zero. *Test:* every region×group fraction-set sums to 1.0±1e-6; national block byte-equals `table4.json`; thin-cell fallbacks logged; script prints per-(region×group) n and `modeled_frac`.

**T02 — Derivation audit memo.** Write `docs/.../RESULT_regional_fraction_derivation.md` (DATA ONLY): per division×group table of the 9 fractions + `modeled_frac` + implied uplift `1/modeled_frac`, side-by-side with national; an explicit **signature check** = is `space_heat` ordered middle_atlantic > pacific ≈ west_south_central for Office and the other heating-sensitive groups (the mechanism's fingerprint, §0)?; the thin-cell fallback list (which region×group fell back to national and why); per-cell n. No interpretation prose. *Why:* CP-1 manager audit gate before wiring in. *Test:* tables non-empty; signature direction reported per group; fallbacks enumerated. **STOP at CP-1.**

**CP-1 — Manager audit (after T02).** Manager verifies: (a) fractions sum to 1.0 and the national block is unchanged; (b) the cold>mild `space_heat` signature holds for Office (else the lever is mis-derived → STOP); (c) thin-cell threshold (DD6 = 25) and fallbacks are sane; (d) no anchor-fitting crept in. Greenlight T03 or correct. STOP.

**T03 — Region-aware reconstruction (backward-compatible).** Edit `openubem/results/service_loads.py`: `reconstruct_building(row, coeffs, region=None)` — when `region` is given AND `coeffs` has `fractions_by_region` AND that region+group exists, use the regional fractions; else use national `coeffs["fractions"][group]` (unchanged path). `reconstruct_frame(df, coeffs=None, region_col="city", city_to_region=None)` derives per-row region from the city/cell column via the F5 map; rows with no resolvable region use national (existing behavior). `load_coefficients` must also accept the regional JSON and validate every region×group sums to 1.0. *Why:* F4 hook; rule 5 backward-compat. *How:* the national-only call signature `reconstruct_building(row, coeffs)` must behave EXACTLY as before (region defaults None → national). *Test:* see T04 tests; specifically a national-path identity test (regional JSON's national block reproduces the pre-change reconstructed totals to 1e-9 on a fixture).

**T04 — Tests.** `tests/test_regional_service_loads.py`: (1) regional JSON loads, all region×group sum to 1.0; (2) a NYC Office fixture row reconstructs with the middle_atlantic `modeled_frac` (≠ national) → different total; (3) an LA Multifamily row falls back to national (DD5) → total unchanged vs national; (4) a row with unresolvable region → national path, byte-identical to pre-change; (5) thin-cell-fallback group uses national. *Test:* all pass; existing `test_service_loads*`/`test_*reconstruct*` still green.

**T05 — Re-score phaseD2: national vs regional.** Write `scripts/validation/phaseD_regional_reconstruct_rescore.py` (clone the phaseD reconstruct driver pattern; import `reconstruct_frame`, `build_city_table`, `CITY_ANCHORS`, `compute_validation_gates`, `_CITY_REGION`). With `OPENUBEM_PHASED_SUBDIR=phaseD2`, score the 12 cells TWICE: national fractions (current adopted) and regional fractions. Emit city anchors (all segments, 3 cities) + national CBECS gates (NMBE/CV/KS/R² per region) for both. *Why:* DD7, the test of §0. *Test:* 8,160 success rows both runs; reconstructed total ≥ raw both; deltas finite; regional Office `modeled_frac` visibly differs from national.

**T06 — Findings memo.** Write `docs/.../RESULT_phaseD2_regional_fractions.md` (DATA ONLY): (a) national-vs-regional `modeled_frac` per region×group; (b) city-anchor deltas national-vs-regional, 3 cities (flag any NYC/LA regression — must not break the passing anchors); (c) national NMBE/CV/KS/R² national-vs-regional, 3 regions; (d) **predicted-vs-actual** NMBE movement table (predicted from D2: NYC +12→~0, LA −17→~0, Austin −13→~0; actual = measured). No interpretation prose. *Why:* CP-2 verdict input. *Test:* all tables joined; predicted-vs-actual quantified. **STOP at CP-2.**

**CP-2 — Manager verdict (after T06).** Did region-correct fractions move NYC/LA national NMBE toward zero as D2 predicted, **without regressing the NYC/LA city anchors** (which already pass) and **without anchor-fitting**? Quantify Austin (proxy-confounded, indicative only). Adopt regional fractions as the new reporting basis (supersede the national table in the adopted model) or keep national? **STOP — user ratifies any baseline change** (as with CP-8).

## 6. Stop-and-report points

- **CP-1** after T02 — fraction derivation correct + shows the expected climate signature, before any reconstruction wiring.
- **CP-2** after T06 — the verdict: did the predicted NMBE improvement materialize, and at what cost to the passing anchors?

(Two checkpoints by design — the derivation and the re-score are the two places a silent error would compound.)

## 7. Kickoff for Sonnet (manager will send)

> Read `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/PLAN_regional_service_load_fractions.md`. Execute T01–T02, then STOP at CP-1: append progress-log entries under §8, run the T01 tests, and report (incl. the §0 signature check) before continuing. Do not propose alternatives — execute the plan. If a verified fact (§4) is contradicted by the code, STOP and quote the conflict.

## 8. Progress log

_(appended by the executor, one entry per completed task)_

#### T01 — Derive per-division end-use fractions — completed 2026-06-26
- Artifacts: `scripts/validation/cbecs_regional_enduse_fractions.py`, `openubem/data/service_loads/enduse_fractions_regional.json`
- Deviations: None. DD1–DD8 followed exactly. CBECS file reused from %TEMP%. PBA->group inversion via cbecs_pba_map.json + archetype_map per DD4. DD5 applied (mid_rise_apartment kept national). DD6 thin-cell threshold 25 applied: 4 cells fell back to national (middle_atlantic x supermarket n=6, middle_atlantic x full_service_restaurant n=12, pacific x supermarket n=9, west_south_central x supermarket n=13). DD8 national block verified byte-identical to table4.json by Python equality check.
- Test status: All region x group fraction sets sum to 1.0 +/- 1e-6 — PASS. national fractions == table4.json — PASS. archetype_map == table4.json — PASS. Script runs without error.
- Notes: primary_school and secondary_school share PBA 14 (Education) and therefore receive identical regional fractions within each division. pumps column is 0.0 everywhere (no separate CBECS end-use column; per DD3 folded into cooking_other). FLAGGED FOR CP-1: all regional modeled_fracs are below national (0.6084/0.5431/0.5704 vs 0.8300 for large_office) — this means regional reconstruction produces LARGER uplifts for all three cities, opposite to the §0 NMBE correction direction. Data-only report in T02 memo; no inference drawn here.

#### T02 — Derivation audit memo — completed 2026-06-26
- Artifacts: `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/RESULT_regional_fraction_derivation.md`
- Deviations: None. Data-only as specified. §0 signature check included per plan. Thin-cell fallback list enumerated. Per-(region x group) n and modeled_frac side-by-side with national included.
- Test status: Tables non-empty — PASS. Signature direction reported per group — PASS. Fallbacks enumerated — PASS. §5 data anomaly flagged (regional mf < national for all groups/divisions) for manager CP-1 review.
- Notes: The §0 signature (cold MA space_heat > mild PAC/WSC) holds for all office and school groups. The lever mechanism is confirmed in the correct direction. However §5 of memo flags that all regional modeled_fracs are below national — the net reconstruction effect may be opposite to §0 prediction; CP-1 manager audit required before T03.

#### CP-1 — Manager audit + RULING (revised method) — 2026-06-26
**Audit:** sums-to-1 ✓, national block verbatim ✓, no anchor-fitting ✓, signature check ✓ (MA space_heat > PAC/WSC for all office/school groups — the climate lever is real and correctly signed). **But the executor correctly STOPPED on a genuine defect:** a wholesale CBECS-level swap is WRONG. Root cause (manager diagnosis): CBECS allocates ~17% of office energy to "Other" (`MFOTBTU`→cooking_other, non-modeled) and only ~7% to office-equipment, whereas table4 puts 27% in `equip_plug` (modeled) and ~0% in other. OpenUBEM's IDF **already models** that "other" plug energy as `equipment_eui`, so DD3's `MFOTBTU→cooking_other` mapping deflates `modeled_frac` (0.83→~0.55) and **inflates every city's uplift uniformly** — a level artifact orthogonal to climate, which would make NYC's NMBE worse, not better. The *relative* cross-region `modeled_frac` ordering is nonetheless correct (MA 0.608 > WSC 0.570 > PAC 0.543, cold highest).

**RULING (amends DD3 → DD3b, ratio-tilt method).** Use CBECS for the cross-region RELATIVE deviation ONLY, anchored on the validated national table4 level (this cancels the "Other"-allocation artifact, which appears in both numerator and denominator):
- Add a computation of `mf_cb_nat[g]` = CBECS **national** modeled_frac per group (ALL CENDIVs, FINALWT-weighted, same formula/cleaning as the regional pass).
- For each group g and region r that received REGIONAL data (not a thin-cell/residential fallback):
  - `r_factor[r][g] = mf_cb_reg[r][g] / mf_cb_nat[g]`
  - `mf_adj[r][g] = clamp( mf_t4[g] * r_factor[r][g], 0.30, 0.97 )` where `mf_t4[g]` = the national table4 modeled_frac for g.
  - Rebuild that region×group's 9 fractions from the **table4 national** set: scale the 4 modeled fractions (sh,sc,lt,ep) by `mf_adj/mf_t4` (→ they sum to `mf_adj`); scale the 5 non-modeled (vf,pm,sw,rf,co) by `(1-mf_adj)/(1-mf_t4)` (→ they sum to `1-mf_adj`). Sum = 1.0±1e-6. (Only `modeled_frac` is validation-relevant, F3; preserving table4's internal proportions keeps the change minimal and the reporting columns sane.)
- Thin-cell (DD6) and residential/data-center (DD5) groups stay national (equivalently `r_factor=1`, `mf_adj=mf_t4`).
- **This is NOT anchor-fitting:** `r_factor` is a pure CBECS climate ratio; the absolute level comes from the pre-existing validated table4; no city anchor is consulted.

**Required assertion (the proof the fix works):** after rebuild, large_office `mf_adj` must be **MA > 0.83 > PAC** (cold region modeled_frac rises above national → NYC uplift falls → NYC NMBE +12.2 shrinks; mild Pacific falls below → LA uplift rises → LA NMBE −16.8 rises toward 0). If that ordering does NOT hold, STOP — the anchor `mf_cb_nat` is mis-computed.

**Disposition:** T01 re-derivation authorized (DD3b). Re-emit `enduse_fractions_regional.json` + update `RESULT_regional_fraction_derivation.md` (add `mf_cb_nat`, `r_factor`, `mf_adj` vs national columns + the new predicted-direction note). Then proceed T03–T06 per plan. CP-2 unchanged (manager verdict → user ratifies any baseline change).

#### T01 (re-derivation, DD3b) — Ratio-tilt regional fractions — completed 2026-06-26
- Artifacts: `scripts/validation/cbecs_regional_enduse_fractions.py` (rewritten for DD3b), `openubem/data/service_loads/enduse_fractions_regional.json` (re-emitted)
- Deviations: None. Implemented DD3b exactly: mf_cb_nat[g] computed over ALL CENDIVs (FINALWT-weighted, same cleaning); r_factor = mf_cb_reg/mf_cb_nat; mf_adj = clamp(mf_t4*r_factor, 0.30, 0.97); 9 fractions rebuilt from table4 national set (modeled keys × mf_adj/mf_t4, non-modeled × (1-mf_adj)/(1-mf_t4)). Thin-cell (DD6) + residential (DD5) groups left national (no override written → national path applies). One clamp triggered: pacific full_service_restaurant mf_adj_raw 0.2929 → floor 0.30.
- Test status: **GUARD ASSERTION PASS** — large_office mf_adj MA(0.8633) > 0.8300 > PAC(0.7706), WSC=0.8093. mf_cb_nat[large_office]=0.5849. All regional override sets sum to 1.0±1e-6. National `fractions`/`archetype_map` blocks verbatim-equal to table4.json (Python equality). Rebuilt modeled_frac == mf_adj verified.
- Notes: The DD3 level artifact is confirmed and cancelled — mf_cb_nat << mf_t4 for most groups (e.g. office 0.585 vs 0.83), but cancels in r_factor. Cold-MA-highest mf_adj signature holds for every group with regional data; PAC consistently lowest mf_adj (highest uplift), WSC between.

#### T02 (update, DD3b) — Derivation audit memo — completed 2026-06-26
- Artifacts: `docs/.../RESULT_regional_fraction_derivation.md` (rewritten for DD3b)
- Deviations: None. Data-only. Added §0 GUARD result, §2 mf_cb_nat table, §3 r_factor/mf_adj-vs-national columns, §4 signature check, §5 full rebuilt fractions, predicted-direction note.
- Test status: GUARD PASS documented; all sums 1.0; national verbatim. Tables non-empty.
- Notes: Supersedes the original DD3 memo content.

#### T03 — Region-aware reconstruction (backward-compatible) — completed 2026-06-26
- Artifacts: `openubem/results/service_loads.py` (edited)
- Deviations: None. `reconstruct_building(row, coeffs, region=None)` — regional fracs used only when region given AND coeffs has fractions_by_region AND region+group exists; else national path unchanged (basis "table4_fraction_split"). Regional path sets basis "regional_fraction_split". `reconstruct_frame(df, coeffs=None, region_col="city", city_to_region=None)` derives per-row region via F5 map (_CITY_TO_REGION: nyc→middle_atlantic, la→pacific, austin→west_south_central); unresolvable/missing region → national. `load_coefficients` validates every region×group sums to 1.0±1e-3 when fractions_by_region present.
- Test status: existing tests/test_service_loads.py 42/42 PASS (backward-compat byte-identical confirmed). v19_rescore 5/5 PASS.
- Notes: When coeffs lacks a regional block, has_regional=False → all rows national → byte-identical to pre-change behaviour (proven by test_frame_no_regional_block_is_national + the 42 unchanged tests).

#### T04 — Tests — completed 2026-06-26
- Artifacts: `tests/test_regional_service_loads.py` (NEW, 18 tests)
- Deviations: None. Covers: (1) regional JSON loads + all region×group sum 1.0 + national verbatim; (2) NYC Office uses MA mf_adj 0.8633 ≠ national → lower total (MA mf>national → lower uplift); (3) LA Multifamily falls back to national (DD5) → total byte-identical; (4) unresolvable region (chicago) + missing city col → national byte-identical, and regional JSON's national block reproduces table4 totals to 1e-12; (5) thin-cell supermarket uses national; (6) end-to-end reconstruct_frame region derivation.
- Test status: 18/18 PASS; combined with existing service_loads 60/60 PASS. v19_rescore 5/5 PASS.
- Notes: national-path identity test (test_national_coeffs_identity_with_table4) confirms rule-5 backward compat to 1e-12.

#### T05 — Re-score phaseD2: national vs regional — completed 2026-06-26
- Artifacts: `scripts/validation/phaseD_regional_reconstruct_rescore.py` (NEW)
- Deviations: None. OPENUBEM_PHASED_SUBDIR=phaseD2; 12 cells, 8160 rows, 8160 success. Reconstructs twice (national coeffs → 0 regional rows; regional coeffs → 5286 regional-basis rows). recon≥raw violations=0 both; all finite. Emits city anchors (all + excl-food) and national CBECS gates per region for both.
- Test status: run clean. large_office modeled_frac distinct (nat 0.83, MA 0.8633, PAC 0.7706, WSC 0.8093) confirmed in-run.
- Notes: HEADLINE — national NMBE flips FAIL→PASS all 3 regions: NYC +12.24→+7.70, LA −16.79→−6.10, Austin −12.64→−9.91. CV/KS still fail (structural). City anchors: NYC/LA Overall + NYC Office improved/held; LA Office +4.5→+12.3 and LA Warehouse +9.8→+31.2 (n=38) degraded — flagged in T06 §B.

#### T06 — Findings memo — completed 2026-06-26
- Artifacts: `docs/.../RESULT_phaseD2_regional_fractions.md` (NEW)
- Deviations: None. Data-only. §A modeled_frac nat-vs-reg; §B city-anchor deltas nat-vs-reg with NYC/LA regression flags; §C national gates nat-vs-reg (NMBE/CV/KS/R²); §D predicted-vs-actual NMBE table (all 3 match predicted direction into passing band).
- Test status: all tables joined; predicted-vs-actual quantified.
- Notes: STOP at CP-2. Manager writes verdict; user ratifies any baseline change. Open trade-off for CP-2: national-NMBE win (all pass) vs LA Office/Warehouse city-anchor cost.

#### CP-2 — Manager verdict on regional-fraction adoption — 2026-06-26
**Audit:** method sound (DD3b ratio-tilt, guard passed MA 0.8633>0.83>PAC 0.7706); no anchor-fitting (r_factor pure CBECS, level = pre-validated table4); backward-compatible (national path byte-identical to 1e-12; 60/60 service-loads + 18/18 new + v19 suites green); re-score clean (8,160 success, recon≥raw 0 violations). Numbers trusted.

**What regional fractions bought (the §0 target):** national CBECS NMBE flips **FAIL→PASS in all three regions** — NYC +12.24→**+7.70**, LA −16.79→**−6.10**, Austin −12.64→**−9.91** — in the predicted direction, principled, unfitted. The model has never cleared all three national NMBE gates before. NYC improved across the board (Office +23.3→+18.0, Overall +5.6→+2.1), Austin improved (Office −12.6→−9.3, Overall −11.7→−8.6, both now single-digit), LA Overall held (−4.8→−3.7).

**What it cost:** two LA sub-segments degraded — **LA Office +4.5→+12.3** (the same PAC uplift that fixed LA's national under-prediction pushes the office anchor up) and **LA Warehouse +9.8→+31.2** (n=38, CBECS-Pacific "Other"-heavy, small). CV(RMSE)/KS unchanged (structural — regional fractions are a mean lever only, as predicted).

**Integrity nuance (the crux):** the metric that improved (national CBECS NMBE) is the **composition-confounded** one (model is office/MF-heavy vs all-building-types CBECS — established at the post-CP-8 scoping); the metric that degraded most (LA Office) has the **best independent ground truth** (EBEWE measured). So this trades a small loss on a trustworthy anchor for a win on a confounded gate. Mitigating: LA *Overall* (the headline EBEWE metric, n=2317) HELD in band; the LA Office overshoot (+12.3%) is still within normal archetype-UBEM tolerance; the worst regression (Warehouse) is n=38 / 1.6% of the LA fleet.

**Manager recommendation → ADOPT regional fractions, with disclosure.** Net it is a principled, unfitted improvement: 3 national NMBE gates cleared + NYC/Austin/LA-Overall better-or-held, at a localized, documentable cost (LA Office moderate, LA Warehouse small-n). The user chose Direction A to improve the national scoreboard; A delivered it cleanly. Caveats to carry into the report: (1) the national-NMBE pass does NOT change the structural CV/KS story; (2) LA Office/Warehouse city-anchor regressions disclosed; (3) regional split is commercial-only (MF/data-centers national; RECS-regional MF is future work). **A defensible alternative is KEEP national** (don't trade the trustworthy LA Office anchor for the confounded national gate) — genuinely reasonable given the scoping found the national gates reference-side. **STOP — user ratifies (baseline change).**

**RATIFIED by user 2026-06-26 — "Adopt regional."**
- **Regional CBECS service-load fractions (`enduse_fractions_regional.json`, DD3b ratio-tilt) are the adopted reporting basis** for the phaseD2 model, superseding the single national table in the reconstruction. The adopted whole model is now: **phaseD2 (setback fix) metered PTAC HVAC + V16 reconstruction on REGIONAL fractions.**
- **Reproducibility = `scripts/validation/phaseD_regional_reconstruct_rescore.py` (regional pass)** on phaseD2; `enduse_fractions_table4.json` is RETAINED as the `load_coefficients()` default (backward-compat) — adoption is a documented basis pointer, NOT a default-flip (mirrors phaseD2 superseding phaseD without deleting it).
- **Headline (adopted): national CBECS NMBE passes all 3 regions** (NYC +7.7 / LA −6.1 / Austin −9.9); city Overall NYC +2.1 / LA −3.7 / Austin −8.6.
- **Mandatory disclosures for the report:** (1) LA Office +4.5→+12.3% and LA Warehouse +9.8→+31.2% (n=38) city-anchor regressions; (2) CV(RMSE)/KS still fail (structural — regional fractions are a mean lever only); (3) regional split is commercial-only (MF/data-centers keep national; RECS-regional MF = future work); (4) Austin remains a CBECS-derived proxy (indicative).
- **Next: regenerate `REPORT_phaseD_final.md`** to the adopted phaseD2 + regional-fraction model (city anchors + national gates + the resolved limitations #1 setback & climate-blind-fractions + the new disclosed costs). This consolidates CP-8 (phaseD2) and CP-2 (regional) into the final baseline report.

#### REPORT regeneration — final baseline report updated — completed 2026-06-26 (manager)
- Artifact: `docs/docs_ACTIVE/phaseC_combinedResim/phaseD_realHVAC/REPORT_phaseD_final.md` (rewritten; supersedes the 2026-06-25 edition).
- Content: adopted model = phaseD2 metered PTAC + V16 reconstruction on regional CBECS fractions, zero fitted parameters. Headline city-Overall ±9% all 3 cities (NYC +2.1 / LA −3.7 / Austin −8.6); national CBECS NMBE + R² passing all 3 regions (NYC +7.7 / LA −6.1 / Austin −9.9). Limitations #1 (NYC office over-heat → setback) + climate-blind fractions (→ regional) marked RESOLVED; LA Office (+12.3%) / LA Warehouse (+31%, n=38) regional-fraction costs + structural CV/KS + Austin-proxy + commercial-only-split disclosed.
- Deviations: none. Manager-authored synthesis (validation analysis); numbers transcribed verbatim from RESULT_phaseD2_setback_rescore.md + RESULT_phaseD2_regional_fractions.md; no resim, no code/DESIGN change.
- **Phase-D arc COMPLETE.** Adopted baseline locked; no further resim/calibration indicated (future = RECS-regional MF fractions, reporting-layer, new data).
