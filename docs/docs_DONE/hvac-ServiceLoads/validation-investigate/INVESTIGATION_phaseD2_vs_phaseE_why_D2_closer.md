# INVESTIGATION — Why was Phase-D2 closer to measured than Phase-E?

- **Date:** 2026-06-28
- **Author:** Manager (Opus session)
- **Question (user):** Phase-E shifted the city averages *away* from measured vs Phase-D2. If the external validation anchors (NYC LL84 / LA EBEWE / Austin CBECS-WSC) are correct, *why* was Phase-D2 much closer to measured than Phase-E?
- **Scope:** Diagnostic only. No re-simulation, no code change, no baseline change. Reads the committed `phaseD2/` and `phaseE/` result trees.
- **Inputs:** `docs/docs_VALIDATION/validations/overAll/results/{phaseD2,phaseE}/<cell>/05_results.csv` (12 cells each, 8,160 buildings, osm_id-matched 8,160/8,160); DOE prototype reference `docs/docs_VALIDATION/step1/overAll/results/roundtrip_report.csv`.
- **Reference report under review:** `../REPORT_phaseE_final.md`

---

## 0. TL;DR

The Phase-E report explains the regression as: *"Phase-E removes the V16 reconstruction overlay, and the overlay was carrying the unmodeled 'Other' service-load category (~42% of the gap); the level drop quantifies how much reconstruction was adding."* (REPORT_phaseE_final §3b, §3e, §7, §10-pt-7.)

**That explanation is wrong on the mechanism.** A per-building decomposition of the exact same 8,160 buildings shows:

1. **The regression is almost entirely a HEATING reduction, not the removal of a service-load overlay.** Cooling, lighting, and equipment are byte-identical between D2 and E. Office heating roughly **halved** (NYC SmallOffice 132 → 55 kWh/m²) the moment archetypes switched off blanket PTAC onto their real HVAC families (PSZ / VAV / PVAV).
2. **The two service-load layers are nearly equal.** D2's reconstruction overlay added ~+41 kWh/m² (NYC Overall); Phase-E's physical service loads (fans+pumps+DHW+cooking+refrig) add ~+37. The overlay did **not** carry a large hidden level that Phase-E dropped. The layers cancel to within ~4 kWh/m².
3. **Phase-D2 was closer to measured because its PTAC heating was grossly over-predicted** — ~2× Phase-E and up to ~20× the DOE prototype the model is built on. That heating over-prediction, stacked on the reconstruction overlay, summed to ≈ the measured total. Phase-E corrected most of the heating over-prediction, and the total fell below measured.

So the answer to the user's question: **D2 matched measured by a compensating error — a large PTAC heating over-prediction that happened to fill the space later attributed to "Other." Phase-E removed most of that error. D2 was *closer*, not *more correct*; it was never validated at the end-use level, only at the total.**

**This does not overturn the decision to adopt Phase-E** — Phase-E's heating is far closer to the DOE reference and its end-uses are physical. But the report's *diagnosis* must be corrected, and one real caveat surfaces: Phase-E heating is still ~3–9× the prototype, so the model partly masks the true structural gap with still-elevated heating (§6).

---

## 1. Method

Both result trees carry per-end-use site-EUI columns. Critically, the two `total_eui_kwh_m2` columns mean **different things**, and the report's comparison mixes them:

| Quantity | Definition | Where it lives |
|---|---|---|
| **Phase-D2 raw core** | `total_eui_kwh_m2` in `phaseD2/` = heating + cooling + lighting + equipment **only** (fans excluded, no DHW/cooking/refrig/pumps columns) | the committed phaseD2 files — *never read by the rescore* |
| **Phase-D2 adopted** | raw core **÷ modeled_frac** (V16 regional reconstruction) — grosses up to include DHW/cooking/refrig/fans/pumps **and the implicit "Other"** | hard-coded in `phaseE_rescore.py` as `measured × multiplier`, transcribed from `REPORT_phaseD_final` |
| **Phase-E total** | `total_eui_kwh_m2` in `phaseE/` = h+c+l+e + fans+pumps+DHW+cooking+refrig (no "Other", no gross-up) | the committed phaseE files |

