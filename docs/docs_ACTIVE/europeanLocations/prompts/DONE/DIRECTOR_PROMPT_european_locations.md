# DIRECTOR PROMPT — European locations (v4: the floor plans)

**Project:** OpenUBEM × GSSCanada Step 8 · **Working directory:** `C:\Users\o_iseri\Desktop\OpenUBEM`
**Arc root:** `docs/docs_ACTIVE/europeanLocations/` · **Rewritten lean 2026-08-31 (night).**

**Read, in this order, before acting — and nothing else:**

1. This file.
2. `STATE_european_locations_v4.md` — read-first state, current truth only, never appended below an entry.
3. `BRIEF_european_locations_v4.md` — the same thing in plain language.
4. `prompts/DIRECTOR_PROMPT_group_floor_plans_2026-09-01.md` — **the task prompt in force**: the ten
   shape groups, one floor-plan rule each, and the route to 95 %. Read it before touching any rule.
5. `implementation/PLAN_eu21-group-schemes-2026-09-01.md` — the scheme tasks (P01–P07) and their log.
6. `rules/` — this folder, and only this folder, defines what "according to our rules" means.

**History, cited by section and never re-read wholesale:**
`prompts/previous/DIRECTOR_PROMPT_european_locations_2026-08-31_v3.md` (`D-EU-01`…`D-EU-48`,
`FINDING 001`…`FINDING 210`, the v1–v3 narrative, the Speed waves, the frozen scientific decisions and the
definition of done), and through it `previous/DIRECTOR_PROMPT_european_locations_2026-08-30.md`.
**v3 is cancelled (`D-EU-53`) — nothing in it is executed any further.**

---

## 0. The mission of this session, and the two rules that outrank it

🔴 **Drive the arc to the floor-plan pages in `plans3D/`, continuously, and stop there.**
Owner, 2026-08-31: *"je vais ouvrir une autre session de l'execution jusqu'a la visualisation des plans ici
…\plans3D en avant des simulations … je laisse lui continuer jusqu'a la visualtizions"*. Ruling `D-EU-56`:
packages `EU-18a` (T01–T03), `EU-17` (T04–T11) and `EU-18b` (T12) run **to the end without waiting for the
owner**. Audit each slice, write its progress-log entry, dispatch the next.

🔴 **`D-EU-55` — nothing simulates without the owner's own sentence.**
> *"ne jamais commencer des simulations sauf que mon permission, donc commencer des plans. jusqu'a la fin"*

Covers **every** EnergyPlus run: the Speed campaign, a single-district rerun, a one-building probe, the T13
sample battery. Building IDFs, censuses, the pages, the parity gate and pytest are **geometry, not
simulation** — they proceed freely. Permission is per wave and verbatim, in the owner's words; a relayed
"continue", an approved plan or a signed checkpoint is **not** permission. An executor that reaches a
simulation task stops and reports the exact command it would have run. Never prepare-then-run in one breath.

🔴 **`D-EU-54` — the pages carry geometry only.** `plans3D/PLANS_<district>.html` + `index.html`, drawn from
the **emitted IDF** and never from the side-car. Allowed: footprint, per-storey plan, dwelling polygons,
circulation ring, scheme name, storey index, dwelling count, gross and conditioned area, refusal reason,
circulation share and the `FINDING 204` out-of-band tag. Forbidden, including in tooltips and hidden
fields: EUI, demand, any E+ output, RC/severe/fatal counts, run or job ids, weather.

🔴 **The bar is `D-EU-39`: ≥ 95 % ruled in *every* district, measured on the IDFs**, not a fleet average and
not on side-cars. `rules/EXAMPLE_dwelling_layout_validation_2026-08-28.md` §6 (five conditions, eight named
buildings) is the regression the relaxation must still pass.

---

## 1. Current moment — 2026-09-01

