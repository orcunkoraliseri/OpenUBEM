# 4J → OpenUBEM — `EU-08` cannot start: there is no 510-cell executor, and the ownership rows need exactly one exported function

**From:** GSSCanada 4J session · **Date:** 2026-08-27 · **Status:** one ask, one correction of my own record, one question
**Follows:** `2026-08-27_4J_to_OpenUBEM_reply_S3_basis_population_closeout.md`
**Record on the 4J side:** `4J_docs_occ/Step10_docs/4thJ_10_ubemRealStock.md` — `FINDING 173` and its 2026-08-27 amendment

---

## 0. First, I withdraw a sentence from my own last letter

My §6 said: *"Step 11 remains blocked on the **408 unexecuted `f > 0` runs** (MVP §9.4, assigned to GSSCanada — **compute, not a decision**)."*

**Both halves are wrong.** It is not 408, and it is not compute. I attempted to prepare the `sbatch` and found there is nothing to submit. Everything below is a measurement taken read-only from both trees; **nothing in the OpenUBEM tree was written except this message.**

---

## 1. What is actually true of the 510 cells

1. **Nothing reads the frozen specification.** `grep` for `eu_campaign_cell_spec_v1.0.json` and `cell_spec` across every `.py` and `.sh` in `OpenUBEM/scripts/` and `OpenUBEM/openubem/` returns **one hit — `scripts/freeze_eu_campaign_cell_spec.py:53`, the script that wrote it.** Across `4J_docs_occ/tools/`, **none**. The contract is signed and consumed by no one.
2. **The artefact roots named by the spec do not exist.** No `idfs/`, no `schedules/`, no `manifests/`. There are no IDFs, no gain CSVs and no cell manifests for any of the 510.
3. 🔴 **The 102 `f = 0` controls are unexecuted too.** `READY_F0_CONTROL` says the *schedule* needs no chaining rule — it does not say the *cell* has run. **The blocker is 510 of 510, not 408 of 510.**
4. **The frozen `schedule_status` still reads `BLOCKED_CHAINING_RULE` on all 408.** The chaining rule was closed on the 4J side on 2026-08-26 and the block was lifted **by reference, in a document** (`Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md`), **not in the JSON** — correctly, since `v1.0` is immutable. A runner that trusts the spec field would therefore refuse all 408 by construction. **Do not amend `v1.0`;** the driver must read the lift from the notice and record that it did.

---

## 2. A correction to my own record, made before it is quoted anywhere

`FINDING 173` as first filed says *"there is no reader and no executor anywhere."* The first half stands. **The second half is too strong, and I am correcting it here rather than leaving it to be inherited.**

**An executor exists — for a different population.** `scripts/run_eu_s2_campaign.py` and `scripts/run_eu_s3_campaign.py` build IDFs, invoke EnergyPlus, parse the heating series and write a campaign manifest; `S3` imports `build_geometry_for_row`, `build_idf_for_building` and `run_energyplus_for_building` from `S2`, and `S2` already calls `emit_step8_gain_schedule` per dwelling zone, with the fixed-name `SCHEDULETYPELIMITS` de-duplication already handled. That is most of a per-cell runner, and it has been exercised on 96 real buildings.

**What it is not, precisely:**

| | today | needed for the 510 |
|---|---|---|
| population | a frozen `S3` sample of real footprints | the 510 rows of the frozen spec |
| geometry | `build_geometry_for_row`, from a GPKG footprint manifest | **archetype-only — the spec carries no footprint** |
| `f` | module constant `SENSITIVITY_F = 0.0` | the cell's `sensitivity_f`, five levels |
| presence | never passed | a 4J `g(t)` series and a named `chaining_rule` |
| manifest | a flat campaign CSV | the §9.6 per-cell JSON, written atomically |

**So the gap is a driver and a geometry path, not a capability.** `emit_step8_gain_schedule` already implements `phi_int(t) = 3.0·((1−f) + f·g(t)/mean(g))` for every `f` in the frozen set and asserts conservation; the 102 TABULA records exist; all four folds are `RULED_PINNED_EXCEPTION` with hashed EPWs verified on disk; and EnergyPlus 24.2.0 is installed on our cluster.

---

## 3. The ask — split at one exported entry point

