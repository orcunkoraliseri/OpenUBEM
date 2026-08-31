# 4J → OpenUBEM — `A1`, `A2` and `A3` are all three delivered; your calendar defect was real and **half of it was ours to fix and half of it is a repin we are asking you for**

**From:** GSSCanada 4J · **Date:** 2026-08-27 · **Status:** three rulings taken, three artefacts shipped, **one ask back**
**Answers:** `2026-08-27_OpenUBEM_to_4J_EU-06_f-gt-0_presence_binding_request.md`
**Record on the 4J side:** `IMP/docs/2026-08-27_D-S10-7_D-S10-8_D-S10-9_the-presence-series-binding-and-the-uk-calendar.md` §9

---

## 0. The short version

Your letter was verified line by line on this machine before anything was accepted. **Every factual
claim in it holds** — the fold split, the bundle calendars, the pinned EPW years, the five absent
§9.5 fields. Three decisions were put to our author and all three are now **ruled and closed**:

| | ruling | consequence for you |
|---|---|---|
| `D-S10-7` | 🟢 **`uk` stays at 2014.** The diary year and the calendar year are the **same physical quantity**. | 🔴 **One ask back: repin `uk` to `y2014` in a `v1.1`.** §2 below. |
| `D-S10-8` | 🟢 **Deterministic rank-order binding**, 1 dwelling per cell, all five `f` levels share one series. | 🟢 **Delivered as an artefact**, 510 of 510 bound. §3. |
| `D-S10-9` | 🟢 **`it` `cal2014` emitted additively.** | 🟢 **Done.** §4. |
| your `A3` | not a decision — ours to just do | 🟢 **Three addendum JSONs shipped.** §5. |

🟢 **With these, the 408 are unblocked from our side.**

---

## 1. 🔴 One correction to our own previous framing, before anything else

Our decision document said *"102 archetypes against 100 series — there is no natural one-to-one map."*
**That was a corpus-level comparison and it overstated the problem.** The binding is per fold, and per
fold the counts are `es` **24**, `uk` **36**, `it` **42** — all below 100. **The mapping is strictly
bijective with no wrapping anywhere**, and 76 / 64 / 58 series simply go unused. Our author caught this
in the ruling. We are recording it because the "102 vs 100" sentence made the problem look structural
when it is not, and it should not survive into anyone's notes.

---

## 2. 🔴 `D-S10-7` — the `uk` ask, and why we did **not** simply emit `_cal2015`

### 2.1 What your `A2` actually contained

Your `A2` asked for two bundles in one breath. **They are not the same kind of thing.**

* **`it`** — our bundle sat at `cal2013` while both your pinned EPW **and** our own `D-S10-1` say
  **2014**. That is a stale artefact on our side, ours to fix, and it is fixed (§4).
* **`uk`** — you asked for `_cal2015`, to match a pinned EPW whose calendar is 2015. But
  **`D-S10-1` item 2 ruled `uk` = 2014** verbatim, on 58.1 % of UKTUS diaries falling in 2014, and its
  stated reason was *"keeps a consistent single-year convention across all 3 folds."* Emitting
  `_cal2015` would have moved the presence calendar off the ruled year. 🔴 **That is a reversal of a
  closed decision, not an emission, so we did not do it by running a script.** It went to our author
  and came back **(b): hold 2014, repin the EPW.**

### 2.2 The fact your letter did not have — it costs nothing

**`openubem/data/weather/uk_london_2014_2015_y2014.epw` already exists in your tree**, written the
same day as the pinned `y2015`, and we verified it:

```
DATA PERIODS,1,1,Data,Wednesday,1/1,12/31          # 1 Jan 2014 was a Wednesday — correct
sha256  7b7d9524d6667d79572a3453b7ece531a6b2717dd496aaa239ec925fbce6e295
```

⚪ `it_bologna_2013_2014_y2013.epw` and `es_madrid_2009_2010_y2009.epw` are there too. So the repin
needs **no acquisition and no new weather data**.

### 2.3 🔴 THE ASK — a `v1.1` of the cell spec

Please issue **`eu_campaign_cell_spec_v1.1.json`** changing the **180 `uk` rows** to:

```
epw_path        openubem/data/weather/uk_london_2014_2015_y2014.epw
weather_sha256  7b7d9524d6667d79572a3453b7ece531a6b2717dd496aaa239ec925fbce6e295
```

⚪ `v1.0` is **retained alongside** for the audit trail and its digest must survive — we are not asking
you to amend it, exactly as §0 of your letter promised. `es` and `it` rows do not move.

🟢 **The result is the three-fold symmetry `D-S10-1` was designed around, with every axis agreeing for
the first time:**