🔴 **`D-EU-63` (2026-09-01) — the ten-group rule document is delivered and has been reviewed group by
group by the owner.** `rules/RULES_dwelling_layout_groups_2026-09-01.html` (92 KB, generated, static SVG,
no JS) carries one sheet per group: two drawings of **the same building** — the plate as surveyed, then
the very same plate cut by the engine into flats `F1…Fn` plus a hatched circulation zone — beside the
filter, the plate statistics, the circulation rule, the thermal zones per floor and the scheme. The
coverage table is in plain English with the term defined above it; **engine vocabulary is barred from every
user-facing string** (owner: *"'ruled today'????"*). Task prompt:
`prompts/DIRECTOR_PROMPT_group_floor_plans_2026-09-01.md` §2 records the owner's verdict per group and the
four fixes already made — same-building figures, the S5 gallery ring, cores on groups 09/10, and the
renames `TRIANGLE` → *Triangle or trapezoid* / `TRAPEZOID` → *Parallelogram* (display names only; the
on-disk group keys are unchanged). **One thing is waiting on the owner:** `courtyard_gallery_ring` (S5) is
a director proposal, drawn on sheet 01 but **not in the engine** — it is written only if the owner adopts
it, and then additively, behind `courtyard_wing_unfold` and `courtyard_perimeter_band`. Next free
`D-EU-64`.

🔴 **`D-EU-64` (2026-09-01) — one core per plate; leftover space belongs to the flats.** Owner ruling on
the group document: a plate carries exactly **one** circulation zone, the interior stair core. Every other
pocket the scheme leaves against the outer wall is **folded into the flat it adjoins** — *"generally
circulation or core is in the center … adding the other core zones inside the flats, it is highly
possible"* — and no square metre of the plate may be left unassigned (the courtyard sheet had white space
beside `F3`). Applied to the document today: cores 2 → 1 on L shape, U or T and Complex multi-wing;
circulation falls to **8 % · 7 % · 6 %** of the plate, in line with the ~9 % of the ruled grids; plate
coverage is 99.9 % on all ten sheets. **Not yet in the engine** — `european_residential.py` still emits the
extra pockets; adopting this is a separate, additive change the owner has not ordered. Next free `D-EU-65`.

🔴 **FINDING 224 (2026-09-01, superseded in presentation by `D-EU-64`) — `regularized_envelope_grid` pays
for irregularity in unheated area.**
The scheme puts the flats on the largest inscribed rectangle and hands the **whole residue** to the
circulation zone (`european_residential.py:1776-1781`), so circulation is core + residue, not a core: on
the drawn representatives it reaches **23 % (L shape) · 31 % (U or T) · 36 % (Complex multi-wing)** of the
plate against ~9 % for every `ruled_grid_NxM` plate. It is refused past a 0.35 residual fraction, so the
scheme is bounded — but a group cut this way carries a materially smaller conditioned fraction than the
same building cut by a wing decomposition, and the two are **not comparable on floor-area-normalised
demand**. Never pool them in one EUI without stating the split. Under `D-EU-64` the document no longer
shows that residue as circulation — it is given to the flats — so **the finding now describes the engine,
not the drawing**, and the gap between the two is itself the open item. Next free `FINDING 225`.

🔴 **Stop-and-report 3 FAILED — owner rejected the `plans3D/` pages as delivered.** Owner, verbatim:
*"no you failed, this is not what i want update this prompt ... i will continue with fresh session"* — said
after opening `plans3D/PLANS_ES-MAD-BERRUGUETE.html` and comparing it, unprompted, against
`rules/RULES_dwelling_layout_scheme_2026-08-28.html`. The rejected page is a bare dark-theme JS
building-browser (sidebar list + on-click SVG storey panes, `~230` lines, self-built styling). The file
the owner pointed at as the bar is a published Claude Artifact: light "Public Sans"/"Archivo"/"IBM Plex
Mono" typeset document, sectioned with an eyebrow/tally/rulehead layout, redrawn dwelling plans presented
as a designed report rather than a raw interactive tool. **The delta between the two has not been
narrowed to a spec** — do not invent one. First action of the next session: get the owner's own sentence
on what specifically is wrong (interactivity vs. static-document form, visual design language, page-per-
building vs. one-document-per-district, or something else) before touching `scripts/eu18_emit_plan_pages.py`.
Next free `D-EU-59` (this rejection has not yet been given a ruling number — assign one once the owner's
requirement is captured, not before). Next free `FINDING 221` (unused so far).