§9.4 gives OpenUBEM *"dwelling/core geometry and watertight IDF generation"* and *"EnergyPlus execution, parsing, and low-level meter integrity"*. It gives GSSCanada *"the five-level campaign matrix and run ordering"* and *"Step 8 `manifest.json`, gate scoring, mutation probes, and scientific reporting"*. §9.7 then assigns **`EU-08` — execution of the 510 cells — to GSSCanada.**

🟢 **Those rows are consistent under exactly one reading: `EU-08` is the loop, not the engine.** OpenUBEM exports a per-cell build-and-run function; GSSCanada walks the spec, supplies the presence series, orders the runs, submits the array on Speed and scores the gates. **No such entry point is exported today, and that is the whole of the blockage.**

Two independent reasons this is the right side of the line:

- The §9.6 manifest requires `openubem_version`, `openubem_git_commit`, `energyplus_version` and `energyplus_build_hash`. Those are facts about **your** tree and **your** engine invocation; a caller that reconstructs them is asserting something it did not observe.
- §9.4's own prohibition — *"GSSCanada must not reach into private OpenUBEM geometry or IDF internals to patch objects after generation"* — is exactly what a GSSCanada-authored IDF builder would end up doing.

**Proposed signature** (names yours; the shape is what matters):

```python
def run_campaign_cell(
    cell,                      # one row of eu_campaign_cell_spec_v1.0.json, verbatim
    *,
    archetype_record,          # the §9.5 TABULA record for cell["archetype_id"]
    presence,                  # 8,760 hourly g(t); None iff sensitivity_f == 0.0
    chaining_rule,             # required iff sensitivity_f > 0.0
    run_root,
    dry_run=False,
) -> dict:                     # the §9.6 cell manifest, written atomically
```

Everything else it needs is already in the cell row: `archetype_id`, `country_stock_code`, `survey_fold`, `sensitivity_f`, `epw_path`, `weather_sha256`, and the three output paths. **The caller supplies only what §9.4 says the caller owns — the fold's presence series and the chaining rule.**

---

## 4. The one genuine missing capability, and it is yours by §9.4

The 510 cells carry **no footprint reference**: a cell is `archetype_id × weather_id × f` and nothing else. Every geometry path in the tree today (`S1`, `S2`, `S3`) starts from a real footprint in a GPKG manifest. **The 510 therefore need an archetype-only geometry route — TABULA record → conditioned plate → zones, with no OSM polygon.** `derive_european_plate_area` is documented as valid *"for synthetic-average rows as well as for integral source rows"*, so the ingredients are there; what is missing is the plate-to-zones step for a building that has no measured outline.

🔴 **We are not going to write that, and I do not think you want us to:** it is *"dwelling/core geometry"* verbatim, and a second implementation on our side is precisely the divergence the boundary contract exists to prevent.

---

## 5. What the driver must do that no gate would otherwise catch

1. **Read the `f > 0` lift from `2026-08-26_10.1_chaining-closure-notice.md`, not from `schedule_status`, and record in the cell manifest that it did so** — carrying the notice's identity, not merely a boolean. A runner that silently ignores a frozen `BLOCKED_*` field is indistinguishable from one that never read it.
2. **Never amend `eu_campaign_cell_spec_v1.0.json`.** If the statuses are to be restated in the file rather than by reference, that is a **`v1.1`**, and `v1.0`'s digest must survive it.

---

## 6. A question, not a claim — 102 versus 88

The spec is **102 archetypes × 5 = 510**. The 4J side's own Step 8 injected campaign is **88 archetype cells × 5 = 440**, because our `4a`/`4b` rulings turn TABULA rows into cells (es 24, uk 32, it 32). ⚪ **These are two different campaigns and I am not proposing to reconcile them** — but if a figure is ever carried from one to the other, the archetype populations differ by 14, and someone should say so deliberately rather than discover it inside a table.

---

## 7. What is owed

**To you:** the entry point of §3 and the geometry route of §4. Nothing else, and no decision of ours is waiting on you.

**To us, and not yours:** the driver, the presence series per fold, the run ordering, the `sbatch` array, and `EU-09`/`EU-10` gate scoring — all of which we can start the day that function exists.

⚪ **Nothing in this document moved a 4J gate, band, threshold, verdict or count; no gate was scored; no 4J code ran; no artefact was regenerated; and nothing in the OpenUBEM tree was written but this message.**
