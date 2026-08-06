# MEASUREMENT — OPEN-03: is the loads/envelope vintage split deliberate, and how big is it?

> Executes M03 of `docs/docs_ACTIVE/openings/implemenation/PLAN_published-numbers.md` §6.
> Measurement only. No remediation performed or proposed. No EnergyPlus run.

---

## Verdict (part a)

> **undocumented but deliberate (traceable to a decision that was never written into a spec)**

The decision to leave `layout_assign`'s internal loads at the DOE `STD2022` prototype's own
density — while patching the envelope to the real building's resolved vintage — is real,
intentional, and traceable to a specific task's scope. It is **not** an accident of the code. But
it was never written into a `DESIGN`/`OVERVIEW` doc (this project's own "spec" tier per
`CLAUDE.md` §"Documentation layout") as a reasoned, accepted approximation the way the arc's other
open question (Q3, the √S geometry distortion) explicitly was. See "Evidence" below for the full
trail and the one place a reader could plausibly read this the other way.

---

## Part (a) — Intent: the evidence trail

### 1. No DESIGN doc anywhere mentions `layout_assign` or `resolution_mode` at all

`Grep -r "layout_assign|resolution_mode" docs/docs_main` — **zero matches**, confirmed live in
this session. `docs/docs_main` is this project's DESIGN/OVERVIEW tier (`CLAUDE.md`: "OVERVIEW /
DESIGN / flowchart = source-of-truth specs, never edited by Claude or Sonnet"). The `layout_assign`
resolution mode — including its internal-loads handling — was built entirely outside the DESIGN-doc
structure, tracked only in the `layoutAssigner` arc's own PLAN docs. This rules out **"documented
approximation"** in the strict sense CLAUDE.md defines "documented": nothing in the binding-contract
tier says anything about this at all.

### 2. The arc's own architecture table scoped loads out from day one — this is the "deliberate" half

`docs/docs_DONE/SETUP/layoutAssigner/DONE/DONE-implementation_plan.md:148-159`, §4 "Architecture
(unchanged from v2, with corrections)" — written before any `layout_assign` code existed:

| Step | Standard modes | `layout_assign` |
|---|---|---|
| Loads/Schedules/HVAC | `assign_*()` | Already in baseline; scale absolute levels × S |

(`:155`, verbatim row.) From the very first architecture pass, `layout_assign` was designed to
**never** call the standard per-building `assign_*()` pipeline (the functions that consume
`row["lighting_w_m2"]`, `row["equipment_w_m2"]`, `row["occupant_m2_per_person"]` — themselves
vintage-**invariant** by a separate, actually-documented design choice; see §3 below). Internal
loads for `layout_assign` were always meant to be "already in baseline," i.e. the DOE prototype's
own native density, scaled only by area ratio S. This is a genuine, prospective design decision —
not a retroactive excuse — but the table gives no rationale for it and never mentions vintage at
all; it simply draws the mode's scope boundary.

### 3. Only envelope was ever an open question; loads never were

The arc tracked exactly three open questions across its life — Q1 (envelope adaptation), Q2
(design-day weather), Q3 (√S geometry distortion) — `DONE-implementation_plan.md:278-317`. Loads
vintage was never a fourth open question. Q1's own text
(`DONE-implementation_plan.md:280-281`) frames the entire envelope-patching effort narrowly:

> "**Q1 Envelope adaptation:** patch CZ-specific U-values (T11) or accept Buffalo CZ 6A envelope
> for initial validation?"

T16's task scope (`DONE-implementation_plan.md:252-257`, "Un-defer T11: `envelope_patcher.py`
cross-CZ envelope patching") is explicitly envelope-only in its "What," "Why" and "How" — it never
proposes, considers, or rejects a parallel loads patch. The narrowing to envelope-only long predates
any measurement of the loads consequence.

### 4. The consequence was discovered after the fact, named, and explicitly deferred — not adopted as policy

T16's own progress-log entry, written the day the envelope patch was implemented and tested
(`DONE-implementation_plan.md:494`, verbatim excerpt):

