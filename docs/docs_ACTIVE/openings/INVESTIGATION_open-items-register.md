# INVESTIGATION — Register of everything open in OpenUBEM

> **Slug:** `open-items-register` · **Opened:** 2026-08-04 · **Author:** manager session
> **Status:** INVESTIGATION document. This is a **register and a diagnosis**, not a plan.
> **Successor:** execution plans (`PLAN_*.md`) are written *after* this document, one per item or
> per bundle the user selects. Nothing here is scheduled, scoped, costed, or approved.

---

## 0. What this document is, and what it is not

**Amended 2026-08-04:** OPEN-23 (`layoutGenerator`) **excluded by the user** — not an option being
continued. Recorded in §7.0, ID retired.

**Amended 2026-08-05:** OPEN-28 added (see §2). OPEN-21 (mixed-use classification key) **deferred by
the user** to `docs/docs_TODO/mixed_use_classification.md` — one function per building stands, the
question is closed to further asking, ID retired. Recorded in §6. **OPEN-05 CLOSED** — full defect-ID
sweep made, no further duplicates, ID retired (§3). **OPEN-29 added** — the same sweep exposed that
defects can be OPEN at their defining line yet absent from this register (§3). **OPEN-22's stated
premise verified FALSE at HEAD** and the item rewritten (§6). **26 items remain.**

**Is:** a single place listing every item this project has left open, with — for each — what is
actually known, what is only believed, where the evidence lives, and **what single measurement would
have to be made before an execution plan could responsibly be written.**

**Is not:** a plan, a priority order, or a recommendation of what to do next. Item order inside each
theme is not a ranking. Sequencing is the user's call and is deliberately absent.

**Why it exists.** Open items in this project have been recorded in ~8 different places — arc plan
docs, `PROJECT_CHECKLIST.md`, defect logs, memory pointers, two audit docs from June — and several
have gone stale, been duplicated, or been rediscovered as "new". This session found one such
duplicate (see **OPEN-05**). A single register is the countermeasure.

### Where this arc's files go — **user instruction, 2026-08-05**

**`docs/docs_ACTIVE/openings/` stays clean.** It holds this register and `prompts/` only. **Every
supporting document an item produces — measurement reports, evidence dumps, per-item working notes —
goes in `docs/docs_ACTIVE/openings/extra/`.** The user does not want to open the arc folder and see a
pile of documents. Figures still follow the project rule: flat into `openubem/outputs/`.

### How to read the evidence column

Every claim below carries its verification state, because they are not equal:

| Mark | Meaning |
|---|---|
| ✅ **verified** | Re-derived from a raw artifact **in this session** — file named, recomputation run |
| 📄 **documented** | Recorded in a named plan/audit doc by a prior session; **not** re-verified here |
| ⚠️ **stale-risk** | Recorded ≥3 weeks ago against code or data that has since changed; treat as a lead, not a fact |
| ❓ **unmeasured** | Believed on reasoning, never measured — the belief itself is the open item |

**Rule for whoever writes the execution plans: never carry a 📄 or ⚠️ number into a plan without
re-deriving it first.** Three separate executor entries in the storey-matching arc alone shipped
headline numbers that did not reproduce from the file they cited, and one stale figure (the
81.6%/98.4% inert shares) survived four documents before being caught.

---

## 1. Summary — **26 open items** (OPEN-01 … OPEN-29; OPEN-23 excluded, OPEN-21 deferred, OPEN-05 closed — all three IDs retired)

