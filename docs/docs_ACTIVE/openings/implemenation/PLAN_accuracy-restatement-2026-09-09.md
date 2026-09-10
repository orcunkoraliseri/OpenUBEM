# PLAN — accuracy restatement of the fleet figure, 2026-09-09

**Slug:** `accuracy-restatement-2026-09-09`
**Date opened:** 2026-09-09
**Register:** `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` (14 live, next free `OPEN-65`)
**Predecessor (ARCHIVED 2026-09-09, citations swept):**
`docs/docs_ACTIVE/openings/implemenation/previous/PLAN_open61-dh-remedy-2026-08-22.md`
**Opened on:** the user's four rulings of 2026-09-09 (§4) plus *"lets include inside the plan"* /
*"of course, lets go"*.

---

## 1. Why this plan exists

Two things happened on 2026-09-09 and together they change what the open list means.

**First, the user ruled on the four questions that had blocked every remaining item**, and one of
those rulings removes the constraint that shaped every plan since 2026-08-19: *"we are not hurry, our
focus is accuracy, so if we need to re-simulate lets do it. i am okay with that."* **Re-simulation of
the fleet is authorised.** Every previous arc was written around the assumption that it was not.

**Second, the director checked the code state of the three defects that make the published figure too
low, and two of them are already fixed** (§5 F1–F6). The register rows for OPEN-56 and OPEN-60 both
still say *"remedy not proposed / not authorised"*; **both statements are false as of today**. The
fixes were written during the European arc and never fed back into the register.

🔴 **What that means for the published number.** `153.8231 kWh/m² pooled over 8,153` was produced
by **run 4**, which predates all of it.
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.
The fleet has never been simulated with the zone-volume fix,
never parsed with the multiplier fix, never built with the imputation tiers connected, and the
district-heating energy fix (OPEN-61 T01/T01b) has never been applied to the **adopted** population.
**The one arithmetic CP-2 could not do — restate the adopted figure rather than the census
rebuild — becomes possible for the first time in this plan.**

**This plan therefore does one thing: it puts every landed fix and every ruled decision into one
rebuild, re-simulates the fleet, and restates the published figure on its own population.**

---

## 2. Hard rules for the executor

1. **Execute this plan top-to-bottom. Do not propose alternatives.** If this plan or the DESIGN is
   ambiguous, **STOP and quote the conflict.** Never invent a value that is not in §5.
2. **Before debugging ANY error, search `docs/docs_EXPLANATION/OpenUBEM_debug_References.md`.
   After solving ANY error, register it there** in house format before closing the task.
3. 🔴 **No compute on the Speed login node.** Login = `mkdir`, `scp`, `tar`, `squeue`, `sacct`
   only. Every simulation goes out as **one `sbatch --array=…%32`**, fire-and-forget, `--time=7-00:00:00`
   minimum. **Never one job per building, never a sequential loop.** The login shell is tcsh — wrap
   every remote command in `bash -lc`.
4. 🔴 **A task that has written nothing for ~10 minutes is dead, not slow — but confirm with
   `sstat -a -j <jobid>_<idx> -o JobID,AveCPU,MaxRSS` BEFORE cancelling.** If `AveCPU` still tracks
   `Elapsed`, it is alive in a long sizing phase and must not be touched.
5. **Never estimate a finish time by feel.** `sacct -j <id> -n -X -o Elapsed,State` over the completed
   tasks, mean × remaining ÷ 32. State the measurement.
6. **Nothing published moves until CP-4.** `153.8231 kWh/m² pooled over 8,153` stays the adopted
   figure through T01–T07, and every intermediate figure this plan produces is a **candidate**.
   ⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.
7. **Never difference two figures computed on different populations.** The whole of CP-2's 2026-08-22
   reasoning rests on this; it still holds.
8. Never edit root `main.py`, OVERVIEW or DESIGN docs. No `.py` under `docs/`. Figures →
   `openubem/outputs/` flat. **Git is handled externally — never commit.**
9. **Do not regenerate a delivered artifact** without the ruling that authorises it. The four
   European districts' side-cars and EUIs are delivered and are **out of scope** (§5 F5, F6).

---

## 3. File layout

| What | Where |
|---|---|
| This plan | `docs/docs_ACTIVE/openings/implemenation/PLAN_accuracy-restatement-2026-09-09.md` |
| Register | `docs/docs_ACTIVE/openings/INVESTIGATION_open-items-register-II.md` |
| Debug reference | `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` |
| Production code | `openubem/` — parser, carbon, config, imputation router |
| Analysis scripts | `scripts/analysis/` |
| Measurements this plan produces | `docs/docs_ACTIVE/openings/extra/` |
| Figures | `openubem/outputs/` (flat) |

---

## 4. Dependency decisions (pinned) — the user's four rulings, 2026-09-09

These are the user's own answers, taken today. **They are pinned: no task re-opens them.**

**D-A — OPEN-17, the imputation tiers: CONNECT THE ROUTER AND SWITCH IT ON.** The user was offered
the low-risk shape (connect it but leave it off, so the 15 dormant tests wake and no number moves) and
**chose the accurate shape instead**: *"you recommend do it later, but we are not hurry, our focus is
accuracy, so if we need to re-simulate lets do it. i am okay with that."* 🔴 **This is the ruling
that authorises the whole rebuild.** It changes the inputs of every building, so every published
number has to be re-derived — which is now explicitly accepted rather than avoided.

**D-B — OPEN-63, carbon and district heating: FIND ONE PUBLISHED VALUE AND USE IT.** A single
district-heating emission factor, taken from the literature, cited in the config beside the existing
gas factor, applied everywhere. ⚠️ **The value is not invented and not chosen by an executor** —
T05 gathers candidates with full citations and the **director** picks one.
🟢 **Discharged 2026-09-09: `0.226 kgCO2/kWh`, US EPA *GHG Emission Factors Hub* (Jan 2025 ed.),
table "Steam and Heat"** — three candidates gathered, one chosen, reasoning recorded in §8 under
*D-B resolved*.

**D-C — OPEN-64, district heating outside hot water: FIX THE CODE AND RAISE THE REFERENCE VALUES.**
Read all fourteen ABUPS district-heating rows into their matching end-use columns instead of one, and
move the three golden expected values upward, **recording old and new side by side**. The trap being
removed is that the fixtures currently certify the defect.

**D-D — OPEN-61: STAYS OPEN.** The director proposed closing it; the user ruled **keep it open**,
so the pending swap stays visible on the open list. 🟢 **This plan is what discharges it** — the
restatement it has been waiting for happens at T08.

**D-E — OPEN-17, what "switch the imputation on" is allowed to replace: RULED by the user
2026-09-09 — keep the deterministic ladder** (raised by the director 2026-09-09, at T04). T04's step 2 turned out to be un-executable as written,
and the reason changes what the task is, so it is a ruling and not a deviation. Three measured facts,
each verified by the director and not taken from the executor that reported the block:

1. The global switch that step names is **contractually frozen**. `docs/docs_DONE/INPUTS/imputation/
   implementation/IMPLEMENTATION_phaseC_ml_imputer.md:276,299,399` says **"NEVER touch
   `IMPUTE_ENABLED_TIERS`"**, and `tests/test_draw_methods.py:66-69,577-579` are live, unskipped tests
   asserting the tuple stays `("fusion","spatial","statistical")` forever. That design's own escalation
   chain (`:326`) is `per_input_tiers[attr]` → `enabled_tiers` → the global tuple: the draw tier is
   meant to be enabled **per call**, never globally. This half is settled and needs no ruling.
2. The router is **not on the fleet build path at all**. `impute_missing` has no production caller —
   only `openubem/validation/mask_recover.py:330,338` and two `scripts/analysis/` one-offs. The single
   production import of that module is `impute_column` (`openubem/semantic/construction_sets.py:415`),
   a one-series KDE gap-fill for envelope U-values that never reaches the tier router.
3. 🔴 **F10 is true of the router and false of the build, and this plan inherited the confusion.**
   "Every other target is filled by nothing at all" describes the router's coverage. On the production
   path `levels` **is** filled, by a signed-off deterministic ladder in
   `openubem/semantic/building_classifier.py:145-155` — observed value, else `HEURISTIC_HEIGHT`
   (height ÷ floor-to-floor), else `GROUPMEDIAN_LEVELS_MED` (use-class median), else
   `LEVELS_DEFAULT_LOW` = 1 — reached from `openubem/idf/builder.py:158`.

**So the question is not "fill a gap" but "replace an estimator".** Enabling the draw tier for `levels`
would substitute a random draw for that ladder across thousands of buildings, moving storey count, then
floor area, then the denominator of every EUI in the restatement. D-A authorised the **cost** of a full
re-simulation; it did not authorise swapping a deterministic estimator for a sampled one. **This must be
answered before T06 rebuilds, or the fleet is simulated twice.**

🟢 **RULING, user, 2026-09-09:** the director recommended keeping the fixed floor rule and the user
answered *"ok, i turst your judgement. that is brilliant idea. progress as you suggest."* — so the
deterministic ladder at `openubem/semantic/building_classifier.py:145-155` **stays**, and the draw tier is
**not** enabled for `levels` or for any other target already covered by a signed-off estimator on the
production build path. The user's own words earlier in the same turn, *"if it is possible we can apply
imputation"*, are a permission and not an instruction: it is conditional, and the condition fails here,
because the only place imputation could be applied is a slot that is already filled deterministically.

