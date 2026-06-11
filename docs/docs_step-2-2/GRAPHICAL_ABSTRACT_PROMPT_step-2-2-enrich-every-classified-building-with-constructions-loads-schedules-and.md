# Graphical Abstract Prompt — Step 2.2: Climate-Located Buildings → Constructions, Loads, Schedules, and Imputation

> **Slug:** `step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and` &nbsp;•&nbsp; **Companion to:** `DESIGN_step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and.md` &nbsp;•&nbsp; **Generated:** `2026-06-09` &nbsp;•&nbsp; **Revised:** `2026-06-10` (IECC table marked inert Phase-2 hook per OQ-6 resolution; downstream arrow added)

---

## Concept

The figure must communicate the *standards-to-columns* enrichment that completes the simulation-ready table: each building's three keys (archetype, climate zone, vintage) pull rows out of stacked standards tables, an imputation funnel catches everything the tables cannot answer, and the table widens from 29 to 57 columns alongside a deck of 180 schedule cards. The single most important takeaway in 5 seconds: **every physical parameter EnergyPlus will ever see — envelope, loads, thermostats, schedules — is looked up from open standards by (archetype × climate zone × vintage), and whatever the tables can't answer is filled by an explicit, seeded statistical tier, never silently defaulted.** The visual story is "three keys open three tables; one funnel catches the rest; the table is now full."

## Suggested Structure

3-panel left-to-right horizontal flowchart, with a small "imputation funnel" inset under Panel 2 (the KDE/PDE tier with the `OpenUBEMUnknown` route) and a schedule-card strip under Panel 3 (the 30 × 6 library).

Reasoning: the step is three deterministic lookups converging on one column-append, with the imputation tier as the explicit exception path — so a main lookup row with one funnel inset reads truthfully; the schedule library is a parallel deliverable and earns the only strip.

## Key Elements to Show

- **Panel 1 — Keyed input rows**: a slim table icon captioned `02a_buildings_climate.gpkg (N, 29)` with three highlighted key chips per row: `archetype_id · MediumOffice`, `climate_zone · 5A`, `year_built · 1962`; an arrow from `year_built` to a small bin-ruler icon labelled `vintage bins → DOERefPre1980` with a tiny flag chip `NaN → permissive default`.
- **Panel 2 — Standards table stack** (construction_sets.py + loads.py): three stacked open-book/table icons — `ashrae_90_1_2019.json` (showing a row `roof 0.273 · wall 0.701 · win 3.69/0.25`), `iecc_residential.json` rendered **faded with a tag `Phase-2 hook — inert`** (all 30 archetypes route through 90.1 in Phase 1, per the 2026-06-10 OQ-6 resolution), `doe_prototype_loads.json` (showing `10.76 W/m² · 18.58 m²/p · 21.1/23.9 °C · wwr 0.40`); a `×1.6` multiplier badge on a `pre-1980` arrow; **inset funnel below**: a funnel icon labelled `impute_column — KDE | PDE (seeded)` catching a dashed `OpenUBEMUnknown` building icon and a dashed `table gap` cell, emitting chips `HEURISTIC`, `PDE_GENERATED`, `KDE_IMPUTED`; a small inert chip `ML — Phase 2`.
- **Panel 3 — Widened table + gate**: the table icon now captioned `02b_buildings_enriched.gpkg (N, 57)` with a `+28 columns` banner and small column-group chips `envelope ×14` and `loads ×14`; in front of it a checklist gate `zero NaN ✓ · U ∈ [0.1,7.0] ✓ · heating < cooling ✓ · 28/29 byte-identical ✓`; **strip below**: a fanned deck of schedule cards labelled `02b_schedule_library.json — 30 archetypes × 6 families = 180 Schedule:Compact`, one card face showing a tiny weekday step-profile and the name `Heating_Setpoint_MediumOffice` with a tag `plateau == column value`; an exit arrow from the widened table labelled "→ Step 3 IDF generation".
- Key numbers: `29 → 57 columns`, `×1.6 pre-1980`, `30 × 16 × 5 = 2,400 combos validated`, `180 schedules`, `seed-reproducible`.
- What to **NOT** show: maps, footprints, or climate-zone geography (Step 2.1); IDF geometry or extrusions (Step 3); simulation/EUI imagery (Steps 4–5); any neural-network iconography — the ML tier is inert in Phase 1 and must not dominate.

## Visual Metaphors

- **Three keys opening stacked reference books** — standards lookup as the literal mechanism.
- A **funnel** beneath the tables — the explicit, narrow path for everything the tables cannot answer.
- A **fanned card deck** for the schedule library — 180 pre-written cards Step 3 will deal into IDFs.
- A **checklist gate** before the output table — only physically plausible, fully-filled rows leave.

## Style Guidance

- **Palette:** muted slate-blue for table/file icons and arrows; warm amber reserved for the three key chips and the `×1.6` badge; a soft teal for the imputation funnel and its provenance chips; neutral grey labels; one red accent only on the gate's abort condition.
- **Typography:** clean technical sans-serif (Inter / IBM Plex / Helvetica). Labels are short tokens (`5A`, `×1.6`, `wwr 0.40`, `180`) — never sentences.
- **Background:** clean white; no gradients.
- **Target width:** journal double-column (≤ 180 mm). 3 panels + 1 funnel inset + 1 card strip; readable at quarter-page without zoom.
- **Density:** ≤ 7 visible top-level labels (one per panel, funnel, card strip, gate, key-number chips). All other detail lives in the figure caption.