> "...internal loads (lighting+equipment = 45.7 of 72.2 total, **63%** of this archetype's total
> EUI) are structurally untouched by envelope patching, because `layout_assign` never calls
> `assign_loads()` — internal loads are always the DOE baseline's own native density scaled by S
> (plan §4 architecture table), never the real building's pipeline-derived
> `row["lighting_w_m2"]`/`row["equipment_w_m2"]`/`row["occupant_m2_per_person"]`. **This is the
> most likely dominant driver of the ~2x `layout_assign`-vs-fleet EUI gap**... Flagged as a finding
> for a future arc (internal-load density mismatch is out of T16's scope — **no plan task
> currently addresses it**); §7 Q1 updated accordingly."

`§7 Q1`'s updated text (`DONE-implementation_plan.md:281`) repeats the same framing: "Flagged as a
finding for a future arc, not a T16 blocker." This is disclosure of a known, measured gap — written
down, real, and honest — but it reads as *"we found this and haven't gotten to it,"* not *"we
decided this tradeoff is acceptable and are documenting it as such."* No task, ADR, or open-question
entry anywhere ever says "we accept internal loads staying at prototype vintage" the way Q3
literally does (`:297`: *"Default: accept... document the approximation"*) for the unrelated √S
geometry issue.

### 5. The register itself, and the results doc, both call it "documented" — the one place a reader could read this differently

`docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register.md:179` (OPEN-03 entry): **"Status:
documented in results §7, never actioned."** And the results doc itself,
`docs/docs_DONE/SETUP/layoutAssigner/figures/OpenUBEM_results_LayoutAssigner.md:460-463` (§7.2):

> "Lighting and equipment come from the `ASHRAE901_*_STD2022` prototypes. `layout_assign` therefore
> models every building's internal loads as 2022-code construction regardless of its real vintage.
> The envelope *is* re-patched to the real vintage and climate zone by `envelope_patcher` (T16);
> the internal loads are not. **This is a direct consequence of prototype substitution, not a
> defect** — but it had never been quantified before this section, and it is roughly half the
> total gap."

This is the strongest evidence *for* "documented approximation": a results document explicitly
says "not a defect." **This is a contradictory statement and is reported as such, not adjudicated
away.** But per CLAUDE.md's own tier system, a results doc (`docs_DONE/.../figures/`) is not a
DESIGN/OVERVIEW spec either — it is post-hoc explanation, written the same day as the T16
discovery above, by the same close that flagged it "for a future arc." Read together, both
documents describe the same fact-finding, not a prior design decision that was later written up.

**Verdict, restated:** the split is a real, deliberate, code-traceable design boundary (§4's
architecture table drew it before implementation began), but no DESIGN/OVERVIEW spec anywhere
states it, reasons about it, or accepts it as an approximation — it is disclosed only in PLAN-doc
progress logs and a results doc, after the fact. That is exactly the shape of **"undocumented but
deliberate."**

---

## Part (b) — Magnitude: static field comparison, no simulation

### Method

For the 12 archetypes with **both** a 90.1-2013 source IDF
(`docs/docs_DONE/LOADS & SCHEDULES/scheduleDigitization/sources/*.idf`, read-only, untouched) and a
`layout_assign` `STD2022` baseline (`config.BASELINE_IDF_DIR`, `openubem.geometry.layout_assigner.
ARCHETYPE_IDF_MAP`), loaded both files with `geomeppy.IDF` under the project's locked 23.1 IDD
(`config.ENERGYPLUS_IDD_PATH`) and used the project's own zone-floor-area accessor,
`openubem.geometry.layout_assigner.parse_baseline_zones()`, to area-weight every `Lights`,
`ElectricEquipment` and `People` object across all zones (no hand-rolled IDF text parser, per plan
§4). `Watts/Area`-method objects contribute `W/m² × zone_area`; absolute-method objects
(`LightingLevel`/`EquipmentLevel`/`Number_of_People`) contribute their literal value; `ZoneList`
references are expanded to their member zones. Script: session scratchpad
`m03_load_ratios.py` (not a repo artifact, per plan rule "no `.py` under `docs/`").