Consequences, all now fixed:
- **T04 is closed at step 1.** The two opt-in, empty config dicts and the `+195` lines of dormant draw-tier
  machinery in `openubem/semantic/imputation.py` stay in the tree, reachable only per call. Step 2
  (extend `IMPUTE_ENABLED_TIERS`) is **void**, and the fill-count deliverable is **withdrawn**, not deferred.
- **T06 rebuilds on the current estimator.** No storey counts move, so no floor areas move, so no EUI
  denominator moves. The restatement is a pure district-heating factor change, exactly as T06 was amended.
- **The fleet is simulated once.** That was the reason this ruling was blocking.
- **F10 stands corrected** in the form given above: it is true of the router and false of the build.

---

## 5. Facts with citations — all director-verified on 2026-09-09

**F1 — OPEN-56 is already fixed in code, and the register row saying otherwise is stale.**
`write_zone_volumes()` is defined at `openubem/idf/builder.py:217` and called unconditionally from the
per-building orchestrator at `openubem/idf/builder.py:663`. It writes `Zone.Volume` explicitly as
floor area × ceiling height instead of leaving EnergyPlus to compute it, which is exactly the third
remedy shape the register recorded as *"neither applied — the remedy ruling is still owed to the
user"*. It also has a regression test, `tests/test_eu_zone_volume_written.py`. Introduced in commit
`8d816be0` during the European arc.

**F2 — and it demonstrably works, on preserved output rather than on the code reading.** Across the
**81** preserved EnergyPlus working directories of the Bologna recut
(`openubem/outputs/eu_evidence/EU-11/IT-BOL-GALVANI2_recut_2026-09-08/local_out/*/eplusout.err`),
the string `Indicated Zone Volume` appears **0 times**. The same string appears on **8,160 / 8,160**
buildings of run 4. **The defect is real, the fix is real, and the published fleet has never had it.**

**F3 — what OPEN-56 still owes is therefore a RE-RUN, not a fix.** Measured cost of the fix, from the
69-building controlled experiment of 2026-08-18: **mean +0.98 %, median +0.84 %, 65/69 same
direction, ≈ +1.0 kWh/m² per building**, a fixed per-building offset (the per-zone model was
refuted, corr 0.113).

**F4 — OPEN-60 is also already fixed and wired.** `parse_eio_zone_multipliers()` is defined at
`openubem/results/parser.py:416`, called at `openubem/results/parser.py:910`, and consumed by
`_compute_eui()` (signature `:493`, contract `:534-540`), which scales each per-zone Interior
Lighting / Interior Equipment sum by that zone's own multiplier so the numerator matches the
multiplier-aware denominator. Tests: `tests/test_parser_open60_multiplier.py`. **The register row's
*"remedy not proposed and not authorised"* is stale.** What OPEN-60 owes is a **re-parse**.

**F5 — OPEN-60's exposure on the European districts is ZERO, and this is a census, not a sample.**
All **4,171** recut IDFs were read (`ES 1,187 · FR 529 · GB 1,240 · IT 1,215` files carrying a
`Multiplier` field): **0 objects carry a value other than 1.** The four delivered European EUIs are
untouched by OPEN-60.

**F6 — OPEN-64's exposure on the European districts is ZERO on the evidence available.** All **81**
preserved Bologna `eplusout.sql` were queried for `AnnualBuildingUtilityPerformanceSummary / End Uses`
cells in any `District*` column: **no row is greater than zero in any file.** These buildings carry no
district heating at all. ⚠️ **This is a sample of 81, not a census of 4,171** — the remaining
buildings' `.sql` are not preserved locally. It is enough to say no European number is *known* to
move; it is not enough to say none *can*.

**F7 — OPEN-62 is genuinely still open, and it is the only one of the three that is.** The omission is
documented but not repaired: `scripts/analysis/open03_storey_census_2026-08-20.py:138` states the
mechanism and `:299` only raises the `layout_assign_z_origin_collapse_risk` flag;
`scripts/analysis/open03_envelope_decomposition_2026-08-20.py:244` carries the same reading. The
**correct** handling already exists in production code and can be copied verbatim:
`openubem/geometry/layout_assigner.py:471` reads each zone's `Z_Origin` and `:491-493` adds it back
into every vertex when the coordinate system is `RELATIVE`. Scope: **2,983 of 8,160 buildings
(36.6 %)**, six archetypes, **one CSV column** — no EUI depends on it.

**F8 — the carbon gap, unchanged since 2026-08-22.** `openubem/results/carbon.py:106` reads
`gwp_dhw = dhw_gas_eui * f_gas + dhw_elec_eui * f_elec` — the two fuel-specific columns only, never
the combined `dhw_eui_kwh_m2`. `openubem/config.py:83` carries `GWP_NATURAL_GAS_KGCO2_KWH = 0.181`
(*Iseri et al., 2025*) and **no district-heating factor of any kind**; electricity is per-state via
`get_elec_factor(state)`.

**F9 — the imputation router, as it stands today.** `openubem/config.py:100` sets
`IMPUTE_ENABLED_TIERS = ("fusion", "spatial", "statistical")`. The `ml` tier is deliberately excluded
by the comment at `:103-104` (*"stays OUT … until CP-3 passes + user sign-off"*) and is reachable only
via `ImputeConfig.per_input_tiers`. The six variance-preserving draw-tier imputers have **no router
hook in any commit**. **15 of the suite's 55 skips are OPEN-17's** and are the only skips in the suite
waiting on a live decision.

**F10 — what the imputation machinery actually covers today, measured on all 8,160 buildings.** One
target out of seven. `year_built` is filled **5,913 of 5,913 (100 %)**
(`VINTAGE_NAN_PERMISSIVE_DEFAULT` 4,256 · `GROUPMODE_MED` 1,521 · `HOTDECK_NEIGHBOR_HIGH` 90 ·
`HOTDECK_NEIGHBOR_MED` 46). **Every other target is filled by nothing at all** — `levels` 7,719
missing, `function_tag` 7,741, `postcode` 4,183, and three more.

**F11 — the population problem CP-2 could not solve.** `153.8231` is run 4 over **8,153**;
`152.3011 → 171.7718` is the census rebuild over **8,144**. They are different populations and were
never differenceable. **A rebuild that carries every fix produces one population and one figure**, and
that is the whole point of T06–T08.
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.

---

## 6. Tasks

### T01 — Confirm the two "already fixed" claims at the artifact, not in the source *(executor, read-only)*

**What.** Prove F1/F2 and F4 by building and running, not by reading code.

**Why.** §5 F1 and F4 were established by the director from source and from preserved European output.
Before an 8,160-building campaign is launched on the strength of them, they must be shown to hold on a
**North American** building built by today's `auto` path. A control that re-reads the suspect source
cannot exonerate it — the same lesson as OPEN-62's control C9.

**How.**
1. Pick **3 buildings** from run 4 that carried the `Indicated Zone Volume <= 0.0` warning, one each
   from three different cells. Rebuild their IDFs with today's code, `resolution_mode="auto"`.
2. Assert every `ZONE` object in each rebuilt IDF has a **positive, non-stub** `Volume` field, and
   that it equals floor area × ceiling height to within 0.5 %.
3. Run all three through EnergyPlus **locally** (3 buildings — no cluster needed) and grep each
   `eplusout.err` for `Indicated Zone Volume`.
4. Parse all three with today's parser and record the EUI beside their run-4 EUI.

**How to test.** 3/3 rebuilt IDFs carry positive `Volume`; 3/3 `.err` are free of the warning; the EUI
delta is reported per building. 🔴 **If any of the three still warns, STOP and report — the whole
plan's premise is wrong.** Do not proceed to T06.

---

### T02 — OPEN-62: add `Z_Origin` to the two analysis parsers *(executor, analysis code)*

**What.** Make `parse_idf()` in `scripts/analysis/open03_envelope_decomposition_2026-08-20.py` add each
zone's `Z_Origin` to its wall vertices when `GlobalGeometryRules` coordinate system is `Relative`, and
carry the same through `scripts/analysis/open03_storey_census_2026-08-20.py`.

**Why.** It is the only one of the three storey/volume defects that is genuinely unfixed (F7), and the
correct four lines already exist in production code.

**How.** Copy the handling at `openubem/geometry/layout_assigner.py:471` and `:491-493` — do **not**
invent a second way of doing it. Re-run the storey census over all 8,160 buildings.

**How to test.** 🔴 **Control C9 will change, and that is expected, not a failure.** C9 compares the
census against the predecessor's 48-building sample and passes 96/96 *because both used the same naive
method*. Report C9's new value **and** the old one, and state the count of the six flagged archetypes
whose `layout_assign_storey_count` moves. The `layout_assign_z_origin_collapse_risk` column should
become all-`False` by construction — say so explicitly if it does not.

---

### T03 — OPEN-64: read all fourteen district-heating rows *(executor, production code)*

