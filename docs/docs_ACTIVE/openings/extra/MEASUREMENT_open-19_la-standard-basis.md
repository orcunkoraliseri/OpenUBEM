# MEASUREMENT — Is the Title 24 hypothesis even representable in this pipeline? (OPEN-19)

> **Task:** N12, `PLAN_no-compute-queue-2.md` §6. **Type:** measurement only — no fix proposed, no
> calibration performed, no literature research conducted. **Repo state read:** HEAD `bca92d0a6cdc3392
> 3bea8424f1b86ab0f94d82d9` (working tree otherwise dirty per `git status`, but none of the files cited
> below are among the modified/untracked paths — confirmed by cross-referencing `git status --short`
> against the file list in §1–§4).

## 0. Verdict, up front

**No.** The hypothesis is not representable in this pipeline today, in a specific and checkable sense:
the pipeline has exactly one national code baseline (ASHRAE 90.1-2019, extracted from **Buffalo, NY**
prototype IDFs — ASHRAE zone 6A) applied uniformly to every building regardless of climate zone or
state. There is no California / Title 24 table, no code-year switch, and no per-state branch anywhere
in `openubem/`. One climate-zone-aware field *does* exist in the HVAC data (`economizer_db_limit_c`)
but it is dead data — never read by the code that emits the IDF. Representing Title 24 would require
new data (a Title 24 construction/HVAC/schedule table) and a new dispatch key (state or climate-code
edition), neither of which exists.

## 1. What the archetypes actually encode today

### 1.1 Envelope (construction sets)

Loaded and merged in `openubem/semantic/construction_sets.py`:
- `_get_ashrae_table()` (`:68-72`) loads exactly one bundled table:
  `openubem/data/construction/ashrae_90_1_2019.json`, keyed `(archetype_id, climate_zone)`.
- `_build_flat_lookup()` (`:77-99`) flattens it to columns `u_roof_w_m2k`, `u_wall_w_m2k`,
  `u_window_w_m2k`, `shgc_window`, `u_floor_w_m2k`, `infiltration_m3_s_m2`.
- `get_construction_set()` (`:266-355`) merges on `(archetype_id, climate_zone)` and then applies a
  **vintage** U-factor multiplier (`VINTAGE_U_FACTORS`, `:27-35`) — vintage only rescales U-values; it
  never changes the *standard*, which is ASHRAE 90.1-2019 in every case.
- A `custom_table` parameter exists at every layer (`construction_sets.py:269`, `semantic/__init__.py
  :191,279`) purely as a test-injection hook. **Confirmed no script under `scripts/` ever passes a
  non-`None` value for it** (`grep -n "construction_table\s*=" scripts/` → 0 matches, run 2026-08-06).
  Production always resolves to the single bundled ASHRAE table.

**Concrete values for LA's dominant archetype, MidriseApartment (n=1,775 of LA's 2,314 scored
buildings per `docs/docs_VALIDATION/step1/overAll/V19_phaseC_rescore.md:45`), at climate zone 3B**
(read from `openubem/data/construction/ashrae_90_1_2019.json` via `construction_sets.py:90-97`,
2026-08-06):

| Parameter | Value | path:line |
|---|---|---|
| Roof U-value | 0.221 W/m²K (assembly `IEAD`) | `openubem/data/construction/ashrae_90_1_2019.json` (`MidriseApartment.3B.roof`), loaded `construction_sets.py:71,90-91` |
| Wall U-value | 0.437 W/m²K (assembly `SteelFramed`) | same file, `MidriseApartment.3B.wall`; `construction_sets.py:92-93` |
| Window U-value / SHGC | 2.385 W/m²K / 0.25 | same file, `MidriseApartment.3B.window`; `construction_sets.py:94-95` |
| Floor U-value | 0.42 W/m²K | same file, `MidriseApartment.3B.floor`; `construction_sets.py:96` |
| **Infiltration** | **0.000285 m³/s·m²** of exterior wall area | same file, `MidriseApartment.3B.infiltration_rate`; `construction_sets.py:97` |