| ID | Item | Theme | Blast radius | Evidence |
|---|---|---|---|---|
| OPEN-01 | EUI denominator wrong for non-`applied` buildings (E-LA-41) | Reported numbers | 6,939 / 7,442 evaluated | ✅ |
| OPEN-02 | No fleet-scale EUI has a simulation-verified denominator (`.eio` deleted) | Reported numbers | every EUI, T08→T20 | ✅ |
| OPEN-03 | `layout_assign` models all internal loads as 2022-code regardless of real vintage | Reported numbers | ~half of a −29% cross-mode gap | 📄 |
| OPEN-04 | Labelled-accuracy gate drifted 92.0% → 88.0%, root cause unconfirmed | Reported numbers | classifier-wide | ⚠️ |
| ~~OPEN-05~~ | ~~`has_fatal` dead column logged twice~~ | **CLOSED 2026-08-05** — full ID sweep run, no further duplicates. See §3. ID retired. |
| OPEN-06 | Archetype labels wrong for 41 of 8,160 buildings (E-LA-38) | Simulation correctness | 41 buildings; 100% of failures | 📄 |
| OPEN-07 | 3 buildings regressed success → failure (E-LA-40) | Simulation correctness | 3 / 8,160 | ✅ |
| OPEN-08 | Archetype/vintage not reproducible locally for data-poor buildings (E-LA-22) | Reproducibility | all cross-generation comparison | 📄 |
| OPEN-09 | `thermal_mass=True` drives warmup non-convergence; "cosmetic" never tested (E-LA-23) | Simulation correctness | 64% vs 5.3% control | 📄 |
| OPEN-10 | `ZoneGroup` list-multiplier edit would restore exact expressibility (E-LA-37) | Capability | 90 buildings + future | ❓ |
| OPEN-11 | 6 inverted-geometry buildings need post-hoc remediation, not re-applied | Simulation correctness | 6 / 8,160 | ⚠️ |
| OPEN-12 | Rural `height_m` residual — `nyc_rural` 36.4%, `austin_rural` 19.2% still absent | Data acquisition | 2 cells | 📄 |
| OPEN-13 | E-UTCI-12 and E-UTCI-13, forwarded out of the UTCI arc | Data / Stage 6 | unknown | 📄 |
| OPEN-14 | UTCI height backfill is not reproducible from a clean checkout | Reproducibility | Stage 6 inputs | 📄 |
| OPEN-15 | Imputation Phase E — documented-deferred, never executed | Imputation | fleet inputs | 📄 |
| OPEN-16 | `ml` imputation tier built but permanently off | Imputation | opt-in only | 📄 |
| OPEN-17 | 6 variance-preserving draw-tier imputers built, off, awaiting a promotion decision | Imputation | opt-in only | 📄 |
| OPEN-18 | **Q3 — √S vertical-form distortion**, now confirmed unreachable by the mechanism built for it | Method | small buildings, cold cells | ✅ |
| OPEN-19 | LA runs ~+40% hot — Title 24 vs ASHRAE 90.1 question, never researched | Method | one whole city | 📄 |
| OPEN-20 | Wider validation matrix beyond 3 cities × 4 rings | Method | external validity | 📄 |
| ~~OPEN-21~~ | ~~Mixed-use classification key re-cut~~ | **DEFERRED to future by the user 2026-08-05** — one function per building stands; moved to `docs/docs_TODO/mixed_use_classification.md`. See §6. ID retired. |
| OPEN-22 | "Which exam does the answer key grade" — label-review basis undecided | Decision owed | accuracy metric itself | ⚠️ |
| ~~OPEN-23~~ | ~~`layoutGenerator` production zone-mode~~ | **EXCLUDED by the user 2026-08-04** — see §7.0. ID retired, not reused. |
| OPEN-24 | LIVE_SMOKE gate still parked from the June audit | Test integrity | Stage 3 → 4 | ⚠️ |
| OPEN-25 | Modules 04/05/06 bridge — named as the next construction project, June | Architecture | Stage 4/5 seams | ⚠️ |
| OPEN-26 | Manifest/provenance polish items (4, none load-bearing) | Housekeeping | reporting only | ⚠️ |
| OPEN-27 | A DESIGN doc carries a wrong name; must be fixed at the external source | Housekeeping | one doc | ⚠️ |
| OPEN-28 | **Cross-mode comparisons mix two harvest generations** — `layout_assign` is T20, the other four modes are still T08 | Reported numbers | every cross-mode claim | ✅ |
| OPEN-29 | **Defects last recorded OPEN that this register never adopted**, incl. E-LA-21 itself | Register hygiene | unknown, ~8 candidate IDs | ❓ |

**Next free defect ID: E-LA-42** (verified by full sweep 2026-08-05, OPEN-05). **Next free UTCI defect
ID: E-UTCI-17** (same sweep; stated in no other document). **Next free item ID: OPEN-30.**

> **Amendment 2026-08-05.** OPEN-28 added, found while auditing the `layout_assign` documentation
> surfacing work (`layoutAssigner/PLAN_docs-explanation-surfacing.md`, closed the same day). It had
> existed only as a figure caption, never as a tracked item. **It bundles with OPEN-01 and OPEN-02 —
> see OPEN-28's own section: one fleet re-run closes all three.**

---

## 2. Theme A — Integrity of the numbers we publish

This theme is first because it is the only one that can make *already-published* results wrong rather
than merely incomplete.

### OPEN-01 — The EUI denominator is wrong for every non-`applied` building ✅

**What is known.** In `layout_assign`, `match_storeys()` mutates the prototype **only** when it
returns status `applied` — its own docstring is explicit
(`openubem/geometry/layout_assigner.py:542-544`: *"every other status leaves `idf` untouched"*). So
`identity`, `fallback_shorter` and `fallback_not_expressible` all simulate the **prototype's** storey
count. Energy per unit area is then published against the **real** building's
`footprint_area_m2 × levels`. The error factor is `n_storeys_represented / num_floors`.

**Measured, directly** (`openubem/outputs/comparisons/r06c_local_results.csv`, real fleet buildings,
real `eplusout.eio`): `applied` buildings hold the assertion to ~0.002% (N=4). `MidriseApartment`
`identity` buildings fail at **exactly 4/3** (N=2) — the untouched prototype is a 4-storey-equivalent
(3 Z-bands × a `ZoneGroup` list multiplier of 2) simulated for a 3-storey building.

**Inferred from the code contract, not measured** — `t20_r10_reach_change.csv`:

| `num_floors` | n | factor `4 / num_floors` |
|---|---|---|
| 1 | 1,225 | **4.000×** |
| 2 | 1,048 | **2.000×** |
| 3 | 343 | 1.333× |
| 5 / 7 / 9 | 49 / 16 / 1 | below 1.0× |
| | **2,682** | (`MidriseApartment` non-`applied`) |

Fleet-wide **6,939 of 7,442** evaluated buildings are non-`applied`. Factors for the other 17
archetypes are **unmeasured**.

**The honest reading.** For a 1-storey building the mode simulates a 4-storey apartment prototype and
divides that energy by one storey's area. The published number is not wrong *for the building that was
simulated* — it is a correct number for the **wrong building**. This is the arithmetic expression of a
fallback design that was always documented (E-LA-33: height does not track `num_floors`), now
quantified for the first time.

**What is NOT known, and must be measured before any plan:**
1. `n_storeys_represented` per archetype — only `MidriseApartment` (=4) has been measured. This is a
   cheap read of the 25 baseline IDFs, no simulation.
2. Whether the correct remedy is (a) fix the denominator to match what was simulated, (b) make the
   simulation match the building, or (c) declare the mode's outputs per-prototype and stop publishing
   per-building EUI. **These are different projects.** (a) is a reporting fix; (b) reopens the
   mechanism R04 closed; (c) is a scope decision.
3. Whether any *adopted* result depends on this. `layout_assign` is not the adopted baseline —
   confirm that before sizing anything.

**Do not conflate with OPEN-02.** This is about the *numerator/denominator mismatch*; OPEN-02 is about
our inability to check it at scale.

### OPEN-02 — No fleet-scale EUI has a simulation-verified denominator ✅

**What is known.** Every EUI in every mode and every harvest T08→T20 divides by
`footprint_area_m2 × levels` from Stage-2 enrichment. The file that records what EnergyPlus actually
simulated, `eplusout.eio`, is deleted unconditionally by the shared cluster template —
**verified this session** at `scripts/cluster/submit_fleet_t08.sbatch:63`, `rm -f "$OUTDIR"/*.eio`,
inside a block whose stated purpose is disk economy (">800 GB untrimmed per city"). The template is
byte-identical across T08→T20.

**Consequence, stated plainly:** *no* fleet-scale EUI this project has ever published has a verified
denominator, and none can be reconstructed without re-running the fleet. The entire body of
verified evidence is 6 buildings run locally (OPEN-01).

**What must be decided before a plan:** whether to retain `.eio` on future runs. It is one line, but
the trade is real — the trimming exists because untrimmed output is >800 GB per city. Measure the
actual per-building `.eio` size first; it is a small text file and the fear may not survive contact
with the number. **That measurement is the whole of the investigation for this item.**

### OPEN-03 — Internal loads are modelled as 2022-code construction regardless of real vintage 📄

`layout_assign` runs ~29% below the other four resolution modes on median EUI. Roughly half of that
was traced at the 2026-07-26 close to a design property: internal loads come from
`ASHRAE901_*_STD2022` prototypes, so every building's lighting/equipment/occupancy is modelled as
2022-code **even though the envelope is re-patched to the building's real vintage and climate zone.**

**Status:** documented in results §7, never actioned. **Not re-verified this session.**

**What to measure first:** whether the loads-vs-envelope vintage split is deliberate (a documented
approximation) or an oversight in the patching path. The answer changes whether this is a defect or a
disclosure.

### OPEN-04 — The labelled-accuracy gate drifted 92.0% → 88.0% ⚠️

Surfaced during the input-framework classification-fixes arc (closed 2026-07-21) and explicitly
flagged "for a future arc". Still clears its pass gates. **Proven unrelated** to that arc's own
changes by a live before/after reproduction. Suspected but unconfirmed cause: the already-in-tree
Phase-D fusion/crosswalk work of 2026-07-13.

**Why it matters more than 4 points suggests:** an accuracy gate that drifts without anyone noticing
is a broken instrument regardless of whether it still passes. The open item is *the unexplained
drift*, not the 88%.

**First measurement:** bisect the gate across the commits between the R3-era reference and now. This
is cheap and mechanical, and it either confirms the Phase-D suspicion or falsifies it.

### OPEN-28 — Every cross-mode comparison mixes two harvest generations ✅
*Added 2026-08-05.*

**What is known, verified.** `layoutAssigner/figures/README.md:8`, written by the arc itself:

> **Provenance split.** Figures 2 and 5 mix two harvest vintages: the `layout_assign` bars/star are
> **T20** (2026-08-04); the `auto`/`building`/`floor`/`fast_zone` bars are still the **original T08
> harvest, never re-run on T20.** This is stated directly in both figure titles.

The same split runs through the prose. `docs_EXPLANATION/Results/OpenUBEM_results_Resolution.md` §4's
cross-mode EUI table is **T08 throughout** (2026-07-01); the new §10 is T20. Both are correctly
labelled in isolation. **Neither says that a comparison between them is not like-for-like.**