The report compares **Phase-D2 adopted (reconstructed)** vs **Phase-E total (physical)**. That is a fair *model-output* comparison, but it never decomposes where the difference comes from, and it leaves the **Phase-D2 raw simulation core unused** — even though it is sitting in the files. This investigation recovers the raw core and matches every building 1:1 (osm_id × cell) so population changes cannot confound the comparison (8,160/8,160 matched, success in both).

Decomposition definitions used below:
- **Core** = heating + cooling + lighting + equipment (identical definition in both phases).
- **D2 service** = the reconstruction overlay = `D2 adopted − D2 raw core`.
- **E service** = fans + pumps + DHW + cooking + refrigeration (the physical replacement).

---

## 2. Finding 1 — The regression is heating, and only heating

osm_id-matched medians over the 8,160 buildings present in both runs. Cooling/lighting/equipment are unchanged to the decimal; **the entire core movement is heating.**

**NYC Office (n=2,570) — the cleanest single-segment case:**

| End-use | Phase-D2 | Phase-E | Δ (E − D2) |
|---|---|---|---|
| Heating | 122.0 | 54.7 | **−67.4** |
| Cooling | 13.9 | 12.9 | −1.0 |
| Lighting | 26.5 | 26.5 | 0.0 |
| Equipment | 27.8 | 27.8 | 0.0 |
| **Core (h+c+l+e)** | **191.4** | **123.6** | **−67.8** |
| Service layer (D2 overlay / E physical) | 25.6 | 21.7 | −3.9 |
| **Reported total** | **217.0** | **147.0** | **−70.0** |
| vs measured (183.9) | **+18.0%** | **−20.1%** | |

**67.4 of the 70-point office regression is heating.** The service layer (overlay vs physical) contributes only −3.9. The report attributes the regression to the service layer; the data attribute it to heating by a factor of ~17:1.

**Heating change tracks the HVAC system swap** — segments that kept a PTAC-family system barely moved; segments that switched to central/packaged systems halved:

| Segment | HVAC change D2 → E | Heating D2 → E | Δ heating |
|---|---|---|---|
| NYC SmallOffice | PTAC → PSZ-AC (gas furnace) | 132.1 → 54.7 | −59% |
| NYC MediumOffice | PTAC → PSZ / PVAV | 80.8 → 55.7 | −31% |
| NYC LargeOffice | PTAC → central VAV + HW boiler | 69.0 → 51.2 | −26% |
| NYC Multifamily | PTAC → PTAC/PTHP/WLHP (kept family) | 118.1 → 103.5 | **−12%** |
| Austin Office | PTAC → PSZ | 36.1 → 14.9 | −59% |
| LA Office | PTAC → PSZ | 22.2 → 10.7 | −52% |

This is not a random bug. It is a **systematic consequence of replacing the blanket-PTAC abstraction with archetype-appropriate HVAC.** Even the simplest swap (SmallOffice PTAC → PSZ-AC, both gas-fired single-zone) cut heating ~60%.

---

## 3. Finding 2 — The service-load layers are nearly equal (the report's stated mechanism fails)

City Overall medians (excl. OpenUBEMUnknown):

| City | Measured | D2 raw core | **D2 service (overlay)** | **E service (physical)** | E core | E total | D2 adopted | D2 Δ% | E Δ% |
|---|---|---|---|---|---|---|---|---|---|
| NYC | 219.2 | 182.9 | **+40.9** | **+37.0** | 131.8 | 165.7 | 223.8 | +2.1% | −24.4% |
| LA | 113.6 | 76.1 | **+33.3** | **+39.2** | 69.1 | 107.2 | 109.4 | −3.7% | −5.6% |
| Austin | 162.0 | 120.6 | **+27.5** | **+16.3** | 102.5 | 120.4 | 148.1 | −8.6% | −25.7% |

The reconstruction overlay (D2 service) and the physical service loads (E service) are the **same order of magnitude** — and for LA, Phase-E's physical service loads are actually *larger* than the overlay. The report's claim that "the overlay was carrying the 'Other' level and Phase-E dropped it" is not supported: there is no large overlay surplus to drop. The overlay and the physical loads roughly cancel.

What does **not** cancel is the core:

| City | D2 raw core | E core | Core Δ | …of which heating |
|---|---|---|---|---|
| NYC | 182.9 | 131.8 | −51.1 | ≈ all (cool/light/equip flat) |
| LA | 76.1 | 69.1 | −7.0 | ≈ all |
| Austin | 120.6 | 102.5 | −18.1 | ≈ all |

