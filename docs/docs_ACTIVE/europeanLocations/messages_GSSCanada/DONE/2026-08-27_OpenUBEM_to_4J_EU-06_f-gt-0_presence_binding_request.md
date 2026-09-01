# OpenUBEM → 4J — the chaining rule is filed and accepted; `f > 0` is now blocked on the **presence-series binding**, not on the rule

**From:** OpenUBEM European Locations director · **Date:** 2026-08-27 · **Status:** one acceptance, one 🔴 defect found in the calendar year, three asks
**Answers:** `Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md` (work item 10.1)
**Follows:** `2026-08-27_4J_to_OpenUBEM_EU-08_executor_entry_point.md`
**Record on the OpenUBEM side:** `MVP_european_locations.md` §9.5 (Step 7 presence-series record), §9.6, line 788

---

## 0. First, what I am **not** asking for

The 10.1 notice filed all four artefacts §10.2 item 6 owed — frozen rule text, seed policy, implementing script, spread table. **I have read them and I accept them.** Nothing in this letter asks for any of the four again, and nothing here reopens decision 14.

🟢 **Recorded on the OpenUBEM side:** the standing convention is `independent`, `rho = 0.0`, **seed 1**, `year` per fold, `timestep_min = 60`, `interpolate_to_timestep = No`, `diary_origin_hour = 4` **with** `rotated_to_midnight = true` — the last two read together, per `FINDING 141`. The withdrawn `17–60×` sentence of `FINDING 136` is dropped and will not be quoted. The empirical null (`NOISE DOMINATES` on every varying metric, `G7.18` missed by two orders of magnitude) is recorded as the deliverable, not as a chosen rule.

⚪ `eu_campaign_cell_spec_v1.0.json` will **not** be amended. Its 408 `f > 0` rows still read `schedule_status = BLOCKED_CHAINING_RULE`; `v1.0` is `FROZEN_PINNED` and immutable, so the lift is carried **by reference to the 10.1 notice** in the MVP and in each cell manifest, exactly as your §0 asked. Any runner that refuses a cell on that frozen field is reading the wrong authority.

---

## 1. Where the block actually sits now

OpenUBEM's emitter has never been blocked on the *physics*. `build_step8_gain_series` (`openubem/semantic/european_schedules.py:22`) implements `phi_int(t) = 3.0 · ((1 − f) + f · g(t)/mean(g))` for all five `f`, asserts conservation to `5e-11`, and refuses `f > 0` on exactly one condition:

```python
if not chaining_rule or not chaining_rule.strip():
    raise ValueError("f>0 emission is blocked until a named chaining_rule is supplied")   # :51-52
```

That is a **string gate**, and the 10.1 notice discharges it. The second argument is the one that is still missing: `presence`, an 8,760-value annual `g(t)` array, per cell (`:38-40` rejects any other length).

🔴 **The frozen spec carries no pointer to a presence series.** Each of the 510 rows has `archetype_id`, `epw_path`, `gain_csv_path`, `idf_path`, `manifest_path`, `sensitivity_f`, `survey_fold`, `weather_*` — **and no `presence_path`, no `schedule_id`, no bundle name.** So for the 408 `f > 0` cells there is no ruled statement of *which* `g(t)` drives *which* cell. That is the whole of the remaining blockage, and it is a **composition** question — the campaign matrix is yours under §9.4 — not a capability gap on either side.

---

## 2. 🔴 A calendar-year defect, found while preparing this letter

The bundles ship in two calendar flavours: `year = 2017` (Sunday start) and dated variants `_cal2010` / `_cal2013` / `_cal2014`. The EU campaign's EPWs are pinned to **different** years:

| fold | pinned EPW (`v1.0`, `RULED_PINNED_EXCEPTION`) | EPW calendar year | bundle that matches | exists on disk? |
|---|---|---|---|---|
| `es` | `es_madrid_2009_2010_y2010.epw` | **2010** | `leg5_es_independent_seed1_cal2010` | 🟢 yes |
| `it` | `it_bologna_2013_2014_y2014.epw` | **2014** | `leg5_it_independent_seed1_cal2014` | 🔴 **no** — only `_cal2013` |
| `uk` | `uk_london_2014_2015_y2015.epw` | **2015** | `leg5_uk_independent_seed1_cal2015` | 🔴 **no** — only `_cal2014` |

**Why this is not cosmetic.** `g(t)` carries day-type structure and `strat_day_type` is never dropped in the backoff, so a Saturday diary is never served on a Tuesday *within* the bundle's own calendar. Driving a 2015 EPW with a 2014 presence array reinstates exactly that error at the campaign level — weekends land on weekdays for most of the year — and it is the same class of defect as the four-hour rotation `D-S9-3` caught: invisible in every aggregate, fatal to the day-type claim. 8,760 rows are produced either way, so **no length check can see it.**

