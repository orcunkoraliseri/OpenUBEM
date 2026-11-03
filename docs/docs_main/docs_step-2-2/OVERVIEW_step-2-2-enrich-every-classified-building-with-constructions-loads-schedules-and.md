# OVERVIEW — Step 2.2 — Climate-Located GeoDataFrame → Construction Sets, Internal Loads, Schedule Library, and Imputation
### OpenUBEM Stage 2 / Modules 04, 05, 06, 06b — append 28 semantic columns (29 → 57, completing Step 3's frozen input contract), emit the 30 × 6 `Schedule:Compact` library, close every NaN via the KDE/PDE tier

> **Slug:** `step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and` &nbsp;•&nbsp; **Snapshot of:** `DESIGN_step-2-2-enrich-every-classified-building-with-constructions-loads-schedules-and.md` &nbsp;•&nbsp; **Generated:** `2026-06-09`
>
> Compact dashboard. For depth → read the DESIGN doc. For revision history → read DESIGN §11.

---

## AIM

Step 2.2 designs the last undesigned module group of the Phase-1 pipeline — Modules 04 (construction sets), 05 (internal loads), 06 (schedules), 06b (imputation). It finishes the column accretion Step 3 assumes: for every building it resolves `vintage_standard` from `year_built` (Step 3's frozen 7-token vocabulary, NaN → permissive `DOERefPre1980`), looks up the ASHRAE 90.1 / IECC envelope for `(archetype_id, climate_zone, vintage)` (pre-1980 → ×1.6 U-multiplier), looks up DOE-prototype loads, thermostat scalars, and WWR per archetype, and routes everything the lookups cannot answer — `OpenUBEMUnknown` rows, table gaps, probabilistic sampling — through the seeded KDE/PDE imputation tier so that **zero NaN survives in the 28 appended columns**. It also emits the schedule library Step 3 binds by name: 30 archetypes × 6 families = 180 `Schedule:Compact` stubs, persisted as `02b_schedule_library.json`, with a scalar–plateau consistency invariant tying setpoint columns to setpoint schedules. Governing principles: one authoritative copy of every standards number, closed vocabularies with canonical provenance tokens, uncertainty explicit (never silently defaulted), fail-loud on systemic table defects.

---

## PIPELINE

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  3A — Input Gate & Schema Validation (semantic/__init__.py)                  ║
║  Inputs:    02a_buildings_climate.gpkg (N, 29) from Step 2.1                 ║
║  Operation: 29-col schema check; archetype_id ∈ closed 30-element vocab;     ║
║             climate_zone ∈ closed 16-token vocab; mismatch ⇒ ABORT           ║
║  Output:    validated frame                                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3B — Vintage Resolution (Module 04: construction_sets.py)                   ║
║  Operation: year_built → 5 half-open bins → Step 3's frozen 7-token          ║
║             vintage_standard vocab (90.1-2010/-2016 bin-unreachable);        ║
║             NaN → DOERefPre1980 (permissive, row 86) + HEURISTIC envelope    ║
║             provenances + VINTAGE_NAN_PERMISSIVE_DEFAULT flag token          ║
║             (the SINGLE pass-through exception)                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3C — Envelope Lookup (Module 04: construction_sets.py)                      ║
║  Inputs:    ashrae_90_1_2019.json / iecc_residential.json (bundled)          ║
║  Operation: ONE vectorized merge on (table, climate_zone, vintage);          ║
║             vintage = U-multiplier on one baseline (pre-1980 ×1.6, spec);    ║
║             9 envelope values + 5 provenance; KDE lookup-gap guard           ║
║  Validation: MediumOffice@1A golden fixture; U-monotonicity across vintages  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3D — Loads & WWR Lookup (Module 05: loads.py)                               ║
║  Inputs:    doe_prototype_loads.json + openstudio_loads.json (bundled)       ║
║  Operation: ONE merge keyed archetype_id alone; 8 values + 6 provenance;     ║
║             wwr group anchors 0.21/0.40/0.30/0.10 (row 90); DataCenter ITE   ║
║             bound to NREL openstudio-standards (row 89, OQ-3)                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3E — Imputation & Unknown Handling (Module 06b: imputation.py)              ║
║  Operation: impute_column AUTO (KDE partial | PDE total | ML inert Phase 1); ║
║             OpenUBEMUnknown: envelope = MediumOffice@DOERefPre1980 donor     ║
║             (HEURISTIC); densities+wwr = PDE over cross-archetype [min,max]  ║
║             (PDE_GENERATED); setpoints = cross-table median, heating<cooling ║
║             guard; probabilistic mode perturbs ONLY 3 density columns;       ║
║             one seeded np.random.default_rng per run                         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3F — Schedule Library (Module 06: schedules.py)                             ║
║  Operation: 30 archetypes × 6 families = 180 Schedule:Compact stubs under    ║
║             Step 3's exact name contract (Occupancy/Lighting/Equipment_      ║
║             Schedule_{arch}, Heating/Cooling_Setpoint_{arch},                ║
║             Infiltration_Schedule_{arch}); Weekday/Sat/Sun day-types;        ║
║             dual-plateau setpoints == scalar columns (invariant);            ║
║             Unknown = MediumOffice clone under own key; Activity_Level       ║
║             excluded (row 87) → 02b_schedule_library.json                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  3G — Column Append + validate_schema() Gate + Emit                          ║
║  Operation: append EXACTLY 28 columns (14 envelope + 14 loads, 11 prov.      ║
║             under pinned sharing rules) → (N, 57); gate: zero-NaN,           ║
║             plausibility envelopes (U ∈ [0.1,7.0], SHGC (0,1], equip ≤ 2500, ║
║             heating < cooling row-wise), 28/29 byte-identical, schedule      ║
║             completeness; failure ⇒ ABORT                                    ║
║  Output:    02b_buildings_enriched.gpkg + .schema.json (57) +                ║
║             02b_schedule_library.json  →  Step 3's frozen input contract     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## KEY NUMBERS

