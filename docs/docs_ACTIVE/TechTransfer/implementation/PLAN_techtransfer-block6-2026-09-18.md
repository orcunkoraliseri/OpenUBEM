# PLAN — TechTransfer block 6 (successor to block 5)

**Slug:** techtransfer-block6 · **Date:** 2026-09-18 · **Manager-authored.** Executors append to §4 only.

**Predecessor:** `PLAN_techtransfer-block5-2026-09-17.md` (🔒 CLOSED 2026-09-18, lane J done, no open
items inside that block).

**Opened by:** user decision 2026-09-18 — close block 5 / open block 6 — approved as "housekeeping
only": this doc is parked, no task is authorized to start yet.

---

## 1. State at open

Per `docs/docs_ACTIVE/TechTransfer/Prompt/PROMPT_MANAGER_techtransfer_2026-09-18.md` §2, ten of eleven
report items are done or parked by design. Everything shipped so far stays behind default-OFF flags;
nothing is wired into the build path; no published OpenUBEM number has moved. Test baseline at open:
108 passed across the eight TechTransfer test files (command in the prompt-manager doc header).

## 2. Parked tasks — none may start without a specific user ask, item by item

| Item | What it is | Gate |
|---|---|---|
| C04 | Per-archetype per-end-use regression fixture (block 1, lane C leftover) | User must ask for C04 by name. |
| Wire `pv.py` | Connect the PV library into the build path | User must ask; ruled out deliberately at SR-H2. |
| Wire `openubem/scenarios/` | Connect the retrofit measure applier into the build path | User must ask; ruled out deliberately at block 5 §1c. |
| Flip `ENVELOPE_PATCH_SKIP_WHEN_BETTER`, `PREP_ABORT_ON_FAILURE`, `PV_INJECTION_ENABLED`, `SCENARIO_LAYER_ENABLED` | Turn any of the four flags on (`openubem/config.py:112,123,223,224`) | User must ask; flipping any one changes simulation behaviour. |
| Any EnergyPlus run for this arc | Nothing here has been simulated | User must ask; when approved, `sbatch --array ...%32` on Speed or a local pool of 20 — never sequential. |
| D9 | The prototype IDF library that lives inside idf_reader | Out of scope per §0 ownership rule; not to be pulled in. |
| Warehouse `auto`-mode IDF failure | Pre-existing, known, out of scope | Not part of this arc. |
| Racking / `Shading:Building:Detailed` for PV | Inter-row shading | Not started; no ask yet. |
| Rewrite OpenUBEM's table-driven envelope applier | — | Not started; no ask yet. |
| Write to `05_results` | Published 70-entry schema | Not touched on a blanket go-ahead. |
| T11 benchmark anchors / heat pumps | Waits for a Canadian district case or heat-pump scenario | Parked by design, nothing to do. |

## 2a. Execution authorized 2026-09-18 — run the list, item by item, no per-item ask

User instruction: "put them in a list and follow them by executing consecutively, no need to ask my
opinion." This authorizes running the in-scope items of §2 in sequence without stopping to pick
between them. It does not authorize reversing a deliberate ruling (SR-H2 for PV, §1b of block 5 for
scenario packaging) or moving the published fleet number — those still need the one specific input
named below, not a style-of-work choice.

**Order:**
1. **C04** — regression fixture. No wiring, no flag, no simulation risk. Runs first. Full task spec
   below.
2. **PV validation run** — SR-H2's own stated condition to ever revisit wiring: one real EnergyPlus
   run on one PV-injected prototype IDF, completing without a fatal and reporting non-zero generation.
   This is a single standalone run, not build-path wiring — in scope to execute now.
3. **Wire `pv.py` into the build path (flip `PV_INJECTION_ENABLED`)** — gated on item 2 succeeding
   *and* is still a build-path change with a fleet-wide compute cost; report item 2's result before
   this one runs.
4. **Wire `openubem/scenarios/` into a campaign** — gated on one input only I cannot pick: the
   packaging design (cumulative ladder vs. isolated single-domain runs vs. full factorial), stated in
   block 5 §1b as the user's compute-budget call (8,139 × 16 cells vs. × 5). Everything built so far
   is packaging-agnostic, so this step waits for that one answer and does not block items 1-3 or 5-6.