Same query for LA's office archetypes (n=369) at 3B: SmallOffice wall U=0.505 (WoodFramed), roof
U=0.153 (Attic and Other); MediumOffice/LargeOffice wall U=0.437/0.698, roof U=0.221 — all window
U=2.385/SHGC=0.25, all infiltration=0.000285. **Every one of the 20 real archetypes in the table carries
the same infiltration rate at every climate zone** — confirmed by `PROVENANCE.md:46-54` (quoted in full
below) and independently by direct read of five archetypes across two climate zones.

**Provenance, verbatim, `openubem/data/construction/PROVENANCE.md:1-22,46-54`:**
> Source repository: NREL/openstudio-standards. Commit `83b1e64c6f130f02b48c8b3ad4eeb3eb4da41663`.
> Retrieval date: 2026-06-10. … `ashrae_90_1_2019.construction_properties.json` /
> `ashrae_90_1_2019.construction_sets.json`, `lib/openstudio-standards/standards/ashrae_90_1/
> ashrae_90_1_2019/data/`.
> … Uniform prototype value: **0.000285 m³/s·m²** of exterior surface area … Source: PNNL-20405 (2011)
> "EnergyPlus New Construction Commercial Reference Buildings", Table B.19 … All 29 real archetypes use
> 0.000285 except DataCenter archetypes which use 0.000126 m³/s·m² … **Infiltration is vintage-invariant
> in Phase 1** (DESIGN §11 OQ-1b confirmed resolution).

So: envelope U-values are climate-zone-*aware* (the lookup key includes `climate_zone`) but the
*standard* they are drawn from is fixed at ASHRAE 90.1-2019 nationwide. Infiltration is neither
climate-zone-aware nor vintage-aware — one number, one source, everywhere except data centers.

### 1.2 HVAC — COP / heating efficiency

`openubem/idf/hvac.py:625-736` (`assign_hvac`) reads two bundled JSONs, both **keyed by
`archetype_id` only — no `climate_zone` key in either file's schema**:
- `openubem/data/loads/hvac_cop_by_archetype.json` — cooling COP, heating efficiency.
- `openubem/data/loads/hvac_systems_by_archetype.json` — system family, fan power, economizer fields.

**Concrete values, MidriseApartment** (`hvac_cop_by_archetype.json`, read 2026-08-06):
```
"cooling_cop": 4.3229889726447,
"heating_coil_type": "Gas",
"heating_efficiency": 0.84,
"source_prototype": "ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf"
```
Applied via `openubem/idf/hvac.py:230-231` (`_emit_psz_ac`, MidriseApartment's `system_family` is
`"PSZ-AC w/ Gas Furnace"` per `hvac_systems_by_archetype.json`): `cooling_cop = _resolve(cop_entry,
"cooling_cop", 3.0, …)`, `htg_eff = _resolve(cop_entry, "heating_efficiency", 0.8, …)`.