- T02/T03 code (`scripts/eu18_emit_plan_pages.py`, `scripts/eu18_parity_gate.py`) is otherwise sound —
  the rejection is presentation only, not the underlying geometry-extraction logic. Do not re-run T04–T15;
  they are audited complete (below). Do not touch `D-EU-54`'s content rules (geometry-only, no EUI/E+/RC)
  when redesigning the page — those still apply to whatever new format is agreed.

🔴 **`FINDING 221` — 941 buildings are already ruled and are thrown away at IDF-writing time, not by the
rules.** Measured 2026-09-01 by the director directly on the EU-17 tree (side-car `geometry_outcome`
tally vs. the IDFs' own zone names): `DWELLING_LAYOUT_EMITTED_INTERZONE_MISMATCH_REROUTED` = ES 434 ·
FR 91 · GB 21 · IT 395 = **941**, every one of which carries only a `_whole` zone in the `.idf` that
would simulate. Cause is `FINDING 210`'s safety net: `build_idf_for_building` silently rewrites `zones`
to `one_zone_per_floor` when geomeppy's `intersect_match` leaves an unresolved interzone vertex mismatch
(`run_eu_s2_district_campaign.py:388-392`, `emit_eu11_layout_sidecars.py:299-309`); `FINDING 219`
(`ZeroDivisionError` on rotated multi-storey stacks) is the same defect seen from the other side.
**Consequence for the 95 % bar:** ruled coverage measured on the IDFs is 541/2,544 = 21.3 %
(ES 194/961 · FR 105/297 · GB 17/82 · IT 225/1,204); repairing the reroute alone lifts it to
**1,482/2,544 = 58.3 % with no rule changed at all**. Only the remaining 1,096 true refusals
(L-shape 739 + courtyard 249 = 90 % of them) need the additive scheme catalogue, and 95 % requires
**935 of those 1,096 (85 %)** to be recovered by it. Owner instruction 2026-09-01: *"do not change the
current ones, just add"* — the two figure-4.2 schemes stay byte-identical, new schemes are appended and
tried only after they refuse. Next free `FINDING 222`.

- The 917 massing boxes with no refusal-census row are exactly this population — they were never refused,
  so no cause was ever recorded for them. `refusal_census.csv` covers only the 1,096 real refusals.

🔴 **`D-EU-60` (owner, 2026-09-01) — the rule set is the durable product, and the arc runs to the end.**
Three owner sentences, verbatim: *"i like this document i do not want to you change it … create another
version based on the groups, you can check the buildings and define groups, then propose schema for each
group and we can apply these"* · *"because rule set important to me, we will expand the building and
country database later we will use these rule sets in order to expand"* · *"continuer jusqu'a la fin"*.
Consequences, all binding:
1. `rules/RULES_dwelling_layout_scheme_2026-08-28.html` is **frozen** — never edited, never regenerated.
   The group document is a **new, additional** file beside it.
2. The two figure-4.2 schemes stay byte-identical. New schemes are **appended** and tried only after the
   existing ones refuse (`FINDING 221`).
3. Every group boundary and every new scheme must be **dimensionless or metric-absolute** and nameable as
   a European building typology — no percentile of this fleet, no threshold tuned to hit 95 %, no
   district- or country-conditional rule. The rule set will be reused to expand the building and country
   database, so it must be computable for a country the project has never touched.
4. The arc runs continuously without owner pause **up to but excluding** any EnergyPlus run — `D-EU-55`
   is untouched by this ruling.
5. **Token discipline is a dispatch rule, not a preference** (owner flagged a 168 k-token executor):
   every dispatch prompt caps command output, forbids printing CSV/JSON/SVG/log bodies, and states the
   report format. `model: "sonnet"` always explicit; the director never writes feature code.

**Work in force:** `implementation/PLAN_eu20-morphology-atlas-2026-09-01.md` (M01–M04, the morphology
census + one named representative per group) — dispatched 2026-09-01. The scheme proposal per group and
the new grouped rules document are the **director's** work, written from that plan's output, not an
executor's. Next free `D-EU-61`.

---

🔴 **FINDING 222 (2026-09-01) — morphology is the second problem, not the first.** EU-20 measured all
2,544 footprints and joined them to the emitted outcomes. The ruled share is nearly flat across shape —
`COMPLEX_MULTI_WING` 9.9 % … `SLAB` 35.7 %, with `SQUARE` at 29.1 % and `RECTANGLE` at 25.1 %. A square
plate is the textbook case the ruled grid was written for, so it cannot be failing on shape, and it is
not: 143 of `SQUARE`'s 156 boxes and 121 of `RECTANGLE`'s 152 are `FINDING 221` reroute victims. Fleet
split: **541 emitted · 941 rerouted · 1,062 truly refused**. The 1,062 carry exactly five reasons —
`L_SHAPE_DECOMPOSITION_FAILED` 605, `INTERIOR_RING_COURTYARD_UNFOLD_FAILED` 239, `NARROW_FOOTPRINT_LT_8M`
134, `DWELLING_DENSITY_EXCEEDS_RULED_GRID_GT_8` 75, `PARTITION_AUDIT_FAILED` 9. Consequence: the ceiling
reachable by answering every *shape* refusal is 2,544 − 75 − 9 = **2,460 = 96.7 %**, and the 95 % bar sits
just under it — there is no slack, every shape refusal must be answered, and the density rule need not be
touched. Next free `FINDING 223`.

**`D-EU-61` (2026-09-01) — the group scheme set is planned; four new schemes, additive only.**
`implementation/PLAN_eu21-group-schemes-2026-09-01.md` is in force: P01 repairs `FINDING 221`; S1
`courtyard_perimeter_band` (perimeter block, ray cuts about the void — never unfolds); S2
`row_house_depth_bands` (terrace, full-width bands, no corridor below 8 m); S3 `wing_spine_decomposition`
(morphological opening instead of reflex-vertex cutting, so chamfered and non-orthogonal elbows decompose);
S4 `regularized_envelope_grid` (terminal — dwellings on the largest inscribed rectangle, the residue
becomes the storey's unconditioned circulation, refused past a 0.35 residual fraction). Every new scheme
is reachable **only** where the current engine returns `dwelling_layout_emitted=False`, carries its own
`scheme` string, and writes into a new `EU-21/` tree — `EU-17/` is never written. Next free `D-EU-63`.

🔴 **FINDING 223 (2026-09-01) — `FINDING 221` is geomeppy's clipper, not our rings.** P01 snapped every
shared interzone vertex onto the 1 mm `_stabilize_ring_coords` grid and the reroute tally moved 941 → 939,
ruled 541 → 543. The hypothesis is disproved: the raw `coords_m` were already bit-identical at shared
vertices. The real exception is `ZeroDivisionError` in `geomeppy/geom/vectors.py:105`
(`Vector3D.set_length` on a zero-length normal) raised inside geomeppy's own `intersect()` clipping — the
degenerate sliver is *produced by* `intersect_match`, not present in our geometry. The `IndexError` named
in the comment at `openubem/idf/surfaces.py:863-864` also occurs (Lyon `f07c2c6a5deab600`), so the
population carries both signatures. This is the same mechanism as the already-`[OPEN]` `FINDING 219`/`220`.
Next free `FINDING 224`.

**`D-EU-62` (2026-09-01) — CP-1 failed; P02–P05 released anyway, and the plan is decoupled from the IDF.**
CP-1's bar (ruled ≥ 1,450) was not met. Three rulings, full text in
`implementation/PLAN_eu21-group-schemes-2026-09-01.md` §8 under `CP-1 — verdict`: (1) P02–P05 proceed,
because they act on `openubem/geometry/european_residential.py`, which decides a layout *before*
`extrude_geometry` runs — the 1,062 refusals they target are refusals of shape, not of extrusion; (2)
P01b opens — `scripts/emit_eu11_layout_sidecars.py:300-313` stops blanking the ruled rings of a rerouted
building, since the deliverable is a **drawing** and `D-EU-55` forbids simulating any of it; the
`FINDING 213 → 0` integrity guard survives as an explicit `idf_reroute_divergence` flag instead of as
deleted geometry, and no energy figure may ever be attached to a flagged plan; (3) P01c opens — an
intersect ladder (`idf.match()` without `idf.intersect()`, `geomeppy/idf.py:54,59`) replaces the
disproved snapping hypothesis. Next free `D-EU-63`.

## 1a. Prior state — 2026-08-31, night (superseded by the above; kept for what already happened)

- **v4 is the only track.** `EU-01`–`EU-16` are built; context geometry landed (all 2,544 IDFs carry
  shading). The floor plans did not: ruled coverage **56.9 %** against a 95 % bar (`FINDING 211`), the
  refusal is a morphology refusal (`FINDING 212`), **61.1 % (1,555 of 2,544)** of the IDFs that ran are
  undivided massing boxes and **459** of them are drawn in the viewer with a layout the IDF does not carry
  (`FINDING 213`), and the EUI denominator is still gross on 2,544 of 2,544 rows (`FINDING 214`).
- Districts and counts: `ES-MAD-BERRUGUETE` 961 · `FR-LYO-HAUTCOEURPENTES` 297 · `GB-LDN-STDUNSTANS` 82 ·
  `IT-BOL-GALVANI2` 1,204 = **2,544**.
- **Slice 1 (`EU-18a`, T01–T03) returned 2026-08-31.** T01/T02 done clean (reader matches eppy 23/23; 4
  offline pages + index, 0 forbidden-term hits, 0.18–2.95 MB). T03 hit its own designed STOP: the parity
  gate finds **518** divergent, not the pinned 459 (Madrid 234 not 175; Lyon/London/Bologna match §2
  exactly). `FINDING 215`: 59 Madrid buildings, disjoint from `FINDING 213`, where the side-car's
  `storey_span` for an absorbed floor group is self-consistent but the IDF's own emitted zone for that
  group is physically shorter (50 off by one storey, 5 by two, 2 by three, 2 by four); root cause not
  located, registered `[OPEN]` in `debugs/DEBUG_REFERENCES_european_locations.md` ch.3. Director rules:
  T04 (deep refusal census) does not depend on the 459 figure — slice 2 dispatched without owner pause,
  `FINDING 215` carried forward for T05–T09 to account for or close.
- **Slice 2 (`EU-17` T04) returned 2026-08-31.** Refusal totals reproduce §2 exactly (345/99/42/610,
  fleet 1,096/2,544), no code touched. `FINDING 216`: 148/1,096 (13.5 %) of recorded refusal reasons were
  masked by `_secondary`'s legacy-cutter reason hint — every one of the 144 fleet-wide
  `NARROW_FOOTPRINT_LT_8M` refusals and 4/9 `PARTITION_AUDIT_FAILED` were really an upstream
  `L_SHAPE_DECOMPOSITION_FAILED`/`INTERIOR_RING_COURTYARD_UNFOLD_FAILED`/audit failure; true fleet counts
  L-shape 629→739, courtyard 239→249, partition-audit 9→25, new
  `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` 0→8. Consequence for slice 3: T07 (narrow-plate rule) recovers
  **0** directly — narrow width was never itself a true top-level cause on this fleet, only reachable
  from inside T05/T06's routes as the plan's own T07 "How" already allows. One bug hit+fixed in the new
  census script (1-dwelling-wing layout object), registered `debugs/…` ch.1. Director rules: proceed to
  slice 3 (T05–T09) with the corrected targets; `PARTITION_AUDIT_FAILED` (25) and
  `INSUFFICIENT_EXTERIOR_FACADE_LT_2_50M` (8) are out of T05–T08's scope and stay open residual after T10.
- **Slice 3 (`EU-17` T05–T09) returned 2026-08-31.** T05 (wing decomposition, split at every reflex
  vertex, `_wing_count_candidates` rebalance): 71 synthetic tests pass; real-fleet recovery 29/739
  L-shape (ES 13, FR 1, GB 0, IT 15). T06 (courtyard hardened): found+fixed a real pre-existing bug,
  `FINDING 217` — corner circulation nodes were centred on the void's own corner, overstating carved
  circulation area and breaking the gross−void=conditioned+circulation identity; fixed
  (`european_residential.py:786-797`). Real-fleet recovery 0/249 — one building
  (`relation/12582232`) has a residual ~0.11 % wing-tiling `AREA_GAP` on every possible dwelling-count
  split, `FINDING 218`, `[OPEN]`, out of T06 scope. T07 (narrow-plate corridor-free route): new scheme
  wired only into the gallery route carrying the 1.80 m spine; fleet top-level recovery 0/0 exactly as
  T04 predicted. T08 (`D-EU-49`): circulation now gated once at building level; fleet-wide 46
  single-storey buildings (matches §2), 0 now carry circulation (was 3), all 3 named buildings verified
  individually. T09 partial: (a) not fixed — `idf.intersect_match()` raises `ZeroDivisionError` on
  rotated non-axis-aligned multi-storey zone stacks, unreachable from `EU-17`'s editable files without
  EnergyPlus proof (`D-EU-55` forbids it here), `FINDING 219`, `[OPEN]`, routed to `T13`; (b) fixed —
  the side-car emitter now overrides outcome/areas when the built IDF's own zones (T01's reader)
  disagree with the independently recomputed layout, verified only in isolation (EU-11 is read-only).
  The 459/518 divergence count is **not** re-measured here — left to T10, so as not to mix today's
  generator against yesterday's IDFs. One out-of-scope regression test (a fixture that now correctly
  recovers) disclosed, not fixed, not in the file list. `pytest -q -n 8 tests/` → 2,540 passed / 55
  skipped / 5 failed (4 pre-existing, 1 the intended T05 consequence). Files touched: exactly
  `european_residential.py`, `scripts/emit_eu11_layout_sidecars.py`, `tests/test_eu17_relaxed_layout.py`
  — matches plan §3. Director rules: audit clean, proceed to slice 4 (T10–T11) with `FINDING 217`
  fixed and `FINDING 218`/`FINDING 219` carried forward as residuals for `T13`.