This also explains the city-by-city pattern the report noted but did not explain (§3b: *"LA Overall delta is nearly unchanged"*):

- **NYC regresses hardest** — office-heavy, offices switched to PSZ/VAV, big heating cut.
- **Austin regresses** — office-heavy + low physical DHW (few apartments), so heating cut **and** a smaller service layer than its overlay.
- **LA barely moves (−1.9 pp)** — apartment-dominated; apartments kept the PTAC-family system (small heating change) and carry a large physical DHW load that matches the overlay. There is no central-HVAC heating cut to speak of, so nothing regresses.

---

## 4. Finding 3 — DOE-prototype benchmark: Phase-E does NOT under-heat

If Phase-E's lower total were caused by *too little heating*, Phase-E heating should fall below the DOE prototypes the archetypes are built from. It does the opposite. Reference = `roundtrip_report.csv`, ASHRAE 90.1-**2022** prototypes in **Buffalo** (climate zone 5A/6A — **colder** than NYC's 4A, so if anything these should heat *more* than NYC):

| Archetype | DOE prototype heating (Buffalo, colder) | Phase-D2 NYC heating | Phase-E NYC heating |
|---|---|---|---|
| SmallOffice | **6.0** | 132.1 (**~22×** proto) | 54.7 (~9× proto) |
| MediumOffice | **23.1** | 80.8 (~3.5×) | 55.7 (~2.4×) |
| LargeOffice | **18.8** | 69.0 (~3.7×) | 51.2 (~2.7×) |

Reading:
- **Phase-D2's PTAC heating was absurd** — up to 22× the reference prototype for the dominant SmallOffice. This is the over-prediction that made D2's total land near measured.
- **Phase-E heating is far closer to the reference but still elevated** (~2.4–9×). It is **above** the prototype, never below. **A model that over-heats relative to its own reference cannot be under-predicting the total because of heating.** Hypothesis "Phase-E's central HVAC under-heats / mis-meters heating" is **rejected.**
- Corroborating that heating is metered correctly: LargeOffice (central VAV + HW boiler) reports heating 51.2 with pumps 8.7 kWh/m² (223/232 buildings pump>0). If the boiler-gas meter were dropped, central-plant heating would read ≈0; it does not.

**Therefore the residual −24% gap is non-heating** — it is the genuinely unmodeled "Other"/process category (elevators, IT/process loads, miscellaneous plug loads) that neither the DOE prototypes nor Phase-E specify. This is the R6-4B residual, and on *this* point the report's conclusion is right even though its mechanism is wrong: Phase-E NYC office = heat 55 + cool 13 + light 27 + equip 28 + fans 16 + DHW 5 ≈ 147; measured 184; the ~37 kWh/m² shortfall is plausibly all "Other" (CBECS office misc/computing/other is routinely 30–40 kWh/m²).

---

## 5. Finding 4 — Pumps/fans verified (no meter regression)

Because city-median pumps = 0.0 looked suspicious, it was checked directly: **695/8,160** buildings have pumps>0 (max 16.1), and **8,154/8,160** have fans>0 (mean 16.6). LargeOffice pumps median = 8.7–11.1 across cities. The city-wide zero is correct — the median building is a SmallOffice or apartment with no water loop. The Phase-E end-use meters are intact; this is not a parser regression.

---

## 6. The honest answer, and a caveat the report omits

**Why was Phase-D2 closer to measured?** Because Phase-D2's total was the sum of two upward biases that the measured anchor absorbed:

1. a **PTAC heating over-prediction** of roughly +70–120 kWh/m² per office vs the DOE reference, plus
2. a **reconstruction overlay** that grossed up via `÷ modeled_frac` and implicitly carried "Other".

Phase-E corrected (1) by giving each archetype its real HVAC — heating fell by about the size of the over-prediction — and replaced (2) with comparable physical service loads that do **not** include "Other". The measured anchors are correct; D2's agreement with them was a **compensating-error coincidence at the total level**, never confirmed end-use by end-use. Phase-E trades that coincidence for a model whose individual end-uses are defensible, at the cost of a now-visible structural under-prediction.