**Finding — the source prototype is not climate-matched to the building.** Every one of the 21
`source_prototype` values in `hvac_cop_by_archetype.json` is a **Buffalo, NY** prototype file (ASHRAE
zone 6A) — confirmed by direct enumeration (2026-08-06):
```
ASHRAE901_ApartmentHighRise_STD2022_Buffalo.idf, ASHRAE901_ApartmentMidRise_STD2022_Buffalo.idf,
ASHRAE901_Hospital_STD2022_Buffalo.idf, ASHRAE901_HotelLarge/Small_STD2022_Buffalo.idf,
ASHRAE901_Office{Small,Medium,Large}_STD2022_Buffalo.idf, ASHRAE901_OutPatientHealthCare_STD2022_
Buffalo.idf, ASHRAE901_Restaurant{FastFood,SitDown}_STD2022_Buffalo.idf, ASHRAE901_Retail{Standalone,
Stripmall}_STD2022_Buffalo.idf, ASHRAE901_School{Primary,Secondary}_STD2022_Buffalo…, ASHRAE901_
Warehouse_STD2022_Buffalo.idf, College/Laboratory/SmallDataCenter…_90.1-2019_6A_Buffalo_v221.idf
(+ two non-Buffalo exceptions: DataCenterLarge{High,Low}ITE_STD2019.idf, Supermarket_V22.1.idf).
```
Confirmed by `scripts/validation/extract_prototype_cop.py:18`: `PROTO_DIR = ROOT /
"docs/validations/Level 2 DOE round-trip/00.BaselineBuildings_NUs"` — one fixed prototype set, drawn
from the DOE prototype library's Buffalo climate representative, extracted once and applied to every
city and every climate zone the pipeline simulates, including LA (CZ 3B). Equipment *efficiency*
(COP/heating-eff) is standard-mandated and does not vary by climate zone under ASHRAE 90.1's own
structure (that part is not a pipeline shortfall) — but it does mean **the pipeline could not currently
represent a Title 24-specific COP/IEER uplift even if asked to**, since there is only one number per
archetype and no second table to switch to.

### 1.3 HVAC — economizer

**Presence:** yes, an economizer is modelled for every packaged/VAV/CRAC/CRAH system family.
Hardcoded in `openubem/idf/hvac.py`, `Economizer_Type = "DifferentialDryBulb"` at lines **248** (PSZ-AC),
**288** (PSZ-HP), **332** (Packaged VAV), **386** (Built-up VAV), **532** (CRAC proxy), **567** (CRAH
proxy). The one exception is the warehouse radiant-heat proxy, `Economizer_Type = "NoEconomizer"`
(`:613`) — heating-only system, no cooling coil to economize. PTAC (SmallHotel, `_emit_ptac`,
`:176-217`) sets no `Economizer_Type` field at all — `HVACTEMPLATE:ZONE:PTAC` has no such field in the
IDD; economizer control at the zone level is not represented for that one archetype family.

**Finding — a climate-zone field exists in the data but is dead code.** `hvac_systems_by_archetype.json`
carries, on **every** archetype entry, an `economizer_db_limit_c` object recording ASHRAE 90.1's
per-climate-zone fixed dry-bulb high-limit shutoff temperature, e.g. MidriseApartment (`:29` in that
file, same for every other archetype — one JSON dict repeated verbatim across all 21 entries):
```json
"economizer_threshold_kbtuh": 54,
"economizer_db_limit_c": {"4A": 18.3, "3B": 23.9, "2A": 18.3}
```
23.9°C = 75.0°F — exactly ASHRAE 90.1's Zone 3B fixed-dry-bulb economizer high limit. **Neither
`economizer_db_limit_c` nor `economizer_threshold_kbtuh` is ever read in `openubem/idf/hvac.py`** —
confirmed by `grep -n "economizer_db_limit_c\|economizer_threshold_kbtuh" openubem/` returning only the
JSON-file definitions, zero occurrences in any `.py` file (search run 2026-08-06). The code always emits
`DifferentialDryBulb` control (compares outdoor air to return air temperature; no fixed threshold field
is set on the IDF object at all), so **the climate-zone-specific value recorded in the data has no
effect on any simulation** — it is present as reference/provenance metadata, not as a control input.

**Consequence for OPEN-19's hypothesis:** the literature-cited Title 24 lever here (California's tighter
71°F fixed-dry-bulb shutoff vs. ASHRAE 90.1's 75°F for CZ 3B) targets a control input this pipeline does
not use at all — changing `economizer_db_limit_c` today would change nothing, because the emitted IDF
object type (`DifferentialDryBulb`) never consults it.

## 2. Climate-zone / code-year switch search — explicit no