**What.** Fold **each** ABUPS `District Heating` end-use row into its own end-use column, instead of
folding only `Water Systems`.

**Why.** Ruling D-C. Today thirteen of the fourteen rows are read by no code path anywhere in
`openubem/`, and no meter covers them (0 of 8,152 buildings carry a district-heating meter).

**How.**
1. Extend the ABUPS read so every one of the fourteen rows lands in its matching column (Heating,
   Cooling, Interior Lighting, Exterior Lighting, Interior Equipment, Exterior Equipment, Fans, Pumps,
   Heat Rejection, Humidification, Heat Recovery, Water Systems, Refrigeration, Generators).
2. 🔴 **Raise the three golden expected values and record old → new in the progress log**, one line
   per fixture: `r1_single_zone` (+105.0456 kWh/m² of district-heated space heating),
   `r2_one_zone_per_floor` (+78.8878), `r6_perimeter_core` (+101.6580).
3. **Do not touch any golden `.sql`.** Only the expected values move.

**How to test.** Full suite, foreground. Baseline is **1,937 passed / 55 skipped / 0 failed**. Report
the new triple and name every test whose expectation changed. **Fleet exposure is zero buildings**, so
no fleet number may move at this task — say so from measurement, not from assumption.

---

### T04 — OPEN-17: connect the imputation router and switch it on *(executor, production code)*

**What.** Build the router hook the draw tier has never had, and enable the tiers for the six targets
that are filled by nothing today.

**Why.** Ruling D-A. This is the task the user accepted a full re-simulation for.

**How.**
1. Add the router hook so the six variance-preserving draw-tier imputers are reachable from the
   production path — not only from the validation entry point.
2. Extend `IMPUTE_ENABLED_TIERS` (`openubem/config.py:100`) as the design requires for the six unfilled
   targets. 🔴 **The `ml` tier stays OUT** — its exclusion at `:103-104` is a separate, still-live
   sign-off and this plan does not lift it.
3. The 15 dormant tests unskip themselves once the hook exists. **Run them and report each by name.**

**How to test.** Suite green with **15 fewer skips** and 15 more passes than T03's baseline; if the
arithmetic does not close exactly, name every test that moved in either direction. Then report, for all
8,160 buildings, the **before/after fill count per target** against F10's table.

🛑 **STOP at CP-1 after this task. Nothing is rebuilt or simulated until CP-1 is signed.**

---

### T05 — OPEN-63: gather candidate district-heating emission factors *(executor, literature only)*

**What.** Find published district-heating CO₂ emission factors and present them for the director to
choose from. **Do not pick one. Do not write one into the config.**

**Why.** Ruling D-B chose "find one published value and use it" — but the choice of value is a
literature decision, and no session in this project invents a number.

**How.** For each candidate report: the value in kgCO₂/kWh, the exact source (author, year, title,
page or table), the geography it applies to, and whether it is a delivered-heat or primary-energy
basis. **Minimum three candidates.** Note explicitly whether a US-applicable value exists, since the
fleet is North American while the factor literature is largely European.

**How to test.** A table of ≥ 3 candidates, each with a citation a reader can check. **No code
changed by this task.**

---

### T06 — Apply the ruled factor, then rebuild the fleet inputs and IDFs *(executor, production code + compute)*

**What.** Write the director-chosen factor into `openubem/config.py` beside `GWP_NATURAL_GAS_KGCO2_KWH`,
apply it to **every** end use that can carry district heat — not the DHW term alone — then rebuild every
input and every IDF for all 8,160 buildings.

🔴 **Amended by the director 2026-09-09, after T03 landed.** This task was written when the only
district-heating column was DHW, so it said "`openubem/results/carbon.py:106`'s DHW term". T03 widened
the fold to all fourteen ABUPS rows and that instruction is now **incomplete**. As the code stands after
T03, district-heat energy is charged at the wrong factor or at none:

- **Seven mixed columns** — `heating`, `cooling`, `fans`, `pumps`, `refrigeration`, `lighting`,
  `equipment` (`openubem/results/parser.py:624-651`) — add district heat straight into a column that
  `openubem/results/carbon.py:101-109` then multiplies by the **gas** factor (heating) or the
  **electricity** factor (the other six).
- **Six pure-district columns** — `exterior_lighting`, `exterior_equipment`, `heat_rejection`,
  `humidification`, `heat_recovery`, `generators` (`:657-662`) — enter `total_eui_kwh_m2` but are
  multiplied into **no** `gwp_*` term at all, so their carbon is silently zero.
- **`dhw_district_eui_kwh_m2`** (`:645`) already carries its provenance and is likewise charged at
  nothing; its own comment says so.

The fix, therefore: **carry a `*_district_eui_kwh_m2` provenance column for each of the fourteen rows**
in `_DISTRICT_HEATING_ROWS` (`openubem/results/parser.py:66-81`) — six exist already as pure-district
columns, `dhw_district` exists, seven must be added for the mixed ones — and in `carbon.py` multiply
every district column by the new factor while the gas and electricity terms take only their
**non-district** part. `total_eui_kwh_m2` must not change by a single digit: the provenance columns
split the existing columns, they do not add to them. Expect the R1/R2/R6 `gwp_*` goldens T03 raised to
move again, and report each one old → new; the `*_eui_*` goldens must **not** move.

**Why.** One rebuild carries all of it: the zone volumes (F1), the connected imputation router (T04),
and the district-heating carbon factor. Building it twice would produce two populations again — the
exact error F11 describes.

**How.** Rebuild inputs first, then IDFs. 🔴 **Building 8,160 IDFs is multi-building work: it goes
out in parallel, never in a `for` loop.** Record the row count at every stage; a stage that loses
buildings must say which and why before the next stage starts.

**How to test.** Row counts reported per stage against 8,160. Every IDF carries a positive
`Zone.Volume`. The per-target fill counts match T04's report. On the carbon change: the R1/R2/R6
`total_eui_kwh_m2` and every `*_eui_kwh_m2` golden are **byte-identical** to their T03 values, the
`gwp_*` goldens that move are each reported old → new, and the suite closes against T04's triple with
no new failures. 🔴 Fleet exposure to district heating is **zero buildings of 8,152** (T03, measured),
so **no fleet EUI and no fleet carbon number may move at this task** — say so from the rebuilt
manifest, not from assumption.

🛑 **STOP at CP-2 before any simulation is submitted.**

---

### T07 — Re-simulate the fleet on Speed *(executor, cluster)*

**What.** One `sbatch --array=0-8159%32`, `--time=7-00:00:00`, fire-and-forget.

**Why.** The published figure cannot be restated on its own population without it (F11).

**How.** Stage inputs with `scp`/`tar` from the login node — **no compute there**. State the total case
count and the parallel width **before** submitting. Supplement with the local 20-process pool only if
the case count justifies it. Then leave it alone: poll no more often than every 30 minutes, and read
`sacct` rather than guessing.

**How to test.** `squeue -u o_iseri` empty **and** the completed-task count equal to the submitted
count. Any straggler gets the `sstat` `AveCPU`-vs-`Elapsed` check in §2 rule 4 **before** it is
cancelled. Report the mean per-task elapsed from `sacct`.

🛑 **STOP at CP-3 when the array is complete.**

---

### T08 — Harvest, re-parse, and produce the restated figure *(executor, arithmetic)*

**What.** Parse every result with today's parser and produce the new pooled fleet EUI **and its
population count**, plus the carbon total on the same population.

**Why.** This is the arithmetic CP-2 could not do on 2026-08-22, and it is what discharges OPEN-61
(ruling D-D keeps the item open precisely until this lands).

**How.** Report the pooled figure **always with its n**. Produce, as separate lines, the movement
attributable to each landed fix where it can be separated, and say plainly where it cannot.
🔴 **Do not difference the new figure against 153.8231 without stating both populations.** If the
populations differ, the difference is not a correction — it is two numbers.
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.

**How to test.** Pooled EUI + n; carbon total + n; the count of buildings that failed to simulate, with
the reason class for each. Compare the **population** against 8,153 before comparing any value.
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.

🛑 **STOP at CP-4. The published figure does not move until CP-4 is signed.**

---

### T09 — Sweep every document that quotes the old figure *(director)*

**What.** Once CP-4 is signed, find every place `153.8231` (or `8,153`) is published and attach the
supersession marker; update the register rows for OPEN-56, OPEN-60, OPEN-61, OPEN-62, OPEN-63 and
OPEN-64; update the board and the two memory files.
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.

**Why.** *A restated number invalidates every artifact downstream of its source.* An arc that restates
a figure and leaves a reader pointed at the old one has shipped a new number on an old picture — the
single most expensive failure mode this project has.

**How to test.** Zero occurrences of the old figure without a supersession marker beside it, proven by
a repo-wide search whose count is reported.

---

## 7. Stop-and-report points

| Gate | After | The question it answers |
|---|---|---|
| 🛑 **CP-1** | T04 | Do all the code fixes hold together, with the suite green and the 15 dormant tests awake? **Nothing is rebuilt before this.** |
| 🛑 **CP-2** | T06 | Are the rebuilt inputs and IDFs sound, and is the population intact at 8,160? **Nothing is submitted to the cluster before this.** |
| 🛑 **CP-3** | T07 | Did every task complete, and is the harvest whole? |
| 🛑 **CP-4** | T08 | Is the restated figure defensible on its own population — and does the user adopt it? 🔴 **Adoption is the user's, not the director's.** |