**n = 12 archetypes matched, 0 unmatched.** Every archetype named in the plan's 12-file source set
had a mapped `STD2022` baseline via `ARCHETYPE_IDF_MAP`. The 2 files without a literal
`_90.1-2013.idf` suffix (`Restaurant_FullServiceRestaurant.idf`,
`Restaurant_QuickServiceRestaurant.idf`) were verified by header inspection
(`AnalysisCodeYear = 2013`, `CodeName = DOE.determination2013_ASHRAE90.1_STD2013`) to genuinely be
part of the same 2013 set despite the filename.

### Result table (full data: `openubem/outputs/comparisons/open03_load_vintage_ratios.csv`)

| Archetype | Lights W/m² 2013→2022 | ratio | Equip. W/m² 2013→2022 | ratio | People m²/person 2013→2022 | ratio |
|---|---|---|---|---|---|---|
| HighriseApartment | 4.660 → 1.864 | **2.500** | 13.813 → 10.899 | 1.267 | 31.434 → 31.434 | 1.000 ⚠ |
| Hospital | 10.646 → 8.476 | 1.256 | 18.456 → 18.414 | 1.002 | 32.869 → 32.869 | 1.000 ⚠ |
| LargeHotel | 9.756 → 6.325 | 1.542 | 24.872 → 24.813 | 1.002 | 3.854 → 3.854 | 1.000 ⚠ |
| MediumOffice | 10.196 → 5.804 | 1.757 | 8.158 → 7.027 | 1.161 | 18.579 → 18.579 | 1.000 ⚠ |
| MidriseApartment | 4.651 → 1.859 | **2.502** | 9.766 → 8.156 | 1.197 | 31.434 → 31.434 | 1.000 ⚠ |
| Outpatient | 12.198 → 8.590 | 1.420 | 20.209 → 18.570 | 1.088 | 8.017 → 8.017 | 1.000 ⚠ |
| FullServiceRestaurant | 9.833 → 6.034 | 1.630 | 103.148 → 97.095 | 1.062 | 1.777 → 1.777 | 1.000 ⚠ |
| QuickServiceRestaurant | 9.568 → 6.850 | 1.397 | 99.128 → 92.955 | 1.066 | 2.477 → 2.477 | 1.000 ⚠ |
| RetailStandalone | 14.152 → 7.945 | 1.781 | 5.244 → 5.244 | 1.000 ⚠ | 7.231 → 7.231 | 1.000 ⚠ |
| PrimarySchool | 11.656 → 6.910 | 1.687 | 15.972 → 15.887 | 1.005 | 4.040 → 3.857 | 1.047 |
| SmallHotel | 9.285 → 4.809 | 1.931 | 14.109 → 12.292 | 1.148 | 13.375 → 13.375 | 1.000 ⚠ |
| Warehouse | 7.482 → 4.227 | 1.770 | 2.938 → 2.938 | 1.000 ⚠ | 41.148 → 41.148 | 1.000 ⚠ |

**Summary (n=12 each):**
- **Lights (LPD):** median ratio **1.722**, range 1.256–2.502. No archetype at exactly 1.000.
- **Equipment (plug loads):** median ratio **1.064**, range 1.000–1.267.
- **People (occupant density):** median ratio **1.000**, range 1.000–1.047.

### ⚠ Exactly-1.000 flags (plan rule: flag, do not silently accept as a finding)

**11 of 12 People ratios and 2 of 12 Equipment ratios (RetailStandalone, Warehouse) are exactly
1.000.** Per plan instruction these are flagged rather than reported as findings outright. They
were investigated, not just flagged:

- **Spot-checked raw IDF text directly** (bypassing the parser entirely) for Hospital `People` and
  RetailStandalone `ElectricEquipment` between the two files: the numeric fields
  (`100.5885` people, `3065.7123` W) are **byte-identical** in both the 2013 source and the 2022
  baseline. This is not a parser artifact — the source documents themselves carry identical values.
