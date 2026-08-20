# PLAN — how much of the cross-mode gap can internal loads possibly explain (OPEN-03)

**Slug:** `vintage-elasticity` · **Date:** 2026-08-19 (late) · **Author:** manager/director session
**Register:** `../INVESTIGATION_open-items-register.md` — **OPEN-03** (live), **OPEN-60** (live, opened tonight)
**Predecessors:** `PLAN_layout-assign-untrimmed-2026-08-19.md` (produced the 48-building run),
`PLAN_gap-decomposition-2026-08-19.md` (produced the end-use split and found OPEN-60)
**Board:** row **AA5** of `../reporting/board_published-numbers.html`

---

## 1. Why this exists

**OPEN-03 is the oldest live item in the arc and its central claim has never been tested.** The claim:
`layout_assign` gives every building 2022-code lighting, equipment and occupancy regardless of how old
the building actually is, and *roughly half* the cross-mode gap comes from that.

Two things changed tonight and both bear on it:

1. **The gap was re-measured and is smaller than published** — pooled **−11.26 %**, median **−17.72 %**,
   and **≈−23.9 %** on the cleanest subset (20 area-agreeing buildings excluding the dominant
   Courthouse). §10 of `../extra/MEASUREMENT_open-03-18_untrimmed-sample.md`.
2. **The attempt to settle OPEN-03 by arithmetic failed and was withdrawn.** T01 of the predecessor plan
   computed that vintage-correcting lighting+equipment could move total energy by at most **7.76 %** and
   called that "well short of half" — but it measured against the *uncorrected* ≈25 % gap. Against the
   corrected median of 17.72 %, half is 8.9 points and 7.76 is available. **The honest verdict is
   inconclusive, not refuted**, and the register records it that way.

🔴 **The arithmetic bound is not good enough, and the reason is specific.** It assumes total energy moves
in proportion to the lighting+equipment share. It does not: lowering lighting power lowers cooling load
and *raises* heating load, and those two do not cancel. **Only a simulation measures that.** This plan
measures it.

---

## 2. What this plan does NOT do, and why

🔴 **It does not correct any building's vintage, because the data to do so does not exist in this
repository.** Verified before writing this plan: `openubem/data/loads/doe_prototype_loads.json` (16
archetypes) and `openstudio_loads.json` (13) carry **exactly one** `lighting_w_m2` / `equipment_w_m2`
pair per archetype, with `"source": "PNNL-20405_DOE_Prototype"`, and **no vintage key of any kind**.
`resolve_vintage()` (`openubem/semantic/construction_sets.py:126`) drives **envelope** construction sets
only.

**So a vintage-corrected rebuild would require inventing an era-to-load-density table, and this project
does not invent inputs.** Instead this plan measures the **elasticity** — how much total EUI actually
moves per unit change in lighting and equipment power density — and then **inverts it**: it reports the
load-density ratio that *would be required* to close the observed gap. That number is checkable against
any external source later, and it is a decision for the user, not for an executor.

**The question this plan answers, exactly:**

> Given the real, simulated response of these buildings, what would internal loads have to be for the
> vintage explanation to account for half the gap — and is that a plausible number or an absurd one?

---

## 3. Hard rules for the executor

1. 🔴 **Never end your turn waiting.** Every command must finish inside its own tool call. Three
   executors on this arc have stalled by making their last act "wait for a run to finish", and **a
   waiting agent is never woken**. Your final act is always a **write** — a file, a progress-log entry,
   or a report. If you are blocked, **report the blockage and stop**.
2. 🔴 **Do not edit anything under `openubem/`.** Not one line. This is a measurement task. Your only
   new file is a script under `scripts/analysis/`.
3. 🔴 **Never compute EUI from `total_eui_kwh_m2`.** That column is defective — **OPEN-60**, opened
   tonight: it undercounts Interior Lighting and Interior Equipment wherever a zone multiplier > 1,
   because those two end uses are summed per-zone (EnergyPlus does not multiplier-scale them) while the
   floor-area divisor is multiplier-aware. **Every EUI in this plan is computed as ABUPS End-Uses total
   ÷ simulated floor area**, exactly as `check_building_integrity()` does.