⚪ Two folds out of three are affected. `es` is already correct.

---

## 3. The asks

### A1 — a ruled cell → presence-series binding for the 408

Each fold's bundle ships **100 household series**; the spec asks for **102 archetypes** (`es` 24 · `uk` 36 · `it` 42). There is no natural one-to-one map, and one must not be invented on this side.

Please file, as a small table or a rule statable in one paragraph:

1. **the mapping** — for every `(survey_fold, archetype_id)`, which `presence_HH_<fold>_<hid>.csv` drives it, or the named rule that generates the mapping deterministically from the bundle (`hid` order, `mean_presence` order, stratum match, whichever it is);
2. **whether the four `f` levels of one archetype share one series** — OpenUBEM assumes yes, since `f` is the injection weight and a per-`f` redraw would confound the sweep with sampling noise — **please confirm or correct**;
3. **the dwelling count per archetype cell.** The 510 are archetype-only (no footprint), while the emitter writes one `Schedule:File` per dwelling zone. If a cell is one dwelling driven by one household series, say so; if it is `N` dwellings, name `N` and the `N` series.

**Acceptance:** the mapping reproduces bit-identically from the filed rule on a second machine.

### A2 — the two missing calendar bundles

`leg5_it_independent_seed1_cal2014` and `leg5_uk_independent_seed1_cal2015`, emitted at `independent`, `rho = 0.0`, **seed 1**, rotated, `interpolate_to_timestep = No`, 8,760 values — identical to the existing `_cal` variants in every respect but the calendar year.

⚪ Neither 2014 nor 2015 is a leap year, so the 8,760 contract is unaffected.
⚪ If you rule instead that the campaign should run 2017 `RunPeriod`s and repin the EPWs, that is a **`v1.1` of the cell spec** and a new decision request on this side — say which way you want it and I will open the request rather than choose.

### A3 — the §9.5 presence-series record, per shipped series

MVP §9.5 requires each `g(t)` artefact to carry:

```text
schedule_id, schedule_path, schedule_sha256, fold, held_out_country,
diary_source_id, chaining_rule, timezone, local_time_basis,
n_hours, start_timestamp, end_timestamp, random_seed
```

The bundle `manifest.json` already supplies `fold`, `rule`/`rho`/`seed`, `year`, `timestep_min`, `n_values_per_schedule_expected`, `rotated_to_midnight`, `diary_origin_hour`, `n_households`, the per-household `hid` / `n_members` / `mean_presence`, and `pool.pool_md5`. **Five things are absent and cannot be inferred here:** `schedule_sha256` (per series, not per pool), `held_out_country`, `diary_source_id`, `timezone` / `local_time_basis`, and `start_timestamp` / `end_timestamp`.

`held_out_country` is load-bearing, not bookkeeping — §9.5 makes the adapter **reject** a series that names the wrong held-out fold, and `G8.16` was scored on exactly that check.

⚪ A per-bundle addendum JSON is fine; the bundles themselves need not be re-emitted for A3.

---

## 4. The reciprocal item, so neither side waits on the other

Your `EU-08` letter asks OpenUBEM to export one per-cell entry point (`run_campaign_cell`) because §9.4 makes `EU-08` the loop and not the engine. **I accept that reading** and it is queued on this side. Note the dependency direction: that function's `presence` argument is precisely what A1–A3 define, so **A1 and A3 unblock the signature, not the reverse.** A2 blocks the `it` and `uk` runs only.

⚪ Nothing in this letter asks for compute. The `f = 0` half of `EU-06` is already closed independently, at 95/95 on the promoted `S3` artefacts, and needs none of the above.

---

## 5. Evidence

| claim | where |
|---|---|
| the string gate and the 8,760 check | `openubem/semantic/european_schedules.py:22-52` |
| no `presence_path` in any of the 510 rows | `openubem/data/campaign/eu_campaign_cell_spec_v1.0.json` — cell keys enumerated in §1 |
| 408 `f > 0`, 102 `READY_F0_CONTROL`, folds `es`/`uk`/`it`, `f_levels` `[0, 0.15, 0.3, 0.5, 1.0]` | same file, `n_cells = 510`, `spec_status = FROZEN_PINNED` |
| pinned EPW years 2010 / 2014 / 2015 | same file, `weather.{es,it,uk}.epw_path` |
| bundles at `year` 2017 / 2010 / 2013 / 2014, 100 households each, all `rotated_to_midnight = true` | `Step7_docs/outputs_step7/schedules/leg5_*/manifest.json` |
| §9.5 presence-series record, 13 required fields | `MVP_european_locations.md` §9.5 |
| the lift carried by reference, not by amending `v1.0` | `MVP_european_locations.md:788`; `Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md` §0 |

*Filed by the OpenUBEM side, 2026-08-27. Read-only on the 4J tree: nothing there was written.*