- **Nothing is running.** No Speed job is authorised; confirm the queue is empty once (`squeue` on the login
  node — read-only, no compute) and record it.
- **All four district EUIs stay barred from quotation** until `EU-19` lands on plans that were seen and
  proven. Bologna additionally carries `IMPUTED_CENSUS_SECTION_CONSTRUCTION_PERIOD` on 100 % of rows.
- **Next free identifier `D-EU-58`, next free finding `FINDING 221`.**

---

## 2. Dispatch ledger — one fresh Sonnet session per slice, `model: "sonnet"` always passed explicitly

Never two in parallel; each slice consumes the previous one's artefacts. Write one self-contained,
paste-able `PROMPT_*.md` per slice in `prompts/`, and move it to `prompts/previous/` when it returns.

| # | Slice | Tasks | Ends at | Status |
|---|---|---|---|---|
| 1 | `EU-18a` — reader, pages, parity gate | T01–T03 | Four pages open offline; gate reproduces 459 and exits 1 | 🟡 **STOP — 518 not 459, `FINDING 215`, audited, closed as-is** |
| 2 | `EU-17` — the deep refusal census | T04 | True cause distribution per district, beside the recorded one | 🟢 done — `FINDING 216` |
| 3 | `EU-17` — the relaxation | T05–T09 | Wings, courtyards, narrow plates, `D-EU-49`, divergence killed | 🟢 done — `FINDING 217`/`218`/`219` |
| 4 | `EU-17` — rebuild, census, denominator | T10–T11 | ≥ 95 % on the IDFs + the `rules/` §6 regression | 🔴 **STOP — 23–39 % not 95 %, `FINDING 220`. `D-EU-57` (owner, 2026-09-01): option (a) — halt, no T12, root-cause first.** |
| 5 | `EU-17a` — root-cause the STOP | T14 | Stop-and-report 4 — architectural gap, not a bug | 🟢 done — `D-EU-58` escalated to owner, ruled option (a) |
| 5b | `EU-17b` — apply the fallback tier | T15 | 633/633 buildings recovered, `FINDING 220` closed | 🟢 done — 2026-09-01 |
| 6 | `EU-18b` — regenerate and prove | T12 | Pages regenerated, parity gate re-run (970 divergent, reproduces `FINDING 213`/`215`, not new) | 🟢 code/data done — 🔴 **owner rejected the page format itself, not the data — see §1** |
| 6b | `EU-18b` — rework `plans3D/` presentation | new | Owner's own spec for the page format, then re-emit | ⚪ **next dispatch — get the requirement first, do not guess** |
| 7 | T13 sample battery, then `EU-19` | — | 🔴 **BLOCKED — `D-EU-55`, owner's own sentence** | ⛔ |