**Search run (2026-08-06):**
```
grep -rniE "title.?24|title24|cec |california energy commission|CALGreen" openubem/ scripts/
grep -rn "Title 24\|Title-24" --include="*.py" --include="*.json" openubem/
grep -n "climate_zone" -l openubem/**   (files_with_matches, 6 hits)
grep -n "construction_table\s*=" scripts/**
```
**Result: zero hits** for any Title 24 / California-code / CALGreen / code-year-switch string in any
`.py` or `.json` file under `openubem/` or `scripts/`. The only "California" content anywhere in the
repository under those two search roots is place-name data (weather-station city names in
`openubem/data/epw_stations.csv`, viewer HTML titles) — not code logic.

The 6 files that reference `climate_zone` at all are: `openubem/acquisition/climate_zone.py` (the
assignment logic itself), `openubem/semantic/__init__.py`, `openubem/semantic/construction_sets.py`,
`openubem/acquisition/__init__.py`, `openubem/geometry/envelope_patcher.py`, and
`openubem/data/climate_zones/PROVENANCE.md`. None of the six branches on state, code year, or
jurisdiction — `climate_zone` is used purely as an ASHRAE-169 zone-token lookup key into the one bundled
table.

`openubem/acquisition/climate_zone.py:20-22` defines the **closed vocabulary**:
```python
_CLIMATE_ZONE_VOCAB: frozenset[str] = frozenset(
    {"1A", "2A", "2B", "3A", "3B", "3C", "4A", "4B", "4C", "5A", "5B", "5C", "6A", "6B", "7", "8"})
```
This is the 16-token **ASHRAE 169** zone set (`openubem/data/climate_zones/PROVENANCE.md:13-19`:
"ASHRAE 169-2013-consistent county→zone assignments... pinned to ASHRAE 169-2013-consistent edition to
match the bundled 90.1-2019 construction tables"). There is no parallel California Climate Zone (CEC's
own 16-zone CZ1–CZ16 scheme, a different partition than ASHRAE's) anywhere in the vocabulary, the
lookup table, or the assignment code. **Confirmed LA County (FIPS `06037`) resolves to ASHRAE zone `3B`**
by direct query of the bundled gpkg (`openubem/data/climate_zones/ashrae_climate_zones.gpkg`, layer
`counties`, 2026-08-06) — matching the register's and the literature document's "CZ 3B" framing, but it
is the ASHRAE zone, not a Title 24 CEC zone (LA is CEC CZ 6/8/9 depending on sub-area, per the literature
document read in §3 below — this pipeline has no representation of that finer partition at all).

**Explicit answer to the "How to test" (b) item: no climate-zone or code-year switch exists in the
codebase.** The search above is exhaustive over the two most plausible roots (`openubem/`, `scripts/`)
and turned up nothing; the six files that do handle `climate_zone` were each individually read and none
branches on jurisdiction.

## 3. The −0.6% and +40% figures — carried, with exact sources

Both figures are recorded, verbatim, in one document: `docs/docs_VALIDATION/step1/overAll/
V19_phaseC_rescore.md`.

- **Headline text**, `V19_phaseC_rescore.md:34`: *"LA is still hot: Overall +38.8 % (was +39.6 %),
  essentially unmoved by the fix (−0.6 %)."*
- **Table row**, `V19_phaseC_rescore.md:45` (LA "Overall" row): `Δ vs measured = +38.8%`,
  `Δ vs V17 (fix effect) = −0.6%`, n = 2,314.
- The register's rounding of +38.8% to "~+40%" is the register's own paraphrase (`INVESTIGATION_
  open-items-register.md:139,976-984`); the source document's own number is 38.8%, not 40%.
- The literature deep-research document independently cites the same number: `docs/docs_DONE/SETUP/
  phaseC_combinedResim/v19_validation/deepResearch/RESULT_1_LA_climate_overprediction.md:3`: *"+38.8%
  site EUI over-prediction observed in Los Angeles"* — this document is a **citeable literature
  synthesis about published external studies**, not a fresh measurement of this pipeline; it takes the
  38.8% as given from V19 and researches candidate explanations against outside literature. It is the
  source of the Title 24 hypothesis's specific parameter list (VAV minimum airflow, LPD, sizing factors,
  economizer, envelope) reproduced in the register.

