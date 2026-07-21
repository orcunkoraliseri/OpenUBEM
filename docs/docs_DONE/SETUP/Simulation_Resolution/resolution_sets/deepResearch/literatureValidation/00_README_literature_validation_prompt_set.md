# Literature-Validation — Deep-Research Prompt Set (INDEX)

> READ FIRST. This is a **focused follow-on** to the main resolution-mode research set
> (`../00_README_resolution_prompt_set.md`, `../RESULT_01..16`) and the layout-mapping sub-set
> (`../layoutMapping/RESULT_L01..L06`). Those answered *what* zoning each mode should use and *how* to
> build it. This sub-set answers the remaining question the implementation raises: **do OpenUBEM's
> measured cross-mode differences fall inside the ranges the published literature reports for the same
> effects?** Run each prompt in your deep-research tool; save the answer beside it as
> `RESULT_<id>_<slug>.md`. The manager then compares OpenUBEM's T08 sweep numbers against the returned
> envelopes and folds the verdict into the plan.

---

## The exact decision this set must inform

OpenUBEM now exposes a user-selectable `resolution_mode` with four validated modes — **`auto`**
(adaptive default), **`floor`** (one zone per storey), **`fast_zone`** (geomeppy core/perimeter), and
**`building`** (single zone, footprint × num_floors) — plus **`zone`** (detailed DOE layout) which is
deferred (`NotImplementedError`). Because OpenUBEM uses **zero fitted parameters**, its defensibility is
**external agreement**: the only way to say a cross-mode delta is *correct physics* rather than a bug is
to show it lands inside the range independent studies report for the same coarsening. The T08 12-cell
sweep (8,160 buildings, 3 cities, CZ 2A/3B/4A) has produced OpenUBEM's *own* cross-mode deltas; this set
commissions the **published quantitative envelopes** to test them against.

**We are not asking the researcher to re-derive OpenUBEM's numbers — we are asking what the peer-reviewed
UBEM / building-simulation literature says the magnitude and direction of each zoning-resolution effect
should be, with sources**, so the manager can mark each OpenUBEM result **in-envelope** or
**out-of-envelope (investigate)**. Every prompt must surface real, cited ranges, not invented ones.

---

## OpenUBEM's observed cross-mode deltas — the numbers each prompt must find an envelope for

These are what the validation must bracket. All are *building-scale unless noted*; the EUI denominator is
`footprint_area_m2 × num_floors` in every mode. Direction convention: coarser = fewer zones
(`building` < `floor`/`fast_zone` < `zone`).

| Effect (axis) | OpenUBEM observed (T08 / CP4) | Prompt |
|---|---|---|
| Annual site-EUI zoning sensitivity | `building/floor` median 0.86–1.00 per cell (building 0–14 % below floor); largest in tall/dense cells (nyc_centre 0.861) | V01 |
| Heating / cooling resolution effect | expected `zone ≥ floor ≥ building` heating; single-zone core/perimeter cancellation | V02 |
| Peak / equipment-sizing sensitivity | coarse modes expected to mis-size peak substantially; not used for sizing in v1 | V03 |
| Daylighting / lighting over-prediction | coarse modes cannot host perimeter daylighting; D7 (daylighting off) in v1 | V04 |
| District-scale wash-out | zoning effect expected to shrink sharply when aggregated to city scale | V05 |
| Archetype-cohort stratification | effect concentrates in resolution-sensitive cohorts (offices, high-rise residential) vs washes out (warehouse, low-rise) | V06 |

The internal expectations these came from are `../RESULT_08` (conservation/§9 magnitudes),
`../RESULT_09` (LOD accuracy + city-scale wash-out), `../RESULT_11` (validation methodology),
`../RESULT_12` (shading/solar), `../RESULT_13` (daylighting). Cite the *external* literature, not these.

---

## The prompts

| # | File | What it validates |
|---|------|-------------------|
| V01 | `V01_annual_eui_zoning_sensitivity_prompt.md` | Published ranges for how much **annual whole-building EUI** shifts with thermal-zoning resolution (single-zone vs multi-zone vs detailed), at building scale — the master envelope for OpenUBEM's `building/floor` ratio. |
| V02 | `V02_heating_cooling_resolution_effect_prompt.md` | Split by **end use**: how coarsening changes **annual heating** and **annual cooling** specifically (core/perimeter cancellation in a lumped zone), with direction and magnitude. |
| V03 | `V03_peak_equipment_sizing_sensitivity_prompt.md` | How zoning resolution changes **peak demand and equipment/HVAC sizing** — the effect that is largest and why coarse modes must not be used for sizing/peak studies. |
| V04 | `V04_daylighting_lighting_overprediction_prompt.md` | Published magnitude of **lighting-energy over-prediction** when perimeter daylighting controls cannot be hosted (coarse zoning) — and how it behaves in *relative* mode comparison with daylighting off. |
| V05 | `V05_district_scale_washout_prompt.md` | The **aggregation / wash-out** evidence: how much the building-scale zoning error shrinks when summed to district/city scale, and where resolution ranks among EUI drivers. |
| V06 | `V06_archetype_cohort_stratification_prompt.md` | Which **building-type cohorts** are resolution-sensitive vs resolution-insensitive, so validation is reported stratified (offices / high-rise residential / warehouse) rather than city-average. |