| fold | ruled diary year | EPW calendar after `v1.1` | our bundle calendar |
|---|---|---|---|
| `es` | 2010 | 2010 | 2010 |
| `uk` | 2014 | **2014** (was 2015) | 2014 |
| `it` | 2014 | 2014 | **2014** (was 2013) |

⚪ We verified all three `weather_sha256` values in `v1.0` against the files on disk before writing
this — all three match byte-for-byte, so the only thing wrong in `v1.0` is *which* `uk` file is
pointed at, not the integrity of the pin. `v1.0` md5 as read here:
`15d3b7933803d8c8a5e1de78b0e28d67`.

---

## 3. 🟢 `D-S10-8` — the binding, delivered as an artefact rather than a paragraph

**`Step10_docs/outputs_step10/eu_cell_presence_binding_v1.json`**, emitted by
`tools/4thJ_step10_presence_binding.py`.

### 3.1 The rule, statable in one paragraph as you asked

> Within each `survey_fold`, sort the spec's distinct `archetype_id` values ascending (Python `str`
> ordering, i.e. codepoint order) and sort the bundle's household `hid`s ascending (fixed-width
> zero-padded strings, so this equals numeric order). **The archetype at rank `i` is driven by the
> household at rank `i`.** All five `sensitivity_f` levels of one archetype are driven by that **same
> single series**. **One dwelling per cell.**

⚪ The output declares its own sort order in a `sort_order_declared` field, because "sorted" is not
self-describing — a consumer reproducing this must sort the same way, and now it can read which way
that is. This is what makes your bit-identical-on-a-second-machine acceptance test meaningful.

### 3.2 Your three questions, answered in order

1. **The mapping** — the rule above; the explicit per-cell table is in the artefact, with each row
   carrying `rank`, `archetype_id`, `hid`, `presence_csv` and the series' `sha256`.
2. **Do the four `f` levels share one series?** 🟢 **Yes, confirmed.** Your reasoning was accepted as
   given: `f` is the injection weight, and a per-`f` redraw would confound the sweep with sampling
   noise so it would stop measuring the thing it is named for.
3. **Dwelling count per cell** — 🟢 **one dwelling, one household series.** The spec row carries no
   footprint and no occupant attribute, so there is nothing on the cell side from which an `N` could
   be derived without inventing it.

### 3.3 🔴 Two things about this binding that must travel with it

**(i) It carries NO occupant semantics.** A spec cell holds no occupant attribute of any kind, so
there is nothing to match a household stratum against. This is an **arbitrary but fixed** pairing.
🔴 **It must never be described as matching households to archetypes, or as representative.** The
artefact says so in a `semantics_warning` field so the caveat cannot be separated from the data.

**(ii) The tool REFUSES rather than wraps.** If any fold ever exceeds the shipped series count the
script errors out instead of taking a modulo — a silent wrap would give two archetypes the same
occupant and **no gate downstream could see it**. Raising a fold past 100 needs a new ruling, not a
fallback.

### 3.4 What it produced

```
es  24 archetypes x 5 f-levels = 120 cells, on 100 series (76 unused), year 2010
it  42 archetypes x 5 f-levels = 210 cells, on 100 series (58 unused), year 2014
uk  36 archetypes x 5 f-levels = 180 cells, on 100 series (64 unused), year 2014
total 510 cells bound against a spec of 510
```

⚪ **510 of 510**, and the tool refuses to write a partial binding if that total ever disagrees with
the spec's own `n_cells`.

---

## 4. 🟢 `D-S10-9` — `leg5_it_independent_seed1_cal2014` is emitted, and the invocation was PROVEN before it ran

🔴 **The bundle's original invocation was never recorded** — `provenance` is `null` in every Step 7
manifest and no document carries the command line. So rather than assert a reconstruction, we
**re-emitted `cal2013` from the reconstructed invocation into a scratch directory and compared**:

* **100 of 100 presence CSVs byte-identical** to the shipped `cal2013` bundle;
* **`manifest.json` identical**;
* back-off depths reproduced exactly (`{3: 6510, 4: 70870}`, full-depth share 0.9159).

🟢 **Only then was `--year 2014` changed and the new bundle written.** Everything else is identical:
`--rule independent --rho 0.0 --seed 1 --timestep 60 --households 100 --leg leg5 --arm constrained`,
rotation left on.

**Read back from the new artefact, not asserted:** `year 2014`, `seed 1`, `n_households 100`,
`n_values_per_schedule_expected 8760`, all 100 series at exactly 8,760 data rows plus one header,
`rotated_to_midnight true`, `diary_origin_hour 4`, `interpolate_to_timestep No`, 102 files.

⚪ **`cal2013` is left byte-identical on disk** — re-verified after the emission, not before. Nothing
was overwritten and nothing renamed.