| Quantity | Value | Source |
|---|---|---|
| Input → output schema             | (N, 29) → (N, 57): + 28 columns (14 envelope + 14 loads) | DESIGN §3G, §4 |
| Provenance columns / sharing      | 11 for 17 value columns; pinned sharing rules; tokens ∈ {ASHRAE_STANDARD, HEURISTIC, KDE_IMPUTED, PDE_GENERATED} | DESIGN §3G |
| `vintage_standard` vocabulary     | 7 tokens (Step 3 frozen); 5 reachable from year bins | DESIGN §3B |
| Pre-1980 envelope factor          | ×1.6 on 90.1-2019 baseline U-values (spec-sourced; other eras OQ-1) | DESIGN §3C |
| Golden fixture                    | MediumOffice@1A: 0.273/IEAD, 0.701/Mass, 3.69/0.25, 1.89, 0.000285; 10.76/10.76/18.58; 21.1/23.9/15.6/29.4; wwr 0.40 | DESIGN §3C, §3D |
| Schedule library                  | 30 archetypes × 6 families = 180 `Schedule:Compact` stubs | DESIGN §3F |
| Exhaustive lookup sweep           | 30 × 16 × 5 = 2,400 combos, zero NaN, zero gaps | DESIGN §5.1 |
| Pass-through                      | 28 of 29 upstream byte-identical; `data_quality_flag` single-token exception | DESIGN §3B, §4 |
| Wall-clock (Boston 500 m)         | < 10 s | DESIGN §6 |
| GPU hours                         | 0 | DESIGN §6 |
| Open Questions                    | 6 | DESIGN §7 |

---

## VALIDATION SUMMARY