> Load-bearing core: **V01 + V05** (the building-scale envelope and its district-scale wash-out — together
> they decide whether OpenUBEM's zoning error matters at the scale it reports). V02–V04 refine by end use;
> V06 sets the reporting stratification that RESULT_11 requires.

---

## Shared facts (all prompts assume these — same engine/geometry as the parent set)

- **Engine / geometry:** EnergyPlus 23.1, one IDF per building, annual 8760-hour run, **geomeppy**
  (`add_block`; native `core/perim` splits the perimeter ring into one zone per exterior wall edge and
  forms the core by inward offset at **4.57 m** / 15 ft depth).
- **Modes under test:** `auto` (default, validated to city EUI within **±9 %** of measured), `floor`
  (one zone/storey), `fast_zone` (core/perimeter), `building` (single zone, area = footprint × num_floors).
  `zone` (detailed DOE layout) is **deferred** — do not build the envelope around it, but published
  single→multi→detailed ladders are welcome as the outer bound.
- **Footprint is REAL and FIXED:** the building's true OSM polygon, never a resized DOE rectangle.
- **Floor-to-floor:** 3.5 m. **EUI denominator:** `footprint_area_m2 × num_floors`, all modes (so a
  cross-mode delta is a *physics* difference, never a normalization artefact — F11/F14 already proven).
- **Daylighting (D7):** OFF in v1 (no perimeter daylighting controls in any mode). This matters for V04:
  report both the *absolute* over-prediction vs metered data **and** what survives in a *relative* mode
  comparison when daylighting is off everywhere.
- **Zero-fitted-parameters:** OpenUBEM tunes nothing; the whole point of this set is external ranges. Any
  "OpenUBEM should target X" must be a **published** range, not a tuned knob.
- **Cities / climate:** Los Angeles (CZ 3B), Austin (CZ 2A), New York (CZ 4A) — cooling-, mixed-, and
  heating-leaning respectively; prefer sources that report climate dependence.

## Seed references (starting points — each prompt must go beyond these)

- **Chen, Hong & Piette (2017/2018)**, *Automatic generation and simulation of urban building energy
  models* (CityBES), *Applied Energy* — city-scale LOD and zoning effects.
- **Dogan & Reinhart (2017)**, *Shoeboxer*, *Energy & Buildings* 140 — zoning abstraction & error vs
  full multi-zone.
- **Cerezo Davila, Reinhart & Bemis (2016/2017)**, *Modeling Boston* — archetype-based UBEM validation
  against measured data, stratified reporting.
- **Johari, Munkhammar, Shadram & Widén (2022/2023)** — UBEM review / bottom-up model resolution and
  accuracy.
- **Faure, Rakovec et al. (2022)** and related **zoning-resolution sensitivity** studies — single vs
  multi-zone annual and peak error.
- **Iseri (2025)** — OpenUBEM methodology / prior validation anchor.
- **DOE/PNNL Commercial Prototype Building Models (STD2022)** — the multi-zone prototypes that define the
  "detailed" end of the ladder.
- Tool documentation where it reports accuracy: **URBANopt/OpenStudio, CityBES, AutoBEM, UMI, CEA**.

## Conventions for every answer (enforced by each prompt)

1. **Lead with the filled tables**; prose after. Empty / "TBD" cells are failures.
2. Every value carries a **named, dated source** — a peer-reviewed UBEM / building-simulation paper
   (author, venue, year), tool documentation, or a standards/prototype document. Blogs/vendor pages last
   resort, labelled.
3. All energy in **SI** (kWh/m²·yr, W/m²); note any IP the source uses + conversion. Ranges as
   **signed % relative to the finer/detailed model** with the sign convention stated.
4. **No fabricated precision.** If a range is your synthesis across sources, say so. If the literature is
   silent, write **"GAP — no published range"** + the closest defensible proxy and its source.
5. **Map onto OpenUBEM's four modes** (single-zone = `building`; per-floor = `floor`; core/perimeter =
   `fast_zone`; detailed = `zone`, deferred) and onto its **archetype roster**
   (`../00_README_resolution_prompt_set.md`).
6. **State the ±9 % tolerance context:** the manager will mark an OpenUBEM delta *in-envelope* if it sits
   inside the published range for that effect; each prompt must therefore return a **numeric range**, not
   just a direction.

---

*OpenUBEM resolution-mode — literature-validation sub-set. Markdown only; binding specs remain
`docs/docs_main/`. 2026-07-01.*