5. **Flip `ENVELOPE_PATCH_SKIP_WHEN_BETTER`, `PREP_ABORT_ON_FAILURE`** — no dependency on PV/scenarios;
   runs after C04, audited individually (each changes simulation behaviour).
6. **Any fleet-scale EnergyPlus run** — only after 2-5 land; `sbatch --array ...%32` on Speed, never
   sequential, case count stated before submission per CLAUDE.md cluster rules.

Out of scope, not part of this execution order: D9 (idf_reader's own prototype library — ownership
rule), Warehouse auto-mode bug (pre-existing, unrelated arc), PV racking/shading, envelope-applier
rewrite, `05_results` write, T11 benchmark anchors — these stay parked exactly as §2 states.

### Task C04 — Per-archetype, per-end-use regression fixture (report order 1, carried from block 1 lane C)

**What.** A golden table (archetype × end use) written from a current sample run, plus a test that
compares a fresh run against it and reports **which archetype and which end use moved**, not just a
pass/fail.
**Why.** In the source project an engine upgrade moved one archetype's gas use by **+56.6 %** while the
fleet total looked fine. A fleet-level regression check would have missed it.
**How.** Sample ≥ 12 buildings over ≥ 4 archetypes; run **in parallel** (never sequential — Speed
32/local 20 per CLAUDE.md). Store the golden under `tests/reference/` if that is where the repo's
existing goldens live — check first; if not, ask.
**How to test.** Test passes against its own golden; deliberately perturb one value and confirm the
failure message names the archetype and the end use.
**Gate.** None — cleared to start now.

### Task SCEN-01 — Full-factorial campaign definition (report order 10 / T5, campaign-design half)

**What.** A pure-data/pure-function campaign generator inside `openubem/scenarios/`: given the 3 active
measures (`lighting_power_density`, `thermostat_setback`, `infiltration_tightening`), produce the 8
cells of the full factorial (baseline + every non-empty subset of the 3, i.e. all 2³ combinations), each
cell as an explicit, named tuple of which measures are ON. No cell may silently omit a combination.
**Why.** Packaging decision resolved below (§2b): Option C, full factorial, so every combination must
exist as an addressable unit before any campaign can ever be submitted.
**How.** A function that takes the measure table already shipped (`openubem/data/scenarios/measures.json`,
active entries only — `envelope_u_upgrade` stays excluded, withdrawn) and returns the 8 cells, each with
a stable name (e.g. `baseline`, `lighting`, `setback`, `infiltration`, `lighting+setback`, …,
`lighting+setback+infiltration`) and the ordered list of measure keys to apply for that cell. Applying a
cell's measures to an IDF must go through the existing applier — this task does not add a second way to
call a measure. **No EnergyPlus run. No `05_results` write. No viewer change. Not imported from
`openubem/idf/`, `openubem/geometry/`, `openubem/campaign/` or `openubem/simulation/`** — same
build-path isolation rule as lane J (block 5 §2 rule 3). The only importer is the test.
**How to test.** One test asserts exactly 8 cells, no duplicates, and that the all-three cell's applied
IDF is identical (byte-for-byte after mutation) whether measures are applied in any of the 3! possible
orders, to prove cell definition is order-independent even though a single call still applies its
measures in a fixed internal order. One test that applying a cell twice (idempotence) matches applying
it once, reusing the idempotence proof each measure already carries individually.
**Gate.** None — packaging decision is resolved (§2b). Cleared to start now, in parallel with C04.

## 2b. Packaging decision resolved 2026-09-18 — Option C, full factorial

User routed the decision in `2026-09-18_DECISION_scenario-packaging-for-gemini.md` to Gemini and
relayed its answer: **Option C, full factorial**, all 2³ = 8 combinations of the 3 active measures
(baseline, each single, each pair, all three), reasoning being that a cumulative ladder cannot be
converted to a fair per-measure ranking after the fact and isolated runs cannot answer combined-measure
questions, while the factorial cost here is only 2x either simpler option (3 measures, not a larger
catalogue). At 8,139 buildings that is **65,112 total EnergyPlus runs** if and when a fleet campaign is
ever submitted (still not authorized — see below).