- Golden-fixture exactness: `MediumOffice @ 1A @ 90.1-2019` reproduces **all 13 spec values exactly**; `DOERefPre1980` fixture reproduces the ×1.6 set (0.437/1.122/5.90/3.02)
- Exhaustive sweep: **2,400/2,400** archetype × zone × vintage combos with zero NaN and zero `construction_lookup_gap` warnings on bundled tables
- Vintage U-monotonicity: U-values **non-increasing** from `DOERefPre1980` → `90.1-2019` for every archetype × zone (gates OQ-1 factor values)
- Unknown identity: all 11 provenance values on `OpenUBEMUnknown` rows ∈ {HEURISTIC, PDE_GENERATED}; `PDE_GENERATED` appears **only** there in deterministic mode
- Setpoint sanity: **100%** of rows `heating_setpoint_c < cooling_setpoint_c` (including Unknown median branch)
- Schedule contract: **180/180** stubs; names match Step 3's reference patterns; occupied plateaus **==** setpoint scalar columns per archetype
- Seed reproducibility: same `RANDOM_SEED` ⇒ byte-identical; different seeds differ **only** in the 3 perturbed density columns
- Determinism: deterministic mode ⇒ byte-identical `02b_*` artifacts across re-runs
- True Future Test: n/a — lookups + seeded max-entropy sampling, nothing trained

---

## KEY DECISIONS

> Mirrors DESIGN §9 — same rows, one line each.

| Decision | Rationale (one line) |
|---|---|
| 28-column append with 11 provenance columns under pinned sharing rules | Completes Step 3's frozen 57-column contract and closes its one ambiguity (which value shares which provenance) inside §1–§9. |
| 5 half-open year bins into Step 3's frozen 7-token vintage vocabulary; NaN → `DOERefPre1980` + flag token (single pass-through exception) | Vocabulary is Step 3's; permissive direction (row 86) avoids overstating envelope quality on older untagged stock. |
| Envelope = one vectorized merge; vintage as multiplier on one committed baseline; KDE lookup-gap guard | One authoritative copy of every number; gaps degrade traceably for user tables, bundled tables stay gap-free via the §5.1 sweep. |
| Loads + `wwr` keyed on `archetype_id` alone; DataCenter ITE bound to NREL openstudio-standards; infiltration owned by Module 04 only | Matches the DOE source's key structure; one owner per column kills the spec's duplicated-infiltration ambiguity. |
| `OpenUBEMUnknown`: donor envelope (MediumOffice@Pre1980, HEURISTIC) + PDE densities/wwr + median setpoints with heating<cooling guard + cloned schedule set | Row 73 semantics — uncertainty explicit, physically coherent envelope, no thermostat inversion. |
| Schedule library 30 × 6 under Step 3's exact name contract; scalar–plateau consistency invariant; persisted JSON; Activity_Level excluded | Step 3 binds by name at IDF parse time; the invariant makes column-vs-schedule drift impossible to miss. |
| `impute_column` AUTO with ML inert (row 33); probabilistic mode perturbs only 3 density columns through one seeded Generator; zero-NaN + plausibility gate | KDE/PDE is the confirmed Phase-1 doctrine; seeded runs are byte-identical; wrong-units tables die at minute 0. |

---

## OPEN QUESTIONS

- **OQ-1** — Numeric vintage factors for `DOERef1980to2004` / `90.1-2007` / `90.1-2013` + bin-edge mapping confirmation + infiltration-vintage decision. *(blocks §3C for non-baseline vintages)*
- **OQ-2** — One-time digitization of `doe_schedules.json` (30 × 6 × 3 day-types incl. setpoint plateau windows) from DOE prototype schedule sets. *(blocks §3F on real data)*
- **OQ-3** — DataCenter ITE `equipment_w_m2` extraction from NREL/openstudio-standards (inherits row 89 / Step 3 OQ-4). *(blocks §3D for the two HighITE archetypes)*
- **OQ-4** — Full 30-row per-archetype WWR table beyond the four group anchors. *(blocks §3D table finalization)*
- **OQ-5** — ASHRAE 90.1 PDE bounds table for probabilistic mode + Unknown cross-archetype `[min,max]` policy confirmation. *(blocks probabilistic mode only)*
- **OQ-6** — IECC residential pathway: `iecc_residential.json` extraction, era→IECC edition mapping, `residential_set` routing membership. *(blocks §3C residential path; commercial unblocked)*
