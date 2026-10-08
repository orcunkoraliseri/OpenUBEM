# Decision request: D-EU-20 — which OpenUBEM-side work package resumes first

**Status:** RULED — CLOSED 2026-08-27 (Option A)
**Opened:** 2026-08-27
**Ruled:** 2026-08-27 by Project Lead / Evaluator
**Raised by:** director, at the owner's request (*"il y a beaucoup de choses à compléter, guide moi"*)
**Blocks:** nothing is running; this decision decides what starts.

---

## 0. Ruling

**RULED 2026-08-27 — Option A: resume `EU-04`, close `S2` acceptance, then take `S3`.** Signed by
*Project Lead / Evaluator*; the completed approval block is §5.

The owner's dependency reading agrees with §2 of this request on every point: `EU-08`/`EU-09`/`EU-10`
sit inside GSSCanada's execution perimeter (conditioned on the 510 campaign cells); `EU-06` `f>0` is
blocked upstream by the Step 7 chaining rule (`D-EU-09`) and is **outside OpenUBEM's perimeter**;
`EU-05` follows directly from the geometry samples `EU-04` forms; and `EU-04` has all its data on disk
and is **the only work package actionable in full autonomy**.

**The ruling is explicitly two-step, and the order is binding:**

1. **Formalise the `S2` acceptance** against its promotion rule ("stable outputs and measured
   resources") on the authoritative `s2_campaign_v3/` bundle. **No new simulation.**
2. **Open a decision request for the `S3` French typology balance rule** — the `SFH` ceiling of 7 in
   the Lyon study area — **before** the 96-building `S3` manifest is generated or frozen.

**Executed the same day.** Step 1 produced
`docs/docs_ACTIVE/europeanLocations/ACCEPTANCE_S2_promotion_2026-08-27.md`;
step 2 opened `docs/docs_ACTIVE/europeanLocations/debugs/docs/DONE-docs/DECISION_REQUEST_D-EU-21_s3_fr_balance_2026-08-27.md`.
`S3` is therefore **not started and must not be started** until `D-EU-21` is ruled.

---

## 1. Why this decision exists

§9.4 — the boundary contract — was **signed and frozen** on 2026-08-27
(`eu_campaign_cell_spec_v1.0.json`, `FROZEN_PINNED`, `510 510 22 FROZEN`, all four weather folds
pinned). **That is not the closure of the MVP.** Six work packages remain *In progress* in MVP §9.7,
and they do not all have the same owner:

| WP | Owner of what remains | Can it start today? |
|---|---|---|
| `EU-04` | **OpenUBEM** | **Yes** |
| `EU-05` | **OpenUBEM** | Partly — its `S1`–`S3` acceptance rides on `EU-04`'s samples |
| `EU-06` | **OpenUBEM** for `f=0`; **upstream Step 7** for `f>0` | **No** for `f>0` |
| `EU-08` / `EU-09` / `EU-10` | **GSSCanada** | No — they need the 510 cells executed |

An earlier director note said every remaining work package merely awaited GSSCanada. **That was
wrong and is corrected** in the MVP §9.7 arc-status blockquote; it was true only of `EU-08`–`EU-10`.

---

## 2. What each candidate actually is, measured

### `EU-04` — dwelling/core layout adapter

**Done and evidenced.** `S0` complete across all four residential typologies (ES SFH, FR TH, ES MFH,
ES AB) with a no-severe-diagnostic assertion. `S1` ran 2026-08-25 and **met its ladder criterion**
("12/12 accounted for; failures classified"): **8** `NON_CONVEX_FOOTPRINT` refusals, **3**
`NARROW_FOOTPRINT_LT_8M` fallbacks, **1** `DWELLING_LAYOUT_EMITTED`, and — after the 2026-08-26
correction — **12 of 12 `EPLUS_COMPLETED`**. `S2` ran: **31/31** EnergyPlus runs returned 0, severe
0, fatal 0 (`EU-04/s2_campaign_manifest.csv`), headline restated twice to **60.7087 kWh/m²**
(`s2_campaign_v3/`, the authoritative bundle).

**What remains.** `S2` has *run* but its promotion rule — *"stable outputs and measured resources"* —
has never been **declared met**; and `S3` (96 observed buildings, annual controlled baseline) has not
started. `GEO-08` Grasshopper parity is deferred by ruling `D-EU-04-F` until after `S1`–`S3`.

🔴 **Known obstruction inside `S3`, already measured:** `S3` **cannot be typology-balanced for
France** — `SFH` caps at **7** buildings in the Lyon quarter. This was accepted as a consequence when
`D-EU-04-G` was ruled, but the balance rule `S3` should use instead has **never been ruled**. Picking
`EU-04` therefore buys one further decision, not zero.

### `EU-05` — residential HVAC/ventilation adapter

**Done and evidenced.** 102 ES/GB/IT heating-only, constant-air, all-convective control records
audited; the runnable `S0` SFH fixture passes EnergyPlus zone sizing with a nonzero design heating
load; control objects namespaced per zone; `F_red_temp` ruled Option 1 (strictly positive source
multiplier).

**What remains.** `S1`–`S3` and dwelling/core acceptance. **These are the same `S1`–`S3` samples
`EU-04` owns** — `EU-05` cannot reach its acceptance on samples `EU-04` has not formed. It is a
follower, not an independent start.

### `EU-06` — external occupancy schedule adapter

**Done and evidenced.** The `f=0` schedule-file path is locally tested. The `f=0` control is the only
level OpenUBEM has ever executed and is the level against which any non-zero `f` result must be read.

🔴 **`f>0` is NOT ours to unblock.** Every non-zero level is stamped `BLOCKED_CHAINING_RULE`. That
block is **`D-EU-09` = parent Step 7 open decision 14 (chaining rule)**, and the MVP states it
explicitly: *"that block is D-EU-09, upstream in Step 7, and it is **not** OpenUBEM's to lift"*
(`MVP_european_locations.md:1563`; see also `:1124`, `:1178`, `:1213`). Without a ruled chaining
convention there is no annual schedule to run, and if chaining sensitivity exceeds 25 % on peak
demand the campaign is partly measuring the convention — which the Step 8 gates cannot separate.

⚠️ **The director's own chat recommendation of 2026-08-27 named `EU-06` as the one to resume first.
That recommendation is withdrawn here**, on re-reading `:1563`: `EU-06` is the one candidate that
cannot be started by this project at all. It is recorded rather than deleted.

---

## 3. Options

**Option A — resume `EU-04`, close `S2` acceptance, then take `S3`.** *(recommended)*
The only candidate whose next step is entirely inside this project and has all its inputs on disk.
`S2` needs a declaration against its own promotion rule, not new machinery. Unblocks `EU-05`'s
acceptance as a by-product, since they share the ladder.
*Cost:* one further ruling on the `S3` French balance rule before `S3` can be formed.

**Option B — resume `EU-05` first.**
Possible only for the parts that do not need `S1`–`S3` samples. Its stated remaining scope is
precisely `S1`–`S3` plus dwelling/core acceptance, so this option is mostly waiting on Option A.

**Option C — resume `EU-06` `f>0`.**
**Not available.** Requires a Step 7 ruling this project cannot take. What *is* available under
`EU-06` is nothing new — the `f=0` path is already tested.

**Option D — declare OpenUBEM-side work parked and hand the whole MVP to GSSCanada.**
Legitimate and cheap. It makes MVP §9.7 honest in one direction (nothing is owed here) at the cost of
leaving `EU-04`/`EU-05` permanently *In progress*, and leaves `S3` — the only annual controlled
baseline in the ladder — never run.

---

## 4. Recommendation

**Option A.** It is the only start with no external dependency, its inputs are on disk, and it is the
prerequisite for `EU-05`. It should be taken in two steps so the French balance question is not
smuggled into an execution task:

1. **`S2` acceptance declaration only** — measure the run against its promotion rule ("stable outputs
   and measured resources") on `s2_campaign_v3/` and declare it met or not met. No new simulation.
2. **`S3` scoping** — return a decision request for the French balance rule (`SFH` caps at 7) before
   any `S3` sample is frozen. **Do not select the sample on the outcome being tested** — the mistake
   `D-EU-04-H` was opened to prevent.

---

## 5. Owner response

```
D-EU-20 ruling: Option A (resume EU-04, close S2 acceptance, then take S3)
(A = EU-04 / B = EU-05 / C = EU-06 / D = park OpenUBEM-side work)

Notes: Option A approved.
1. Formalize the S2 acceptance declaration against its promotion rule ("stable outputs and measured resources") based on the authoritative s2_campaign_v3/ bundle (31/31 rc 0, severe 0, fatal 0; 60.7087 kWh/m²).
2. Open a decision request for the S3 French typology balance rule (handling the SFH ceiling of 7 in the Lyon dataset) before freezing the 96-building S3 manifest.

Owner name / initials: Project Lead / Evaluator
Date: 2026-08-27
```

*Evidence: MVP §9.7 Table 9 (`MVP_european_locations.md:688-703`), §9.7.3 work-package notes
(`:767-789`), Table 10 sample ladder (`:725-733`), chaining block (`:1124`, `:1178`, `:1213`,
`:1563`), `openubem/outputs/eu_evidence/EU-04/s2_campaign_v3/`.*