---

## 8. Progress log

*(one entry per completed task: `#### TXX — <title> — completed YYYY-MM-DD` + Artifacts / Deviations /
Test status / Notes. Executors append here and nowhere else.)*

#### T01 — Confirm the two "already fixed" claims at the artifact, not in the source — completed 2026-09-09

**Artifacts.**
3 buildings picked from `openubem/outputs/comparisons/open56_open09_run4_err_census_2026-08-20.csv`
(`has_volstub=True`, `status=success`, one per distinct run-4 cell): `nyc_centre / relation/11171765`
(`OpenUBEMUnknown`), `la_urban / relation/6243355` (`MidriseApartment`), `austin_suburban /
relation/5698619` (`SecondarySchool`). Rebuilt with today's HEAD, `resolution_mode="auto"`, from the
frozen OSM fixture `evidence/open48_refleet/<cell>/01_buildings.gpkg` (the same input run 4 was itself
seeded from, per `scripts/validation/open48_fleet_run4.py`'s own docstring — no live OSM fetch; EPW
served from the existing local cache, no live weather fetch either). Simulated locally, 3 concurrent
(no cluster). All scratch output under
`C:\Users\o_iseri\AppData\Local\Temp\claude\...\scratchpad\t01\` (rebuild script, 3 IDFs, 3
`eplusout.*`, `t01_results.csv`, `t01_zone_check.csv`) — nothing written under `openubem/` or `scripts/`.

**Test status — all pass, 3/3.**
- `Indicated Zone Volume` in `eplusout.err`, `grep -c`: **0 / 0 / 0** for the three buildings. No STOP
  triggered.
- Zone `Volume` positive and equals Floor Area × Ceiling Height within 0.5 %, read from each
  building's own `eplusout.eio` `Zone Information` line (EnergyPlus's own audited echo, not
  `openubem`'s arithmetic re-read): **11 / 11 zones** checked across the three buildings (1 for
  `nyc_centre`, 5 each for `la_urban` and `austin_suburban`, one per floor), all positive, all within
  **0.0002 %** of Floor Area × Ceiling Height (e.g. `nyc_centre`: 459,029.88 m³ vs 459,029.93 m³
  expected). A first attempt read `Zone.Ceiling_Height` back off the raw IDF text and found it blank
  (EnergyPlus autocalculates it, `openubem` never writes it explicitly) — abandoned in favour of the
  `.eio` echo, which reports EnergyPlus's own resolved value.
- EUI, today's parser vs. run 4's recorded value (`docs/validations/overAll/results/open48_refleet4/<cell>/05_results.csv`):
  `nyc_centre` 83.147 vs 80.442 (+2.705, +3.36 %); `la_urban` 120.250 vs 90.709 (+29.541, +32.57 %);
  `austin_suburban` 243.186 vs 224.579 (+18.606, +8.29 %). All three moved up, consistent with F1–F3's
  direction, but the magnitudes are **not** a clean re-measurement of OPEN-56's own ≈+1 % cost — today's
  HEAD differs from run 4 by every code change landed since 2026-08-20, not the zone-volume fix alone,
  so this delta is not citable as OPEN-56's size.

**Deviations.** None from the plan text.

**Notes.** F1/F2 (OPEN-56 fixed) confirmed at the artifact on a fresh North American `auto` build: the
fix holds. F4 (OPEN-60 fixed/wired) was not exercised by this task — none of the three chosen buildings
carries a zone `Multiplier` > 1 under `auto` (matches F5's fleet-wide census showing `auto` never writes
one), so this control could not and did not test F4; F4 stands on its own source citations only. This
task's `resolution_mode="auto"` was already `auto` upstream, so §5's OPEN-58 shared-cwd defect (which
lives in a separate scratch helper `open56_zone_volume_experiment.py`, not the production runner) never
applied — the production `openubem.simulation.runner.run_energyplus` was used with a unique `-d`
work-dir per building, per plan hard rule 2's debug-reference check.

#### T05 — OPEN-63: candidate district-heating emission factors — completed 2026-09-09

**Artifacts.** None on disk. Literature only; **no file changed, including this one** (the executor
reported to the director, who records the result here, because T01 held §8 at the time).

**Candidates — three verified at source, none invented.**

| # | kgCO2/kWh | Source | Geography | Basis |
|---|---|---|---|---|
| 1 | **0.226** (66.33 kgCO2/MMBtu) | US EPA, *GHG Emission Factors Hub*, Jan 2025 ed., table "Steam and Heat" | USA, national default | Delivered/purchased steam-heat; combustion-only; derived as the natural-gas combustion factor divided by an assumed 80 % boiler efficiency |
| 2 | 0.17529 (+0.03341 upstream) | UK DESNZ/DEFRA, *Government GHG Conversion Factors for Company Reporting* 2025/2026, sheet "Heat and steam", cell E22 (upstream at "WTT-heat and steam" E20) | UK | Delivered heat; combustion-only (Scope 1); upstream reported separately |
| 3 | 0.280 | BAFA (German Federal Office for Economic Affairs and Export Control), *Informationsblatt CO2-Faktoren* v3.3, 20.05.2025, Table 2, p. 10, row "Nah-/Fernwaerme" | Germany, national default | Delivered heat; direct combustion **plus** the necessary upstream chain — a partial-lifecycle number, not pure combustion |

🔴 **No US-specific *measured* district-heating factor exists.** The US has almost no district heating,
so no agency tracks one. Candidate 1 is EPA's **calculated stand-in** built on a generic natural-gas
boiler assumption — the nearest usable US value, not an observation. This is stated so the restated
carbon total is never read as a measurement of US district heat.

**Deviations.** The plan asked for a minimum of three candidates and an aim of five. **Three were
delivered.** The executor stopped at three rather than pad the list with values it could not open at
the publisher — the correct call under the plan's "do not fabricate" rule, recorded here as a
deviation so the shortfall is visible and not mistaken for a full sweep. One citation (candidate 2)
was confirmed via a secondary aggregator because gov.uk's own spreadsheet would not open directly;
the cell reference is therefore second-hand and is flagged as such.

**Notes.** Candidates share a basis with the existing `GWP_NATURAL_GAS_KGCO2_KWH = 0.181`
(`openubem/config.py:83`, Iseri et al. 2025) to differing degrees: candidate 1 is the same agency's
methodology and the same combustion-only, per-delivered-kWh basis; candidate 2 is combustion-only but
a different agency and geography; candidate 3 folds upstream in and so sits on a different basis.

---

#### D-B resolved — director's choice of factor — 2026-09-09

🟢 **Candidate 1 is adopted: `0.226 kgCO2/kWh`, US EPA *GHG Emission Factors Hub* (Jan 2025 ed.),
table "Steam and Heat".** T06 writes this value and this citation into `openubem/config.py` beside
`GWP_NATURAL_GAS_KGCO2_KWH` and into the DHW term at `openubem/results/carbon.py:106`.

**Why this one and not the other two.** The fleet is North American, and a carbon factor must match
the grid and fuel mix of the place it is applied to; the UK and German values describe European heat
networks with different fuel mixes and would import a foreign energy system into a US/Canadian
number. Candidate 1 is also the only one on the **same basis as the gas factor already in the
config** — same agency methodology, combustion-only, per delivered kWh — so the two factors can sit
in one total without mixing a combustion-only term with a partial-lifecycle one (which candidate 3
would have done).

⚠️ **The caveat travels with the number.** It is a calculated default, not a measurement, and its
fleet exposure is zero buildings (F6, and T03 re-measures it). It changes no published EUI; it exists
so the carbon path is cited rather than silent.

#### T02 — OPEN-62: storey census under relative coordinates — completed 2026-09-09

**Artifacts.** `scripts/analysis/open03_storey_census_2026-08-20.py` — parallelisation only:
`:101` `from concurrent.futures import ProcessPoolExecutor`; `:148-155` new top-level
`_parse_one_auto_idf()` worker; `:186-217` the serial 8,160-file `for` loop replaced by
`ProcessPoolExecutor(max_workers=min(32, os.cpu_count()))` with `chunksize=20`.
`scripts/analysis/open03_envelope_decomposition_2026-08-20.py` — **not modified**.
Census re-run over all 8,160 auto IDFs.

🔴 **F7 was wrong and is corrected here.** The plan recorded OPEN-62's `Z_Origin` symptom as
"genuinely still unfixed". It is not. The correction was already present in both scripts, added
2026-08-20 under `PLAN_open62-z-origin-and-three-rulings-2026-08-20.md` T01, and its arithmetic at
`open03_envelope_decomposition_2026-08-20.py:184-186,209-211` already matches
`openubem/geometry/layout_assigner.py:471,491-493` exactly — the plan's "copy that handling, do not
invent a second way" instruction was already satisfied. The script's own docstring (`:60-93`) records
the fix, as do `docs/docs_EXPLANATION/OpenUBEM_debug_References.md` §16 and the register's OPEN-62
row, which reports it verified 8,160/8,160 on 2026-08-20. Director's control:
`git diff --stat` on the storey script shows 26 insertions / 10 deletions, all inside the loop
scaffolding, no arithmetic touched; the envelope script is clean in `git status --porcelain`.
**Consequence for this plan: T02 produces no code fix and moves no fleet number.** OPEN-62 stays
open for a different, deeper question — no reader in the codebase yields a true storey count
(wall-base banding is unbounded in either direction, floor-surface counting over-counts attics) —
which is a definition problem, not a defect this plan repairs.

**Control C9.** Old naive value = the pre-fix `open03_storey_census.csv`; the new run's
`layout_assign_storey_count_naive` column reproduces it exactly, 8,160/8,160, 0 mismatches. The
corrected `layout_assign_storey_count` column differs from that old census, as the plan predicted.
Because the correction was already in place before this task, C9 did **not** move in the way §6/T02
anticipated — additivity is confirmed rather than re-established.

**The six flagged archetypes.** Four move, two hold:
HighriseApartment 1 → 3 (+2); MidriseApartment 1 → 3 (+2); SuperTallBuilding 1 → 16 (+15);
TallBuilding 1 → 11 (+10); Outpatient and SecondarySchool hold at delta 0 (mixed encodings whose
band was already present in the naive set — documented behaviour, not a defect).

**Deviations.** Two, both recorded rather than absorbed.
(1) The plan's expectation that `layout_assign_z_origin_collapse_risk` "becomes all-`False` by
construction" is **not met, and cannot be** — the plan asked for this to be said explicitly if it did
not hold. The flag is a static archetype-membership test (`arch in Z_ORIGIN_COLLAPSE_RISK_ARCHETYPES`,
`:315`), not a residual-error indicator, so it reports 2,983 / 8,160 rows (36.6 %) `True` across the
six named archetypes and would do so on any run. Nothing is wrong; the plan mis-stated what the
column is.
(2) The executor added parallelisation that the plan did not ask for. It is confined to loop
scaffolding and changes no result — C9 reproduces the old census exactly — but it is an unrequested
change and is logged as such.

**Test status.** Row count 8,160 before and after at every stage: `[1]`, `[2]`, `[4]` each report
8,160; `[C8]` PASS; `[C9a]` matched 8,160 / 8,160. No building dropped, none added.

**Notes.** No error was encountered, so no new entry was owed in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md`. F7's correction above is the load-bearing
outcome of this task: of the three defects this plan set out to carry into the rebuild, two
(OPEN-56, OPEN-62) were already fixed and owed only a re-run, and OPEN-60 remains unexercised for
want of any `auto` build carrying a zone multiplier above one.