**Slice 1 kickoff, paste as written into a fresh Sonnet session (adjust the range for later slices):**

```
Read C:\Users\o_iseri\Desktop\OpenUBEM\docs\docs_ACTIVE\europeanLocations\implementation\PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md.
Execute T01 through T03 in order. Obey §1 hard rules literally — in particular: never run EnergyPlus,
never write outside §3's file list, measure on the emitted IDFs and never on the side-cars.
Append one progress-log entry per completed task under §8 of that doc, run the tests the plan calls for,
and report results. Do not propose alternatives — execute the plan. If the DESIGN is ambiguous, STOP and
quote the conflict.
```

**Audit every return before dispatching the next slice:** progress-log entry in plan §8 · a
`content/walkthrough_progress_log.csv` row · the exact test command and its output · only plan §3 files
touched · a `file:line` citation for any unplanned decision. Missing any one → send it back first.

**T12 must not overwrite T02's pages** — they are the starting-state evidence. Move them to
`plans3D/previous/` before regenerating (`D-EU-56` item 3).

---

## 3. Standing rules

**Models.** Cheapest model that can do the job, brand-new session every dispatch, `model: "sonnet"` always
explicit (`haiku` for pure monitoring). This session plans, audits and dispatches — **it never writes
feature code**. Never resume a finished agent for new work.