**Caveat the report should state (it currently does not):** Phase-E heating is still ~2.4–9× the DOE prototype. Some elevation is legitimate — OpenUBEM applies DOE *internal loads/schedules* onto *OSM geometry* with a leakier-than-2022-code envelope, and the LL84 stock is old, so real heating is well above a new-construction prototype. But it means **part of Phase-E's reported total is itself still-elevated heating that partly masks the true "Other" gap.** If Phase-E heating were at prototype levels, NYC office total would be ~110, i.e. −40% vs measured, not −20%. The −24% city gap should therefore be read as a *lower bound* on the structural service-load deficit, not its full size. This is an open question, not a defect to fix now.

---

## 7. Implications for `REPORT_phaseE_final.md`

The **disposition (adopt Phase-E) stands.** The **diagnosis needs correction.** Specifically:

| Report location | Current claim | Correction |
|---|---|---|
| §1, §3e, §7 "Red bar", §10-pt-7 | The regression "quantifies how much the reconstruction was carrying" (the "Other" overlay) | The regression is ~90% (NYC) / ~65% (Austin) a **PTAC→archetype-HVAC heating correction**. The service-load layers (overlay vs physical) are near-equal and roughly cancel. |
| §3c, §7 reason 1 | R² 0.71→0.90 implies "the model is physically correct" | R² measures **shape/rank**, not level. Phase-E ranks buildings well **and** under-predicts level. Both are true simultaneously; the R² gain does not validate the level. |
| §3b | "LA Overall delta nearly unchanged… as expected" | Now explained: LA is apartment-dominated and kept the PTAC-family system, so there is no central-HVAC heating cut and nothing to regress. |
| (missing) | — | Add the caveat from §6: Phase-E heating is still elevated vs the DOE prototype, so −24% under-states the true structural "Other" gap. |

---

## 8. Recommendation

1. **Keep Phase-E as the physical baseline.** Its end-use structure (real fans/pumps/DHW, heating ~3× rather than ~20× the reference) is more defensible than Phase-D2's compensating-error match. D2 was closer to the measured *total* but was not closer to the *truth*.
2. **Correct the report's mechanism** per §7 (a focused edit pass, not a re-score). The numbers in the report are fine; the causal story is not.
3. **Do not "fix" the gap by fitting.** The −24% is the R6-4B "Other" residual, confirmed non-heating here. Closing it requires either modelling process/elevator/misc loads (no DOE spec → fitting) or accepting it. The zero-fitted-parameters rule says accept + document.
4. **Optional future diagnostic (not blocking):** quantify why Phase-E heating sits ~3–9× the DOE prototype — isolate the OSM-envelope/infiltration contribution. This is the same upward direction across Phase-C/D/E and is the lever that makes heating "high enough" to partly hide the Other gap. It is also the most likely place a *real* future calibration could live, and it bears on the LA hot-bias (Limitation #2).

---

## Appendix A — reproduction

```
.venv/Scripts/python.exe scripts/validation/phaseE_gap_investigation.py
```
Read-only diagnostic: osm_id-matched decomposition of all 8,160 buildings (Findings 1–4) + DOE-prototype heating benchmark. Reference heating from `docs/docs_VALIDATION/step1/overAll/results/roundtrip_report.csv`, columns `openuben_archetype`, `ref_heat` (DOE prototype, ASHRAE 90.1-2022, Buffalo).

## Appendix B — key numbers (osm_id-matched, 8,160/8,160, medians, kWh/m²/yr)

| Metric | NYC | LA | Austin |
|---|---|---|---|
| Measured anchor (Overall) | 219.2 | 113.6 | 162.0 |
| Phase-D2 raw core (h+c+l+e) | 182.9 | 76.1 | 120.6 |
| Phase-D2 adopted (reconstructed) | 223.8 (+2.1%) | 109.4 (−3.7%) | 148.1 (−8.6%) |
| Phase-E core (h+c+l+e) | 131.8 | 69.1 | 102.5 |
| Phase-E physical service loads | 37.0 | 39.2 | 16.3 |
| Phase-E total | 165.7 (−24.4%) | 107.2 (−5.6%) | 120.4 (−25.7%) |
| Core movement D2→E (≈ all heating) | −51.1 | −7.0 | −18.1 |
| D2 overlay vs E physical service | +40.9 vs +37.0 | +33.3 vs +39.2 | +27.5 vs +16.3 |