- Plausible domain explanation (not verified against any spec, offered only as context): ASHRAE
  90.1's code-driven revisions between cycles target envelope U-values and lighting power density;
  occupant density and plug-load density are process/occupancy assumptions the DOE prototype
  comparison series appears to hold constant across `STD` vintages for most archetypes. This is
  **not confirmed against any ASHRAE or DOE methodology document** — it is offered as the most
  likely reading of a repeatedly-observed pattern, not a verified fact.
- **This still bounds the numerator error correctly for Lights**, which is the largest single
  end-use difference (median 1.72×) and is never exactly 1.000 for any archetype.

### The 2013-vs-2022 ratio is a proxy, not the fleet's real vintage spread

Stated plainly, per plan instruction: comparing 90.1-2013 to `STD2022` bounds a **9-year** code
gap. It is not the fleet's actual vintage distribution, which the next section shows is far wider
for most buildings.

### Fleet-wide `vintage_standard` distribution

**No fleet-wide vintage column exists in any current, canonical fleet artifact** (searched every
`.csv` in `openubem/outputs/` and the full repo tree for a `vintage`-named column; the `t20`/`t08`
harvest and comparison CSVs used elsewhere in this plan carry `archetype_id`/`num_floors`/EUI
columns but no `vintage_standard`). The one fleet-wide re-derivation found anywhere in the tree is
**not from this task or the current T20 fleet build**:

`scratchpad/e-la-20-investigation/i04/fleet_enriched_all_cells.csv` (7,510 rows, all 12
validation cells, `OpenUBEMUnknown` archetype rows excluded) — generated by
`scratchpad/e-la-20-investigation/i04/run_step2_all_cells.py`, which calls the real production
`openubem.semantic.enrich_semantics()` (which internally calls `resolve_vintage()`,
`openubem/semantic/construction_sets.py:126`) over the same 12 cells' raw OSM fixtures used for
phase-E validation. **Caveats, stated explicitly:** this file is a byproduct of the closed E-LA-20
investigation (dated before the 2026-08-04 storey-matching arc), not regenerated by this task; its
row count (7,510) does not match the current T20 fleet's 8,160 or 7,442, and its code version may
predate later fixes. It is reported because it is the only fleet-wide `vintage_standard`
distribution anywhere in the tree, not because its provenance is fully current.

| `vintage_standard` | n | % of 7,510 |
|---|---|---|
| `DOERefPre1980` | 6,975 | **92.9%** |
| `DOERef1980to2004` | 213 | 2.8% |
| `90.1-2013` | 178 | 2.4% |
| `90.1-2007` | 122 | 1.6% |
| `90.1-2019` | 22 | 0.3% |

**93% of this sample resolves to `DOERefPre1980`** — pre-1980 construction, the oldest of the
vocabulary's tokens. If this distribution is representative of the real published fleet, the
9-year 2013-vs-2022 proxy used above **understates** the real numerator error for the great
majority of buildings: most of the fleet is far older than even 90.1-2013, and `layout_assign`
models 100% of it — regardless of measured vintage — at 2022-code internal-load density.

---

## How-to-test results

**Part (a):** every verdict-relevant claim above carries a `path:line` citation opened and quoted
directly from the file, not inferred from code behaviour. The one contradictory statement found
(results doc §7.2's "not a defect") is reported in full in §5 above, not adjudicated away.

**Part (b):** n = 12 archetypes matched between the two libraries; 0 unmatched (all 12 named files
in the source directory found a mapped `STD2022` baseline). Every People ratio and 2 Equipment
ratios landed at exactly 1.000; both were investigated by direct raw-IDF-text spot-check (bypassing
the parser) rather than accepted at face value, and confirmed as genuine source-file agreement, not
a parsing defect.

---

## Artifacts

- `openubem/outputs/comparisons/open03_load_vintage_ratios.csv` — full per-archetype table (12
  rows), including object counts, unresolved-reference counts, and calculation methods used, for
  reproducibility.
- This report.