**Speed HPC** (only relevant once `EU-19` is authorised). Never compute on the login node — `sbatch --array`
fire-and-forget, then read outputs; login node is `mkdir`/`scp`/`tar`/`squeue`/`sacct` only. Remote shell is
**tcsh** — wrap every remote command in `bash -lc` via `scripts/cluster/t08_harvest_results.py:104`, and
never put `!` in a remote command. **`--time=7-00:00:00` minimum on every submission** — the cancelled v3
wave timed a Lyon resubmit out twice at 3 h. Waves under the ~20k-task cap; `ps` partition, one E+ process
per array task. A Speed number and a Windows number are not the same measurement (`FINDING 187`/`190`).

**Errors.** Search `debugs/DEBUG_REFERENCES_european_locations.md` (arc, `D-EU-52`) and
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` (repo) **before** debugging anything; append the
solved entry in house format **before** closing the task.

**Working tree.** Dirty and user-owned. Inspect before editing. Never `git add`/`commit`/`stash`/`restore`/
`checkout`/`reset`/`clean` — git is handled externally.

**Documents.** After every material result, update in the same pass: §1 of this file,
`content/walkthrough_progress_log.csv` (append-only, failures included), the plan's §8 log, and the arc
error index. Never paste raw logs into a planning doc. Never edit MVP Table 9.7 beyond its status cells.
Superseded prompts and docs move to `previous/`, never deleted, with the citation sweep the archiving rule
requires. Close this file again once it exceeds ~1,000 lines.

**Replies to the owner.** English even when they write French. The fixed template in `CLAUDE.md` — one
opening line, 3–5 short bullets, an `Evidence:` line, a `Next:` line of 3–4 words. ~80 words. No tables, no
narration, no unrequested files.

---

## 4. Fresh-session checklist

1. Read §0 and §1 of this file, then `STATE_european_locations_v4.md`, then the plan.
2. `git status --short` — preserve unrelated dirty work, touch none of it.
3. Confirm nothing is running: no background agent, and `squeue` empty on Speed.
4. Dispatch the first ⚪ row of §2 as its own fresh Sonnet session. Audit the return, update the documents,
   dispatch the next. Continue to slice 5 without pausing (`D-EU-56`).
5. Stop at slice 5 and report. Do not touch slice 6 — it needs the owner's sentence (`D-EU-55`).
6. Stop and ask only on a genuine authority conflict or spec ambiguity; quote it, never invent a resolution.

---

## 5. Slice ledger

- **2026-08-31 (night) — v4 documented, execution not yet started.** `D-EU-56` ruled (the geometry arc runs
  to the end in one session; only the `plans3D/` confirmation and the simulation permission remain owner
  gates). This prompt cut from 321 lines to a lean v4 handoff; v3 version archived. `plans3D/` empty, T01
  un-started. Next free `D-EU-57`/`FINDING 215`.
- **2026-09-01 (afternoon) — the ten-group rule document delivered and reviewed.** EU-20's census turned
  into `rules/RULES_dwelling_layout_groups_2026-09-01.html`: ten sheets, each with the engine's own floor
  plan drawn on a real district plate (flats + circulation, same building in both figures), a plain-English
  coverage table, and a per-group route to 95 %. Owner accepted groups 02/03/04/05/08 outright and raised
  four objections; all four are answered (§1, `D-EU-63`). `FINDING 224` recorded. `courtyard_gallery_ring`
  (S5) proposed and drawn but **not written into the engine** — awaiting the owner. Task prompt
  `prompts/DIRECTOR_PROMPT_group_floor_plans_2026-09-01.md` opened. No simulation of any kind was run
  (`D-EU-55`). Next free `D-EU-64`/`FINDING 225`.
- **2026-09-01 — T14/T15/T12 executed, audited clean; Stop-and-report 3 failed on presentation.** T14
  diagnosed the T10 population loss as an architectural gap, not a bug (`FINDING 220`, `D-EU-58`
  escalated); owner ruled option (a); T15 added the fallback tier, recovered 633/633, closed
  `FINDING 220`, `pytest` unchanged (2,540/55/5, same 5 pre-existing named failures). T12 regenerated
  `plans3D/` and re-ran the parity gate on the corrected tree (970 divergent, confirmed a reproduction of
  already-disclosed `FINDING 213`/`215`, not forced to pass, not a new defect) and re-ran the sidecar
  emitter as an authorised companion step. Director audited both slices against git status, timestamps
  and the plan's own progress log — clean. Owner then opened `plans3D/PLANS_ES-MAD-BERRUGUETE.html`,
  rejected it on sight against `rules/RULES_dwelling_layout_scheme_2026-08-28.html`, and asked for this
  prompt to be updated for a fresh session. §1 above records the rejection; no redesign spec exists yet.
- **2026-08-31 — v4 opened, v3 cancelled.** `D-EU-49`–`D-EU-55` ruled; `FINDING 211`–`214` recorded; the
  Speed waves and the v3 tasks stopped (`D-EU-53`); `STATE`/`BRIEF` v4 written and the v3 pair frozen to
  `previous/`; `PLAN_eu17-eu18-boxrule-atlas-2026-08-31.md` written (13 tasks, three stop-and-report
  points). **All four district EUIs stay barred from quotation.**