**What this unblocks now:** item 4 of §2a, building the 8-cell campaign definition inside
`openubem/scenarios/`, in-memory and testable exactly like the measure table and applier already
shipped — no EnergyPlus run, still behind `SCENARIO_LAYER_ENABLED` (default OFF), nothing written to
`05_results`.

**What this does not unblock:** item 6, the real 65,112-run fleet campaign. `05_results` write and any
viewer change are separately gated in §2 above ("not touched on a blanket go-ahead") and neither is on
the authorized-execution list. Running EnergyPlus at that scale before there is a sanctioned place to
write its output means the compute produces nothing usable. Flagging this now rather than submitting a
65k-run cluster job with nowhere for the results to land.

## 3. Standing rules carried forward

Unchanged from block 5 §5–§6 of the prompt-manager doc: audit by measurement against a real DOE
prototype IDF, never by report; a `Schedule:Compact` measure ships a test copied verbatim from a real
prototype block; a cited standard's own figure may not be restated by an OpenUBEM convention;
withdraw don't tune; the manager owns its own spec's defects; register every solved error in
`docs/docs_EXPLANATION/OpenUBEM_debug_References.md` before closing a task; fail closed with a named
gate; close this doc too if it passes ~1,100 lines.

## 4. Progress log

#### SCEN-01 — Full-factorial campaign definition — completed 2026-09-18

**Artifacts:** `openubem/scenarios/campaign.py` (new — `Cell` namedtuple, `active_measure_ids()`,
`build_full_factorial_campaign()`, `apply_cell()`), `tests/test_scenario_campaign.py` (new, 8 tests).

**Deviations:** none from the task's "How". `apply_cell()` applies each cell's measures by
delegating to `measures.apply_measure()` only — no second way to call a measure. Cell names use a
curated short-label map (`lighting`, `setback`, `infiltration`) since none of the 3 full measure ids
shorten to those forms mechanically; this mapping is not specified elsewhere in the repo, so it was
authored to match the task's own example names exactly.

**Test status:** `python -m pytest tests/test_scenario_measures.py tests/test_scenario_campaign.py -q`
-> `........................................................  [100%]` / `56 passed in 2.85s` (48
pre-existing measures tests unchanged + 8 new campaign tests, zero failures).

**Notes:** The 8 cells (baseline + all 2**3 combinations of the 3 active measures, `envelope_u_upgrade`
excluded as withdrawn): `baseline` (none), `lighting` (`lighting_power_density`), `setback`
(`thermostat_setback`), `infiltration` (`infiltration_tightening`), `lighting+setback`,
`lighting+infiltration`, `setback+infiltration`, `lighting+setback+infiltration` (all three).
`build_full_factorial_campaign()` fails closed (raises `ValueError`) if the active measure set in
`measures.json` ever stops matching exactly these 3 ids, rather than silently building a partial
campaign — covered by
`test_build_full_factorial_campaign_rejects_mismatched_active_table`. Order-independence proved by
applying the all-three cell's measures in all 3! = 6 orders on fresh fixtures and comparing
`idf.idfstr()` byte-for-byte (`test_all_three_cell_is_order_independent`); idempotence proved by
applying the same cell twice via `apply_cell()` (`test_applying_a_cell_twice_matches_applying_it_once`).
Verified `openubem/scenarios/campaign.py` is not imported from `openubem/idf/`, `openubem/geometry/`,
`openubem/campaign/` or `openubem/simulation/` (`grep -rn "openubem\.scenarios" openubem/idf/
openubem/geometry/ openubem/campaign/ openubem/simulation/` -> no matches); the only importer is
`tests/test_scenario_campaign.py`. No EnergyPlus run, no `05_results` write, no viewer change. No new
error encountered, so no new entry in `OpenUBEM_debug_References.md`.
