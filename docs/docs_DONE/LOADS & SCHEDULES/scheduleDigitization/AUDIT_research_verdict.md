# AUDIT — Deep-research schedule reports (RESULT_1–5) — manager verdict

**Date:** 2026-06-17 • **Auditor:** Manager (Opus) • **Inputs:** `deepResearch/RESULT_1..5_*.md`, saved `sources/*.idf`, local `docs/validations/Level 2 DOE round-trip/00.BaselineBuildings_NUs/*.idf`, the live STD2013 apartment/office IDFs.

## Verdict: ACCEPT the research as a verified reference + cross-check. PIVOT the digitization method to **direct IDF parse** (do not transcribe the markdown by hand).

---

## 1. What I verified against ground truth

- **RESULT_2 (apartment) is byte-for-byte faithful.** I extracted `ltg_sch_apartment_hardwired` from the saved `sources/MidriseApartment_90.1-2013.idf`: `0.01132, 0.03395, 0.07355, 0.07921, …, 0.18106 (peak), 0.12448, 0.0679, 0.02829`. Matches RESULT_2 exactly. The saved `sources/*.idf` artifacts are real (anti-fabrication gate passed for RESULT_2/3).
- **Decisive modeling catch — residential lighting is diversity-baked.** The apartment lighting schedule **peaks at 0.181, not 1.0**, and is paired in the IDF with the **full installed LPD** (`Watts/Area = 7.64237` hardwired + `0.96875` plug-in). So the DOE model's real apartment lighting energy ≈ **4.5 kWh/m²·yr**, versus OpenUBEM's current **43.9** — a ~**10× overcount** caused entirely by OpenUBEM's synthetic schedule (peak ~0.9). Equipment is fine: `EQP_APT_SCH` peaks at 1.0, ~38 kWh/m², ≈ unchanged.
  - **Implementation rule (load-bearing):** use the DOE residential lighting schedule **verbatim (peak 0.181); do NOT normalize to peak 1.0.** Keep OpenUBEM's LPD (7.53 ≈ DOE 7.64). Normalizing would re-inflate it 5×.
- **The low-peak pattern is residential-specific.** The DOE office lighting (`ltg_sch_office`, local STD2022) peaks at **1.0** with diversity decimals (0.1358…0.6111…1.0). Confirms per-group digitization is the right model: each type carries its own genuine shape.

## 2. Issues found

- **Sourcing inconsistency / unsaved artifacts (RESULT_4 & 5).** RESULT_2/3 used **energycodes.gov DOE prototype STD2013** IDFs (saved to `sources/`). RESULT_4 (office/retail/warehouse/supermarket) used the **`pnnl/tesp`** repo — a *different lineage* with **round-number** office schedules (peak 0.90), and **did not save** its source artifacts. RESULT_5 (school/hospital/outpatient) likewise was not manager-line-checked and its sources are not saved. Mixed lineages → inconsistent schedule conventions; the TESP office (round 0.90) ≠ the energycodes office (diversity-decimal, peak 1.0).
- **Edition/object-name drift.** The local round-trip set is **STD2022**; the saved `sources/` are **STD2013**. Object names differ across editions (e.g., the STD2022 apartment IDF does not use `ltg_sch_apartment_hardwired`). Must pin ONE edition.
- **Multi-zone schedules.** DOE prototypes define per-zone schedules (restaurant dining vs kitchen; warehouse office vs storage; school classroom vs gym). OpenUBEM stores **one schedule per archetype per family** → need a documented collapse rule.

## 3. Rulings (fold into PLAN §4/§5)

1. **Single pinned source = energycodes.gov DOE Commercial Prototype IDFs, edition 90.1-2013.** Rationale: the saved `sources/` + the *verified* apartment finding + RESULT_2/3 are all STD2013; keeps one lineage and avoids the STD2022 object-name drift. (Schedules are largely edition-stable; pinning removes surprises.)
2. **Method = parse schedules DIRECTLY from the STD2013 IDFs**, not transcribe the RESULT markdown. Executor fetches the 7 missing STD2013 prototype IDFs (office, retail, warehouse, primary-school, hospital, outpatient, supermarket) to `sources/`, reuses the 3 already saved (apartment, hotel, restaurant). The RESULT_1–5 tables become a **cross-check**: any parsed value deviating >2% from the corresponding RESULT value is flagged in the report. This is a *stronger* anti-fabrication posture than hand-transcription.
3. **Use schedules verbatim — never re-normalize peaks.** Especially residential lighting (peak 0.181). Pair with existing OpenUBEM LPD/EPD scalars (do not touch the loads table).
4. **Multi-zone collapse = dominant-floor-area zone per family:** apartment→dwelling unit; hotel→guest room; restaurant→dining for occupancy+lighting, `BLDG_EQUIP_SCH` (electric plug) for equipment (kitchen gas cooking is out of scope — OpenUBEM `equipment_w_m2` is electric plug); office/retail/warehouse/supermarket→`BLDG_*` whole-building objects; school→classroom; hospital→patient-room/standard (`BLDG_OCC_SCH`); outpatient→exam/office. Document the exact object name used per group in `PROVENANCE.md`.
5. **DataCenter** stays 24/7-constant (no DOE prototype) — documented exception, unchanged.
6. **Supermarket regrouping (open, low-priority):** RESULT_4 confirms supermarket plug-equipment EFLH is only ~2.5% above retail (refrigeration is modeled by separate `Refrigeration:*` objects, NOT the plug schedule). So lumping SuperMarket with Retail for *schedules* is acceptable; its refrigeration is already handled in OpenUBEM's reconstruction layer. No regroup needed for this fix.

## 4. Expected impact (verify at EFLH + resim checkpoints; do not tune)

- MidriseApartment lighting EUI **43.9 → ~4.5 kWh/m²**. Combined with the zoning fix, Midrise 4-end-use total drops from the pilot's ~189 toward ~150 (still above measured ~116, but the residential-lighting artifact — the single biggest distortion — is removed). Office/retail change modestly. This is a large, correct move; some types may land low — that is the expected "more correct, then re-anchor" outcome.
</content>
</invoke>