**Why this is an open item and not a caption.** Between T08 and T20 the codebase changed
substantially — E-LA-20's convergence fix alone recovered 150 buildings, and the storey-matching
arc's R01/R02/R03/R10 all landed. So any cross-mode difference currently reported is **the method
difference plus everything that changed in the code between July and August, with no way to separate
them.** The mode comparison is the thing the resolution-mode feature exists to support, so this is
not a peripheral defect.

**It is worse than "older code", because of OPEN-08.** E-LA-22 establishes that re-running a past
generation at current HEAD silently diverges in **archetype and vintage** for data-poor buildings. So
the two harvests may not even be describing the same buildings the same way. That confound is
**unquantified**. Read OPEN-28 and OPEN-08 together.

**The −29.1% figure inherits this.** The arc results doc §7.2 reports `layout_assign` running ~29%
below the other four modes on median EUI, and OPEN-03 attributes roughly half of it to the 2022-code
internal loads. **Which harvest each side of that −29.1% came from has not been established** — that
is part of the first measurement below, not an assumption to carry forward.

**The bundle — this is the operationally useful part.** One fleet re-run of **all five modes on one
harvest, retaining `eplusout.eio`**, closes three items at once:

| Item | What the re-run gives it |
|---|---|
| **OPEN-01** | a verified, multiplier-aware denominator for every building instead of a 6-building local sample |
| **OPEN-02** | the `.eio` file that has never existed for any fleet building |
| **OPEN-28** | all five modes on one generation, so a cross-mode delta means the method |

It requires one change to `scripts/cluster/submit_fleet_t08.sbatch:63` (stop deleting `*.eio`) and a
disk-budget check — the trim exists because untrimmed `fast_zone` city passes exceed 800 GB, so
**retaining `.eio` is a storage decision, not a one-line edit.** That check is the gate on the bundle.

**What is NOT known, and must be measured before any plan:**
1. **How many buildings are actually shared** between T08 and T20 with identical Stage-2 inputs, and
   whether their archetype/vintage agree. This is a table join, no simulation, and it directly
   quantifies the OPEN-08 confound.
2. **The `.eio` disk cost** for one full five-mode fleet pass. Needed before the bundle can be sized
   at all. A per-building `.eio` size × 8,160 × 5 estimate from any existing local run is enough.
3. Whether a **cheaper subset** suffices — one cell, or one archetype family, re-run across all five
   modes — to establish the harvest-generation effect without a full fleet pass. If the effect is
   small, the full bundle may not be justified; if it is large, no existing cross-mode number stands.

**Do not conflate with OPEN-02.** OPEN-02 is that we cannot verify a denominator at all. OPEN-28 is
that the five modes were not measured at the same time. They travel together operationally but they
are different defects, and OPEN-28 would remain even if every denominator were verified.

---

## 3. Theme B — Register hygiene

### ~~OPEN-05~~ — The same defect is logged twice, as E-LA-21 and E-LA-39 — **CLOSED 2026-08-05** ✅

**Disposition.** The item's required first measurement — sweep the full `E-LA-nn` and `E-UTCI-nn` ID
space for further duplicates — **has been made.** Report:
`docs/docs_ACTIVE/openings/extra/MEASUREMENT_open-05_defect-id-sweep.md`.

**Result: no further duplicates exist.** 41 logged `E-LA` IDs (01–41; `E-LA-42` appears only as a
"next free" marker, not a defect) and 16 logged `E-UTCI` IDs (01–16). **Both sequences are fully
dense — no gaps, so no lost records.** No ID carries two unrelated meanings. Three further candidate
pairs were examined and all three rejected with reasons (E-LA-06 vs the E-LA-14/16/18/19/23 lineage —
already self-corrected by the project at its own 2026-07-26 audit; E-LA-33 vs E-LA-34 — same origin,
different objects, one fix does not close both; E-LA-38 vs E-LA-40 — subset population but the causal
link is explicitly an unconfirmed hypothesis). **E-LA-21 = E-LA-39 remains the only true duplicate.**

**Director audit, 2026-08-05.** Both ID ranges were independently re-enumerated by the director from
the working tree; the inventory reproduces exactly. The sweep's method was validated by requiring it
to rediscover the known E-LA-21/E-LA-39 pair without being given it as an answer — it did, from the
raw content sweep. **Signed.**

**Standing consequence, carried forward:** treat **E-LA-39 as an alias of E-LA-21**. Neither frozen
progress-log entry is to be rewritten. **Next free IDs: `E-LA-42`, `E-UTCI-17`** — the latter was
derived here and appears in no other document.

*(Original entry preserved below, unedited.)*

### OPEN-05 — The same defect is logged twice, as E-LA-21 and E-LA-39 ✅

**Found while compiling this register.** Both describe the identical defect: the harvest scripts'
`has_fatal` column tests for `"** Fatal **"` (one space) against EnergyPlus's real `"**  Fatal  **"`
(two spaces), so it reads `False` on all 8,160 rows — including the 7 that carry a literal Fatal.

- **E-LA-21** — logged 2026-07-25, `e-la-20/PLAN_e-la-20_investigation.md:493`, carried OPEN through
  two subsequent plans as explicitly out of scope.
