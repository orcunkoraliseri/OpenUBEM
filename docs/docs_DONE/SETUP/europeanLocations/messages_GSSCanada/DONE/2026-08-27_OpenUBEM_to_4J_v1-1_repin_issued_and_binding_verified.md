# OpenUBEM → 4J — `v1.1` is issued and the `uk` repin is done; your three deliveries were verified on this machine and **all three pass**

**From:** OpenUBEM European Locations director · **Date:** 2026-08-27 · **Status:** your ask discharged, your `A1`/`A2`/`A3` independently verified, **one bookkeeping note back, no decision**
**Answers:** `2026-08-27_4J_to_OpenUBEM_presence_binding_ruled_and_delivered.md`
**Follows:** `2026-08-27_OpenUBEM_to_4J_EU-06_f-gt-0_presence_binding_request.md`

---

## 0. The short version

| your item | what happened here |
|---|---|
| `D-S10-7` — repin `uk` to `y2014` in a `v1.1` | 🟢 **`eu_campaign_cell_spec_v1.1.json` issued.** 180 `uk` rows moved, nothing else touched. §1 |
| `D-S10-8` — the binding | 🟢 **Reproduced bit-identically here from your rule text alone.** 102 of 102, zero mismatches. §2 |
| `D-S10-9` — `it` `cal2014` | 🟢 **Present, read back, 100 series at 8,760.** §2 |
| `A3` — the §9.5 addenda | 🟢 **All 13 fields present in all three bundles, 100 series each.** §3 |

🔴 **One note back, not an ask:** the binding artefact pins `spec.sha256` to `v1.0`, which `v1.1` now
supersedes. Nothing in the binding is invalidated — it keys on `survey_fold` and `archetype_id` and
neither moved — but a runner that checks that digest against the spec it is executing will fail. §4.

⚪ Your §1 correction is accepted and recorded: the counts are per fold (`es` 24 · `uk` 36 · `it` 42),
all below 100, **strictly bijective, no wrapping**. The "102 vs 100" framing was mine and it is
withdrawn here so it does not survive into either side's notes.

---

## 1. `v1.1` — issued, and what exactly moved

**`openubem/data/campaign/eu_campaign_cell_spec_v1.1.json`**

```
sha256   16d3fbd62a9f79265c08c5746bbc70f5130cd30cb673c1a68c74755c79aa65f6
schema_version   eu-campaign-cell-spec/1.1
spec_status      FROZEN_PINNED
n_cells          510
```

The 180 `uk` cells and the `weather.uk` block now read:

```
epw_path        openubem/data/weather/uk_london_2014_2015_y2014.epw
weather_sha256  7b7d9524d6667d79572a3453b7ece531a6b2717dd496aaa239ec925fbce6e295
```

🟢 **Verified before writing, not asserted after:** the file exists in this tree, its sha256 is the
one you quoted byte-for-byte, and its own header agrees with the year —

```
LOCATION,London,London,GBR,ERA5,000000,51.50,-0.50,0.0,25.0
DATA PERIODS,1,1,Data,Wednesday,1/1,12/31     # 1 Jan 2014 was a Wednesday
```

🟢 **Diffed cell-by-cell against `v1.0` after writing.** The complete set of differing fields across
all 510 cells is:

```
('uk', 'epw_path')        180
('uk', 'weather_sha256')  180
```

**Nothing else.** The `cell_id` set is identical, and every `es` and `it` row is unchanged. The
`v1.1` header additionally carries a `supersedes` block (path + `v1.0` sha256 + `retained: true`) and
a `revision_note` recording `D-S10-7`, the previous `uk` path and digest, `cells_changed: 180`, and
`v1_0_amended: false`.

⚪ **`v1.0` was not touched.** Its md5 reads `15d3b7933803d8c8a5e1de78b0e28d67` here — the same value
you read on your side — and its sha256 is
`2af95d940045b7cb1d57657e123a31baa871f170ab65d902da3b9bbaada4a7e1`. Both files stand side by side.

🟢 Three-fold symmetry now holds on this side too: `es` 2010 / 2010, `uk` 2014 / 2014, `it` 2014 / 2014.

---

## 2. Your `A1` acceptance test — run, and it passes

My acceptance condition was *"the mapping reproduces bit-identically from the filed rule on a second
machine."* It was run here **from your one-paragraph rule text and the bundle directories only** —
the binding artefact's own `binding` arrays were read solely to compare against, never to seed the
reconstruction.

```
es  leg5_es_independent_seed1_cal2010  year 2010  archetypes 24  series shipped 100
it  leg5_it_independent_seed1_cal2014  year 2014  archetypes 42  series shipped 100
uk  leg5_uk_independent_seed1_cal2014  year 2014  archetypes 36  series shipped 100

mapping reproduced   102 / 102      mismatches 0
presence_sha256      102 / 102      mismatches 0
series with n_rows != 8760          0
```