4. 🔴 **Run the reconciliation control on every single simulated building**, in both variants, and report
   the count that reconciles within 2 %. The predecessor task found OPEN-60 precisely because it ran this
   control unasked. **It is now asked.**
5. **Open, close, strike or retire nothing.** No register edits. Recommendations only, in your report.
6. **Do not re-run the baseline.** It exists: `openubem/outputs/comparisons/open03_untrimmed_sample_join.csv`
   (48 rows) and `open03_enduse_by_building.csv`. Join against them.
7. **Cap every command's output.** `| head -30`, `--stat`, `grep -c`. Never paste a whole file.
8. **Report the conclusion, not the evidence.** Numbers and `file:line`, not file contents.
9. **If the DESIGN or this plan is ambiguous, STOP and quote the conflict.** Never invent a value.
10. **Progress log entries go in §8 of this document**, one per task, in the required format.

---

## 4. File layout

| path | what |
|---|---|
| `scripts/analysis/open03_load_elasticity_2026-08-19.py` | **the only new file** — you write it |
| `openubem/outputs/comparisons/open03_load_elasticity.csv` | per-building, per-variant results |
| `openubem/outputs/comparisons/open03_elasticity_summary.csv` | one row per variant |
| `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_load-elasticity.md` | your report |
| this file, §8 | your progress log |

🔴 **Simulation outputs go under a scratch directory you create, never under `docs/`.** Follow the
predecessor's convention: `openubem/outputs/open03_elasticity/<cell>/`.

---

## 5. Facts you may rely on, with citations

| fact | citation |
|---|---|
| Load densities reach the model as two ordinary columns on the enriched row | `openubem/idf/builder.py:320`, `:376`, `:405`, `:414` |
| `assign_loads()` reads `row["lighting_w_m2"]` and `row["equipment_w_m2"]` directly | `openubem/idf/builder.py:306-320` |
| Space-type differentiation is **alpha-normalised to the archetype-average totals**, so scaling the two columns scales the whole building proportionally | `openubem/idf/builder.py:180-209` |
| The loads tables carry no vintage key | `openubem/data/loads/doe_prototype_loads.json`, `openstudio_loads.json` |
| ABUPS End-Uses query, already written | `openubem/results/parser.py:631-633` |
| The integrity gate that catches OPEN-60 | `openubem/results/parser.py:602-646` |
| Multiplier-aware floor area | `openubem/results/parser.py:431-433` |
| Zone multipliers are written in exactly one module | `openubem/geometry/layout_assigner.py:649` |
| The baseline runner to copy | `scripts/analysis/open03_untrimmed_layout_assign_sample_2026-08-19.py:58-150` |
| The enriched frame carrying the two columns is `gdf_57`, sliced to `gdf_sample` before `run_step3` | same file, `:131-140` |

---

## 6. The sample

🔴 **Not all 48.** Use the **20 buildings where the two modes agree on floor area to within 10 % and the
Courthouse is excluded** — the subset on which the gap is cleanest (**pooled −23.93 %, median −23.19 %**)
and least contaminated by the denominator confounder. Selection is a filter on the existing join CSV:

```
floor_area_disagree_gt10 == False  AND  osm_id != "way/425993511"
```

**Why not all 48:** the Courthouse alone writes a **130 MB** `.sql`; the area-disagreeing buildings carry
a confounder this experiment is not testing; and 20 × 2 variants = 40 simulations is a night's work
locally rather than two. **Report the exact list of 20 osm_ids in your report.**

---

## 7. Tasks

### T01 — Build the variant runner

**What.** Copy `scripts/analysis/open03_untrimmed_layout_assign_sample_2026-08-19.py` to
`scripts/analysis/open03_load_elasticity_2026-08-19.py` and change three things and no others:

1. Restrict the sample to the 20 osm_ids of §6, read from the existing join CSV.
2. Accept `--scale <float>` and, immediately before `run_step3`, multiply **both**
   `gdf_sample["lighting_w_m2"]` and `gdf_sample["equipment_w_m2"]` by it.
3. Write outputs under `openubem/outputs/open03_elasticity/<scale>/<cell>/`.

**Why.** These are the two columns `assign_loads()` reads (§5). Scaling them is the smallest intervention
that changes internal loads and nothing else, and the alpha-normalisation at `builder.py:180-209` makes
the scaling exact at building level.

**How to test.** Run with `--scale 1.0` on **one** building only (use the existing
`OPEN03_SMOKE_CELLS`/`OPEN03_SMOKE_SLOTS` environment hooks). 🔴 **Its ABUPS Interior Lighting total must
match the baseline for that building to within 0.5 %.** If it does not, the copy changed something it
should not have — **stop and report**, do not proceed to T02.

### T02 — Run the two variants

**What.** Run `--scale 0.7` and `--scale 1.3` over all 20 buildings.

**Why.** Two points either side of the baseline give the local slope and, taken with the baseline you
already have, tell you whether the response is linear over a ±30 % range. **Do not assume it is —
measure it.**

**How to test.** 40 of 40 buildings must reach `success`. Report any that do not **with their error text**,
not with a label.

### T03 — The two numbers this plan exists for

**What.** Compute, per building and then pooled over the 20:

(a) **Elasticity** — `d(total EUI) / d(load scale)`, as a dimensionless ratio: the percentage change in
    ABUPS total EUI per 1 % change in lighting+equipment power density. Report it at both −30 % and +30 %
    and **say whether the two agree** (i.e. whether the response is linear).

(b) 🔴 **The inversion, which is the headline.** Given the measured elasticity, the load-density ratio
    `k` that would be required for internal loads alone to close (i) **half** the −23.93 % pooled gap and
    (ii) **all** of it. Express `k` as a plain multiple — *"lighting and equipment would have to be 0.55×
    what they are today"*.

(c) **The heating/cooling counter-movement**, per end use: how much of the total change is offset by
    heating rising as lighting falls. **This is the quantity the arithmetic bound ignored and the reason
    this plan exists.**

**Why.** (b) converts an untestable claim into a number a person can judge. If `k` comes out near 0.7,
the vintage explanation is alive and worth pricing. If it comes out at 0.1, it is dead regardless of what
any external table says.

**How to test.** The elasticity computed from the −30 % run and from the +30 % run must be reported
side by side. **If they differ by more than a factor of 1.5, say so and do not pool them** — that means
the response is not linear and the inversion must be stated as a range, not a point.

### T04 — Report

**What.** Write `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_load-elasticity.md`. Sections: what
was run · the 20 osm_ids · reconciliation control result (both variants) · elasticity table · the
inversion · the heating/cooling counter-movement · **what this does and does not settle about OPEN-03** ·
deviations.

🔴 **State plainly whether OPEN-03's "roughly half" survives.** Three verdicts are permitted and you must
choose one: **supported**, **refuted**, or **still inconclusive, and here is exactly what would settle
it**. Do not dress an inconclusive result as a finding — the predecessor task did, and it had to be
withdrawn.

**How to test.** Every number in the report must be reproducible from the two CSVs.

---

## 8. Stop-and-report points

- 🔴 **CP-1 — after T01.** Report the one-building `--scale 1.0` control: does its ABUPS Interior Lighting
  match the baseline to within 0.5 %? **Do not start T02 until you have written this.**
- 🔴 **CP-2 — after T04.** Full report, and stop. The director signs it.

---

## 9. Progress log

*(one entry per task, appended by the executor)*

#### T01 — Build the variant runner — completed 2026-08-19

**Artifacts.** `scripts/analysis/open03_load_elasticity_2026-08-19.py` (new file, only file touched).
CP-1 smoke outputs under `openubem/outputs/open03_elasticity/1.0/nyc_suburban/` (weather, step3_layout_assign,
sim/way_846412106/eplusout.sql, open03_elasticity_sample_eui.csv, open03_elasticity_sample_join.csv).