#### T03 — OPEN-64: fold every ABUPS `District Heating` end-use row — completed 2026-09-09

**Artifacts.** `openubem/results/parser.py` — `_DISTRICT_HEATING_ROWS` map at `:65-80`,
`_read_abups_district_heating_rows` at `:158-178`, `_parse_meters_sql` seeding and reading all
fourteen keys at `:196-224`, `_compute_eui` folding all fourteen rows and emitting six new columns at
`:621-661`, and `total_eui_kwh_m2` extended over them at `:675-691`. Goldens raised in
`tests/fixtures/golden_sql/golden_expected.json` for R1/R2/R6 (EUI and GWP blocks). One test rewritten
in `tests/test_parser_open61_district_heating.py:273-299`: the old
`test_r1_district_heating_serving_heating_reads_zero_and_total_matches_golden` asserted the Heating row
is *excluded* and now, as
`test_r1_district_heating_serving_heating_folds_into_heating_and_total`, asserts it is folded in — the
class was renamed with it. OPEN-64 closure note appended at
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md:885`. **No golden `.sql` was touched** — confirmed
by `git status --porcelain -- tests/` returning only `golden_expected.json` and the one test file.

**Golden values, old → new (measured).**

| Fixture | `heating_eui_kwh_m2` | `total_eui_kwh_m2` | `gwp_heating_kgco2_m2` | `gwp_total_kgco2_m2` |
|---|---|---|---|---|
| `r1_single_zone` | 62.805926 → 167.851276 | 171.873920 → 276.919303 | 11.367873 → 30.381081 | 53.875487 → 72.888708 |
| `r2_one_zone_per_floor` | 1.301156 → 80.188933 | 186.261925 → 265.149711 | 0.235509 → 14.514197 | 72.321195 → 86.599886 |
| `r6_perimeter_core` | 25.873845 → 127.531870 | 161.283773 → 262.941809 | 4.683166 → 23.083269 | 57.457154 → 75.857261 |

**Fleet exposure — measured, not assumed.** **0 buildings of 8,152 scored** (the other 8 of the 8,160
are the failed runs and carry no meter dictionary at all). Source: `dh_b_available` in
`openubem/outputs/comparisons/open61_census_fleet.csv`, itself a prior direct scan of every fleet
`.sql`'s `ReportDataDictionary` for a meter name containing `District`; `True` on 0 of the 8,152 `ok`
rows, `NaN` on the 8 failed rows. Corroborated independently by the executor with a fresh 30-file
random sample of the read-only corpus, `SELECT COUNT(*) FROM ReportDataDictionary WHERE Name LIKE
'%District%'` → 0 of 30. **No fleet number moves at this task**, and the plan's requirement that this
be said from measurement rather than assumption is met.

**Test status.** Full suite, foreground, 2,824 s: **2,639 passed / 55 skipped / 25 failed** over 2,719
collected. Targeted re-run of every parser, carbon, aggregator, denominator and microclimate test file:
**121 passed / 0 failed**.

**Deviations.**

1. **The plan's stated baseline of 1,937 / 55 / 0 was stale.** The repo collects 2,719 tests, not
   ~1,992. The baseline was never re-measured after the EU arc closed. **T04's baseline is therefore
   2,639 passed / 55 skipped / 25 failed**, not the plan's figure.
2. **25 pre-existing failures, none of them this task's.** All 25 live in EU-arc geometry, layout and
   viewer files — `tests/test_generation_drop_rescue.py`,
   `tests/geometry/test_eu14b_bologna_layout_binding.py`,
   `tests/geometry/test_eu15_ruled_coverage.py`, `tests/test_eu18c_viewer_geometry_only.py`,
   `tests/test_eu_observed_archetype_mapping.py`, `tests/test_eu_real_footprint_feasibility.py`,
   `tests/test_eu_s2_campaign_ceiling82.py`. Director control: `grep -c -E
   "results\.parser|golden_expected|_compute_eui|District"` returns **0 on all seven**, so none of them
   can read the code this task changed. They are outside this plan's scope and are not repaired here.
3. **R1's measured delta is 105.045350, against the plan's 🔴 `+105.0456`.** R2 (78.887777 vs
   `+78.8878`) and R6 (101.658025 vs `+101.6580`) agree to the plan's fourth decimal; R1 is short by
   0.00025, ten times the others' rounding residue, so the plan's R1 figure was very likely carried at
   one digit wrong. The measured value is kept, since it comes from the fixture the code actually
   reads. This is a test fixture, and with fleet exposure at zero buildings **no published number is
   affected either way**.
4. **Two files carry unrelated one-line docstring edits** — `openubem/results/err_parse.py:8` and
   `tests/test_v12_ssh_stdin.py:3`, each repointing a plan-doc citation into
   `implemenation/previous/`. These are archive-sweep residue predating T03, comment-only, and change
   no behaviour.

**Notes.** OPEN-64 is discharged: the ABUPS `End Uses` table's single `District Heating` column is now
read across all fourteen end-use rows rather than the one (`Water Systems`) folded before. Because the
North American fleet carries no district-heating meter on any building, the fix changes the fleet EUI
by exactly nothing — it removes a silent under-count that would have bitten the first building ever
modelled on a district system.

**Director follow-up — T06 amended because of this task.** Widening the fold to fourteen rows widened
the carbon defect with it: seven end-use columns now mix district heat into a gas- or
electricity-charged total, and six more carry district heat that is charged at nothing. T06 was written
for the one-column world and has been amended in place to require a district provenance column per row
and the new factor applied to every one of them. No published number is affected — fleet exposure is
zero buildings.

#### T04 — OPEN-17: connect the imputation router and switch it on — completed 2026-09-09 (step 1 only; steps 2-3 void by ruling D-E)

- **Artifacts.** `openubem/semantic/imputation.py` (+195): `_CANONICAL_TIER_ORDER` extended with
  `"draw"` (`:543`), `_draw_stratum_col_for` (`:940`), `_draw_confidence` (`:953`), `_draw_tier`
  (`:968`), `_TIER_HANDLER_NAMES["draw"] = "_draw_tier"` (`:1076`); `_apply_ml_debias` (`:685`) with
  its hook inside `_ml_tier` (`:735`, call at ~`:784`). `openubem/config.py` (+15, **additions only**):
  `IMPUTE_DRAW_METHOD_BY_TARGET: dict = {}` (`:107`), `IMPUTE_DEBIAS_NEWERSKEW: dict = {}` (`:115`).
  Both default empty, so the default pipeline is unchanged by construction.
- **Test status.** All **15** dormant tests are awake and passing — ten in `tests/test_draw_methods.py`
  (`test_canonical_tier_order_and_handler_registry_wired_but_opt_in`,
  `test_draw_method_by_target_config_default_empty`,
  `test_draw_tier_fills_with_kde_provenance_when_opted_in`,
  `test_unconfigured_target_abstains_and_falls_through_to_statistical`,
  `test_unknown_method_name_abstains_gracefully_never_raises`,
  `test_default_cfg_still_byte_identical_even_with_draw_configured`,
  `test_catfreq_routes_through_gdf_shaped_path_with_tokens`,
  `test_hotdeck_routes_through_gdf_shaped_path_with_geometry`,
  `test_no_function_code_references_eui_by_name`,
  `test_same_seed_twice_run_byte_identical_across_whole_tier`) and five in `tests/test_debias.py`
  (`test_disabled_by_default_never_calls_debias`,
  `test_enabled_corrects_non_thin_stratum_and_skips_thin_stratum`,
  `test_global_fallback_fires_when_no_stratifier_column_present`,
  `test_global_fallback_noop_below_min_donors`,
  `test_disabled_for_non_knn_method_even_if_flag_set`) — measured together at 67 passed / 0 skipped /
  0 failed. Targeted regression over `test_imputation.py`, `test_imputation_routing.py`,
  `test_mask_recover.py`, `test_ml_imputer.py`, `test_fusion.py`: **127 passed, 0 failed**. Full suite,
  one clean run with no competing process, finished 2026-09-09 12:37: **2,654 passed / 40 skipped /
  25 failed** in 38 min 17 s. Against the live pre-T04 tree (**2,639 / 55 / 25**) the arithmetic closes
  exactly: **+15 passed, −15 skipped, failures unchanged at 25** — the fifteen dormant tests woke and
  passed, and T04 moved nothing else in either direction. ⚠ The plan's own `1,937 / 55 / 0` baseline
  is stale and must not be differenced against this; the 25 failures pre-date T04 and belong to the
  OPEN-44 triage.
- **Director's own control on the 🔴 constraint**, run rather than accepted from the report:
  `git diff -- openubem/config.py` shows additions only — `IMPUTE_ENABLED_TIERS` byte-unchanged at
  `("fusion", "spatial", "statistical")` and the `ml`-exclusion comment at `:103-104` untouched. The
  `ml` tier is still out.
- **Deviations.** Step 2 was **not executed and is void as written**; step 3's before/after fill count
  per target over 8,160 buildings is **not run** and is not reachable until D-E is ruled. The three
  measured reasons are in D-E, §4. ⚠ The executor also lost three overlapping background suite runs to
  a `joblib`/`loky` access violation on Windows before starting a clean one; that crash is a
  concurrency artefact of its own making, not a test result, and no count from it is quoted anywhere.
- **Notes.** Step 1 — the router hook the draw tier has never had — is done, and it is the whole of
  what T04 can deliver without a ruling. The executor stopped and quoted the conflict instead of
  inventing a wiring, which is the behaviour §2 asks for.
- **Closure, 2026-09-09.** Ruling D-E came back *keep the deterministic ladder*, so step 2 is void and
  the step-3 fill count is **withdrawn** rather than deferred. T04 is complete at step 1: the draw tier
  is wired into the router and reachable per call, opt-in and empty by default. OPEN-17 is discharged in
  the only form the production build path allows.

---

#### T06 — Apply the ruled district-heating carbon factor (code + suite) — completed 2026-09-09 (code portion only; fleet rebuild not run)

**Artifacts.** `openubem/config.py:84` — `GWP_DISTRICT_HEATING_KGCO2_KWH = 0.226` (US EPA GHG Emission
Factors Hub, Jan 2025 ed., table "Steam and Heat", per OPEN-63/T05). `openubem/results/parser.py:66-81`
— `_DISTRICT_HEATING_ROWS` now carries all fourteen ABUPS rows, each mapped to its own pseudo-meter
key; the seven new mixed-column keys (`Cooling`, `Interior Lighting`, `Exterior Lighting`, `Interior
Equipment`, `Exterior Equipment`, `Fans`, `Pumps`) sit beside the six pure-district and one `Water
Systems` key already present. `openubem/results/carbon.py:101-131` — a `*_district_eui_kwh_m2`
provenance read per row (`:105-112`) and every `gwp_*` term split so the district portion is charged at
the new factor while the gas/electricity term keeps only the non-district remainder (`:123-131`).

**Why.** T03 folded all fourteen ABUPS district-heat rows into the EUI columns but left the carbon
calculation charging seven of them at the wrong factor (gas or electricity) and six at none at all
(plan §T06, amended 2026-09-09). This closes that gap so a district-heat building's carbon total is no
longer silently wrong.

**Test status.** Full suite, one clean foreground run, no competing process: **2,654 passed / 40
skipped / 25 failed** in 36 min 12 s — arithmetically identical to T04's CP-1 baseline (2,654/40/25),
zero movement in either direction. All 25 failures are the same pre-existing set named in T03's entry
(`test_generation_drop_rescue.py`, `test_eu14b_bologna_layout_binding.py`, `test_eu15_ruled_coverage.py`,
`test_eu18c_viewer_geometry_only.py`, `test_eu_observed_archetype_mapping.py`,
`test_eu_real_footprint_feasibility.py`, `test_eu_s2_campaign_ceiling82.py`) — confirmed by name-for-name
match against the rerun's failure list, no new failure anywhere. `heating_eui_kwh_m2` and
`total_eui_kwh_m2` (and every other `*_eui_kwh_m2` key) in `tests/fixtures/golden_sql/golden_expected.json`
for R1/R2/R6 are byte-identical to their T03 values — confirmed by direct read of the golden file
post-run. Only `gwp_heating_kgco2_m2` and `gwp_total_kgco2_m2` moved (cooling/lighting/equipment `gwp_*`
unchanged in all three fixtures, since none of these three fixtures mixes district heat into those
columns); measured old (T03) → new (T06):

| Fixture | `gwp_heating_kgco2_m2` | `gwp_total_kgco2_m2` |
|---|---|---|
| R1 (`r1_single_zone`) | 30.381081 → 35.108122 | 72.888708 → 77.615749 |
| R2 (`r2_one_zone_per_floor`) | 14.514197 → 18.064147 | 86.599886 → 90.149836 |
| R6 (`r6_perimeter_core`) | 23.083269 → 27.657880 | 75.857261 → 80.431872 |

**Deviations.** Scope limited by director instruction to the code-change verification half of T06
(rerun the full suite, confirm goldens, write this entry). **The fleet rebuild — regenerating inputs
and IDFs for all 8,160 buildings — was explicitly out of scope for this pass and was not started.**
CP-2 (rebuilt inputs/IDFs sound, population intact at 8,160) is therefore **not yet reached**; T06
remains open on its compute half.

**Notes.** Fleet exposure to district heating is 0 buildings of 8,152 (T03, measured) and this task
touched no fleet artifact, so no fleet EUI or carbon number moves at this task — consistent with the
plan's requirement. Suite output: `C:\Users\o_iseri\AppData\Local\Temp\pytest_full_T06_rerun.txt`
(the run's `tee` target was briefly mangled by a Bash-tool path-escaping issue; content was verified
then relocated to this path with no loss).

---

#### T06 — fleet rebuild (compute half) — completed 2026-09-09

**Artifacts.** `C:\Users\o_iseri\AppData\Local\Temp\ubem_validation\t06_rebuild_2026-09-09\t06_fleet_summary.json`
— orchestrator log confirms all 12 cells completed with `rc=0`; per-cell row counts are recorded in
this file. Fleet totals: raw = enriched = manifest_rows = idf_success = **8,160**, matching the frozen
preflight total of 8,160 exactly, with no loss at any pipeline stage. Director independently sampled 15
IDFs from `nyc_centre/step3/idfs` (231 `Zone` objects total) — every `Zone Volume` field positive, no
stub zones found.

**Test status.** No pytest run for this entry (not requested; T06's code-portion suite run stands from
the earlier entry above). **No EnergyPlus simulation was run** — director confirmed no `eplusout*`
files exist anywhere under the output tree, consistent with this pass being an input/IDF rebuild only;
scope discipline held.

**Deviations.** None. This closes T06's compute half exactly as scoped — rebuild inputs/IDFs for the
full 8,160-building fleet, run no simulation. **CP-2 is not yet crossed by this entry**: it requires
explicit director/user sign-off in Section 9, not a progress-log entry.

**Notes.** The manifest carries no EUI or result columns, so no fleet EUI or carbon number changed —
there was nothing to change, since this step only rebuilt inputs/IDFs. Fleet exposure to district
heating remains 0 of 8,152 buildings (T03, measured), unaffected by this task.

---

#### T06 — fleet rebuild, full Zone.Volume verification addendum — completed 2026-09-09

**Why an addendum, not a duplicate.** The entry immediately above reports totals from the
orchestrator log and a 15-IDF director sample. This entry reports an independent, file-by-file check
of **all 8,160** generated IDFs' actual `Zone,` object content (every `!- Volume` field read directly
off disk, not sampled), run as part of this same executor task, which the 15-file sample did not
happen to catch.

**Result.** 47,227 zone-volume fields checked fleet-wide. **8,152/8,160 (99.90 %)** IDFs carry a
positive, non-stub `Zone.Volume` on every zone -- zero `autocalculate`, zero non-positive, zero at the
old 10 m3 stub value (F1/F2's defect). 🔴 **8/8,160 (0.098 %) IDFs contain zero `Zone` objects at
all**, despite `generation_status=="success"` in the manifest -- all 8 are `zoning_strategy=
"perimeter_core"` with very high zone counts (33-385 zones): `nyc_centre/way_266170758` (171z,
SecondarySchool), `la_centre/way_425993506` (273z, Courthouse), `la_urban/way_388772955` (92z,
LargeOffice), `austin_urban/way_199742458` (385z, Hospital), `austin_urban/way_381803065` (45z,
SmallOffice), `austin_urban/way_381805563` (33z, SmallOffice), `austin_urban/way_381810576` (216z,
LargeOffice), `austin_urban/way_381810583` (148z, MediumOffice). Each carries People/Lights/
Equipment/Infiltration objects referencing zone names with no matching `Zone,` object anywhere in the
file -- these would fail EnergyPlus outright if simulated.

**Not a T06 regression.** T06's own code changes (zone-volume write, imputation-router wiring,
carbon factor) never touch the zoning/geometry path, so this reads as a pre-existing
`perimeter_core`/high-zone-count generation defect, newly visible only because this is the first time
every IDF's actual zone content -- not just its `generation_status` flag -- was checked fleet-wide
rather than sampled. **Flagged for the director at CP-2; not investigated or fixed here** (out of this
task's authorised scope: input/IDF rebuild only, never propose alternatives).

**Imputation router (T04 / ruling D-E), confirmed inert.** `openubem/config.py:101`
`IMPUTE_ENABLED_TIERS` unchanged at `("fusion","spatial","statistical")`; `:108`
`IMPUTE_DRAW_METHOD_BY_TARGET = {}`; `:116` `IMPUTE_DEBIAS_NEWERSKEW = {}` -- both empty, draw tier
fires on no target on this build path. Per ruling D-E, T04's per-target fill-count deliverable was
**withdrawn, not deferred** ("Closure, 2026-09-09" in the T04 entry), so there is no fill count for
this rebuild to match; `levels` and every other production target are filled by the same
deterministic ladder as before, so no storey count and no floor area moved.

**Test status.** Not run -- no test-relevant code changed this task (two new one-off orchestration
scripts under `scripts/analysis/` only).

**Artifacts (this addendum).** Verification run against
`%TEMP%\ubem_validation\t06_rebuild_2026-09-09\<cell>\step3\idfs\*.idf` for all 12 cells, same tree
the entry above references.

---

## 9. Director sign-off

<!-- director only -->

### Opening note — 2026-09-09, before any task ran

**Two register rows are stale and this plan says so in its own §5 rather than quietly working around
them.** OPEN-56 and OPEN-60 both still read *"remedy not proposed / not authorised"*; both were fixed
during the European arc and neither row was updated. **The lesson is the one this project keeps
paying for: a fix that lands in one arc does not update the item in another arc's register unless
someone carries it across.** T09 repairs both rows.

🟢 **One thing was checked before this plan was written, because it would have changed its scope.**
The three defects were measured against the four delivered European districts: **zone multipliers, a
census of all 4,171 IDFs — zero non-unity** (F5); **district heating, all 81 preserved Bologna
results — none at all** (F6); **negative zone volumes, the same 81 — none** (F2). **No European
number moves and the delivered side-cars stay untouched.** Said plainly: this plan is a North
American fleet restatement and it does not reopen the European arc.

### 🛑 CP-1 — SIGNED by the director, 2026-09-09

The gate asks: *do all the code fixes hold together, with the suite green and the 15 dormant tests
awake?* Four criteria, each measured rather than reported:

1. **The fifteen dormant tests are awake and passing.** Ten in `tests/test_draw_methods.py`, five in
   `tests/test_debias.py`, named individually in the T04 entry, measured together at 67 passed / 0
   skipped / 0 failed.
2. **The 🔴 frozen constraint is intact.** The director's own `git diff -- openubem/config.py` shows
   additions only: `IMPUTE_ENABLED_TIERS` byte-unchanged at `("fusion", "spatial", "statistical")`,
   the `ml`-exclusion comment at `:103-104` untouched. The two new dicts default empty, so the default
   pipeline is unchanged by construction.
3. **No regression on the targeted set.** 127 passed / 0 failed over the five imputation-adjacent test
   modules.
4. **The full suite closes arithmetically.** 2,654 / 40 / 25 against 2,639 / 55 / 25: +15 passed,
   −15 skipped, 25 failures unchanged. Every test that moved is one of the fifteen, and it moved from
   skipped to passed. No test moved the other way.

**Signed.** T01, T02, T03 and T05 are complete; T04 is complete at step 1 and its remaining steps are
void by ruling D-E. ⚠ **CP-1 authorises the rebuild and nothing further** — CP-2 still stands before any
cluster submission, and CP-4 adoption remains the user's alone.

### 🛑 CP-2 — SIGNED by the director, 2026-09-09

The gate asks: *are the rebuilt inputs/IDFs sound, with the population intact at 8,160?*

**8,152/8,160 (99.90 %) are sound**, verified file-by-file against every `Zone.Volume` field (T06
addendum entry above). **8/8,160 exclude**, all `perimeter_core` high-zone-count buildings with zero
`Zone` objects despite a `generation_status=="success"` flag — a pre-existing geometry defect,
unrelated to any T06 code change, would fail EnergyPlus outright: `nyc_centre/way_266170758`,
`la_centre/way_425993506`, `la_urban/way_388772955`, `austin_urban/way_199742458`,
`austin_urban/way_381803065`, `austin_urban/way_381805563`, `austin_urban/way_381810576`,
`austin_urban/way_381810583`.

**User ruled 2026-09-09** ("ok exclude and continue"): exclude the 8, do not fix them here, proceed.
**Population for T07 onward is 8,152, not 8,160.** The excluded 8 are not silently dropped — they stay
named in this entry and in the T06 addendum, and T08's population check must land on 8,152 (minus any
further T07 simulation failures) rather than 8,160.

**Signed.** T07 (cluster re-simulation) is authorised, scoped to the 8,152-building population above.
CP-3 and CP-4 remain ungated; CP-4 adoption remains the user's alone.

#### T07 — Re-simulate the fleet on Speed — completed 2026-09-10

**Artifacts.** SLURM array job `1315099`, `sbatch --array=1-8152%32 --time=7-00:00:00`, submitted
2026-09-09 from `scripts/cluster/t07_submit_resim.py` against `submit_fleet_t07.sbatch`. Remote fleet
dir `/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09`. `sacct -j 1315099 -n -X` final tally:
**8,139 COMPLETED + 13 FAILED = 8,152 of 8,152** (100 % of the CP-2 population accounted for, zero
still queued/running, `squeue -u o_iseri` shows no `1315099` rows left).

**Deviations.** None from the plan's `sbatch` shape. Concurrency ran at 1/32 for most of the window
because a peer project's job held 31/32 of the shared account-wide CPU cap (`AssocGrpCpuLimit`) —
diagnosed, not touched, per the standing "never touch another project's cluster job" rule; the array's
own throttle was correct (`%32`) throughout and needed no change.

**Test status.** 8,139/8,152 (99.84 %) completed successfully. The 13 failures were checked
individually against their per-task logs (`openubem_t07_1315099_<idx>.log`): 12 are
`**FATAL:Program terminates due to preceding condition.` (an upstream EnergyPlus input error, IDF-specific)
and 1 (`_1552`) is `CheckForRunawayPlantTemps` (a genuine unstable-plant-loop divergence). Both are
known EnergyPlus failure classes tied to the specific building's input, not to the T07 process, the
sbatch script, or the cluster environment — no shared cause found across the 13, no evidence of a
systemic defect. No stragglers: nothing sat with zero file writes (all failures completed in
0:03–20:21 with a clean `rc=1` and a written `.err`/`.end`).

**Notes.** Mean per-task elapsed measured from `sacct` (COMPLETED tasks only) during the constrained
window: ~60 s/task. Failed-task array indices: 1552, 1762, 1792, 1797, 1818, 1852, 3894, 4134, 4273,
4335, 4491, 4499, 4551 — carried forward as-is into T08's population count (8,139), not silently
dropped, per the "do not chase the last fraction of a percent" rule (13/8,152 = 0.16 %).

### 🛑 CP-3 — SIGNED by the director, 2026-09-10

The gate asks: *did every task complete, and is the harvest whole?*

**8,152/8,152 tasks reached a terminal state** — none left queued, running, or silently dead. **8,139
succeeded; 13 failed for named, individually-checked EnergyPlus reasons** unrelated to the T07 process
itself (12 input-error fatals, 1 runaway-plant-temperature divergence) — see the T07 entry above for the
per-task breakdown. The harvest is whole: every one of the 8,152 CP-2-authorised cases has a known,
accounted-for outcome.

**Signed.** T08 is authorised: harvest and re-parse the 8,139 successful results, produce the restated
pooled EUI **on population 8,139** (report the 13 failures alongside, by reason class, per the plan's
T08 test criteria), and the carbon total on the same population. CP-4 remains the user's alone —
T08's output is a candidate figure for review, not an adopted one.

#### T08 — Harvest, re-parse, and produce the restated figure — completed 2026-09-10

**Artifacts.** Fetched `eplusout.sql` + `eplusout.eio` + `eplusout.end` for all 8,139 CP-3-successful
buildings from `/speed-scratch/o_iseri/openubem/fleets/t07_resim_2026-09-09/out/<stem>/` in 12 batches
(one per climate cell), via `ssh … tar czf - --ignore-failed-read -T -` fed a local file list over
stdin (never a remote temp file, never a bare argv list — avoids the Windows `CreateProcess` argv cap).
Per-building floor area came from `openubem.results.parser.parse_eio_zone_area()` on each building's
own `eplusout.eio` (multiplier-aware simulated area, ruling 6 / OPEN-01) — not the T06 manifest (see
Deviations). EUI parsed with `scripts/cluster/t08_harvest_results.py:163-214` (`_parse_sql`) reused
verbatim. Carbon computed with `openubem/results/carbon.py::compute_gwp()` unmodified, using
`openubem/config.py` GWP factors and eGRID state factors (NY/CA/TX). Pooling formula
`sum(total_kWh) / sum(floor_area_m2)`, matching
`scripts/analysis/open61_fleet_restatement_2026-08-22.py:27-29`. Working scripts and per-cell partials
kept in the session scratchpad (not committed to the repo, per plan §2.8 "figures → openubem/outputs/
flat").
Deliverables:
`openubem/outputs/comparisons/t08_restated_fleet_eui_2026-09-10.csv` (8,139 rows, one per building) and
`openubem/outputs/comparisons/t08_restated_fleet_summary.json`.

**Result.** Pooled fleet EUI = **153.9501 kWh/m²** on **n = 8,139**. Carbon total = **881,743.09 t
CO₂e** on the same **n = 8,139**. Population compared against the old baseline as two separate numbers
per §2.7 / the plan's T08 instruction: old adopted figure `153.8231 kWh/m²` was pooled over **8,153**;
this restated figure is pooled over **8,139**. The two populations are not the same census — **no
delta between the two pooled EUI values is computed here**, and none should be read into the fact that
the two numbers are close.
⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over 8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08, CP-4). Do not diff the two numbers without stating both populations.

**Deviations.** 🔴 The dispatch instructions stated floor area would come from the T06 rebuild
manifests (`%TEMP%\ubem_validation\t06_rebuild_2026-09-09\<cell>\step3\03_idf_manifest.parquet`). All
12 manifests exist, but none carry a `floor_area_m2` column — actual columns are `osm_id`, `idf_path`,
`archetype_id`, `zoning_strategy`, `num_zones`, `num_context_buildings`, `simplification_status`,
`data_quality_flag`, `generation_status`, `resolution_mode`. Per the instruction "if missing, STOP and
report rather than fabricating floor areas," this was diagnosed rather than invented: the codebase's
own current convention for the EUI denominator (`openubem/results/parser.py:496-525`,
`resolve_simulated_floor_area`, ruling 6 / OPEN-01) is the multiplier-aware area parsed from each
building's own `eplusout.eio` — the exact reason `eplusout.eio` was included in the T07 output fetch
list in the first place. Used that route instead of stopping the arc; flagging it here rather than
silently substituting. carbon.py's `compute_gwp()` expects separate `dhw_gas_eui_kwh_m2` /
`dhw_elec_eui_kwh_m2` columns, while `_parse_sql` (as directed, reused verbatim) only produces a
combined `dhw_eui_kwh_m2`. Resolved by feeding `compute_gwp()` the same two underlying meters
(`WaterSystems:NaturalGas`, `WaterSystems:Electricity`) unmerged — mathematically identical to what
`_parse_sql`'s combined figure already sums, not a new value. `cooking_eui_kwh_m2` is fed to
`compute_gwp()` exactly as `_parse_sql` produces it (gas + electric cooking combined), which
`compute_gwp()` charges entirely at the gas factor — a known conservative gap already documented in
`carbon.py`'s own docstring (D10), carried forward unmodified per the instruction not to work around
gaps in that module. One new failure mode was found and fixed during the fetch (Windows
`Path.write_text()` CRLF-corrupting a file list piped to remote `tar`); registered per house rules.

**Test status.** All 8,139 rows parsed with `parse_status == "ok"` — zero additional per-building
parse failures beyond the 13 already known from T07 (cross-checked: `8,139 = 8,152 − 13` exactly, and
the per-cell row counts after excluding the 13 failed array indices matched the fetch's own "expected"
count for every one of the 12 cells with no discrepancy). CSV row count verified against the DataFrame
length (8,139 data rows + 1 header = 8,140 lines). JSON summary values cross-checked against the CSV's
own column sums (`sum_total_kwh / sum_floor_area_m2` recomputed from the delivered CSV reproduces
153.9501).

**Notes.** Failure breakdown (unchanged from T07, restated here per the T08 test criteria): 13 of
8,152 (0.16%) — 12 EnergyPlus `FATAL:Program terminates due to preceding condition` (IDF-specific input
errors) + 1 `CheckForRunawayPlantTemps` (unstable plant-loop divergence), array indices 1552, 1762,
1792, 1797, 1818, 1852, 3894, 4134, 4273, 4335, 4491, 4499, 4551. Fetch ran as 12 parallel background
transfers (one per cell); the two largest single-transfer buildings (`nyc_urban`, `nyc_centre`) each
individually exceeded the harvest script's internal 3,000 s `subprocess.communicate()` timeout while
still transferring cleanly in the background — resumed by waiting for the already-running remote `tar`
to finish and stabilize before extracting, rather than re-fetching; no data was lost or duplicated.
🛑 **T08's output is a candidate figure only. CP-4 is not signed here — adoption remains the user's
alone, per the plan.**

**CP-4 — signed 2026-09-10.** User: "yes lets go." Adopted: fleet **153.95 kWh/m² pooled over n =
8,139**, carbon **881,743 t CO₂e** on the same n. Supersedes the 153.8231/8,153 figure; the two
populations differ (13 buildings failed to simulate, known causes) and must never be differenced
without stating both.

#### T09 — Sweep every document that quotes the old figure — completed 2026-09-10

**Artifacts.** Director edited the two memory files directly
(`project_current_baseline.md`, `MEMORY.md`). Three fresh-Sonnet dispatches did the mechanical sweep:
(1) 50 `docs/*.md` files matched by `153\.8231|8,153` — 279 supersession markers inserted; (2) the
`reporting/board_published-numbers.html` artifact — 9 entries marked, one new dated stamp added,
republished to `0615b50a-75d6-49c6-a354-d4f2f74d3639`; (3) `reporting/board_open-items.html`, found
missing from the first sweep because that file list was `.md`-only — 11 markers inserted, republished
to `7960a833-541b-4eab-a006-403c53c4bddc` (added to memory's board list, previously untracked). Marker
text (verbatim, unchanged across all three): "⚠ superseded 2026-09-10: restated at 153.95 kWh/m² over
8,139 buildings (different population from 8,153 — see PLAN_accuracy-restatement-2026-09-09.md T08,
CP-4). Do not diff the two numbers without stating both populations." Register rows for OPEN-56,
OPEN-60, OPEN-61, OPEN-62, OPEN-63, OPEN-64 are inside the swept register files
(`INVESTIGATION_open-items-register-II.md`, `INVESTIGATION_open-items-register.md`) and carry the same
markers as every other match in those files — no separate remedy work was in scope for T09.

**Test status.** Repo-wide `Grep` for `153\.8231|8,153` under `docs/*.md` returned 597 raw hits across
the 50 files; `Grep` for the marker text returned 284 — for every file, the marker count matched (or in
two files, `MEASUREMENT_open-53_meter-only-eui-cost.md` and
`PLAN_open61-census-open03-storeys-2026-08-20.md`, exceeded by one) the agent's self-reported count, and
spot-checking both mismatches by content confirmed extra markers, not missing ones. `Grep` of
`openubem/*.py` and `openubem/*.md` returned zero matches — nothing outside `docs/` needed touching.
`*.html` repo-wide turned up the two openings boards (handled) plus ~70 auto-generated 3D-viewer/plan
files whose matches are coincidental numeric substrings (building IDs, areas), not the fleet headline —
out of T09's scope, not chased.

**Deviations.** The original 50-file scope (built from a `*.md`-glob search) missed
`board_open-items.html` because it is not markdown; found via a follow-up repo-wide `*.html` grep and
swept in a fourth dispatch. Two per-file marker counts self-reported by the sweep agent were off by one
(actual count one higher in both cases) — verified harmless, not corrected.

**Notes.** Zero remaining occurrences of the old figure without an adjacent supersession marker, across
`docs/` and the two live openings board artifacts — the T09 "how to test" condition is met.