## Generation Prompt

> Paste directly into Midjourney, DALL-E, or Ideogram.

```
Clean technical scientific diagram, three-panel horizontal flowchart on a white background, illustrating standards-based semantic enrichment in an urban building energy modeling pipeline. Panel 1 (left): a slim data-table icon captioned "02a_buildings_climate.gpkg (N, 29)" with three highlighted key chips "MediumOffice", "5A", "1962", and a small bin-ruler icon labelled "vintage bins → DOERefPre1980" with a tiny flag chip "NaN → permissive default". Panel 2 (center): three stacked reference-table icons labelled "ashrae_90_1_2019.json" (visible row "roof 0.273 · wall 0.701 · win 3.69/0.25"), "iecc_residential.json" rendered faded with a small tag "Phase-2 hook (inert)", and "doe_prototype_loads.json" (visible row "10.76 W/m² · 18.58 m²/person · 21.1/23.9 °C · wwr 0.40"), with an amber "×1.6" badge on an arrow tagged "pre-1980"; below, a teal funnel icon labelled "impute_column — KDE | PDE (seeded)" catching a dashed building icon tagged "OpenUBEMUnknown" and a dashed empty cell tagged "table gap", emitting three small chips "HEURISTIC", "PDE_GENERATED", "KDE_IMPUTED", plus a faded chip "ML — Phase 2". Panel 3 (right): the data-table icon now captioned "02b_buildings_enriched.gpkg (N, 57)" with a "+28 columns" banner and group chips "envelope ×14", "loads ×14", preceded by a checklist gate with ticks "zero NaN ✓", "U ∈ [0.1,7.0] ✓", "heating < cooling ✓"; beneath, a fanned deck of cards labelled "02b_schedule_library.json — 30 × 6 = 180 Schedule:Compact", the top card showing a tiny step-profile curve named "Heating_Setpoint_MediumOffice"; an exit arrow from the widened table labelled "→ Step 3 IDF generation". Palette: muted slate-blue icons and arrows, amber key chips and multiplier badge, teal funnel, neutral grey labels, single red accent on the gate. Typography: clean technical sans-serif (Inter or IBM Plex), short token labels, no sentences. Style: precise CAD-inspired technical illustration, vector-clean lines, no photorealism, no neural-network imagery, no clutter, journal double-column width (180 mm). Publication quality.
```

## Alternative Prompt — schematic / technical variant

```
Schematic boxes-and-arrows diagram for a technical report figure, white background, four sequential modules left-to-right: [Module 04: construction_sets.py — resolve_vintage() maps year_built through five half-open bins into the frozen 7-token vintage_standard vocabulary (NaN → DOERefPre1980, permissive direction); one vectorized merge on (climate_zone, vintage_standard) against bundled ashrae_90_1_2019.json — all 30 archetypes in Phase 1, the IECC residential pathway an inert Phase-2 hook; pre-1980 U-values ×1.6; emits 9 envelope values + 5 provenance columns] arrow to [Module 05: loads.py — one merge keyed on archetype_id alone against doe_prototype_loads.json ∪ openstudio_loads.json; lighting/equipment/occupant densities, 4 thermostat scalars, per-archetype wwr (0.21/0.40/0.30/0.10 anchors); 8 values + 6 provenance columns] arrow to [Module 06b: imputation.py — impute_column AUTO: partial missing → KDE (Silverman), total missing → PDE uniform within bounds, ML tier inert Phase 1; OpenUBEMUnknown rows get MediumOffice@DOERefPre1980 donor envelope (HEURISTIC), PDE-sampled densities and wwr over cross-archetype [min,max] (PDE_GENERATED), cross-table median setpoints with heating<cooling guard; one seeded np.random.default_rng per run] arrow to [Module 06 + emit: schedules.py builds 30 archetypes × 6 families = 180 Schedule:Compact stubs (Occupancy/Lighting/Equipment_Schedule_{arch}, Heating/Cooling_Setpoint_{arch}, Infiltration_Schedule_{arch}; dual-plateau setpoints equal the scalar columns) → 02b_schedule_library.json; validate_schema() gate asserts 57 fixed-order columns, zero NaN in 28 appended columns, plausibility envelopes, 28/29 byte-identical pass-through → 02b_buildings_enriched.gpkg (N × 57) + schema.json]. Bottom annotation strip lists validation gates: MediumOffice@1A golden fixture exact, 2,400-combo exhaustive sweep, vintage U-monotonicity, Unknown ⟺ {HEURISTIC, PDE_GENERATED} identity, seed reproducibility. Monochrome blue-grey line art with one amber accent on the ×1.6 vintage badge; clean technical sans-serif labels (Inter / IBM Plex); no shadows, no gradients, vector-precise; suitable for a methods-section figure of an energy-modeling journal article.
```