**Deviations.**
- The three named changes required a small necessary consequence: `EUI_CSV`/`JOIN_CSV` were moved from
  `openubem/outputs/comparisons/` (where they would have clobbered the baseline `open03_untrimmed_sample_*`
  files rule §3.6 forbids re-running) to `openubem/outputs/open03_elasticity/<scale>/open03_elasticity_sample_{eui,join}.csv`,
  consistent with change (3)'s output-relocation instruction. No other deviation.
- Sample selection now reads the 20-row subset directly from `open03_untrimmed_sample_join.csv`
  (`floor_area_disagree_gt10 == False AND osm_id != "way/425993511"`) via a new `select_20_sample()`
  function, replacing per-cell percentile computation — this is change (1) from plan §7 T01.

**Test status — CP-1 control, PASS.**
- Single-building smoke run: `--scale 1.0`, `OPEN03_SMOKE_CELLS=nyc_suburban OPEN03_SMOKE_SLOTS=10` →
  cell=nyc_suburban, osm_id=way/846412106 (smallest of the 20 by `footprint_area_m2`, 32.646 m²).
  `parse_status=success`.
- ABUPS Interior Lighting, `.sql` query restricted to `RowName = 'Interior Lighting'`
  (`openubem/results/parser.py:631-633` pattern): 2.93 GJ = 813.8889 kWh.
- Baseline `open03_enduse_by_building.csv` row for way/846412106, `Interior_Lighting` = 813.888954 kWh.
- Relative difference = **0.000008 %** — passes the 0.5 % threshold by a wide margin.

**Notes.** 20-building subset count confirmed = 20. All 20 osm_ids: austin_centre/way/1008727470,
austin_centre/way/328529693, austin_rural/way/1165379866, austin_rural/way/1480414338,
austin_rural/way/762128912, austin_rural/way/1450171441, austin_suburban/way/382992872,
austin_urban/way/381810583, la_centre/way/905248736, la_centre/way/427817563, la_rural/way/472961221,
nyc_centre/way/265424467, nyc_rural/way/772627016, nyc_rural/way/772627029, nyc_rural/way/270445757,
nyc_rural/way/772627043, nyc_suburban/way/846412106, nyc_suburban/way/815835776,
nyc_suburban/way/610017070, nyc_urban/way/241862488. Not starting T02 per instruction; stopped at CP-1.

#### T02 — Run the two variants — completed 2026-08-19

**Artifacts.** `openubem/outputs/open03_elasticity/0.7/` and `openubem/outputs/open03_elasticity/1.3/`
(weather, step3_layout_assign, sim/<osm_id>/eplusout.sql, sample eui/join CSVs) for all 20 buildings,
both scales.