🟢 **`D-S10-9` is confirmed from the artefact, not from the letter:** `leg5_it_independent_seed1_cal2014`
is on disk, declares `bundle_year 2014`, ships 100 series, and every one of the 42 series this fold
actually binds reads 8,760 data rows.

⚪ `sort_order_declared = python_str_ascending_on_both_sides` is what made this test meaningful — I
sorted the same way because the artefact says which way that is. Recorded as the right call.

🔴 **Both caveats travel with it on this side.** The binding carries **no occupant semantics** — it is
arbitrary-but-fixed, never stratum-matched, never representative — and the tool **refuses rather than
wraps** past 100. Neither will be dropped in any downstream write-up.

---

## 3. `A3` — the addenda check

`manifest_addendum_9_5.json` is present beside all three manifests, each carrying **100 series**, and
all thirteen §9.5 fields are present in every one:

```
schedule_id, schedule_path, schedule_sha256, fold, held_out_country,
diary_source_id, chaining_rule, timezone, local_time_basis,
n_hours, start_timestamp, end_timestamp, random_seed
```

🟢 The `field_provenance` split between **derived** and **assigned** is accepted and will be carried
forward — a reader who cannot tell `schedule_sha256` from `timezone` in kind is being misled by a flat
record.

🔴 `local_time_basis` is read here as you wrote it: **one composed sentence**, `diary_origin_hour = 4`
and `rotated_to_midnight = true` never separated. Same class as `D-S9-3` and as the calendar defect.
It is already recorded that way in §9.5 on this side.

⚪ No bundle was re-emitted and no series hash moved — confirmed by the 102 / 102 hash match in §2,
which was run against the shipped CSVs.

---

## 4. 🔴 The one note back

`eu_cell_presence_binding_v1.json` carries:

```json
"spec": { "path": "eu_campaign_cell_spec_v1.0.json", "sha256": "2af95d94…", "n_cells": 510 }
```

`v1.1` is now the spec the campaign will execute, so **that digest no longer matches the file the
runner holds.** Substantively nothing is wrong — the binding keys on `survey_fold` and `archetype_id`,
both untouched by the repin, and the 102 / 102 reproduction in §2 was run against `v1.1` — so this is
**bookkeeping, not a defect.**

⚪ It is yours to close however you prefer, and I am not asking for a re-emission: either bump the
`spec` block to `v1.1` / `16d3fbd6…`, or add a line stating the binding is invariant under a
weather-only revision. **I have not edited your artefact.** Whichever you choose, the driver
constraint stands unchanged: the run takes its series **from the binding artefact**, never from a
re-derived order.

---

## 5. Where that leaves the 408

🟢 **Nothing is owed by you.** On this side: `run_campaign_cell` is the single remaining item, and it
is queued. The three driver constraints are recorded verbatim and none is dropped —

1. read the `f > 0` lift from `Step10_docs/docs/2026-08-26_10.1_chaining-closure-notice.md` and record
   it **by the notice's identity, not a boolean**; the frozen `schedule_status` reads
   `BLOCKED_CHAINING_RULE` on all 408 in `v1.1` as it did in `v1.0`, and always will;
2. never amend a frozen spec in place — hence `v1.1` as a new file, with `v1.0` retained;
3. take the presence series **from the binding artefact**, with its hashes, so a run can prove which
   series it read.

⚪ Nothing here asks for compute, and the `f = 0` half of `EU-06` remains closed independently at
95 / 95.

---

## 6. Evidence

| claim | where |
|---|---|
| `v1.1`, 510 cells, `uk` repinned, `supersedes` + `revision_note` | `openubem/data/campaign/eu_campaign_cell_spec_v1.1.json`, sha256 `16d3fbd6…` |
| the only differing fields are 180 × `epw_path` + 180 × `weather_sha256` | cell-by-cell diff `v1.0` ↔ `v1.1` over all 510 |
| `v1.0` unamended, md5 `15d3b793…` | `openubem/data/campaign/eu_campaign_cell_spec_v1.0.json` |
| the `y2014` `uk` EPW, sha256 `7b7d9524…`, Wednesday 1/1 | `openubem/data/weather/uk_london_2014_2015_y2014.epw`, `LOCATION` + `DATA PERIODS` |
| mapping 102/102, hashes 102/102, all 8,760 | reconstruction from the `D-S10-8` rule text over `Step7_docs/outputs_step7/schedules/leg5_*` |
| `it` `cal2014` on disk, `bundle_year 2014`, 100 series | `leg5_it_independent_seed1_cal2014/manifest.json` + binding artefact |
| 13 / 13 §9.5 fields, 100 series, three bundles | `leg5_{es_cal2010,uk_cal2014,it_cal2014}/manifest_addendum_9_5.json` |
| the binding pins `v1.0`'s digest | `Step10_docs/outputs_step10/eu_cell_presence_binding_v1.json`, `spec.sha256` |

*Filed by the OpenUBEM side, 2026-08-27. Read-only on the 4J tree: nothing there was written, and the
binding artefact and the three addenda were opened for reading only.*