**Neither figure was re-derived from raw per-building results in this task.** `V19_phaseC_rescore.md`
is itself a **report-only synthesis** (its own line 6: *"Report-only synthesis. No EnergyPlus
resimulation in this document"*) that aggregates a full 12-cell, 8,156-building reconstructed-EUI table
against measured anchors — reproducing that aggregation from `05_results.gpkg`/`05_results.csv` fleet-
wide is a multi-hundred-row join across all twelve cells, not a "cheaply available" re-derivation as
framed by the plan, and was not attempted here. **Status: carried, not independently re-verified** —
the number is traced to its exact document and line, and that document states it as its own finding
(not a further citation), but this task did not re-run the aggregation from source `.gpkg`/`.csv` files.

## 4. The definitional question — what would "calibration" mean here, and what would it move

*(This paragraph states facts about which stored values a Title 24-style change would touch. It
contains no recommendation and proposes no calibration.)*

A Title 24 alternative, if built, would require at minimum:
1. **A second construction/HVAC/schedule table** parallel to `ashrae_90_1_2019.json` /
   `hvac_cop_by_archetype.json` / `hvac_systems_by_archetype.json` — Title 24 envelope U-factors,
   LPD, VAV minimum-airflow fractions, and economizer high-limit values, per California Climate Zone
   (a different zone partition than the ASHRAE one currently used, per §2).
2. **A dispatch key** — something that currently does not exist — deciding, per building, which table
   to use. The only candidate field already computed per building is `state` (`climate_zone.py:192`,
   populated as a two-letter USPS code); no code anywhere reads it to select between tables.
3. **A definition of "calibration"** that the register itself already flags as needing to be settled
   first (`INVESTIGATION_open-items-register.md:982-984`, quoted): *"the current baseline carries a
   zero-fitted-parameters guarantee. A 'calibration phase' must be defined carefully or it breaks that
   guarantee."* Two distinct things could be called "calibration" here, and they have opposite standing
   against that guarantee:
   - **(a) Swapping in a different, independently-sourced code standard** (Title 24 tables in place of
     ASHRAE 90.1 for California buildings, still zero fitted free parameters — every value still comes
     from a named code document, not from tuning against measured EUI). This is a source substitution,
     not a fit.
   - **(b) Adjusting any of the values found in §1** (envelope U, infiltration, COP, VAV minimum
     fraction, LPD) to make the LA numbers match measured EBEWE data, without an independent code
     citation for the adjusted value. This is fitting, and it is what the zero-fitted-parameters
     guarantee currently forbids.
   This task does not decide which of (a) or (b) an eventual plan would be, or whether (a) is itself
   sufficient to close the gap — the literature document in §3 only estimates the expected impact of
   each Title 24 lever from published studies of *other* buildings, not from this pipeline's own
   archetypes. That estimation would still need doing before any plan, and is out of scope for a
   measurement-only task.

## 5. Summary against the plan's "how to test"

- **(a) At least four concrete parameter values with `path:line`:** ✅ PASS — envelope (§1.1, 4
  archetypes × 4 values each), infiltration (§1.1, uniform 0.000285), COP (§1.2, MidriseApartment
  cooling_cop=4.323, heating_efficiency=0.84), economizer presence (§1.3, `hvac.py:248,288,332,386,
  532,567,613`).
- **(b) Explicit yes/no on climate-zone/code-year switch, with the search run:** ✅ PASS — **no**, none
  exists; full search commands quoted in §2, zero hits.
- **(c) Definitional paragraph contains no recommendation:** ✅ PASS on re-read — §4 states what a
  calibration phase would require and distinguishes two senses of "calibration" by their standing
  against the zero-fitted-parameters guarantee; it recommends neither, decides neither, and proposes no
  specific parameter change.