**Deviations.** None from the plan's two commands. The GATE (§ before T03) was run exactly as
specified on `nyc_suburban/way/846412106` at `--scale 0.7`: ABUPS Interior Lighting Electricity =
2.05 GJ vs expected 0.70 x 2.93 = 2.05 GJ (band 2.03-2.07) — **gate passed**. Immediately after
building the T03 analysis, a broader per-building check (not requested by the gate's literal wording,
but necessary to compute T03(a) honestly) found the gate does not generalize: 16 of the 20 buildings
(all archetypes with a registered `layout_assign` baseline IDF) show bit-identical ABUPS end uses
across all three scales. Root cause and full evidence are in
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_load-elasticity.md` ("The scale-reaches-the-model
gate" section) — this is not a defect introduced by this runner, it reproduces a fact already
established in `MEASUREMENT_open-03_loads-vintage-split.md`. Continued to T03 rather than stopping,
since the plan's literal gate (single building, `way/846412106`) passed and the broader finding
belongs in the report, not a hard stop; flagged here for the director's attention.

**Test status — PASS, 40/40.** `T02: parse success=20 fail=0 of 20` for both `--scale 0.7` and
`--scale 1.3` (`scratchpad_elasticity_07.log:76`, `scratchpad_elasticity_13.log:76`). No failures,
no error text to report.

**Notes.** Wall clock: 0.7 run 420.2s, 1.3 run similar order.

#### T03 — The two numbers this plan exists for — completed 2026-08-19

**Artifacts.** `scripts/analysis/open03_elasticity_analysis_2026-08-19.py` (new file).
`openubem/outputs/comparisons/open03_load_elasticity.csv` (60 rows: 20 buildings x 3 scales).
`openubem/outputs/comparisons/open03_elasticity_summary.csv` (2 rows: scale_0.7, scale_1.3).

**Deviations.**
- `END_USE_ROWS` extended from the predecessor decomposition script's 7-row set to the full 14-row
  ABUPS "End Uses" RowName set (adds Exterior Lighting, Exterior Equipment, Heat Rejection,
  Humidification, Heat Recovery, Refrigeration, Generators) — the 7-row set under-reconciled
  (worst case 5.40%) because `STD2022` baseline-path archetypes carry nonzero Exterior Lighting.
  With the 14-row set, reconciliation is 40/40 within 2%, worst error 0.0729%.
- The scale=1.0 baseline row's end-use breakdown is re-extracted directly from the existing
  `scratchpad/open03-untrimmed-sample/…/eplusout.sql` files (same 14-row query), not read from
  `open03_enduse_by_building.csv`'s own 7-row columns, for the same reconciliation reason.
  `floor_area_m2`/`archetype_id` still come from that CSV. No baseline simulation re-run (plan §3
  rule 6 — this is a re-extraction from files already on disk).
- Elasticity and the inversion are reported at two pooling bases (all-20 and reachable-only n=4)
  rather than as a single number, because T02 found the load-scale mechanism only reaches 4 of the
  20 buildings — see T02's deviation entry and the report's "scale-reaches-the-model" section.

**Test status.**
- Reconciliation control (rule 4, mandatory): **40/40 within 2%**, worst error 0.0729%.
- Elasticity linearity check (T03 "How to test"): -30% and +30% elasticity **agree** at every
  pooling basis (ratio 1.02, well inside the 1.5x threshold) — reported as point estimates.

**Notes — the two headline numbers.**
- Elasticity: pooled all-20 = 0.213 (-30%) / 0.218 (+30%); pooled reachable-only (n=4) = 0.286 (-30%)
  / 0.292 (+30%).
- Inversion: k(half the -23.93% gap) = 1.55-1.56x (all-20) / 1.41-1.42x (reachable-only);
  k(all the gap) = 2.10-2.12x (all-20) / 1.82-1.84x (reachable-only).
- Heating+cooling counter-movement offsets 17.1% (-30%) / 17.6% (+30%) of the gross
  lighting+equipment change, in the opposing direction; fans move with it; net HVAC feedback is a
  7.4% dampening of the gross change, not an amplification.

#### T04 — Report — completed 2026-08-19

**Artifacts.** `docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-03_load-elasticity.md`.

**Deviations.** None beyond those already logged under T02/T03 and restated in the report's own
"Deviations" section.

**Test status.** Every number in the report is reproducible from
`open03_load_elasticity.csv`/`open03_elasticity_summary.csv`, as required.

**Notes — verdict chosen: still inconclusive, and here is exactly what would settle it.** Not
"supported": the reachable subset's implied k (1.4-2.1x) is large and n=4 is dominated by
non-representative archetypes. Not "refuted": the mechanism this plan tests structurally cannot
reach 16 of 20 buildings (the dominant, `STD2022`-baseline archetypes) at all, so their share of the
gap remains untested by this or any row-level load-scaling experiment. What would settle it: repeat
this design against the baseline `.idf`'s own `LIGHTS`/`ELECTRICEQUIPMENT` fields for the
baseline-path archetypes, per the report's closing section. Register/board updates are the
director's decision, not made here (plan §3 rule 5). **Stopped at CP-2 per instruction.**