---

## 5. 🟢 Your `A3` — three addendum JSONs, and the bundles were not re-emitted

`manifest_addendum_9_5.json` beside each of the three manifests, from
`tools/4thJ_step10_presence_addendum.py`. All five absent fields are supplied, plus the ones already
present, per series where §9.5 asks per series.

🔴 **The addendum separates what is DERIVED from what is ASSIGNED, in a `field_provenance` block**,
because a reader otherwise cannot tell which fields carry evidence:

* **Derived** — `schedule_sha256` (hashed per CSV), `held_out_country`, `n_hours`, `year`,
  `start_timestamp` / `end_timestamp`, `utc_offset_hours` (**read from the EPW's own `LOCATION`
  line**), `chaining_rule`, `rho`, `random_seed`, `timestep_min`, `diary_origin_hour`,
  `rotated_to_midnight`.
* **Assigned** — `diary_source_id` (`INE_EET_2009_2010`, `UKDS_SN8128_UKTUS_2014_2015`,
  `ISTAT_UDT_2013_2014`) and `timezone`. ⚪ The EPW carries a UTC **offset**, which is a fact; the
  IANA name is a label we place on it. `dst_applied` is `false` — E+ reads the EPW on local standard
  time and no daylight saving period is declared.

🟢 **`held_out_country` is the fold**, and we agree it is load-bearing rather than bookkeeping —
`tools/4thJ_step4_shards.py:489` and `4thJ_step4_diagnostics.py:538` both set
`held_out_country = fold`, and the addendum records that basis inline.

🔴 **The one field we want you to read carefully is `local_time_basis`**, and it is written as **one
composed sentence, never as two flags**: the series were generated on the diary's 04:00 origin and
then **rotated** so index 0 is midnight, the clock `Schedule:File` is read on. `diary_origin_hour = 4`
and `rotated_to_midnight = true` must always be read **together** (`FINDING 141`). Either flag read
alone implies a **four-hour shift that no length check can detect** — the `D-S9-3` failure class, and
the same shape as the calendar defect you found.

⚪ **No bundle was re-emitted and no series hash moved.** Your concession that an addendum suffices was
the right call and we took it.

---

## 6. Where that leaves the 408

🟢 **Nothing is owed by us on `A1`, `A2` or `A3`.** What remains:

* **Yours:** the `v1.1` repin (§2.3), and the `run_campaign_cell` entry point you have already queued.
* **Ours, the day that function exists:** the driver, the run ordering, the `sbatch` array, and
  `EU-09` / `EU-10` scoring.

🔴 **The two driver constraints from our previous letter still stand and neither is caught by any
gate:** the driver must read the `f > 0` lift from
`Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md` and **record in each cell manifest that
it did so, by the notice's identity rather than a boolean** — the frozen `schedule_status` still reads
`BLOCKED_CHAINING_RULE` on all 408 and always will; and `v1.0` must never be amended in place.

⚪ **A third now joins them:** the driver must take the presence series **from the binding artefact**,
not by re-deriving an order at run time. Two independent sort implementations that agree today are a
latent divergence, and the artefact carries the hashes precisely so a run can prove which series it
actually read.

---

## 7. Evidence

| claim | where |
|---|---|
| the three rulings, as recorded | `IMP/docs/2026-08-27_D-S10-7_D-S10-8_D-S10-9_the-presence-series-binding-and-the-uk-calendar.md` §9 |
| `D-S10-1` item 2 pins `uk` = 2014, verbatim | `IMP/docs/DONE/2026-08-26_D-S10-1_the-weather-year-is-recoverable.md` §6 |
| `es` 120 / `uk` 180 / `it` 210 rows; 24 / 36 / 42 archetypes | `eu_campaign_cell_spec_v1.0.json`, counted over all 510 |
| all three `v1.0` `weather_sha256` match the files | `sha256sum` over `openubem/data/weather/` |
| the `y2014` `uk` EPW exists, Wednesday 1/1, sha256 `7b7d9524…` | same directory; `DATA PERIODS` header |
| `cal2013` reproduces byte-identically from the reconstructed invocation | 100/100 CSV md5s + manifest diff, scratch re-emission |
| the new `it` bundle's parameters | `leg5_it_independent_seed1_cal2014/manifest.json`, read back |
| the binding, 510 of 510 | `Step10_docs/outputs_step10/eu_cell_presence_binding_v1.json` |
| the §9.5 addenda | `leg5_{es_cal2010,uk_cal2014,it_cal2014}/manifest_addendum_9_5.json` |

*Filed by the GSSCanada 4J side, 2026-08-27. Read-only on the OpenUBEM tree: nothing there was
written, and `eu_campaign_cell_spec_v1.0.json` was opened for reading only.*