- **E-LA-39** — logged 2026-08-04 in the storey-matching arc, registered as a **new** finding.

**This is the failure mode the register is meant to prevent:** an open defect that stays open long
enough to be rediscovered, consuming a second ID and a second audit. **Neither entry should be
rewritten** (both are frozen progress-log records) — the correction belongs here and in whichever
plan next touches the harvest scripts. **Treat E-LA-39 as an alias of E-LA-21.**

**Before opening any work:** sweep the full `E-LA-nn` and `E-UTCI-nn` ranges for further duplicates.
One found by accident implies others found the same way.

### OPEN-29 — Defects whose last recorded status is OPEN, that this register never adopted ❓
*Added 2026-08-05, found by the OPEN-05 sweep — which was not looking for it.*

**How it was found.** The OPEN-05 sweep had to inventory every `E-LA-nn` ID with its status in order
to compare descriptions. That inventory (`extra/MEASUREMENT_open-05_defect-id-sweep.md` §2.1) shows roughly
**eight IDs whose last status word at their own defining site is OPEN, and which appear nowhere in
this register as an item.** Candidates, from the sweep's own status column: **E-LA-06** (the
flow-balance half, *"never revisited"*), **E-LA-11**, **E-LA-12** (*"OPEN, LATENT/MASKED IN
PRODUCTION"*), **E-LA-13**, **E-LA-15**, **E-LA-16**, **E-LA-17**, **E-LA-18**, **E-LA-19**,
**E-LA-30**, **E-LA-33**.

**And E-LA-21 itself.** Closing OPEN-05 closes the *duplication*, not the *defect*. The `has_fatal`
column is still dead fleet-wide and, with OPEN-05 struck, it is now tracked in this register **only**
inside a closed item's disposition. That is precisely how it got rediscovered as E-LA-39 in the first
place. It is named here so it cannot happen a third time.

**Why this is ❓ and not a finding.** A status word at a defect's *defining* line is not its current
status — several of these were very likely closed by later work whose closure note lives in a
different document. The sweep read defining sites, not closure trails, because that is what
deduplication required. **The candidate list above is unverified and must not be treated as a list of
live defects.**

**First measurement.** For each candidate ID, follow its citations forward to the latest document that
mentions it and record its *final* recorded status, with a `path:line`. Output: a two-column table —
genuinely-still-open vs closed-elsewhere. Cheap, mechanical, no simulation. Only the first column
becomes register items.

**Why it matters more than housekeeping.** The register's stated purpose is to be *the single place
open work is recorded*. If defects can be OPEN at their own defining line and absent from the register,
then the register is not yet that place, and its completeness claim (§0) is overstated. This item is
the register auditing itself.

---

## 4. Theme C — Simulation correctness

### OPEN-06 — Archetype labels are wrong for 41 of 8,160 buildings (E-LA-38) 📄
33 `LargeHotel` + 8 `SmallHotel` are labelled as Office archetypes by `05_results.gpkg`, the archetype
source shared unchanged since T17. **All 7 of the T20 fleet's failures are true `SmallHotel`** — 7 of
the fleet's 8 (87.5%), against 0.00% failure everywhere else. The fleet's only failure population *is*
the mislabel population.

**First measurement:** whether the mislabel originates in `05_results.gpkg` itself or in a step that
writes it. Fixing the symptom in the harvest would leave the source wrong.

### OPEN-07 — Three buildings regressed from success to failure (E-LA-40) ✅
`la_urban/way/401910463`, `nyc_rural/way/965718402`, `nyc_rural/way/965718403` — all inside the
E-LA-38 population above. 3/8,160 = 0.037%. A multiplier-scaling-tips-a-warmup-divergence mechanism
was proposed and is **a hypothesis, not a cause**. Likely closes as a side effect of OPEN-06; confirm
rather than assume.

### OPEN-08 — Archetype and vintage are not reproducible locally for data-poor buildings (E-LA-22) 📄
Re-running a past fleet generation at current HEAD silently diverges in archetype *and* vintage for
buildings with missing inputs. Leading suspect: a semantic-imputation commit landing after the fleet
run. **This is the item that quietly limits every other item** — any cross-generation comparison
(T17 vs T20, before vs after) rests on it. Findings on well-tagged buildings survive it; findings that
span generations may not.

**First measurement:** pin the divergence to a commit. Until then, treat every cross-harvest delta in
this project as carrying an unquantified confound.

### OPEN-09 — `thermal_mass=True` drives warmup non-convergence, and "cosmetic" was never tested (E-LA-23) 📄
A matched control measured 96/150 (64%) engaged rows non-converging vs 8/150 (5.3%) in the control —
same buildings, same code, one variable. Two consequences were forwarded and never decided:
(a) a fixed fleet run at `thermal_mass=True` projects ≈299/8,160 ≈ 3.66% (**a projection, not a
measurement**); (b) the **"cosmetic" label has been inherited unexamined across five log entries**
(E-LA-14/16/18/19/23) and is a claim about *accuracy* that nobody has ever tested.

**The open item is (b).** It is answerable: compare EUI on converged vs non-converged runs of the same
buildings.

### OPEN-10 — Editing the `ZoneGroup`'s own list multiplier would restore exact expressibility (E-LA-37) ❓
A different mechanism from the one built (which writes `Zone.Multiplier`). Would restore exact storey
matching at every `n_real` rather than only `{10, 18, 26, …}` / even `n_real ≥ 4`. **Never tested** —
this is a believed capability, not a measured one. R04 is closed at option (a), so opening this is a
deliberate reopening, not a continuation.

### OPEN-11 — Six inverted-geometry buildings still need post-hoc remediation ⚠️
The Phase-E re-run landed 8,154/8,160; the 6 drops are the REPORT §7 limitation-#6 inverted-geometry
buildings whose `10_fails_solution.md` remediation was not re-applied in the automated run.
Pre-existing, small, and **recorded as not-a-defect-of-that-arc** — but never closed. Confirm the 6
are still the same 6 before planning anything.

---

## 5. Theme D — Data acquisition and imputation

### OPEN-12 — The rural building-height residual 📄
`nyc_rural` 36.4% and `austin_rural` 19.2% of buildings still carry no `height_m` after the UTCI
arc's backfill. The arc's own closing note is unusually clear about the remedy and worth quoting as a
constraint on any plan: **closing this needs better source coverage, not another imputation pass.**

### OPEN-13 — E-UTCI-12 and E-UTCI-13 📄
Forwarded out of the UTCI arc at close, to "whichever arc next owns Stage-1 acquisition or Stage-2
imputation". **Content not re-read this session** — read `docs_DONE/OUTDOOR/UTCI/` before planning.

### OPEN-14 — The UTCI height backfill is not reproducible from a clean checkout 📄
The fix lives in the mechanism rather than in committed data. Anyone rebuilding Stage 6 from a fresh
clone does not get the backfilled heights. This is a **reproducibility defect in shipped inputs**,
which makes it structurally different from the two items above it — and arguably more urgent, because
it silently invalidates a rebuild rather than degrading a known cell.

### OPEN-15 / OPEN-16 / OPEN-17 — The imputation tiers that are built and switched off 📄
- **Phase E** — documented-deferred, never executed.
- **`ml` tier** — built, verified EUI-neutral and not harmful, permanently off.
- **Draw tier** — 6 variance-preserving imputers built opt-in/OFF; the CP-DRAW leaderboard found **no
  method dominates on every axis**, and the promotion decision was never taken.

These are one decision, not three: **does this project want a non-deterministic input tier at all?**
Recorded in memory alongside a hard-won constraint — NMBE is blind to variance collapse and must never
be used alone as an imputation-accuracy metric (measured variance ratios 0.06–0.31).

---

## 6. Theme E — Method and validation questions

### OPEN-18 — Q3, the √S vertical-form distortion ✅
**The largest open modeling problem in the project.** `scale_baseline_idf()` scales vertices in plan by
√S while preserving height, so a 79 m² building becomes a 4-storey prototype shrunk to 2.5% of its
area with all 27 zones and an extreme surface-to-volume ratio. Isolating one cell to remove the
climate confound: `layout_assign` heating is **~2× `auto` at every building size** — a *stable* ratio,
i.e. geometry, not an unscaled-quantity defect. Median S for `MidriseApartment` is 0.054; 67% of rows
are under 500 m².

**New as of 2026-08-04, and it narrows the search:** the storey-matching arc built the
`Zone.Multiplier` mechanism that the base plan named as Q3's "obvious first candidate", and it is now
**confirmed structurally unable to close it** — twice over. It expresses only `n_real > n_proto`
(taller) while Q3's population is the shorter case; and it changes simulated load, not rendered
geometry, so it could not address a vertical-form defect even if extended. A candidate has been
eliminated with evidence, which is progress.

**What remains open:** a mechanism that actually removes zones, or archetype re-selection by height
(which would relocate Q3 from a Stage-3 geometry defect to a Stage-2 assignment defect). Both are
materially larger than anything closed so far. **Neither has been scoped, and this document does not
scope them.**

### OPEN-19 — Why does LA run ~+40% hot? 📄
Established as **not** the zoning defect (a zoning fix moved it −0.6%), so it is a real
climate/HVAC-response problem. The named hypothesis — California Title 24 vs our ASHRAE 90.1
archetypes: envelope U-values, infiltration, HVAC COP and economizers for cooling-dominated CZ 3B —
has **never been researched**, and was explicitly gated on a user go/no-go for a calibration phase.

**Note the tension with a standing project rule:** the current baseline carries a **zero-fitted-
parameters** guarantee. A "calibration phase" must be defined carefully or it breaks that guarantee.
That definitional question is the first thing an execution plan would have to settle.

### OPEN-20 — Wider validation matrix 📄
Backlog since 2026-06-17. Extend beyond 3 cities × 4 urban-form rings. Blocks nothing; bounds how far
any result can be generalised.

### ~~OPEN-21~~ — Mixed-use classification key — **DEFERRED by the user, 2026-08-05**

**Ruling, verbatim in intent:** this is an important question the project has never actually decided;
**for now we progress with one function per building and the current behaviour stands.** Recorded as a
future task, not a live item. **The question is closed to further asking — do not put it to the user
again.** A future arc opens it deliberately from its own document.

Moved to **`docs/docs_TODO/mixed_use_classification.md`**, which carries the full record: the
verified current behaviour, the four questions a future arc must settle, and the first measurement
required before any plan.

**One fact was established before deferral and belongs in the register** (verified at HEAD 2026-08-05,
`openubem/semantic/building_classifier.py:110-113`, `:307`, `:324-325`, `:352`): a building is called
`mixed` only when its two tags disagree, which hard-codes its dominance score to `0.5`; rule 15
requires `>= 0.60`; so rule 15 is unreachable and **every mixed-use building in the project is
currently simulated as a `MidriseApartment` at MEDIUM confidence.** That is the status quo the ruling
preserves. It is undocumented in any output. **How many fleet buildings this affects is unmeasured** —
that count is the deferred item's first measurement.

**ID OPEN-21 is retired and must not be reused.** Deferred, not closed and not excluded: unlike
OPEN-23 this is a direction the project may still take, it is simply not being taken now.

### OPEN-22 — "Which exam does the answer key grade" ⚠️
From the June audit, parked awaiting a ruling, still parked. Whether the label review grades *what the
tags say* or *what the building really is*. Until this is settled, **the accuracy metric itself is
undefined** — which is worth reading alongside OPEN-04's unexplained 4-point drift in that same metric.

**Status 2026-08-05 — the item's stated premise is FALSE at HEAD. ✅ verified.**

Put to the user this session. The June finding (`INVESTIGATION_steps-1-3-audit.md:99-103`, W2.8) rests
on two claims about classifier behaviour. **Both were checked against
`openubem/semantic/building_classifier.py` at HEAD and both are stale** — the R3-era coverage work
(`E-R3-1`, `E-R3-2`) changed the code underneath the audit without the audit being revisited:

| W2.8 claim (2026-06-09) | Status at HEAD 2026-08-05 |
|---|---|
| "19/50 rows are generic `building=yes` … the classifier will correctly emit `OpenUBEMUnknown`" | **FALSE.** Rule 17a (`:327-329`, tagged `E-R3-2`) routes `use_class == "unknown" and building_tag == "yes"` to `_office_size_tier(...)` — a **size-bucketed office**, at LOW confidence (`:356-357`). `OpenUBEMUnknown` (`:331-332`) is now reached only when there is **no** usable building tag at all. |
| "office tiers were suggested using *total floor area* while DESIGN §3C uses *footprint only*" | **FALSE / inverted.** `:186-187`, tagged `E-R3-1`, states *"office size metric is total floor area (footprint × levels)"* and computes `total_floor_area_m2 = footprint_area_m2 × max(levels, 1)`. Both office paths (`:296`, `:329`) use it. **The code now uses the same metric the human labels used.** |

**What this does to the item.** The conflict as recorded is largely dissolved — the classifier now
produces office archetypes for exactly the rows the labellers called offices, by the same size metric.
**But the philosophical question is not dissolved, it has moved**, and is arguably sharper:

> Rule 17a means that when the map data says only *"this is a building"*, the project **guesses
> office, bucketed by size**. If the human answer key also guessed office for those rows, then the
> labelled-accuracy metric is scoring **agreement between two guesses**, not correctness. A metric
> that rises when the fallback and the answer key are tuned toward each other is not measuring the
> classifier.

**Revised first measurement — do this before any ruling.** Run the current classifier over the 50-row
labelled fixture and produce the confusion detail: for each row, the label, the emitted archetype, the
rule token that fired (`RULE_*` vs `FALLBACK_SIZE_DEFAULT` vs `FALLBACK_UNKNOWN`), and the confidence
tier. Then report **what the accuracy number is once rows decided by `FALLBACK_SIZE_DEFAULT` are
excluded.** That single split — earned matches vs fallback-agreement matches — is what the user needs
to rule with, and it does not exist today. Measurement only; no relabelling inside it.

**Connects to OPEN-04.** OPEN-04's unexplained 92.0% → 88.0% drift is in this same metric, and its
suspected cause (Phase-D fusion/crosswalk, 2026-07-13) has never been confirmed. If a meaningful share
of the metric is fallback-agreement, then the drift may be a change in **tag coverage**, moving rows
across the rule-17a boundary, rather than a change in classifier logic at all. **That is a new,
unverified hypothesis, recorded here as a lead, not a finding.** The measurement above tests it for
free — it is the same run.

⚠️ **Also stale and NOT re-run:** the Boston 41.0% / Chicago 65.4% real-fixture distributions
(`INVESTIGATION_steps-1-3-audit.md:93`) predate `E-R3-2`. Rule 17a converts former FALLBACK rows into
LOW-confidence offices, so those two percentages **cannot be assumed to still hold** and must not be
carried into any plan.

This remains the cheapest item left in the register — but it is no longer "a decision, not an arc": it
needs one small measurement run first.

---

## 7. Theme F — June-audit remnants

### 7.0 — ~~OPEN-23~~ `layoutGenerator` — **EXCLUDED from this register by the user, 2026-08-04**

Room-level interior zoning for non-rectangular footprints (L/U/T/courtyard). DESIGN-buildout closed
2026-07-05; CP-3 met; Phase 5 reached a cluster pilot but CP-4 user sign-off was never reached because
the user wants a root-level engine redesign first.

**User decision, 2026-08-04: this is not an option we are continuing with, and it is excluded from the
register.** Recorded rather than deleted, per this document's own rule that removed items carry a
reason (§9, pattern 4). **The ID OPEN-23 is retired and must not be reused.**

This does not close the arc and does not delete anything — the engine's full record stays where it is,
under `docs/docs_TODO/layoutgenerator/`, and a future redesign could still revive it for the
room-level-fidelity use case that `layout_assign` does not address. It is simply **not open work**, so
it does not belong on a list of open work. Do not re-add it without a new instruction from the user.

### OPEN-24 to OPEN-27 — Remnants of the 2026-06-09 steps 1–3 audit ⚠️
That audit's remediation went green (265 passed), but four items were marked **⏳ STILL OPEN** and have
not been revisited in ~8 weeks. **All four are stale-risk and must be re-checked against current code
before being believed:**
- **OPEN-24** — the LIVE_SMOKE gate (real 23.1 IDD + a real EnergyPlus design-day run) is still
  parked. It was called *"the recommended next remediation block"*. Given this project's recorded
  standing lesson that synthetic-green ≠ live-green, this is the most consequential of the four.
- **OPEN-25** — the Modules 04/05/06 bridge, described in June as *"the next construction project,
  not a defect"*. Whether that is still true is itself unverified.
- **OPEN-26** — four manifest/provenance polish items, none load-bearing.
- **OPEN-27** — a DESIGN doc carries a wrong name; DESIGN docs are read-only here and generated in the
  user's external LLM, so **only the user can fix this at source.**

---

## 8. What is closed and must not be reopened by mistake

Recorded so that a future reader does not mistake a settled decision for an open one:

- **The post-Phase-E "Other" residual** is process + miscellaneous plug loads only. The STOP decision
  on it is **permanent**.
- **R04 is closed at option (a)** — `layout_assign` ships matching thermal-zone topology and plate
  geometry, **not** building height. OPEN-10 and OPEN-18 would each reopen a piece of this
  deliberately; neither should happen by drift.
- **`T_ENGAGE = 0.868 m` and `T_MASS_MAX = 0.35 m` are frozen** on direct measurement. A fleet failure
  reopens the fix plan, never the constants.
- **Any mass-preserving fix to the CTF-convergence defect is dead on arrival** — proven, not assumed.
- **E-LA-20 is fixed and verified** 150/150 on the real production path.
- **Q3's `Zone.Multiplier` candidate is eliminated** (OPEN-18). Q3 stays open; that *approach* does not.
- **`layout_assign` is adopted for zone/HVAC-topology studies and NOT certified for fleet-level EUI
  reporting.** That disposition is current as of 2026-08-04, not a legacy caveat.

---

## 9. Observations across the register

Four patterns are visible only when the items sit in one list, and each is itself worth a decision:

1. **Four items (OPEN-01, 02, 03, 04) can make already-published numbers wrong.** Every other item
   makes the project *less complete*. That is a categorical difference, and it is not reflected in how
   these items have been prioritised historically.
2. **Two items (OPEN-08, OPEN-14) are reproducibility defects**, and they undercut the evidence for
   other items rather than standing alone. OPEN-08 in particular puts an unquantified confound under
   every cross-generation comparison this project has made.
3. **~~Two items~~ One item (OPEN-22) costs a decision, not an arc** — it leaves the accuracy metric
   undefined while OPEN-04 reports an unexplained drift *in that same metric*. Those two should be
   read together. *(OPEN-21 was the other; deferred 2026-08-05 — see §6.)*
4. ~~**The register found a duplicate on its first pass** (OPEN-05). The `E-LA-nn` space has not been
   swept for others.~~ **Resolved 2026-08-05:** the space *was* swept, and E-LA-21/E-LA-39 is the only
   duplicate — but the sweep incidentally exposed a different hygiene defect, **OPEN-29**: defects can
   be OPEN at their own defining line while absent from this register. The pattern to carry forward is
   therefore not "duplicates" but **"the register does not yet demonstrably contain everything open."**

---

## 10. Next step

**This document ends here by design.** Execution plans are written per the project's normal workflow
— manager authors `PLAN_*.md`, fresh executors run it — **after** the user picks which item or bundle
to open, and after the "first measurement" named in that item has been made.

Nothing in this register is scheduled. Nothing is assigned. No cluster time is committed.
